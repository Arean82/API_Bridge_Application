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

def generate_pull_endpoint_swagger_spec(template):
    """
    Generates an OpenAPI 3.0.3 spec for the given template's pull endpoints.
    """
    t_dict = template.to_dict()
    destinations = t_dict.get('destinations', [])
            
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": template.name,
            "description": "Auto-generated API Gateway for Template: " + template.name,
            "version": "1.0.0"
        },
        "servers": [
            {"url": "/"}
        ],
        "paths": {}
    }
    
    if not destinations:
        destinations = [{'name': 'default', 'field_mapping': []}]
        
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
        
        spec["paths"][path] = {
            method: {
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
        }
    
    # Add auth requirements if token is set
    client_creds = json.loads(template.client_credentials_json or '{}')
    if client_creds.get('token'):
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

def get_swagger_ui_html(title, template_slug):
    """
    Returns the HTML string to render Swagger UI configured for the given template.
    """
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
            url: window.location.origin + '/api/bridge/pull/{template_slug}/spec',
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
