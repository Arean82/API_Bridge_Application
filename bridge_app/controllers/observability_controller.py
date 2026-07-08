# ==================================================================
# File: bridge_app/controllers/observability_controller.py
# Description: Exposes /metrics and /health endpoints for Zabbix monitoring.
# ==================================================================

from flask import Blueprint, jsonify
from bridge_app.models import TemplateModel, JobModel, JobLog

obs_bp = Blueprint('obs', __name__)

@obs_bp.route('/health')
def health():
    return jsonify({"status": "UP"})

@obs_bp.route('/metrics')
def metrics():
    # Gather statistics for Zabbix
    total_templates = TemplateModel.query.count()
    
    total_jobs = JobModel.query.count()
    active_jobs = JobModel.query.filter_by(is_active=True).count()
    
    total_logs = JobLog.query.count()
    success_logs = JobLog.query.filter_by(status='SUCCESS').count()
    failed_logs = JobLog.query.filter_by(status='FAILED').count()
    
    # Returning JSON format that Zabbix HTTP Agent can parse
    return jsonify({
        "templates": {
            "total": total_templates
        },
        "jobs": {
            "total": total_jobs,
            "active": active_jobs
        },
        "logs": {
            "total": total_logs,
            "success": success_logs,
            "failed": failed_logs
        }
    })
