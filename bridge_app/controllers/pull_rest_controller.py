# ==================================================================
# File: bridge_app/controllers/pull_rest_controller.py
# Description: Logic for REST pull execution mode.
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

from flask import request, jsonify, render_template_string, abort
import json
from bridge_app.controllers.engine_controller import api_bp

@api_bp.route('/bridge/pull/<template_slug>/<dest_slug>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def pull_endpoint_rest(template_slug, dest_slug):
    """
    Auto-generated REST endpoint for Pull-mode templates.
    ---
    tags:
      - Pull Endpoints
    parameters:
      - name: template_slug
        in: path
        type: string
        required: true
    responses:
      200:
        description: Translated payload
    """
    from bridge_app.models.template import TemplateModel
    from flask import request, abort
    
    all_templates = TemplateModel.query.all()
    template = next((t for t in all_templates if t.slug == template_slug), None)
    if not template:
        abort(404)
    template_id = template.id
    if template.execution_mode != 'pull_rest':
        from bridge_app.utils.errors import APIError
        raise APIError('Template is not configured for REST Pull mode', 400)
        
    import json
    import re
    destinations = json.loads(template.destinations_json or '[]')
    
    def make_slug(name):
        return re.sub(r'[^a-z0-9]', '_', name.lower())
        
    dest = next((d for d in destinations if make_slug(d.get('name', 'client')) == dest_slug), None)
    if not dest:
        from bridge_app.utils.errors import APIError
        raise APIError(f'Destination {dest_slug} not found', 404)
        
    expected_method = dest.get('method') or template.pull_method or 'GET'
    if request.method != expected_method.upper():
        from bridge_app.utils.errors import APIError
        raise APIError(f'Method Not Allowed. Expected {expected_method}', 405)
        
    # Check Auth
    import json
    client_creds = json.loads(template.client_credentials_json or '{}')
    expected_token = client_creds.get('token')
    if expected_token:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer ') or auth_header.split(' ')[1] != expected_token:
            from bridge_app.utils.errors import APIError
            raise APIError('Unauthorized', 401)
            
    # Execute mapping
    from bridge_app.services.task_runner import execute_template_mapping
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("pull_rest_request") as span:
        span.set_attribute("template.id", template_id)
        span.set_attribute("destination", dest_slug)
        result = execute_template_mapping(template_id, dest_slug)
        
    if result is None:
        from bridge_app.utils.errors import APIError
        raise APIError('Failed to execute mapping', 500)
        
    # --- Universal Audit Engine ---
    from bridge_app.services.logger import log_audit
    log_audit(
        mode='PULL_REST',
        caller=request.remote_addr or 'unknown',
        payload=result,
        endpoint=request.path,
        template_id=template_id
    )
    # ------------------------------

    from flask import jsonify
    return jsonify(result)

@api_bp.route('/bridge/pull/<template_slug>/spec', methods=['GET'])
def pull_endpoint_swagger_spec(template_slug):
    from bridge_app.models.template import TemplateModel
    from flask import jsonify, abort, request
    all_templates = TemplateModel.query.all()
    template = next((t for t in all_templates if t.slug == template_slug), None)
    if not template:
        abort(404)
        
    requested_version = request.args.get('version', '3.2.0')
    from bridge_app.services.swagger_service import generate_pull_endpoint_swagger_spec
    spec = generate_pull_endpoint_swagger_spec(template, requested_version)
    return jsonify(spec)

@api_bp.route('/bridge/pull/<template_slug>/docs', methods=['GET'])
def pull_endpoint_swagger_ui(template_slug):
    from bridge_app.models.template import TemplateModel
    from flask import render_template_string, abort, request
    all_templates = TemplateModel.query.all()
    template = next((t for t in all_templates if t.slug == template_slug), None)
    if not template:
        abort(404)
        
    requested_version = request.args.get('version', '3.2.0')
    from bridge_app.services.swagger_service import get_swagger_ui_html
    html = get_swagger_ui_html(template.name, template_slug, requested_version)
    return render_template_string(html)
