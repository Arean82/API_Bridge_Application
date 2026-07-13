# ==================================================================
# File: bridge_app/controllers/connection_controller.py
# Description: API routes for managing Swagger connections.
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

from flask import request, jsonify, current_app
import json
from bridge_app.controllers.engine_controller import api_bp
from bridge_app.services.swagger_utils import fetch_swagger_json, fix_swagger_urls

def get_connection_headers(conn):
    headers = {}
    if conn.custom_headers:
        headers.update(conn.custom_headers)
    
    if conn.auth_type == 'bearer' and conn.auth_config and 'token' in conn.auth_config:
        headers['Authorization'] = f"Bearer {conn.auth_config['token']}"
    elif conn.auth_type == 'api_key' and conn.auth_config and 'header_name' in conn.auth_config and 'header_value' in conn.auth_config:
        headers[conn.auth_config['header_name']] = conn.auth_config['header_value']
    elif conn.auth_type == 'basic' and conn.auth_config and 'username' in conn.auth_config and 'password' in conn.auth_config:
        import base64
        credentials = f"{conn.auth_config['username']}:{conn.auth_config['password']}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode('utf-8')
        headers['Authorization'] = f"Basic {encoded_credentials}"
        
    return headers

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
        environments=data.get('environments'),
        connection_type=data.get('connection_type', 'rest'),
        auth_type=data.get('auth_type', 'none'),
        auth_config=data.get('auth_config'),
        custom_headers=data.get('custom_headers'),
        schema_source=data.get('schema_source', 'introspection'),
        spec_auth_type=data.get('spec_auth_type', 'none'),
        spec_auth_config=data.get('spec_auth_config'),
        spec_custom_headers=data.get('spec_custom_headers')
    )
    
    # Fetch initial JSON if URL provided
    error_message = None
    if conn.connection_type == 'graphql':
        conn.is_active = True
    elif conn.url and not conn.is_local_file:
        try:
            req_headers = get_connection_headers(conn)
            json_text, actual_url = fetch_swagger_json(conn.url, headers=req_headers)
            import json
            conn.json_content = json.dumps(json_text) if isinstance(json_text, dict) else json_text
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
    if 'connection_type' in data:
        conn.connection_type = data['connection_type']
    
    # Advanced fields
    if 'auth_token' in data:
        conn.auth_token = data['auth_token']
    if 'sync_schedule' in data:
        conn.sync_schedule = data['sync_schedule']
    if 'environments' in data:
        conn.environments = data['environments']
    if 'auth_type' in data:
        conn.auth_type = data['auth_type']
    if 'auth_config' in data:
        conn.auth_config = data['auth_config']
    if 'custom_headers' in data:
        conn.custom_headers = data['custom_headers']
    if 'schema_source' in data:
        conn.schema_source = data['schema_source']
    if 'spec_auth_type' in data:
        conn.spec_auth_type = data['spec_auth_type']
    if 'spec_auth_config' in data:
        conn.spec_auth_config = data['spec_auth_config']
    if 'spec_custom_headers' in data:
        conn.spec_custom_headers = data['spec_custom_headers']
        
    if data.get('json_content'):
        conn.json_content = data.get('json_content')
        conn.last_updated = datetime.utcnow()
        
    error_message = None
    if conn.connection_type == 'graphql':
        conn.is_active = True
        conn.last_updated = datetime.utcnow()
    elif conn.url and not conn.is_local_file:
        try:
            req_headers = get_connection_headers(conn)
            json_text, actual_url = fetch_swagger_json(conn.url, headers=req_headers)
            import json
            conn.json_content = json.dumps(json_text) if isinstance(json_text, dict) else json_text
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
    if conn.connection_type == 'graphql':
        from bridge_app.utils.errors import APIError
        raise APIError("GraphQL connections cannot be refreshed.", 400)
    if conn.is_local_file:
        from bridge_app.utils.errors import APIError
        raise APIError("Cannot refresh local file connections from a URL.", 400)
        
    try:
        json_text, actual_url = fetch_swagger_json(conn.url)
        import json
        conn.json_content = json.dumps(json_text) if isinstance(json_text, dict) else json_text
        conn.last_updated = datetime.utcnow()
        db.session.commit()
        return jsonify(conn.to_dict())
    except Exception as e:
        from bridge_app.utils.errors import APIError
        raise APIError(str(e), 400)

@api_bp.route('/connections/<int:id>/toggle', methods=['POST'])
def toggle_connection(id):
    from bridge_app.models import SwaggerConnection
    from bridge_app.extensions import db
    import requests
    from datetime import datetime
    
    conn = SwaggerConnection.query.get_or_404(id)
    data = request.json
    target_state = data.get('is_active', not conn.is_active)
    
    if target_state == True and not conn.is_local_file and conn.connection_type != 'graphql':
        # Trying to enable. Must fetch docs first to ensure it's valid.
        try:
            json_text, actual_url = fetch_swagger_json(conn.url)
            import json
            conn.json_content = json.dumps(json_text) if isinstance(json_text, dict) else json_text
            conn.last_updated = datetime.utcnow()
            conn.is_active = True
        except Exception as e:
            # Failed to fetch, keep it disabled
            conn.is_active = False
            db.session.commit()
            from bridge_app.utils.errors import APIError
            raise APIError(f"Failed to fetch Swagger JSON: {str(e)}. Connection remains disabled.", 400)
    else:
        conn.is_active = target_state
        
    db.session.commit()
    return jsonify(conn.to_dict())


@api_bp.route('/mock/<int:conn_id>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def mock_server(conn_id, path):
    from bridge_app.models import SwaggerConnection
    conn = SwaggerConnection.query.get_or_404(conn_id)
    if not conn.json_content:
        from bridge_app.utils.errors import APIError
        raise APIError("No Swagger JSON available", 404)
        
    try:
        spec = json.loads(conn.json_content)
    except Exception:
        from bridge_app.utils.errors import APIError
        raise APIError("Invalid Swagger JSON format", 500)
        
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
        from bridge_app.utils.errors import APIError
        raise APIError(f"Path {request_path} not found in Swagger spec", 404)
        
    method = request.method.lower()
    if method not in matched_path_obj:
        from bridge_app.utils.errors import APIError
        raise APIError(f"Method {method.upper()} not supported on {request_path}", 405)
        
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

@api_bp.route('/connections/validate', methods=['POST'])
def validate_connection_spec():
    from bridge_app.services.openapi_validator import OpenAPIValidator
    
    data = request.json
    source_type = data.get('source_type')  # 'url', 'file', 'paste'
    content = data.get('content')
    url = data.get('url')
    
    auth_headers = {}
    auth_type = data.get('spec_auth_type', 'none')
    auth_config = data.get('spec_auth_config')
    custom_headers = data.get('spec_custom_headers', {})
    
    if custom_headers:
        auth_headers.update(custom_headers)
        
    if auth_type == 'bearer' and auth_config and 'token' in auth_config:
        auth_headers['Authorization'] = f"Bearer {auth_config['token']}"
    elif auth_type == 'api_key' and auth_config and 'header_name' in auth_config and 'header_value' in auth_config:
        auth_headers[auth_config['header_name']] = auth_config['header_value']
    elif auth_type == 'basic' and auth_config and 'username' in auth_config and 'password' in auth_config:
        import base64
        credentials = f"{auth_config['username']}:{auth_config['password']}"
        encoded = base64.b64encode(credentials.encode()).decode('utf-8')
        auth_headers['Authorization'] = f"Basic {encoded}"

    validator = OpenAPIValidator()
    
    if source_type == 'url':
        result = validator.process_and_validate(url=url, auth_headers=auth_headers)
    elif source_type in ['file', 'paste']:
        result = validator.process_and_validate(content=content)
    else:
        return jsonify({"success": False, "error": "Invalid source_type specified"}), 400
        
    return jsonify(result)
