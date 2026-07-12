# ==================================================================
# File: bridge_app/controllers/health_controller.py
# Description: Production Health Probes for orchestration.
# ==================================================================

from flask import Blueprint, jsonify
from bridge_app.extensions import db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health/live', methods=['GET'])
def liveness_probe():
    """Liveness probe to check if the application is running."""
    return jsonify({"status": "alive"}), 200

@health_bp.route('/health/ready', methods=['GET'])
def readiness_probe():
    """Readiness probe to check if the application is ready to serve traffic."""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        return jsonify({"status": "ready", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "not_ready", "error": str(e)}), 503
