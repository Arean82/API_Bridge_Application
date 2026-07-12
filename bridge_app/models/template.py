# ==================================================================
# File: bridge_app/models/template.py
# Description: Database model for execution templates and field mappings.
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

from datetime import datetime
from bridge_app.extensions import db
import json

class TemplateModel(db.Model):
    __tablename__ = 'templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Partner Config
    partner_url = db.Column(db.String(255), nullable=True)
    _partner_auth_token = db.Column('partner_auth_token', db.String(255), nullable=True)
    _sources_json = db.Column('sources_json', db.Text, nullable=False, default='[]') # Array of {name, url, auth_token}
    
    # Client Config
    client_name = db.Column(db.String(100), nullable=True)
    client_url = db.Column(db.String(255), nullable=True)
    client_auth_type = db.Column(db.String(50), default='none')
    _client_credentials_json = db.Column('client_credentials_json', db.Text, nullable=False, default='{}')
    execution_mode = db.Column(db.String(50), default='push')
    pull_method = db.Column(db.String(10), default='GET')
    _destinations_json = db.Column('destinations_json', db.Text, nullable=False, default='[]')
    @property
    def slug(self):
        import re
        return re.sub(r'[^a-zA-Z0-9]', '_', self.name).lower()

    @property
    def partner_auth_token(self):
        from bridge_app.services.encryption import decrypt_token
        return decrypt_token(self._partner_auth_token)
        
    @partner_auth_token.setter
    def partner_auth_token(self, value):
        from bridge_app.services.encryption import encrypt_token
        self._partner_auth_token = encrypt_token(value)
        
    @property
    def sources_json(self):
        from bridge_app.services.encryption import decrypt_token
        return decrypt_token(self._sources_json)
        
    @sources_json.setter
    def sources_json(self, value):
        from bridge_app.services.encryption import encrypt_token
        
        if not value:
            raise ValueError("Sources cannot be empty.")
            
        try:
            parsed = json.loads(value) if isinstance(value, str) else value
            value_str = value if isinstance(value, str) else json.dumps(value)
            
            if not parsed:
                raise ValueError("Sources array cannot be empty.")
                
            for idx, src in enumerate(parsed):
                if not src.get('selectedApi'):
                    raise ValueError(f"Endpoint {idx+1} must have a selected API endpoint.")
                if not src.get('url'):
                    raise ValueError(f"Endpoint {idx+1} must have a Source URL.")
                    
        except json.JSONDecodeError:
            raise ValueError("Invalid sources JSON format.")
            
        self._sources_json = encrypt_token(value_str)
        
    @property
    def client_credentials_json(self):
        from bridge_app.services.encryption import decrypt_token
        return decrypt_token(self._client_credentials_json)
        
    @client_credentials_json.setter
    def client_credentials_json(self, value):
        from bridge_app.services.encryption import encrypt_token
        self._client_credentials_json = encrypt_token(value)

    @property
    def destinations_json(self):
        from bridge_app.services.encryption import decrypt_token
        return decrypt_token(self._destinations_json)
        
    @destinations_json.setter
    def destinations_json(self, value):
        from bridge_app.services.encryption import encrypt_token
        value_str = value if isinstance(value, str) else json.dumps(value)
        self._destinations_json = encrypt_token(value_str)


    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = db.relationship('JobModel', backref='template', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(TemplateModel, self).__init__(**kwargs)

    def to_dict(self):
        try:
            sources = json.loads(self.sources_json) if self.sources_json else []
        except:
            sources = []
            
        try:
            client_creds = json.loads(self.client_credentials_json or '{}')
        except:
            client_creds = {}
            
        try:
            destinations = json.loads(self.destinations_json) if self.destinations_json else []
        except:
            destinations = []
            
        return {
            'id': self.id,
            'name': self.name,
            'client_name': self.client_name,
            'partner_url': self.partner_url,
            'partner_auth_token': self.partner_auth_token,
            'sources': sources,
            'client_url': self.client_url,
            'client_auth_type': self.client_auth_type,
            'client_credentials': client_creds,
            'destinations': destinations,
            'execution_mode': self.execution_mode,
            'pull_method': self.pull_method,
            'created_at': self.created_at.isoformat() + "Z"
        }
