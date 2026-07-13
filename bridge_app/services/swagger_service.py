# ==================================================================
# File: bridge_app/services/swagger_service.py
# Description: Service for fetching, parsing, and processing Swagger/OpenAPI files.
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

import json

# Supported OpenAPI versions (default is 3.2.0)
SUPPORTED_OPENAPI_VERSIONS = ['2.0', '3.0.3', '3.1.0', '3.2.0']

def generate_pull_endpoint_swagger_spec(template, requested_version='3.2.0'):
    """
    Generates an OpenAPI spec for the given template's pull endpoints based on requested_version.
    Supports '2.0', '3.0.3', '3.1.0', and '3.2.0'.
    """
    t_dict = template.to_dict()
    destinations = t_dict.get('destinations', [])
    if not destinations:
        destinations = [{'name': 'default', 'field_mapping': []}]

    is_v2 = requested_version.startswith('2.')
    
    # Generate links for markdown description
    links_md = "\n\n**Available API Versions:**\n"
    # Iterate over supported versions, newest first
    for v in SUPPORTED_OPENAPI_VERSIONS[::-1]:
        # Skip the currently requested version
        if v == requested_version:
            continue
        links_md += f"- [View {'Swagger' if v == '2.0' else 'OpenAPI'} {v}](/api/bridge/pull/{template.slug}/docs?version={v})\n"
    
    base_description = "Auto-generated API Gateway for Template: " + template.name + links_md
            
    spec = {}
    if is_v2:
        spec["swagger"] = "2.0"
        spec["info"] = {
            "title": template.name,
            "description": base_description,
            "version": "1.0.0"
        }
        spec["basePath"] = "/"
    else:
        # Use the requested version if it is a supported OpenAPI version, otherwise fall back to 3.2.0
        spec["openapi"] = requested_version if requested_version in SUPPORTED_OPENAPI_VERSIONS[1:] else '3.2.0'
        spec["info"] = {
            "title": template.name,
            "description": base_description,
            "version": "1.0.0"
        }
        spec["servers"] = [{"url": "/"}]
        
    spec["paths"] = {}
    
    for dest in destinations:
        d_slug = dest.get('name', 'default').lower().replace(' ', '_').replace('-', '_')
        d_slug = ''.join(e for e in d_slug if e.isalnum() or e == '_')
        
        properties = {}
        for mapping in dest.get('field_mapping', []):
            target = mapping.get("target")
            if target:
                properties[target] = {"type": "string"}
                
        path = f"/api/bridge/pull/{template.slug}/{d_slug}"
        method = dest.get('method', getattr(template, 'pull_method', None) or 'get').lower()
        
        if is_v2:
            endpoint_def = {
                "summary": f"Fetch and transform data for {dest.get('name', 'Client')}",
                "description": "Pulls data from configured sources and translates it into the mapped schema.",
                "produces": ["application/json"],
                "responses": {
                    "200": {
                        "description": "Successful operation",
                        "schema": {
                            "type": "object",
                            "properties": properties
                        }
                    },
                    "401": {
                        "description": "Unauthorized"
                    }
                }
            }
        else:
            endpoint_def = {
                "summary": f"Fetch and transform data for {dest.get('name', 'Client')}",
                "description": "Pulls data from configured sources and translates it into the mapped schema.",
                "responses": {
                    "200": {
                        "description": "Successful operation",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": properties
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Unauthorized"
                    }
                }
            }
        spec["paths"][path] = {method: endpoint_def}
    
    # Add auth requirements if token is set
    client_creds = json.loads(template.client_credentials_json or '{}')
    if client_creds.get('token'):
        if is_v2:
            spec["securityDefinitions"] = {
                "Bearer": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "description": "Format: Bearer <token>"
                }
            }
        else:
            spec["components"] = {
                "securitySchemes": {
                    "Bearer": {
                        "type": "http",
                        "scheme": "bearer"
                    }
                }
            }
        for path, methods in spec["paths"].items():
            for method in methods:
                spec["paths"][path][method]["security"] = [{"Bearer": []}]
        
    return spec

def get_swagger_ui_html(title, template_slug, requested_version='3.2.0'):
    """
    Returns the HTML string to render Swagger UI configured for the given template.
    """
    spec_url = f"/api/bridge/pull/{template_slug}/spec?version={requested_version}"
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <title>{title} - Swagger UI</title>
      <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    </head>
    <body>
      <div id="swagger-ui"></div>
      <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" crossorigin></script>
      <script>
        window.onload = () => {{
          window.ui = SwaggerUIBundle({{
            url: window.location.origin + '{spec_url}',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            layout: "BaseLayout",
          }});
        }};
      </script>
    </body>
    </html>
    """
