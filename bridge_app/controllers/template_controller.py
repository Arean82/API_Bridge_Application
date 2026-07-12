# ==================================================================
# File: bridge_app/controllers/template_controller.py
# Description: API routes for Template management.
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
import json
from bridge_app.models import TemplateModel, JobModel
from bridge_app.extensions import db, scheduler
from bridge_app.services.task_runner import pull_and_push_job
from bridge_app.controllers.engine_controller import api_bp

@api_bp.route('/templates', methods=['GET'])
def get_templates():
    templates = TemplateModel.query.all()
    return jsonify([t.to_dict() for t in templates])

@api_bp.route('/templates', methods=['POST'])
def create_template():
    data = request.json
    try:
        new_template = TemplateModel(
            name=data.get('name'),
            client_name=data.get('client_name'),
            partner_url=data.get('partner_url'),
            partner_auth_token=data.get('partner_auth_token'),
            sources_json=json.dumps(data.get('sources', [])),
            client_url=data.get('client_url'),
            client_auth_type=data.get('client_auth_type', 'none'),
            client_credentials_json=json.dumps(data.get('client_credentials', {})),
            destinations_json=json.dumps(data.get('destinations', [])),
            execution_mode=data.get('execution_mode', 'push'),
            pull_method=data.get('pull_method', 'GET')
        )
        db.session.add(new_template)
        db.session.commit()
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
        

    if data.get('schedule_immediately'):
        schedule_interval = max(1, int(data.get('schedule_interval', 60)))
        new_job = JobModel(
            template_id=new_template.id,
            schedule_interval=schedule_interval
        )
        db.session.add(new_job)
        db.session.commit()
        
        app = current_app._get_current_object()
        job_id = f"job_{new_job.id}"
        scheduler.add_job(
            id=job_id, 
            func=pull_and_push_job, 
            args=[new_job.id], 
            trigger='interval', 
            seconds=new_job.schedule_interval
        )
        
    return jsonify(new_template.to_dict()), 201

@api_bp.route('/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    data = request.json
    template = TemplateModel.query.get_or_404(template_id)
    
    try:
        template.name = data.get('name', template.name)
        template.partner_url = data.get('partner_url', template.partner_url)
        template.partner_auth_token = data.get('partner_auth_token', template.partner_auth_token)
        if 'sources' in data:
            template.sources_json = json.dumps(data.get('sources'))
        template.client_url = data.get('client_url', template.client_url)
        template.client_auth_type = data.get('client_auth_type', template.client_auth_type)
        if 'client_credentials' in data:
            template.client_credentials_json = json.dumps(data.get('client_credentials'))
        if 'destinations' in data:
            template.destinations_json = json.dumps(data.get('destinations'))
        if 'execution_mode' in data:
            template.execution_mode = data.get('execution_mode')
        if 'pull_method' in data:
            template.pull_method = data.get('pull_method')
            
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400
        
    return jsonify(template.to_dict()), 200

@api_bp.route('/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    template = TemplateModel.query.get_or_404(template_id)
    jobs = JobModel.query.filter_by(template_id=template_id).all()
    for job in jobs:
        try:
            scheduler.remove_job(f"job_{job.id}")
        except Exception:
            pass
        db.session.delete(job)
    db.session.delete(template)
    db.session.commit()
    return jsonify({"success": True}), 200
