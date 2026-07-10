# ==================================================================
# File: bridge_app/services/swagger_service.py
# Description: Service for fetching, parsing, and processing Swagger/OpenAPI files.
# ==================================================================

import json

def generate_pull_endpoint_swagger_spec(template):
    """
    Generates an OpenAPI 3.0.3 spec for the given template's pull endpoint.
    """
    field_mapping = json.loads(template.field_mapping_json or '[]')
    properties = {}
    for mapping in field_mapping:
        target = mapping.get("target")
        if target:
            properties[target] = {"type": "string"}
            
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
        "paths": {
            f"/api/bridge/pull/{template.slug}": {
                "get": {
                    "summary": "Fetch and transform data",
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
        spec["paths"][f"/api/bridge/pull/{template.slug}"]["get"]["security"] = [{"Bearer": []}]
        
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
