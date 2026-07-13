# ==================================================================
# File: bridge_app/controllers/ui_controller.py
# Description: Routes for serving frontend HTML templates.
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

from flask import Blueprint, render_template

from bridge_app.models import TemplateModel, JobModel, JobLog

ui_bp = Blueprint('ui', __name__)

@ui_bp.route('/jobs')
def jobs_page():
    return render_template('jobs.html')

@ui_bp.route('/docs/<int:id>')
def swagger_docs(id):
    from bridge_app.models import SwaggerConnection
    from bridge_app.services.swagger_utils import fix_swagger_urls
    import json
    conn = SwaggerConnection.query.get_or_404(id)
    
    if conn.json_content and conn.url:
        try:
            data = json.loads(conn.json_content)
            conn.json_content = fix_swagger_urls(data, conn.url)
        except Exception:
            pass
            
    return render_template('swagger_ui.html', conn=conn)

@ui_bp.route('/graphql/test/<int:id>')
def graphql_docs(id):
    from bridge_app.models import SwaggerConnection
    conn = SwaggerConnection.query.get_or_404(id)
    if conn.connection_type != 'graphql':
        from flask import abort
        abort(400, "Not a GraphQL connection")
    return render_template('graphql_ui.html', conn=conn)

@ui_bp.route('/')
def index():
    return render_template('index.html')

@ui_bp.route('/audit-logs')
def audit_logs_page():
    from bridge_app.models.audit_log import AuditLog
    # Fetch top 100 most recent logs
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('audit_logs.html', logs=logs)

@ui_bp.route('/htmx/audit/<int:log_id>')
def htmx_audit_details(log_id):
    from bridge_app.models.audit_log import AuditLog
    import json
    log = AuditLog.query.get_or_404(log_id)
    
    formatted_payload = ""
    if log.payload_json:
        try:
            parsed = json.loads(log.payload_json)
            formatted_payload = json.dumps(parsed, indent=2)
        except Exception:
            formatted_payload = log.payload_json
            
    return render_template('partials/audit_details_modal.html', log=log, formatted_payload=formatted_payload)

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
    db.session.commit()
    return _render_dashboard_rows()

@ui_bp.route('/htmx/dashboard/jobs/bulk_toggle', methods=['POST'])
def htmx_bulk_toggle_jobs():
    from bridge_app.models import JobModel
    from bridge_app.extensions import db, scheduler
    from bridge_app.services.task_runner import pull_and_push_job
    from flask import current_app, request
    
    action = request.form.get('action') # 'start' or 'stop'
    job_ids_str = request.form.get('job_ids', '')
    if not job_ids_str:
        return _render_dashboard_rows()
        
    try:
        job_ids = [int(jid.strip()) for jid in job_ids_str.split(',') if jid.strip()]
        jobs = JobModel.query.filter(JobModel.id.in_(job_ids)).all()
        app = current_app._get_current_object()
        
        for job in jobs:
            job_name = f"job_{job.id}"
            if action == 'start' and not job.is_active:
                job.is_active = True
                try:
                    scheduler.add_job(
                        id=job_name, 
                        func=pull_and_push_job, 
                        args=[job.id], 
                        trigger='interval', 
                        seconds=job.schedule_interval,
                        replace_existing=True
                    )
                except Exception:
                    pass
            elif action == 'stop' and job.is_active:
                job.is_active = False
                try:
                    scheduler.remove_job(job_name)
                except Exception:
                    pass
                    
        db.session.commit()
    except Exception as e:
        print(f"Bulk action error: {e}")
        
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

@ui_bp.route('/htmx/docs/<filename>')
def htmx_docs(filename):
    import os
    
    if '..' in filename or '/' in filename:
        return "Invalid filename", 400
        
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    if filename == 'README.md':
        file_path = os.path.join(base_dir, filename)
    else:
        file_path = os.path.join(base_dir, 'docs', filename)
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
            
        return md_content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return f"Error loading document: {e}", 500

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


@ui_bp.route('/settings', methods=['GET'])
def settings_page():
    import os
    import configparser
    from flask import current_app
    
    config = configparser.ConfigParser()
    base_dir = os.path.dirname(current_app.root_path)
    config.read(os.path.join(base_dir, 'config.ini'))
    
    return render_template('settings.html', config=config)

@ui_bp.route('/settings/save', methods=['POST'])
def save_settings():
    import os
    import sys
    import configparser
    from flask import current_app, request, redirect, url_for
    
    base_dir = os.path.dirname(current_app.root_path)
    config_path = os.path.join(base_dir, 'config.ini')
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Store old core settings to detect restart requirement
    old_server_host = config.get('Server', 'host', fallback='0.0.0.0')
    old_server_port = config.get('Server', 'port', fallback='5000')
    old_db_host = config.get('POSTGRES', 'host', fallback='')
    old_db_name = config.get('POSTGRES', 'database', fallback='')
    
    needs_restart = False
    
    # Update config from form
    for key, val in request.form.items():
        if '.' in key:
            section, option = key.split('.', 1)
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, option, val)
            
    # Check if checkbox was unchecked (form doesn't send unchecked boxes)
    if 'Server.debug' not in request.form:
        if config.has_section('Server'):
            config.set('Server', 'debug', 'False')
            
    with open(config_path, 'w') as f:
        config.write(f)
        
    # Check if restart is needed
    if (config.get('Server', 'host', fallback='') != old_server_host or
        config.get('Server', 'port', fallback='') != old_server_port or
        config.get('POSTGRES', 'host', fallback='') != old_db_host or
        config.get('POSTGRES', 'database', fallback='') != old_db_name):
        needs_restart = True
        
    if needs_restart:
        # Trigger an os.execl to restart the server
        print('[System] Core settings changed. Rebooting server...')
        python = sys.executable
        os.execl(python, python, *sys.argv)
        
    return redirect(url_for('ui.settings_page'))

# ==========================================
# Email Templates Editor Routes
# ==========================================
@ui_bp.route('/htmx/email_templates', methods=['GET'])
def htmx_email_templates_modal():
    import os
    from flask import current_app
    
    base_dir = os.path.dirname(current_app.root_path)
    email_dir = os.path.join(base_dir, 'bridge_app', 'templates', 'email')
    
    # Ensure directory exists
    os.makedirs(email_dir, exist_ok=True)
    
    template_files = [f for f in os.listdir(email_dir) if f.endswith('.html')]
    
    return render_template('partials/email_templates_modal.html', template_files=template_files)

@ui_bp.route('/htmx/email_templates/<filename>', methods=['GET'])
def htmx_get_email_template(filename):
    import os
    from flask import current_app
    
    if not filename.endswith('.html'):
        return "Invalid file type", 400
        
    base_dir = os.path.dirname(current_app.root_path)
    file_path = os.path.join(base_dir, 'bridge_app', 'templates', 'email', filename)
    
    if not os.path.exists(file_path):
        return "Template not found", 404
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return render_template('partials/email_template_editor.html', filename=filename, content=content)
    except Exception as e:
        return f"Error reading file: {e}", 500

@ui_bp.route('/htmx/email_templates/<filename>', methods=['POST'])
def htmx_save_email_template(filename):
    import os
    from flask import current_app, request
    
    if not filename.endswith('.html'):
        return "Invalid file type", 400
        
    base_dir = os.path.dirname(current_app.root_path)
    file_path = os.path.join(base_dir, 'bridge_app', 'templates', 'email', filename)
    
    new_content = request.form.get('template_content', '')
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return render_template('partials/email_template_editor.html', filename=filename, content=new_content, success_msg="Template saved successfully!")
    except Exception as e:
        # Re-read original to not lose content in editor
        content = new_content
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        return render_template('partials/email_template_editor.html', filename=filename, content=content, error_msg=f"Failed to save: {e}")
