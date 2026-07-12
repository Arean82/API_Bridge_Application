# ==================================================================
# File: bridge_app/models/job_log.py
# Description: Database model for logging job execution history.
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
import json

class JobLog(db.Model):
    def __init__(self, **kwargs):
        super(JobLog, self).__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False) # 'SUCCESS', 'FAILED'
    http_status = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    payload_json = db.Column(db.Text) # The exact payload we tried to send
    
    # Relationship to job
    job = db.relationship('JobModel', backref=db.backref('logs', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "timestamp": self.timestamp.isoformat() + "Z",
            "status": self.status,
            "http_status": self.http_status,
            "error_message": self.error_message,
            "payload": json.loads(self.payload_json) if self.payload_json else {}
        }
