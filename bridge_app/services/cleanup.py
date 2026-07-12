# ==================================================================
# File: bridge_app/services/cleanup.py
# Description: Background service for cleaning up old payloads and logs.
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
