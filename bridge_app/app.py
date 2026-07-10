# ==================================================================
# File: bridge_app/app.py
# Description: Main entry point and factory for the Flask application.
# ==================================================================

from flask import Flask
from bridge_app.config import Config
from bridge_app.extensions import db, scheduler
from bridge_app.controllers import ui_bp, api_bp, obs_bp

# OpenTelemetry imports
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

current_app_instance = None

def create_app(config_class=Config):
    global current_app_instance
    app = Flask(__name__)
    current_app_instance = app
    app.config.from_object(config_class)

    # Enable CORS for API Mock endpoints
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize OpenTelemetry Trace Provider with OTLP Exporter if enabled
    import configparser
    import os
    import sys
    
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        
    config_ini = configparser.ConfigParser()
    config_ini.read(os.path.join(base_dir, 'config.ini'))
    otlp_enabled = config_ini.getboolean('OPENTELEMETRY', 'enabled', fallback=False)
    
    if otlp_enabled and not isinstance(trace.get_tracer_provider(), TracerProvider):
        provider = TracerProvider()
        otlp_endpoint = app.config.get('OTLP_ENDPOINT', 'http://localhost:4318/v1/traces')
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(provider)

    # Instrument Flask and requests
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()

    # Initialize extensions
    db.init_app(app)
    
    # Initialize Scheduler
    scheduler.init_app(app)
    
    # FIX: Prevent zombie/duplicate scheduler processes when running with Flask reloader.
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug or os.environ.get('FLASK_DEBUG') != 'True':
        scheduler.start()

    # Register Blueprints
    app.register_blueprint(ui_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(obs_bp)

    # Register Global Error Handlers
    from bridge_app.utils.errors import register_error_handlers
    register_error_handlers(app)

    from bridge_app.config import get_theme
    @app.context_processor
    def inject_theme():
        return dict(
            current_theme=get_theme(),
            app_timezone=app.config.get('APP_TIMEZONE', 'UTC'),
            ui_date_format=app.config.get('UI_DATE_FORMAT', 'DD/MM/YYYY HH:mm:ss')
        )

    # Create tables and schedule jobs
    with app.app_context():
        db.create_all()
        
        from bridge_app.models import JobModel
        from bridge_app.services.task_runner import pull_and_push_job
        from bridge_app.services.swagger_utils import update_swagger_connections
        jobs = JobModel.query.filter_by(is_active=True).all()
        for job in jobs:
            job_id = f"job_{job.id}"
            scheduler.add_job(
                id=job_id, 
                func=pull_and_push_job, 
                args=[job.id], 
                trigger='interval', 
                seconds=job.schedule_interval,
                replace_existing=True
            )
            
        # Schedule the background update for Swagger connections
        interval = app.config.get('SWAGGER_REFRESH_INTERVAL', 1)
        unit = app.config.get('SWAGGER_REFRESH_UNIT', 'hours')
        trigger_kwargs = {unit: interval}
        
        scheduler.add_job(
            id='swagger_updater',
            func=update_swagger_connections,
            trigger='interval',
            replace_existing=True,
            **trigger_kwargs
        )

        from bridge_app.services.cleanup import cleanup_failed_payloads
        # Schedule the background cleanup for failed payloads (e.g., every 5 minutes)
        scheduler.add_job(
            id='failed_payloads_cleanup',
            func=cleanup_failed_payloads,
            trigger='interval',
            minutes=5,
            replace_existing=True
        )

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, use_reloader=False) # use_reloader=False to prevent duplicate scheduler starts
