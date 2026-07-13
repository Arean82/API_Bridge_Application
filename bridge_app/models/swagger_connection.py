# ==================================================================
# File: bridge_app/models/swagger_connection.py
# Description: Database model for API connections and Swagger specs.
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

from bridge_app.extensions import db
from datetime import datetime

class SwaggerConnection(db.Model):
    __tablename__ = 'swagger_connections'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=True)
    json_content = db.Column(db.Text, nullable=True)
    is_local_file = db.Column(db.Boolean, default=False)
    local_file_path = db.Column(db.String(500), nullable=True)
    update_interval_hours = db.Column(db.Integer, default=24)
    is_active = db.Column(db.Boolean, default=True)
    
    connection_type = db.Column(db.String(50), default='rest')
    
    # Advanced features
    _auth_token = db.Column('auth_token', db.String(1000), nullable=True)
    sync_schedule = db.Column(db.String(100), nullable=True)
    environments = db.Column(db.Text, nullable=True) # JSON array of environment URLs
    
    auth_type = db.Column(db.String(50), default='none')
    _auth_config = db.Column('auth_config', db.Text, nullable=True)
    _custom_headers = db.Column('custom_headers', db.Text, nullable=True)
    schema_source = db.Column(db.String(50), default='introspection')
    
    spec_auth_type = db.Column(db.String(50), default='none')
    _spec_auth_config = db.Column('spec_auth_config', db.Text, nullable=True)
    _spec_custom_headers = db.Column('spec_custom_headers', db.Text, nullable=True)
    
    @property
    def auth_token(self):
        from bridge_app.services.encryption import decrypt_token
        return decrypt_token(self._auth_token)
        
    @auth_token.setter
    def auth_token(self, value):
        from bridge_app.services.encryption import encrypt_token
        self._auth_token = encrypt_token(value)
        
    @property
    def auth_config(self):
        from bridge_app.services.encryption import decrypt_token
        import json
        decrypted = decrypt_token(self._auth_config)
        if decrypted:
            try:
                return json.loads(decrypted)
            except:
                pass
        return None
        
    @auth_config.setter
    def auth_config(self, value):
        from bridge_app.services.encryption import encrypt_token
        import json
        if value:
            self._auth_config = encrypt_token(json.dumps(value))
        else:
            self._auth_config = None

    @property
    def custom_headers(self):
        from bridge_app.services.encryption import decrypt_token
        import json
        decrypted = decrypt_token(self._custom_headers)
        if decrypted:
            try:
                return json.loads(decrypted)
            except:
                pass
        return None
        
    @custom_headers.setter
    def custom_headers(self, value):
        from bridge_app.services.encryption import encrypt_token
        import json
        if value:
            self._custom_headers = encrypt_token(json.dumps(value))
        else:
            self._custom_headers = None
            
    @property
    def spec_auth_config(self):
        from bridge_app.services.encryption import decrypt_token
        import json
        decrypted = decrypt_token(self._spec_auth_config)
        if decrypted:
            try:
                return json.loads(decrypted)
            except:
                pass
        return None
        
    @spec_auth_config.setter
    def spec_auth_config(self, value):
        from bridge_app.services.encryption import encrypt_token
        import json
        if value:
            self._spec_auth_config = encrypt_token(json.dumps(value))
        else:
            self._spec_auth_config = None

    @property
    def spec_custom_headers(self):
        from bridge_app.services.encryption import decrypt_token
        import json
        decrypted = decrypt_token(self._spec_custom_headers)
        if decrypted:
            try:
                return json.loads(decrypted)
            except:
                pass
        return None
        
    @spec_custom_headers.setter
    def spec_custom_headers(self, value):
        from bridge_app.services.encryption import encrypt_token
        import json
        if value:
            self._spec_custom_headers = encrypt_token(json.dumps(value))
        else:
            self._spec_custom_headers = None
            
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, url=None, json_content=None, is_local_file=False, local_file_path=None, update_interval_hours=24, is_active=True, auth_token=None, sync_schedule=None, environments=None, connection_type='rest', auth_type='none', auth_config=None, custom_headers=None, schema_source='introspection', spec_auth_type='none', spec_auth_config=None, spec_custom_headers=None):
        self.name = name
        self.url = url
        self.json_content = json_content
        self.is_local_file = is_local_file
        self.local_file_path = local_file_path
        self.update_interval_hours = update_interval_hours
        self.is_active = is_active
        self.auth_token = auth_token
        self.sync_schedule = sync_schedule
        self.environments = environments
        self.connection_type = connection_type
        self.auth_type = auth_type
        self.auth_config = auth_config
        self.custom_headers = custom_headers
        self.schema_source = schema_source
        self.spec_auth_type = spec_auth_type
        self.spec_auth_config = spec_auth_config
        self.spec_custom_headers = spec_custom_headers

    def to_dict(self):
        import json
        envs = []
        if self.environments:
            try:
                envs = json.loads(self.environments)
            except:
                pass
                
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "is_local_file": self.is_local_file,
            "local_file_path": self.local_file_path,
            "update_interval_hours": self.update_interval_hours,
            "is_active": self.is_active,
            "auth_token": self.auth_token,
            "sync_schedule": self.sync_schedule,
            "environments": envs,
            "connection_type": self.connection_type,
            "auth_type": self.auth_type,
            "auth_config": self.auth_config,
            "custom_headers": self.custom_headers,
            "schema_source": self.schema_source,
            "spec_auth_type": self.spec_auth_type,
            "spec_auth_config": self.spec_auth_config,
            "spec_custom_headers": self.spec_custom_headers,
            "last_updated": self.last_updated.isoformat() + "Z" if self.last_updated else None,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None
        }
