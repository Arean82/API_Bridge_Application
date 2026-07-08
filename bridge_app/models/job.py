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
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'last_status': self.last_status,
            'created_at': self.created_at.isoformat()
        }
