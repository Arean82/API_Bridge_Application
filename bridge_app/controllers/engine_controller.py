# ==================================================================
# File: bridge_app/controllers/engine_controller.py
# Description: Core engine routes for executing templates.
# ==================================================================

from flask import Blueprint, request, jsonify, current_app
import json
from bridge_app.models import TemplateModel, JobModel
from bridge_app.extensions import db, scheduler
from bridge_app.services.task_runner import pull_and_push_job

api_bp = Blueprint('api', __name__, url_prefix='/api')

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
                    if conn.json_content:
                        try:
                            docs = json.loads(conn.json_content)
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
            # Look for any valid HTTP method for response/request schemas
            method = (path_data.get('get') or path_data.get('post') or 
                      path_data.get('put') or path_data.get('patch') or 
                      path_data.get('delete'))
            if not method:
                continue
                
            fields = []
            try:
                responses = method.get('responses', {})
                success_resp = None
                for code in ['200', '201', '202', 'default', 200, 201, 202]:
                    if code in responses or str(code) in responses:
                        success_resp = responses.get(code) or responses.get(str(code))
                        break
                        
                if not success_resp:
                    continue
                    
                schema = None
                
                # OpenAPI 3.x (3.0, 3.1, 3.2+)
                if 'content' in success_resp:
                    for media_type, media_obj in success_resp['content'].items():
                        if 'schema' in media_obj:
                            schema = media_obj['schema']
                            if 'application/json' in media_type:
                                break # Prefer JSON if available
                # OpenAPI 2.0 (Swagger)
                elif 'schema' in success_resp:
                    schema = success_resp['schema']
                    
                if not schema:
                    continue
                    
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
            except Exception as e:
                pass
                
            endpoints.append({
                'name': method.get('summary', path_name),
                'path': path_name,
                'fields': fields
            })
            
        return jsonify(endpoints)
    except Exception as e:
        from bridge_app.utils.errors import APIError
        raise APIError(str(e), 500)

@api_bp.route('/config/theme', methods=['POST'])
def update_theme():
    """Saves the UI theme and color mode to config.ini"""
    from bridge_app.config import set_theme
    data = request.json
    theme_name = data.get('theme', 'default')
    color_mode = data.get('colorMode', 'auto')
    set_theme(theme_name, color_mode)
    return jsonify({"status": "success"})

