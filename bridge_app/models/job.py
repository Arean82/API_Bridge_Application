# ==================================================================
# File: bridge_app/models/job.py
# Description: Database model for scheduled execution jobs.
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

class JobModel(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)
    
    schedule_interval = db.Column(db.Integer, default=60) # in seconds
    is_active = db.Column(db.Boolean, default=True)
    
    last_run = db.Column(db.DateTime, nullable=True)
    last_status = db.Column(db.String(50), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(JobModel, self).__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'template_name': self.template.name if self.template else None,
            'schedule_interval': self.schedule_interval,
            'is_active': self.is_active,
            'last_run': self.last_run.isoformat() + "Z" if self.last_run else None,
            'next_run': None,  # Can be calculated or omitted
            'last_status': self.last_status,
            'created_at': self.created_at.isoformat() + "Z"
        }
