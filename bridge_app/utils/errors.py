# ==================================================================
# File: bridge_app/utils/errors.py
# Description: Custom error classes and exception handlers.
# ==================================================================

from flask import jsonify

class APIError(Exception):
    """
    Base API Exception class for uniform error handling.
    """
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['status'] = 'error'
        rv['message'] = self.message
        rv['code'] = self.status_code
        return rv

def register_error_handlers(app):
    """
    Registers global error handlers on the Flask application.
    """
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
        
    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify({
            'status': 'error',
            'message': 'Resource not found',
            'code': 404
        }), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({
            'status': 'error',
            'message': 'An internal server error occurred',
            'code': 500
        }), 500
