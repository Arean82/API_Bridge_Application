# ==================================================================
# File: bridge_app/controllers/engine_controller.py
# Description: Internal API endpoints for managing configurations and scheduling.
# ==================================================================

from flask import Blueprint, request, jsonify, current_app
import json
from bridge_app.models import TemplateModel, JobModel
from bridge_app.extensions import db, scheduler
from bridge_app.services.task_runner import pull_and_push_job

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

    # Fallback to local sample if no docs loaded yet
    if not docs:
        doc_path = os.path.join(current_app.root_path, '..', 'sample', 'api-docs.json')
        try:
            with open(doc_path, 'r') as f:
                docs = json.load(f)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
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
        json_content=data.get('json_content')
    )
    
    # Fetch initial JSON if URL provided
    if conn.url and not conn.is_local_file:
        try:
            resp = requests.get(conn.url, timeout=10)
            if resp.ok:
                conn.json_content = resp.text
        except Exception as e:
            # We save it anyway, APScheduler will retry later
            pass

    db.session.add(conn)
    db.session.commit()
    return jsonify(conn.to_dict())

@api_bp.route('/connections/<int:id>', methods=['DELETE'])
def delete_connection(id):
    from bridge_app.models import SwaggerConnection
    from bridge_app.extensions import db
    conn = SwaggerConnection.query.get_or_404(id)
    db.session.delete(conn)
    db.session.commit()
    return jsonify({"status": "deleted"})

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
