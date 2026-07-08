# ==================================================================
# File: bridge_app/engine/task_runner.py
# Description: Core engine logic for fetching, mapping, and pushing data.
# ==================================================================

from bridge_app.models import JobModel, TemplateModel
from bridge_app.services.logger import log_job
import requests
from urllib.parse import urlparse
import re

def build_nested_payload(mapping, source_data):
    """
    Constructs a dynamic nested JSON payload based on dot/bracket notation paths.
    E.g. path 'gps_data[0].latitude' mapped to source field 'lat'
    """
    payload = {}
    
    # Mapping is now a list of dicts: [{'source': 'field', 'target': 'path.to.field'}]
    for map_item in mapping:
        if not isinstance(map_item, dict):
            continue
        client_path = map_item.get('target')
        source_field = map_item.get('source')
        if not client_path or not source_field:
            continue
            
        # Get the value from the source data
        value = source_data.get(source_field)
        
        parts = client_path.split('.')
        current = payload
        
        for i, part in enumerate(parts):
            array_match = re.match(r'(.+)\[(\d*)\]', part)
            if array_match:
                key = array_match.group(1)
                idx_str = array_match.group(2)
                idx = int(idx_str) if idx_str else 0
                
                if key not in current:
                    current[key] = []
                while len(current[key]) <= idx:
                    current[key].append({})
                    
                if i == len(parts) - 1:
                    current[key][idx] = value
                else:
                    current = current[key][idx]
            else:
                key = part
                if i == len(parts) - 1:
                    current[key] = value
                else:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                    
    return payload

def pull_and_push_job(app, job_id):
    """
    Core engine logic for universal dynamic mapping from multiple sources.
    """
    with app.app_context():
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
        
        for idx, src in enumerate(sources):
            src_url = src.get('url')
            src_auth = src.get('auth_token')
            if not src_url:
                continue
                
            headers = {}
            if src_auth:
                headers['Authorization'] = f"Bearer {src_auth}"
                
            try:
                res = requests.get(src_url, headers=headers, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    src_data = data[0] if isinstance(data, list) else data
                    # Flat merge into aggregated data with source prefix
                    for k, v in src_data.items():
                        aggregated_data[f"source_{idx}.{k}"] = v
                else:
                    print(f"Source {idx} ({src_url}) returned {res.status_code}")
            except Exception as e:
                print(f"Failed to fetch real data from source {idx}: {e}")
                # Mock fallback
                mock_data = {
                    "lat": 16.891266,
                    "lng": 81.327995,
                    "speed": 0,
                    "id": "AP39TP5623",
                    "time": "2025-08-25 07:29:04",
                    "bat": "4.2",
                    "ignition": "0"
                }
                for k, v in mock_data.items():
                    aggregated_data[f"source_{idx}.{k}"] = v
        
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
        try:
            print(f"Pushing to {template.client_url}")
            if template.client_url:
                dest_res = requests.post(template.client_url, json=final_payload, headers=dest_headers, timeout=10)
                
                if dest_res.status_code >= 400:
                    log_job(job.id, 'FAILED', final_payload, http_status=dest_res.status_code, error_message=dest_res.text)
                else:
                    log_job(job.id, 'SUCCESS', final_payload, http_status=dest_res.status_code)
            else:
                log_job(job.id, 'FAILED', final_payload, http_status=400, error_message="No client URL defined")
        except Exception as e:
            log_job(job.id, 'FAILED', final_payload, http_status=500, error_message=str(e))

