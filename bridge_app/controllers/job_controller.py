# ==================================================================
# File: bridge_app/controllers/job_controller.py
# Description: API routes for Job management.
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
