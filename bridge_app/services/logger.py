# ==================================================================
# File: bridge_app/engine/logger.py
# Description: Centralized application logging configuration.
# ==================================================================

import json
from datetime import datetime
from bridge_app.models import JobLog
from bridge_app.extensions import db
from flask import current_app

def log_job(job_id, status, payload, http_status=None, error_message=None):
    """
    Logs the outcome of a pull/push job to the database.
    """
    # Needs application context because it's run from the scheduler
    try:
        from bridge_app.models import JobModel
        from zoneinfo import ZoneInfo
        from flask import current_app
        
        job = JobModel.query.get(job_id)
        if job:
            tz_str = current_app.config.get('APP_TIMEZONE', 'UTC')
            job.last_run = datetime.now(ZoneInfo(tz_str)).replace(tzinfo=None)

        log = JobLog(
            job_id=job_id,
            status=status,
            http_status=http_status,
            error_message=error_message,
            payload_json=json.dumps(payload) if payload else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Failed to write log for job {job_id}: {e}")
