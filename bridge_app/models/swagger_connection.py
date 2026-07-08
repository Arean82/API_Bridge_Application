# ==================================================================
# File: bridge_app/models/swagger_connection.py
# Description: Model for storing Swagger API Connections.
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
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "is_local_file": self.is_local_file,
            "local_file_path": self.local_file_path,
            "update_interval_hours": self.update_interval_hours,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
