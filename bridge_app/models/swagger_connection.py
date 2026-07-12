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
    
    # Advanced features
    _auth_token = db.Column('auth_token', db.String(1000), nullable=True)
    sync_schedule = db.Column(db.String(100), nullable=True)
    environments = db.Column(db.Text, nullable=True) # JSON array of environment URLs
    
    @property
    def auth_token(self):
        from bridge_app.services.encryption import decrypt_token
        return decrypt_token(self._auth_token)
        
    @auth_token.setter
    def auth_token(self, value):
        from bridge_app.services.encryption import encrypt_token
        self._auth_token = encrypt_token(value)
        
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, url=None, json_content=None, is_local_file=False, local_file_path=None, update_interval_hours=24, is_active=True, auth_token=None, sync_schedule=None, environments=None):
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
            "last_updated": self.last_updated.isoformat() + "Z" if self.last_updated else None,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None
        }
