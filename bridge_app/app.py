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
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Initialize OpenTelemetry Trace Provider
trace.set_tracer_provider(TracerProvider())
# For MVP, we use ConsoleSpanExporter. In prod, switch to OTLPExporter.
# trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

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

    # Create tables and schedule jobs
    with app.app_context():
        db.create_all()
        
        from bridge_app.models import JobModel
        from bridge_app.services.task_runner import pull_and_push_job
        jobs = JobModel.query.filter_by(is_active=True).all()
        for job in jobs:
            job_id = f"job_{job.id}"
            scheduler.add_job(
                id=job_id, 
                func=pull_and_push_job, 
                args=[app, job.id], 
                trigger='interval', 
                seconds=job.schedule_interval,
                replace_existing=True
            )

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, use_reloader=False) # use_reloader=False to prevent duplicate scheduler starts
