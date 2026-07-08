# ==================================================================
# File: bridge_app/controllers/ui_controller.py
# Description: Web routes for rendering the dashboard UI.
# ==================================================================

from flask import Blueprint, render_template

from bridge_app.models import TemplateModel, JobModel, JobLog

ui_bp = Blueprint('ui', __name__)

@ui_bp.route('/')
def index():
    return render_template('index.html')

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
            
    return render_template('create_template.html', clone_data=clone_data)

@ui_bp.route('/templates')
def templates_page():
    templates = TemplateModel.query.all()
    
    import json
    templates_json = json.dumps([t.to_dict() for t in templates])
    
    return render_template('templates.html', templates=templates, templates_json=templates_json)
