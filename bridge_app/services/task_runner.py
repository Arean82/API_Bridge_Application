# ==================================================================
# File: bridge_app/services/task_runner.py
# Description: APScheduler background task executor for jobs.
#
# Copyright (C) 2026 Arean Narrayan - SynoraStudio
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==================================================================

from bridge_app.models import JobModel, TemplateModel
from bridge_app.services.logger import log_job
import requests
from urllib.parse import urlparse
import re
import json
from bridge_app.services.data_transform import build_nested_payload


def pull_and_push_job(job_id):
    from bridge_app.app import current_app_instance
    if not current_app_instance:
        from bridge_app.app import create_app
        current_app_instance = create_app()
    with current_app_instance.app_context():
        """
        Core engine logic for universal dynamic mapping from multiple sources.
        """
        job = JobModel.query.get(job_id)
        if not job or not job.is_active or not job.template:
            return
        
        template = job.template
        t_dict = template.to_dict()
        print(f"Starting job {job_id} for template {template.name}")
    
        # --- 1. Fetch from Source APIs ---
        sources = t_dict.get('sources', [])
    
        # Backward compatibility
        if not sources and template.partner_url:
            sources = [{'name': 'Legacy', 'url': template.partner_url, 'auth_token': template.partner_auth_token}]
        
        aggregated_data = {}
    
        import concurrent.futures

        def fetch_source_data(idx, src):
            src_url = src.get('url')
            src_auth = src.get('auth_token')
            src_method = src.get('method', 'GET').upper()
            if not src_url:
                return {}
            
            headers = {}
            if src_auth:
                headers['Authorization'] = f"Bearer {src_auth}"
            
            local_aggregated = {}
            try:
                res = requests.request(src_method, src_url, headers=headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    src_data = data[0] if isinstance(data, list) else data
                    # Flat merge into aggregated data with source prefix
                    for k, v in src_data.items():
                        local_aggregated[f"source_{idx}.{k}"] = v
                else:
                    print(f"Source {idx} ({src_method} {src_url}) returned {res.status_code}")
            except Exception as e:
                print(f"Failed to fetch real data from source {idx}: {e}")
                local_aggregated = {}
            return local_aggregated

        # Launch concurrent requests for all sources
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(sources) if sources else 1) as executor:
            future_to_src = {executor.submit(fetch_source_data, idx, src): idx for idx, src in enumerate(sources)}
            for future in concurrent.futures.as_completed(future_to_src):
                local_data = future.result()
                aggregated_data.update(local_data)
    
        # --- 2. Live WebSocket Broadcast ---
        try:
            from bridge_app.extensions import socketio
            socketio.emit(f'feed_{template.id}', {'template_id': template.id, 'data': aggregated_data}, namespace='/ws')
        except Exception as e:
            print(f"WebSocket broadcast failed: {e}")
            
        # --- 3 & 4. Map & Push to Destinations ---
        destinations = t_dict.get('destinations', [])
        # Backward compatibility
        if not destinations and template.client_url:
            destinations = [{
                'url': template.client_url,
                'method': 'POST',
                'auth_type': template.client_auth_type,
                'credentials': t_dict.get('client_credentials', {}),
                'field_mapping': t_dict.get('field_mapping', [])
            }]
            
        for dest in destinations:
            dest_url = dest.get('url')
            if not dest_url:
                continue
                
            mapping = dest.get('field_mapping', [])
            if mapping:
                final_payload = build_nested_payload(mapping, aggregated_data)
            else:
                final_payload = aggregated_data

            dest_method = dest.get('method', 'POST').upper()
            dest_auth_type = dest.get('auth_type', 'none')
            creds = dest.get('credentials', {})
            
            dest_headers = {'Content-Type': 'application/json'}
            if dest_auth_type == 'custom_login':
                email = creds.get('email')
                password = creds.get('password')
                parsed_url = urlparse(dest_url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                auth_url = f"{base_url}/api/v1/login"
                try:
                    auth_res = requests.post(auth_url, json={"email": email, "password": password}, timeout=10)
                    if auth_res.status_code == 200:
                        token = auth_res.json().get('token')
                        dest_headers['Authorization'] = f"Bearer {token}"
                    else:
                        log_job(job.id, 'FAILED', final_payload, http_status=auth_res.status_code, error_message=f"Auth Failed for {dest_url}")
                        continue
                except Exception as e:
                    log_job(job.id, 'FAILED', final_payload, http_status=500, error_message=f"Auth Request Failed for {dest_url}: {e}")
                    continue
            elif dest_auth_type == 'bearer':
                token = creds.get('token')
                if token:
                    dest_headers['Authorization'] = f"Bearer {token}"
                    
            req_timeout = creds.get('timeout', 30)
            req_retries = creds.get('retries', 3)

            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            session = requests.Session()
            retry_strategy = Retry(
                total=req_retries,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST", "PUT", "PATCH", "DELETE", "GET"],
                backoff_factor=1
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
        
            try:
                print(f"Pushing to {dest_url} via {dest_method}")
                dest_res = session.request(dest_method, dest_url, json=final_payload, headers=dest_headers, timeout=req_timeout)
                
                # --- Universal Audit Engine ---
                status_flag = 'SUCCESS' if dest_res.status_code < 400 else 'FAILED'
                from bridge_app.services.logger import log_audit
                log_audit(
                    mode='PUSH',
                    caller=f"Job-{job.id}",
                    payload=final_payload,
                    endpoint=dest_url,
                    template_id=template.id,
                    status=status_flag
                )
                # ------------------------------
                if dest_res.status_code >= 400:
                    error_msg = dest_res.text
                    log_job(job.id, 'FAILED', final_payload, http_status=dest_res.status_code, error_message=f"[{dest_url}] {error_msg}")
                    
                    from bridge_app.models.failed_payload import FailedPayload
                    from bridge_app.extensions import db
                    fp = FailedPayload(job_id=job.id, template_id=template.id, payload_json=json.dumps(final_payload), error_message=f"[{dest_url}] {error_msg}")
                    db.session.add(fp)
                    db.session.commit()
                else:
                    log_job(job.id, 'SUCCESS', final_payload, http_status=dest_res.status_code)
            except Exception as e:
                error_msg = str(e)
                log_job(job.id, 'FAILED', final_payload, http_status=500, error_message=f"[{dest_url}] {error_msg}")
            
                from bridge_app.models.failed_payload import FailedPayload
                from bridge_app.extensions import db
                fp = FailedPayload(job_id=job.id, template_id=template.id, payload_json=json.dumps(final_payload), error_message=f"[{dest_url}] {error_msg}")
                db.session.add(fp)
                db.session.commit()


def execute_template_mapping(template_id, destination_slug=None):
    from bridge_app.models.template import TemplateModel
    from bridge_app.app import current_app_instance
    import json
    import concurrent.futures
    
    with current_app_instance.app_context():
        template = TemplateModel.query.get(template_id)
        if not template:
            return None
        
        t_dict = template.to_dict()
        sources = t_dict.get('sources', [])
        
        # Backward compatibility
        if not sources and template.partner_url:
            sources = [{'name': 'Legacy', 'url': template.partner_url, 'auth_token': template.partner_auth_token}]
        
        aggregated_data = {}

        def fetch_source_data(idx, src):
            src_url = src.get('url')
            src_auth = src.get('auth_token')
            src_method = src.get('method', 'GET').upper()
            if not src_url:
                return {}
            
            headers = {}
            if src_auth:
                headers['Authorization'] = f"Bearer {src_auth}"
            
            local_aggregated = {}
            try:
                res = requests.request(src_method, src_url, headers=headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    src_data = data[0] if isinstance(data, list) else data
                    for k, v in src_data.items():
                        local_aggregated[f"source_{idx}.{k}"] = v
                else:
                    print(f"Pull mode source {idx} ({src_method} {src_url}) returned {res.status_code}")
            except Exception as e:
                print(f"Pull mode fetch error on {src_url}: {e}")
                local_aggregated = {}
            return local_aggregated

        # Launch concurrent requests for all sources
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(len(sources), 1)) as executor:
            future_to_src = {executor.submit(fetch_source_data, idx, src): idx for idx, src in enumerate(sources)}
            for future in concurrent.futures.as_completed(future_to_src):
                local_data = future.result()
                aggregated_data.update(local_data)
        
        # Transform payload using field mapping
        destinations = t_dict.get('destinations', [])
        mapping = []
        if destination_slug:
            for d in destinations:
                d_slug = re.sub(r'[^a-z0-9]', '_', d.get('name', '').lower())
                if d_slug == destination_slug:
                    mapping = d.get('field_mapping', [])
                    break
        elif destinations:
            # Fallback to first destination if none specified
            mapping = destinations[0].get('field_mapping', [])

        if mapping:
            final_payload = build_nested_payload(mapping, aggregated_data)
        else:
            final_payload = aggregated_data
        
        return final_payload


