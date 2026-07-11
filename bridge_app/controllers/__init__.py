# ==================================================================
# File: bridge_app/controllers/__init__.py
# Description: Controller package initialization.
# ==================================================================

from .ui_controller import ui_bp
from .engine_controller import api_bp

# Register all routes on api_bp
from . import template_controller
from . import job_controller
from . import connection_controller
from . import pull_controller

from .observability_controller import obs_bp
