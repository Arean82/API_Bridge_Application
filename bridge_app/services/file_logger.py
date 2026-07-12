# ==================================================================
# File: bridge_app/services/file_logger.py
# Description: File-based logging utility service.
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

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from flask import current_app

_loggers = {}

def get_connection_logger(connection_name):
    """
    Returns a configured file logger for a specific Swagger Connection.
    Logs are placed in <log_dir>/<connection_name>/sync.log and rotated daily.
    """
    if connection_name in _loggers:
        return _loggers[connection_name]
        
    # Get configuration safely, fallback if outside app context
    log_dir = 'logs'
    rotation = 'midnight'
    backup_count = 30
    
    try:
        if current_app:
            log_dir = current_app.config.get('LOG_DIR', log_dir)
            rotation = current_app.config.get('LOG_ROTATION', rotation)
            backup_count = current_app.config.get('LOG_BACKUP_COUNT', backup_count)
    except RuntimeError:
        pass # Not in app context, use defaults

    # Create the directory structure: logs/<connection_name>
    # Safe the connection name to avoid path traversal or illegal characters
    safe_name = "".join([c for c in connection_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    if not safe_name:
        safe_name = "Unknown_Connection"
        
    conn_log_dir = os.path.join(log_dir, safe_name)
    os.makedirs(conn_log_dir, exist_ok=True)
    
    log_file_path = os.path.join(conn_log_dir, 'sync.log')
    
    # Create the logger
    logger = logging.getLogger(f"connection_{safe_name}")
    logger.setLevel(logging.INFO)
    
    # Prevent adding multiple handlers if function is called multiple times
    if not logger.handlers:
        handler = TimedRotatingFileHandler(
            filename=log_file_path,
            when=rotation,
            interval=1,
            backupCount=backup_count,
            encoding='utf-8'
        )
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    _loggers[connection_name] = logger
    return logger
