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
    from bridge_app.models import SwaggerConnection
    connections = SwaggerConnection.query.all()
    conns_json = json.dumps([c.to_dict() for c in connections])
            
    return render_template('create_template.html', clone_data=clone_data, conns_json=conns_json)

@ui_bp.route('/templates')
def templates_page():
    templates = TemplateModel.query.all()
    
    import json
    templates_json = json.dumps([t.to_dict() for t in templates])
    
@ui_bp.route('/connections')
def connections_page():
    from bridge_app.models import SwaggerConnection
    connections = SwaggerConnection.query.all()
    import json
    conns_json = json.dumps([c.to_dict() for c in connections])
    return render_template('connections.html', connections=connections, conns_json=conns_json)
