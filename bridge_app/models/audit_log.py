# ==================================================================
# File: bridge_app/models/audit_log.py
# Description: Universal Audit Engine model for tracking all data transactions.
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

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    def __init__(self, **kwargs):
        super(AuditLog, self).__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    mode = db.Column(db.String(20), nullable=False) # 'PUSH', 'PULL_REST', 'PULL_GRAPHQL', 'WEBSOCKET'
    caller = db.Column(db.String(100), nullable=False) # IP address, Job ID, or API Key
    bytes_transferred = db.Column(db.Integer, default=0)
    record_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), nullable=False) # 'SUCCESS', 'FAILED'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    payload_json = db.Column(db.Text, nullable=True)
    
    # Optional fields for more context
    endpoint = db.Column(db.String(255))
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=True)

    template = db.relationship('TemplateModel', backref=db.backref('audit_logs', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "mode": self.mode,
            "caller": self.caller,
            "bytes_transferred": self.bytes_transferred,
            "record_count": self.record_count,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() + "Z",
            "endpoint": self.endpoint,
            "template_id": self.template_id
        }
