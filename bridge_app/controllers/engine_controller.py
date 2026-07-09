# ==================================================================
# File: bridge_app/controllers/engine_controller.py
# Description: Internal API endpoints for managing configurations and scheduling.
# ==================================================================

from flask import Blueprint, request, jsonify, current_app
import json
from bridge_app.models import TemplateModel, JobModel
from bridge_app.extensions import db, scheduler
from bridge_app.services.task_runner import pull_and_push_job

def fix_swagger_urls(data, source_url):
    from urllib.parse import urlparse
    import json
    import re
    
    parsed = urlparse(source_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    if 'servers' in data:
        for server in data['servers']:
            if server.get('url', '').startswith('/'):
                server['url'] = base_url + server['url']
    elif 'host' not in data:
        data['host'] = parsed.netloc
        if 'schemes' not in data:
            data['schemes'] = [parsed.scheme]
            
    if 'info' in data and isinstance(data['info'], dict) and data['info'].get('description'):
        import re
        # Replace relative markdown links like `](/open-api...)` with absolute ones `](https://base_url/open-api...)`
        data['info']['description'] = re.sub(r'\]\(/', f']({base_url}/', data['info']['description'])
        # Rename the confusing text link from "[Try it out]" to "[API Documentation]"
        data['info']['description'] = data['info']['description'].replace('[Try it out]', '[API Documentation]')
        
    return json.dumps(data)

def fetch_swagger_json(url):
    import requests
    import re
    from urllib.parse import urljoin
    import json
    
    resp = requests.get(url, timeout=10)
    if not resp.ok:
        raise ValueError(f"HTTP {resp.status_code}")
        
    try:
        data = resp.json()
        return fix_swagger_urls(data, url), url
    except Exception:
        html = resp.text
        match = re.search(r'url:\s*["\']([^"\']+)["\']', html)
        if match:
            json_url = urljoin(url, match.group(1))
            resp2 = requests.get(json_url, timeout=10)
            if not resp2.ok:
                raise ValueError(f"Extracted JSON URL {json_url} but got HTTP {resp2.status_code}")
            try:
                data = resp2.json()
                return fix_swagger_urls(data, json_url), json_url
            except Exception:
                pass
        raise ValueError("URL does not return valid JSON and no Swagger URL could be extracted.")

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/templates', methods=['GET'])
def get_templates():
    templates = TemplateModel.query.all()
    return jsonify([t.to_dict() for t in templates])

@api_bp.route('/templates', methods=['POST'])
def create_template():
    data = request.json
    new_template = TemplateModel(
        name=data.get('name'),
        client_name=data.get('client_name'),
        partner_url=data.get('partner_url'),
        partner_auth_token=data.get('partner_auth_token'),
        sources_json=json.dumps(data.get('sources', [])),
        client_url=data.get('client_url'),
        client_auth_type=data.get('client_auth_type', 'none'),
        client_credentials_json=json.dumps(data.get('client_credentials', {})),
        field_mapping_json=json.dumps(data.get('field_mapping', {}))
    )
    db.session.add(new_template)
    db.session.commit()
    
    if data.get('schedule_immediately'):
        schedule_interval = data.get('schedule_interval', 60)
        new_job = JobModel(
            template_id=new_template.id,
            schedule_interval=schedule_interval
        )
        db.session.add(new_job)
        db.session.commit()
        
        app = current_app._get_current_object()
        job_id = f"job_{new_job.id}"
        scheduler.add_job(
            id=job_id, 
            func=pull_and_push_job, 
            args=[app, new_job.id], 
            trigger='interval', 
            seconds=new_job.schedule_interval
        )
        
    return jsonify(new_template.to_dict()), 201

@api_bp.route('/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    data = request.json
    template = TemplateModel.query.get_or_404(template_id)
    
    template.name = data.get('name', template.name)
    template.partner_url = data.get('partner_url', template.partner_url)
    template.partner_auth_token = data.get('partner_auth_token', template.partner_auth_token)
    if 'sources' in data:
        template.sources_json = json.dumps(data.get('sources'))
    template.client_url = data.get('client_url', template.client_url)
    template.client_auth_type = data.get('client_auth_type', template.client_auth_type)
    if 'client_credentials' in data:
        template.client_credentials_json = json.dumps(data.get('client_credentials'))
    if 'field_mapping' in data:
        template.field_mapping_json = json.dumps(data.get('field_mapping'))
        
    db.session.commit()
    return jsonify(template.to_dict()), 200

@api_bp.route('/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    template = TemplateModel.query.get_or_404(template_id)
    jobs = JobModel.query.filter_by(template_id=template_id).all()
    for job in jobs:
        try:
            scheduler.remove_job(f"job_{job.id}")
        except Exception:
            pass
        db.session.delete(job)
    db.session.delete(template)
    db.session.commit()
    return jsonify({"success": True}), 200

@api_bp.route('/jobs', methods=['GET'])
def get_jobs():
    jobs = JobModel.query.all()
    return jsonify([j.to_dict() for j in jobs])

@api_bp.route('/jobs', methods=['POST'])
def create_job():
    data = request.json
    template_id = data.get('template_id')
    schedule_interval = data.get('schedule_interval', 60)
    
    new_job = JobModel(
        template_id=template_id,
        schedule_interval=schedule_interval
    )
    db.session.add(new_job)
    db.session.commit()
    
    app = current_app._get_current_object()
    job_id = f"job_{new_job.id}"
    scheduler.add_job(
        id=job_id, 
        func=pull_and_push_job, 
        args=[app, new_job.id], 
        trigger='interval', 
        seconds=new_job.schedule_interval
    )
    
    return jsonify(new_job.to_dict()), 201

@api_bp.route('/test_mapping', methods=['POST'])
def test_mapping():
    data = request.json
    mapping_list = data.get('mapping', [])
    sample_payload = {}
    
    for map_item in mapping_list:
        if not isinstance(map_item, dict):
            continue
        client_path = map_item.get('target')
        source_field = map_item.get('source')
        if not client_path or not source_field:
            continue
            
        import re
        parts = client_path.split('.')
        current = sample_payload
        
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
                    current[key][idx] = f"<Sample {source_field}>"
                else:
                    current = current[key][idx]
            else:
                key = part
                if i == len(parts) - 1:
                    current[key] = f"<Sample {source_field}>"
                else:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                    
    return jsonify({"sample_payload": sample_payload})

@api_bp.route('/docs', methods=['GET'])
def get_api_docs():
    """Parses swagger docs from either a connection_id or the local sample/api-docs.json"""
    import os
    connection_id = request.args.get('connection_id')
    docs = None
    
    if connection_id:
        from bridge_app.models import SwaggerConnection
        conn = SwaggerConnection.query.get(connection_id)
        if conn:
            if conn.is_local_file and conn.local_file_path:
                try:
                    with open(conn.local_file_path, 'r') as f:
                        docs = json.load(f)
                except:
                    pass
            elif conn.json_content:
                try:
                    docs = json.loads(conn.json_content)
                except:
                    pass

    if not docs:
        return jsonify([]), 200
            
    try:
            
        endpoints = []
        paths = docs.get('paths', {})
        for path_name, path_data in paths.items():
            # Usually look for 'get' or 'post' for response schemas
            method = path_data.get('get') or path_data.get('post')
            if not method:
                continue
                
            fields = []
            # Extract fields from the response schema (simplified parsing for swagger 3.0)
            try:
                schema = method['responses']['200']['content']['application/json']['schema']
                
                # Resolve ref
                def resolve_ref(ref_str, full_docs):
                    parts = ref_str.split('/')
                    curr = full_docs
                    for p in parts:
                        if p == '#': continue
                        curr = curr.get(p, {})
                    return curr.get('properties', {})
                
                if schema.get('type') == 'array':
                    items = schema.get('items', {})
                    if '$ref' in items:
                        props = resolve_ref(items['$ref'], docs)
                    else:
                        props = items.get('properties', {})
                else:
                    if '$ref' in schema:
                        props = resolve_ref(schema['$ref'], docs)
                    else:
                        props = schema.get('properties', {})
                    
                fields = list(props.keys())
            except Exception:
                pass
                
            endpoints.append({
                'name': method.get('summary', path_name),
                'path': path_name,
                'fields': fields
            })
            
        return jsonify(endpoints)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/config/theme', methods=['POST'])
def update_theme():
    """Saves the UI theme and color mode to config.ini"""
    from bridge_app.config import set_theme
    data = request.json
    theme_name = data.get('theme', 'default')
    color_mode = data.get('colorMode', 'auto')
    set_theme(theme_name, color_mode)
    return jsonify({"status": "success"})

# --- Swagger Connections CRUD ---
@api_bp.route('/connections', methods=['GET'])
def get_connections():
    from bridge_app.models import SwaggerConnection
    connections = SwaggerConnection.query.all()
    return jsonify([c.to_dict() for c in connections])

@api_bp.route('/connections', methods=['POST'])
def add_connection():
    from bridge_app.models import SwaggerConnection
    from bridge_app.extensions import db
    import requests
    data = request.json
    
    conn = SwaggerConnection(
        name=data.get('name'),
        url=data.get('url'),
        is_local_file=data.get('is_local_file', False),
        local_file_path=data.get('local_file_path'),
        json_content=data.get('json_content'),
        auth_token=data.get('auth_token'),
        sync_schedule=data.get('sync_schedule'),
        environments=data.get('environments')
    )
    
    # Fetch initial JSON if URL provided
    error_message = None
    if conn.url and not conn.is_local_file:
        try:
            json_text, actual_url = fetch_swagger_json(conn.url)
            conn.json_content = json_text
            conn.is_active = True
        except ValueError as e:
            conn.is_active = False
            error_message = f"Failed to fetch Swagger JSON: {str(e)}"
        except Exception as e:
            conn.is_active = False
            error_message = f"Failed to fetch Swagger JSON: {str(e)}"
    elif conn.is_local_file and conn.json_content:
        if conn.url:
            try:
                import json
                data = json.loads(conn.json_content)
                conn.json_content = fix_swagger_urls(data, conn.url)
            except Exception:
                pass
        conn.is_active = True

    db.session.add(conn)
    db.session.commit()
    
    res = conn.to_dict()
    if error_message:
        res["warning"] = error_message
        
    return jsonify(res)

@api_bp.route('/connections/<int:id>', methods=['DELETE'])
def delete_connection(id):
    from bridge_app.models import SwaggerConnection
    from bridge_app.extensions import db
    conn = SwaggerConnection.query.get_or_404(id)
    db.session.delete(conn)
    db.session.commit()
    return jsonify({"status": "deleted"})

@api_bp.route('/connections/<int:id>', methods=['PUT'])
def update_connection(id):
    from bridge_app.models import SwaggerConnection
    from bridge_app.extensions import db
    import requests
    from datetime import datetime
    
    conn = SwaggerConnection.query.get_or_404(id)
    data = request.json
    
    conn.name = data.get('name', conn.name)
    conn.url = data.get('url', conn.url)
    conn.is_local_file = data.get('is_local_file', conn.is_local_file)
    conn.local_file_path = data.get('local_file_path', conn.local_file_path)
    
    # Advanced fields
    if 'auth_token' in data:
        conn.auth_token = data['auth_token']
    if 'sync_schedule' in data:
        conn.sync_schedule = data['sync_schedule']
    if 'environments' in data:
        conn.environments = data['environments']
        
    if data.get('json_content'):
        conn.json_content = data.get('json_content')
        conn.last_updated = datetime.utcnow()
        
    error_message = None
    if conn.url and not conn.is_local_file:
        try:
            json_text, actual_url = fetch_swagger_json(conn.url)
            conn.json_content = json_text
            conn.last_updated = datetime.utcnow()
            conn.is_active = True
        except ValueError as e:
            conn.is_active = False
            error_message = f"Failed to fetch Swagger JSON: {str(e)}"
        except Exception as e:
            conn.is_active = False
            error_message = f"Failed to fetch Swagger JSON: {str(e)}"
    elif conn.is_local_file and conn.json_content:
        if conn.url:
            try:
                import json
                data = json.loads(conn.json_content)
                conn.json_content = fix_swagger_urls(data, conn.url)
            except Exception:
                pass
        conn.is_active = True
        conn.last_updated = datetime.utcnow()

    db.session.commit()
    
    res = conn.to_dict()
    if error_message:
        res["warning"] = error_message
        
    return jsonify(res)

@api_bp.route('/connections/<int:id>/refresh', methods=['POST'])
def refresh_connection(id):
    from bridge_app.models import SwaggerConnection
    from bridge_app.extensions import db
    import requests
    from datetime import datetime
    
    conn = SwaggerConnection.query.get_or_404(id)
    if conn.is_local_file:
        return jsonify({"error": "Cannot refresh local file connections from a URL."}), 400
        
    try:
        json_text, actual_url = fetch_swagger_json(conn.url)
        conn.json_content = json_text
        conn.last_updated = datetime.utcnow()
        db.session.commit()
        return jsonify(conn.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@api_bp.route('/connections/<int:id>/toggle', methods=['POST'])
def toggle_connection(id):
    from bridge_app.models import SwaggerConnection
    from bridge_app.extensions import db
    import requests
    from datetime import datetime
    
    conn = SwaggerConnection.query.get_or_404(id)
    data = request.json
    target_state = data.get('is_active', not conn.is_active)
    
    if target_state == True and not conn.is_local_file:
        # Trying to enable. Must fetch docs first to ensure it's valid.
        try:
            json_text, actual_url = fetch_swagger_json(conn.url)
            conn.json_content = json_text
            conn.last_updated = datetime.utcnow()
            conn.is_active = True
        except Exception as e:
            # Failed to fetch, keep it disabled
            conn.is_active = False
            db.session.commit()
            return jsonify({"error": f"Failed to fetch Swagger JSON: {str(e)}. Connection remains disabled."}), 400
    else:
        conn.is_active = target_state
        
    db.session.commit()
    return jsonify(conn.to_dict())

@api_bp.route('/save_config', methods=['POST'])
def save_config():
    data = request.json
    save_type = data.get('type')
    mapping_list = data.get('mapping', [])
    
    # Convert [{source: 's', target: 't'}] array to {target: source} dict
    # We use list order. Our engine parses the dict, but python dicts maintain insertion order.
    # To be extremely safe, we should save the array directly, but engine currently expects dict.
    # Let's save the array directly into field_mapping_json and update the engine slightly later.
    field_mapping = mapping_list # Keep it as an ordered list of dicts
    
    new_template = TemplateModel(
        name=data.get('name'),
        field_mapping_json=json.dumps(field_mapping)
    )
    
    if save_type == 'schedule':
        new_template.partner_url = data.get('source_url')
        new_template.client_url = data.get('client_url')
        new_template.client_auth_type = 'none' # simplify for now
    
    db.session.add(new_template)
    db.session.commit()
    
    if save_type == 'schedule':
        schedule_interval = data.get('schedule_interval', 60)
        new_job = JobModel(
            template_id=new_template.id,
            schedule_interval=schedule_interval
        )
        db.session.add(new_job)
        db.session.commit()
        
        app = current_app._get_current_object()
        job_id = f"job_{new_job.id}"
        scheduler.add_job(
            id=job_id, 
            func=pull_and_push_job, 
            args=[app, new_job.id], 
            trigger='interval', 
            seconds=new_job.schedule_interval
        )
        
    return jsonify({"success": True})

@api_bp.route('/mock/<int:conn_id>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def mock_server(conn_id, path):
    from bridge_app.models import SwaggerConnection
    conn = SwaggerConnection.query.get_or_404(conn_id)
    if not conn.json_content:
        return jsonify({"error": "No Swagger JSON available"}), 404
        
    try:
        spec = json.loads(conn.json_content)
    except Exception:
        return jsonify({"error": "Invalid Swagger JSON format"}), 500
        
    request_path = "/" + path
    paths = spec.get('paths', {})
    
    # Path matching (handles static paths and {param} paths)
    matched_path_obj = None
    if request_path in paths:
        matched_path_obj = paths[request_path]
    else:
        import re
        for spec_path, path_obj in paths.items():
            # Convert OpenAPI /users/{id} to regex ^/users/[^/]+$
            regex_path = re.sub(r'\{[^}]+\}', r'[^/]+', spec_path)
            if re.match(f"^{regex_path}$", request_path):
                matched_path_obj = path_obj
                break
                
    if not matched_path_obj:
        return jsonify({"error": f"Path {request_path} not found in Swagger spec"}), 404
        
    method = request.method.lower()
    if method not in matched_path_obj:
        return jsonify({"error": f"Method {method.upper()} not supported on {request_path}"}), 405
        
    operation = matched_path_obj[method]
    responses = operation.get('responses', {})
    
    # Try 200, 201, or default
    success_resp = responses.get('200') or responses.get('201') or responses.get('default')
    if not success_resp:
        return jsonify({}), 200 # Blank success
        
    # Swagger 2.0
    examples = success_resp.get('examples', {})
    if 'application/json' in examples:
        return jsonify(examples['application/json'])
        
    # OpenAPI 3.0
    content = success_resp.get('content', {})
    if 'application/json' in content:
        json_content = content['application/json']
        if 'example' in json_content:
            return jsonify(json_content['example'])
        elif 'examples' in json_content:
            first_key = list(json_content['examples'].keys())[0]
            if 'value' in json_content['examples'][first_key]:
                return jsonify(json_content['examples'][first_key]['value'])
                
    return jsonify({"_mock_message": "No static example defined in spec for this endpoint."}), 200
