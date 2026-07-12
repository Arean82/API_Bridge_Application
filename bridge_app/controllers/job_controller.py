# ==================================================================
# File: bridge_app/controllers/job_controller.py
# Description: API routes for managing background jobs.
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

from flask import request, jsonify, current_app
from bridge_app.models import JobModel
from bridge_app.extensions import db, scheduler
from bridge_app.services.task_runner import pull_and_push_job
from bridge_app.controllers.engine_controller import api_bp

@api_bp.route('/jobs', methods=['GET'])
def get_jobs():
    jobs = JobModel.query.all()
    return jsonify([j.to_dict() for j in jobs])

@api_bp.route('/jobs', methods=['POST'])
def create_job():
    data = request.json
    template_id = data.get('template_id')
    schedule_interval = max(1, int(data.get('schedule_interval', 60)))
    
    new_job = JobModel(
        template_id=template_id,
        schedule_interval=schedule_interval
    )
    db.session.add(new_job)
    db.session.commit()
    
    app = current_app._get_current_object()
    job_id = f"job_{new_job.id}"
    scheduler.add_job(
        id=job_id, 
        func=pull_and_push_job, 
        args=[app, new_job.id], 
        trigger='interval', 
        seconds=new_job.schedule_interval
    )
    
    return jsonify(new_job.to_dict()), 201
