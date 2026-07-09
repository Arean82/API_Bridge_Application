# ==================================================================
# File: bridge_app/controllers/ui_controller.py
# Description: Web routes for rendering the dashboard UI.
# ==================================================================

from flask import Blueprint, render_template

from bridge_app.models import TemplateModel, JobModel, JobLog

ui_bp = Blueprint('ui', __name__)

@ui_bp.route('/jobs')
def jobs_page():
    return render_template('jobs.html')

@ui_bp.route('/docs/<int:id>')
def swagger_docs(id):
    from bridge_app.models import SwaggerConnection
    from bridge_app.controllers.engine_controller import fix_swagger_urls
    import json
    conn = SwaggerConnection.query.get_or_404(id)
    
    if conn.json_content and conn.url:
        try:
            data = json.loads(conn.json_content)
            conn.json_content = fix_swagger_urls(data, conn.url)
        except Exception:
            pass
            
    return render_template('swagger_ui.html', conn=conn)

@ui_bp.route('/')
def index():
    return render_template('index.html')

@ui_bp.route('/htmx/dashboard/status')
def htmx_dashboard_status():
    return _render_dashboard_rows()

@ui_bp.route('/htmx/dashboard/job/<int:job_id>/toggle', methods=['POST'])
def htmx_toggle_job(job_id):
    from bridge_app.models import JobModel
    from bridge_app.extensions import db, scheduler
    from bridge_app.services.task_runner import pull_and_push_job
    from flask import current_app
    
    job = JobModel.query.get_or_404(job_id)
    job.is_active = not job.is_active
    
    try:
        job_name = f"job_{job.id}"
        if job.is_active:
            app = current_app._get_current_object()
            scheduler.add_job(
                id=job_name, 
                func=pull_and_push_job, 
                args=[job.id], 
                trigger='interval', 
                seconds=job.schedule_interval,
                replace_existing=True
            )
        else:
            scheduler.remove_job(job_name)
    except Exception:
        pass # Handle if job doesn't exist in scheduler
        
    db.session.commit()
    return _render_dashboard_rows()

@ui_bp.route('/htmx/dashboard/job/<int:job_id>', methods=['DELETE'])
def htmx_delete_job(job_id):
    from bridge_app.models import JobModel
    from bridge_app.extensions import db, scheduler
    
    job = JobModel.query.get_or_404(job_id)
    try:
        scheduler.remove_job(f"job_{job.id}")
    except Exception:
        pass
        
    db.session.delete(job)
    db.session.commit()
    return _render_dashboard_rows()

def _render_dashboard_rows():
    from bridge_app.models import JobModel, TemplateModel
    from flask import render_template
    jobs = JobModel.query.all()
    
    # Get template names
    for job in jobs:
        if job.template_id:
            t = TemplateModel.query.get(job.template_id)
            job.template_name = t.name if t else "Unknown"
            job.client_name = t.client_name if t else "Unknown"
        else:
            job.template_name = "Unknown"
            job.client_name = "Unknown"
            
    return render_template('partials/dashboard_table_rows.html', jobs=jobs)

@ui_bp.route('/templates/create')
def create_template_page():
    from flask import request
    import json
    clone_id = request.args.get('clone')
    clone_data = None
    if clone_id:
        template = TemplateModel.query.get(clone_id)
        if template:
            # We blank out the client-specific details, but keep everything else.
            t_dict = template.to_dict()
            clone_data = json.dumps(t_dict)
    from bridge_app.models import SwaggerConnection
    connections = SwaggerConnection.query.all()
    conns_json = json.dumps([c.to_dict() for c in connections])
            
    return render_template('create_template.html', clone_data=clone_data, conns_json=conns_json)

@ui_bp.route('/templates')
def templates_page():
    templates = TemplateModel.query.all()
    
    from bridge_app.models import SwaggerConnection
    connections = SwaggerConnection.query.all()
    conns_lookup = {str(c.id): c.name for c in connections}
    
    import json
    templates_json = json.dumps([t.to_dict() for t in templates])
    conns_lookup_json = json.dumps(conns_lookup)
    return render_template('templates.html', templates=templates, templates_json=templates_json, conns_lookup_json=conns_lookup_json)
    
@ui_bp.route('/connections')
def connections_page():
    from bridge_app.models import SwaggerConnection
    connections = SwaggerConnection.query.all()
    import json
    conns_json = json.dumps([c.to_dict() for c in connections])
    return render_template('connections.html', connections=connections, conns_json=conns_json)
