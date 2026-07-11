# ==================================================================
# File: bridge_app/services/cleanup.py
# Description: Background service for cleaning up old payloads and logs.
# ==================================================================


def cleanup_failed_payloads():
    """
    Background job to prune FailedPayload records older than retention_minutes.
    """
    from bridge_app.app import current_app_instance
    if not current_app_instance:
        from bridge_app.app import create_app
        current_app_instance = create_app()
    with current_app_instance.app_context():
        from bridge_app.models.failed_payload import FailedPayload
        from bridge_app.extensions import db
        from datetime import datetime, timedelta
    
        retention_minutes = current_app_instance.config.get('RETRY_QUEUE_RETENTION_MINUTES', 60)
        cutoff_time = datetime.utcnow() - timedelta(minutes=retention_minutes)
    
        try:
            deleted_count = FailedPayload.query.filter(FailedPayload.timestamp < cutoff_time).delete()
            db.session.commit()
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} expired failed payloads.")
        except Exception as e:
            print(f"Failed to cleanup payloads: {e}")
