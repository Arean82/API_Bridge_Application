# ==================================================================
# File: bridge_app/controllers/observability_controller.py
# Description: Routes for system health and monitoring.
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
