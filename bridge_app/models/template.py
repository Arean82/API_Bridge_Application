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
    partner_auth_token = db.Column(db.String(255), nullable=True)
    sources_json = db.Column(db.Text, default='[]') # Array of {name, url, auth_token}
    
    # Client Config
    client_name = db.Column(db.String(100), nullable=True)
    client_url = db.Column(db.String(255), nullable=True)
    client_auth_type = db.Column(db.String(50), default='none')
    client_credentials_json = db.Column(db.Text, default='{}')
    
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
            
        return {
            'id': self.id,
            'name': self.name,
            'client_name': self.client_name,
            'partner_url': self.partner_url,
            'partner_auth_token': self.partner_auth_token,
            'sources': sources,
            'client_url': self.client_url,
            'client_auth_type': self.client_auth_type,
            'client_credentials': json.loads(self.client_credentials_json or '{}'),
            'field_mapping': json.loads(self.field_mapping_json or '{}'),
            'created_at': self.created_at.isoformat()
        }
