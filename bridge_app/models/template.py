# ==================================================================
# File: bridge_app/models/template.py
# Description: 
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
    _sources_json = db.Column('sources_json', db.Text, default='[]') # Array of {name, url, auth_token}
    
    # Client Config
    client_name = db.Column(db.String(100), nullable=True)
    client_url = db.Column(db.String(255), nullable=True)
    client_auth_type = db.Column(db.String(50), default='none')
    _client_credentials_json = db.Column('client_credentials_json', db.Text, default='{}')
    execution_mode = db.Column(db.String(50), default='push')

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
        self._sources_json = encrypt_token(value)
        
    @property
    def client_credentials_json(self):
        from bridge_app.services.encryption import decrypt_token
        return decrypt_token(self._client_credentials_json)
        
    @client_credentials_json.setter
    def client_credentials_json(self, value):
        from bridge_app.services.encryption import encrypt_token
        self._client_credentials_json = encrypt_token(value)
    
    # Field Mapping (Partner Field -> Client JSON Path)
    field_mapping_json = db.Column(db.Text, default='{}')
    
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
            'field_mapping': json.loads(self.field_mapping_json or '{}'),
            'execution_mode': self.execution_mode,
            'created_at': self.created_at.isoformat() + "Z"
        }
