# ==================================================================
# File: bridge_app/engine/task_runner.py
# Description: APScheduler background task executor for jobs.
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
            if not src_url:
                return {}
            
            headers = {}
            if src_auth:
                headers['Authorization'] = f"Bearer {src_auth}"
            
            local_aggregated = {}
            try:
                res = requests.get(src_url, headers=headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    src_data = data[0] if isinstance(data, list) else data
                    # Flat merge into aggregated data with source prefix
                    for k, v in src_data.items():
                        local_aggregated[f"source_{idx}.{k}"] = v
                else:
                    print(f"Source {idx} ({src_url}) returned {res.status_code}")
            except Exception as e:
                print(f"Failed to fetch real data from source {idx}: {e}")
                # Removing mock fallback to avoid injecting fake data in production
                local_aggregated = {}
            return local_aggregated

        # Launch concurrent requests for all sources
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(sources) if sources else 1) as executor:
            future_to_src = {executor.submit(fetch_source_data, idx, src): idx for idx, src in enumerate(sources)}
            for future in concurrent.futures.as_completed(future_to_src):
                local_data = future.result()
                aggregated_data.update(local_data)
    
        # --- 2. Transform Data ---
        mapping = t_dict.get('field_mapping', [])
        if mapping:
            final_payload = build_nested_payload(mapping, aggregated_data)
        else:
            final_payload = aggregated_data
        
        # --- 3. Authenticate with Destination ---
        dest_headers = {'Content-Type': 'application/json'}
        if template.client_auth_type == 'custom_login':
            creds = t_dict.get('client_credentials', {})
            email = creds.get('email')
            password = creds.get('password')
        
            parsed_url = urlparse(template.client_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            auth_url = f"{base_url}/api/v1/login"
        
            try:
                auth_res = requests.post(auth_url, json={"email": email, "password": password}, timeout=10)
                if auth_res.status_code == 200:
                    token = auth_res.json().get('token')
                    dest_headers['Authorization'] = f"Bearer {token}"
                else:
                    log_job(job.id, 'FAILED', final_payload, http_status=auth_res.status_code, error_message="Auth Failed")
                    return
            except Exception as e:
                log_job(job.id, 'FAILED', final_payload, http_status=500, error_message=f"Auth Request Failed: {e}")
                return
        elif template.client_auth_type == 'bearer':
            creds = t_dict.get('client_credentials', {})
            token = creds.get('token')
            if token:
                dest_headers['Authorization'] = f"Bearer {token}"

        # --- 4. Push to Destination ---
        creds = t_dict.get('client_credentials', {})
        req_timeout = creds.get('timeout', 30)
        req_retries = creds.get('retries', 3)

        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        session = requests.Session()
        retry_strategy = Retry(
            total=req_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
    
        try:
            print(f"Pushing to {template.client_url}")
            if template.client_url:
                dest_res = session.post(template.client_url, json=final_payload, headers=dest_headers, timeout=req_timeout)
            
                if dest_res.status_code >= 400:
                    error_msg = dest_res.text
                    log_job(job.id, 'FAILED', final_payload, http_status=dest_res.status_code, error_message=error_msg)
                
                    # Queue failed payload
                    from bridge_app.models.failed_payload import FailedPayload
                    from bridge_app.extensions import db
                    fp = FailedPayload(job_id=job.id, template_id=template.id, payload_json=json.dumps(final_payload), error_message=error_msg)
                    db.session.add(fp)
                    db.session.commit()
                else:
                    log_job(job.id, 'SUCCESS', final_payload, http_status=dest_res.status_code)
            else:
                log_job(job.id, 'FAILED', final_payload, http_status=400, error_message="No client URL defined")
        except Exception as e:
            error_msg = str(e)
            log_job(job.id, 'FAILED', final_payload, http_status=500, error_message=error_msg)
        
            # Queue failed payload
            from bridge_app.models.failed_payload import FailedPayload
            from bridge_app.extensions import db
            fp = FailedPayload(job_id=job.id, template_id=template.id, payload_json=json.dumps(final_payload), error_message=error_msg)
            db.session.add(fp)
            db.session.commit()


def execute_template_mapping(template_id):
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
            if not src_url:
                return {}
            
            headers = {}
            if src_auth:
                headers['Authorization'] = f"Bearer {src_auth}"
            
            local_aggregated = {}
            try:
                res = requests.get(src_url, headers=headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    src_data = data[0] if isinstance(data, list) else data
                    for k, v in src_data.items():
                        local_aggregated[f"source_{idx}.{k}"] = v
                else:
                    print(f"Pull mode source {idx} ({src_url}) returned {res.status_code}")
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
        mapping = t_dict.get('field_mapping', [])
        if mapping:
            final_payload = build_nested_payload(mapping, aggregated_data)
        else:
            final_payload = aggregated_data
        
        return final_payload


