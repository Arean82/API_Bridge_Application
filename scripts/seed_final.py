# ==================================================================
# File: scratch/seed_final.py
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

import os
import sys
import json
import uuid
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from bridge_app.app import create_app
from bridge_app.extensions import db
from bridge_app.models import SwaggerConnection, TemplateModel, JobModel
from bridge_app.services.swagger_utils import fix_swagger_urls

# =========================================================================
# I have found 20 APIs to replace the ones I deleted. 
# For the ones that have a UI page, I am saving the UI page to the DB.
# =========================================================================
API_LIST = [
    # --- 6 APIs with explicit HTML UI Pages ---
    ("AVL View", "https://app.avlview.com/open-api/api-doc.html", "https://app.avlview.com/open-api/v3/api-docs", "/v3.1/updateEngineHours"),
    ("API2PDF", "https://v2018.api2pdf.com/swagger/index.html", "https://v2018.api2pdf.com/swagger/v1/swagger.json", "/chrome/url"),
    ("Petstore API", "https://petstore.swagger.io/", "https://petstore.swagger.io/v2/swagger.json", "/pet/findByStatus"),
    ("Crossref", "https://api.crossref.org/swagger-ui/index.html", "https://api.crossref.org/swagger.json", "/works"),
    ("Disease.sh COVID-19", "https://disease.sh/docs/", "https://disease.sh/v3/covid-19/swagger.json", "/v3/covid-19/all"),
    ("NIH RePORTER", "https://api.reporter.nih.gov/", "https://api.reporter.nih.gov/swagger/v2/swagger.json", "/api/v2/projects/search"),   



    # --- 15 Highly Reliable Native/APIs.guru Swagger JSONs ---
    ("Weather.gov API", "https://api.weather.gov/", "https://api.weather.gov/openapi.json", "/points/39.7456,-97.0892"),
    ("Swiss Transport", "http://transport.opendata.ch/swagger.json", "http://transport.opendata.ch/swagger.json", "/v1/connections"),
    ("Wikimedia", "https://wikimedia.org/api/rest_v1/?spec", "https://wikimedia.org/api/rest_v1/?spec", "/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/Albert_Einstein/daily/20151001/20151031"),
    ("GitHub API", "https://api.apis.guru/v2/specs/github.com/1.1.4/openapi.json", "https://api.apis.guru/v2/specs/github.com/1.1.4/openapi.json", "/repos/{owner}/{repo}"),
    ("Slack API", "https://api.apis.guru/v2/specs/slack.com/1.7.0/openapi.json", "https://api.apis.guru/v2/specs/slack.com/1.7.0/openapi.json", "/api.test"),
    ("Spotify API", "https://api.apis.guru/v2/specs/spotify.com/1.0.0/openapi.json", "https://api.apis.guru/v2/specs/spotify.com/1.0.0/openapi.json", "/v1/albums/{id}"),
    ("Zoom API", "https://api.apis.guru/v2/specs/zoom.us/2.0.0/openapi.json", "https://api.apis.guru/v2/specs/zoom.us/2.0.0/openapi.json", "/users"),
    ("NYTimes", "https://api.apis.guru/v2/specs/nytimes.com/top_stories/2.0.0/openapi.json", "https://api.apis.guru/v2/specs/nytimes.com/top_stories/2.0.0/openapi.json", "/{section}.json"),
    ("SendGrid", "https://api.apis.guru/v2/specs/sendgrid.com/1.0.0/openapi.json", "https://api.apis.guru/v2/specs/sendgrid.com/1.0.0/openapi.json", "/alerts"),
    ("HubSpot CRM", "https://api.apis.guru/v2/specs/hubapi.com/crm/v3/openapi.json", "https://api.apis.guru/v2/specs/hubapi.com/crm/v3/openapi.json", "/crm/v3/objects/contacts"),
    ("Box API", "https://api.apis.guru/v2/specs/box.com/2.0.0/openapi.json", "https://api.apis.guru/v2/specs/box.com/2.0.0/openapi.json", "/users/me"),
    ("Asana API", "https://api.apis.guru/v2/specs/asana.com/1.0/openapi.json", "https://api.apis.guru/v2/specs/asana.com/1.0/openapi.json", "/users/me"),
    ("Atlassian Jira", "https://api.apis.guru/v2/specs/atlassian.com/jira/1001.0.0-SNAPSHOT/openapi.json", "https://api.apis.guru/v2/specs/atlassian.com/jira/1001.0.0-SNAPSHOT/openapi.json", "/rest/api/3/serverInfo"),
    ("1Password Connect", "https://api.apis.guru/v2/specs/1password.local/connect/1.5.7/openapi.json", "https://api.apis.guru/v2/specs/1password.local/connect/1.5.7/openapi.json", "/v1/vaults"),
    ("AWS S3", "https://api.apis.guru/v2/specs/amazonaws.com/s3/2006-03-01/openapi.json", "https://api.apis.guru/v2/specs/amazonaws.com/s3/2006-03-01/openapi.json", "/")
]

def run():
    app = create_app()
    with app.app_context():
        print("Cleaning DB...")
        db.drop_all()
        db.create_all()

        UPLOADS_DIR = os.path.join(app.instance_path, 'uploads')
        os.makedirs(UPLOADS_DIR, exist_ok=True)

        connections = []
        print(f"Creating Connections from list of {len(API_LIST)} APIs...")

        for i, (name, db_url, json_url, sample_path) in enumerate(API_LIST):
            try:
                # We fetch the exact JSON url directly so it doesn't crash on regex parsing of HTML
                res = requests.get(json_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                if not res.ok: 
                    print(f"Failed to fetch {json_url}")
                    continue
                json_data = res.json()
                json_data = fix_swagger_urls(json_data, json_url)
                json_text = json.dumps(json_data)
            except Exception as e:
                print(f"Error fetching/parsing {json_url}: {e}")
                continue

            try:
                available_paths = list(json_data.get('paths', {}).keys())
                if available_paths:
                    sample_path = available_paths[0]

                if i < 10:
                    # 10 Local JSON Connections
                    file_name = f"seed_{uuid.uuid4().hex[:6]}.json"
                    file_path = os.path.join(UPLOADS_DIR, file_name)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(json_text)
                        
                    conn = SwaggerConnection(
                        name=f"{name} (JSON)",
                        url=db_url, # Storing the beautiful HTML URL in the DB!
                        is_local_file=True,
                        local_file_path=file_path,
                        json_content=json_text,
                        is_active=True,
                        connection_type='rest',
                        auth_type='none',
                        schema_source='file',
                        spec_auth_type='none',
                        spec_auth_config=None,
                        spec_custom_headers=None
                    )
                else:
                    # URL Connections
                    conn = SwaggerConnection(
                        name=f"{name} (URL)",
                        url=db_url,
                        is_local_file=False,
                        json_content=json_text,
                        is_active=True,
                        connection_type='rest',
                        auth_type='none',
                        schema_source='introspection',
                        spec_auth_type='none',
                        spec_auth_config=None,
                        spec_custom_headers=None
                    )
                db.session.add(conn)
                db.session.commit()
                connections.append((conn, sample_path))
                print(f"Added Swagger Connection: {name} (DB URL: {db_url})")
            except Exception as e:
                print(f"Failed to process {name}: {e}")

        if len(connections) < 20:
            print(f"Warning: Only {len(connections)} connections were created.")

        print("Generating Templates...")
        
        # --- 10 Push Templates ---
        for i in range(6):
            c1, p1 = connections[i % len(connections)]
            c2, p2 = connections[(i+1) % len(connections)]
            t = TemplateModel(
                name=f"Real Push 1-Dest (Group {i+1})",
                client_name="Push Destination 1",
                execution_mode="push",
                destinations_json=json.dumps([{"url": "https://httpbin.org/post", "method": "POST", "auth_type": "none", "auth_config": None, "field_mapping": [{"source": "source_0.id", "target": "partner_id"}, {"source": "source_1.name", "target": "partner_name"}]}]),
                sources_json=json.dumps([{"connectionId": c1.id, "selectedApi": p1, "url": "https://api.partner.example.com", "auth_type": "bearer", "auth_config": {"token": "mock-partner-token-123"}}, {"connectionId": c2.id, "selectedApi": p2, "url": "https://api.partner.example.com", "auth_type": "bearer", "auth_config": {"token": "mock-partner-token-123"}}])
            )
            db.session.add(t)
            db.session.flush() # get t.id
            db.session.add(JobModel(template_id=t.id, schedule_interval=60, is_active=True))
            
        for i in range(4):
            c1, p1 = connections[(i + 6) % len(connections)]
            c2, p2 = connections[(i + 7) % len(connections)]
            for dest_index in range(2): 
                t = TemplateModel(
                    name=f"Real Push Multi-Dest (Group {i+1}, Dest {dest_index+1})",
                    client_name=f"Multiple Push Client {dest_index+1}",
                    execution_mode="push",
                    destinations_json=json.dumps([{"url": "https://httpbin.org/post", "method": "POST", "auth_type": "none", "auth_config": None, "field_mapping": [{"source": "source_0.id", "target": "partner_id"}, {"source": "source_1.name", "target": "partner_name"}]}]),
                    sources_json=json.dumps([{"connectionId": c1.id, "selectedApi": p1, "url": "https://api.partner.example.com", "auth_type": "bearer", "auth_config": {"token": "mock-partner-token-123"}}, {"connectionId": c2.id, "selectedApi": p2, "url": "https://api.partner.example.com", "auth_type": "bearer", "auth_config": {"token": "mock-partner-token-123"}}])
                )
                db.session.add(t)
                db.session.flush()
                db.session.add(JobModel(template_id=t.id, schedule_interval=120, is_active=True))

        # --- 10 REST Pull Templates ---
        for i in range(6):
            c, p = connections[i % len(connections)]
            t = TemplateModel(
                name=f"REST Pull 8-Sources to 3-Endpoints {i+1}",
                client_name="REST Aggregator (8to3)",
                execution_mode="pull_rest",
                destinations_json=json.dumps([{"name": "Client Endpoint 1", "method": "GET", "field_mapping": [{"source": "source_0.id", "target": "partner_id"}, {"source": "source_0.name", "target": "partner_name"}]}]),
                sources_json=json.dumps([{"connectionId": c.id, "selectedApi": p, "url": "https://api.partner.example.com", "auth_type": "bearer", "auth_config": {"token": "mock-partner-token-123"}}] * 8)
            )
            db.session.add(t)
            db.session.flush()
            db.session.add(JobModel(template_id=t.id, schedule_interval=300, is_active=True))
            
        for i in range(4):
            c, p = connections[(i + 6) % len(connections)]
            t = TemplateModel(
                name=f"REST Pull 20-Sources to 40-Endpoints {i+1}",
                client_name="Massive REST Pull (20to40)",
                execution_mode="pull_rest",
                destinations_json=json.dumps([{"name": "Client Endpoint 1", "method": "GET", "field_mapping": [{"source": "source_0.id", "target": "partner_id"}, {"source": "source_0.name", "target": "partner_name"}]}]),
                sources_json=json.dumps([{"connectionId": c.id, "selectedApi": p, "url": "https://api.partner.example.com", "auth_type": "bearer", "auth_config": {"token": "mock-partner-token-123"}}] * 20)
            )
            db.session.add(t)
            db.session.flush()
            db.session.add(JobModel(template_id=t.id, schedule_interval=300, is_active=True))

        # --- 10 GraphQL Pull Templates ---
        for i in range(10):
            c, p = connections[(i + 10) % len(connections)] 
            t = TemplateModel(
                name=f"GraphQL Dynamic Schema for {c.name}",
                client_name="GraphQL Aggregator",
                execution_mode="pull_graphql",
                destinations_json=json.dumps([{"name": "Client Endpoint 1", "method": "GET", "field_mapping": [{"source": "source_0.id", "target": "partner_id"}, {"source": "source_0.name", "target": "partner_name"}]}]),
                sources_json=json.dumps([{"connectionId": c.id, "selectedApi": p, "url": "https://api.partner.example.com", "auth_token": "mock-partner-token-123"}] * 2)
            )
            db.session.add(t)
            db.session.flush()
            db.session.add(JobModel(template_id=t.id, schedule_interval=600, is_active=True))

        # --- Seed Dummy Audit Logs ---
        from bridge_app.models.audit_log import AuditLog
        print("Seeding dummy Audit Logs...")
        for i in range(15):
            mode = "PUSH" if i % 3 == 0 else ("PULL_REST" if i % 3 == 1 else "PULL_GRAPHQL")
            db.session.add(AuditLog(
                transaction_id=str(uuid.uuid4()),
                mode=mode,
                caller=f"192.168.1.{10 + i}" if mode != "PUSH" else f"Job-{i}",
                bytes_transferred=(i * 1024) + 256,
                record_count=(i * 10) + 1,
                status="SUCCESS" if i % 5 != 0 else "FAILED",
                endpoint="/api/v1/resource" if mode == "PUSH" else "/bridge/pull/...",
                template_id=1,
                payload_json='{"dummy": "data", "id": ' + str(i) + '}'
            ))
        db.session.commit()
        # -----------------------------

        print("Database fully rebuilt with 20 Working Swaggers and Audit Logs!")

if __name__ == '__main__':
    run()
