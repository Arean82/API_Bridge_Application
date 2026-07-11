# ==================================================================
# File: bridge_app/models/failed_payload.py
# Description: Database model for tracking failed payload deliveries.
# ==================================================================

from bridge_app.extensions import db
from datetime import datetime

class FailedPayload(db.Model):
    __tablename__ = 'failed_payloads'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id', ondelete='CASCADE'), nullable=False)
    payload_json = db.Column(db.Text, nullable=False)  # The generated JSON that failed to push
    error_message = db.Column(db.Text, nullable=True)  # The exception or HTTP error
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    job = db.relationship('JobModel', backref=db.backref('failed_payloads', cascade='all, delete-orphan', lazy=True))
    template = db.relationship('TemplateModel', backref=db.backref('failed_payloads', cascade='all, delete-orphan', lazy=True))

    def __init__(self, job_id, template_id, payload_json, error_message=None):
        self.job_id = job_id
        self.template_id = template_id
        self.payload_json = payload_json
        self.error_message = error_message

    def __repr__(self):
        return f"<FailedPayload {self.id} for Job {self.job_id}>"

    def to_dict(self):
        import json
        payload = {}
        try:
            payload = json.loads(self.payload_json)
        except:
            payload = self.payload_json

        return {
            "id": self.id,
            "job_id": self.job_id,
            "template_id": self.template_id,
            "payload_json": payload,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() + "Z" if self.timestamp else None
        }
