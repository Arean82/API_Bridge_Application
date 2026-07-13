# ==================================================================
# File: bridge_app/controllers/pull_graphql_controller.py
# Description: Logic for GraphQL pull execution mode.
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

@api_bp.route('/graphql/<template_slug>', methods=['GET'])
def pull_endpoint_graphql_redirect(template_slug):
    """Redirect to the first destination's GraphQL Playground when no dest_slug is provided."""
    import re, json
    from bridge_app.models.template import TemplateModel
    from flask import redirect, url_for, abort
    
    all_templates = TemplateModel.query.all()
    template = next((t for t in all_templates if t.slug == template_slug), None)
    if not template:
        abort(404)
    if template.execution_mode != 'pull_graphql':
        from bridge_app.utils.errors import APIError
        raise APIError('Template is not configured for GraphQL Pull mode', 400)
    
    try:
        dests = json.loads(template.destinations_json)
    except:
        dests = []
    
    if dests:
        dest_name = dests[0].get('name', 'client')
        dest_slug = re.sub(r'[^a-z0-9]', '_', dest_name.lower())
    else:
        dest_slug = 'default'
    
    return redirect(url_for('api.pull_endpoint_graphql', template_slug=template_slug, dest_slug=dest_slug))


@api_bp.route('/graphql/<template_slug>/<dest_slug>', methods=['GET', 'POST'])
def pull_endpoint_graphql(template_slug, dest_slug):
    from bridge_app.models.template import TemplateModel
    from flask import request, render_template_string, abort
    
    all_templates = TemplateModel.query.all()
    template = next((t for t in all_templates if t.slug == template_slug), None)
    if not template:
        abort(404)
    template_id = template.id
    if template.execution_mode != 'pull_graphql':
        from bridge_app.utils.errors import APIError
        raise APIError('Template is not configured for GraphQL Pull mode', 400)
        
    # GET request - serve the GraphQL Playground IDE
    if request.method == 'GET':
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset=utf-8/>
              <title>GraphQL Playground</title>
              <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css" />
              <link rel="shortcut icon" href="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/favicon.png" />
              <script src="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>
            </head>
            <body>
              <div id="root">
                <style>
                  body { margin: 0; background-color: #172a3a; font-family: Open Sans, sans-serif; height: 100vh; }
                  #root { height: 100%; width: 100%; display: flex; align-items: center; justify-content: center; }
                  .loading { font-size: 32px; font-weight: 200; color: rgba(255, 255, 255, .6); margin-left: 20px; }
                  img { width: 78px; height: 78px; }
                  .title { font-weight: 400; }
                </style>
                <img src='https://cdn.jsdelivr.net/npm/graphql-playground-react/build/logo.png' alt=''>
                <div class="loading"> Loading
                  <span class="title">GraphQL Playground</span>
                </div>
              </div>
              <script>window.addEventListener('load', function (event) {
                  GraphQLPlayground.init(document.getElementById('root'), {
                    endpoint: window.location.href
                  })
                })</script>
            </body>
            </html>
            """)

    # POST request - execute query
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
    with tracer.start_as_current_span("pull_graphql_request") as span:
        span.set_attribute("template.id", template_id)
        span.set_attribute("destination", dest_slug)
        result = execute_template_mapping(template_id, dest_slug)
        
    if result is None:
        from bridge_app.utils.errors import APIError
        raise APIError('Failed to execute mapping', 500)
        
    # GraphQL Execution
    query = request.json.get('query')
    from bridge_app.services.graphql_service import execute_graphql_query
    try:
        response = execute_graphql_query(template, dest_slug, query, result)
        
        # --- Universal Audit Engine ---
        from bridge_app.services.logger import log_audit
        log_audit(
            mode='PULL_GRAPHQL',
            caller=request.remote_addr or 'unknown',
            payload=response,
            endpoint=request.path,
            template_id=template_id
        )
        # ------------------------------

        from flask import jsonify
        return jsonify(response)
    except ValueError as e:
        from bridge_app.utils.errors import APIError
        raise APIError(str(e), 400)
