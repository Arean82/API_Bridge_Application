# ==================================================================
# File: run.py
# Description: Main entry point from the root directory.
# ==================================================================

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from bridge_app.app import create_app
import configparser

app = create_app()

if __name__ == '__main__':
    # Load config.ini
    config_ini = configparser.ConfigParser()
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini')
    config_ini.read(config_path)

    # Read variables with fallbacks
    server_host = config_ini.get('Server', 'host', fallback='0.0.0.0')
    server_port = config_ini.getint('Server', 'port', fallback=5000)
    server_debug = config_ini.getboolean('Server', 'debug', fallback=False)

    # Lightweight DB Migration (Zero data loss)
    with app.app_context():
        from bridge_app.extensions import db
        from sqlalchemy import text
        
        columns_to_add = {
            "auth_token": "VARCHAR(1000)",
            "sync_schedule": "VARCHAR(100)",
            "environments": "TEXT"
        }
        for col_name, col_type in columns_to_add.items():
            try:
                db.session.execute(text(f"ALTER TABLE swagger_connections ADD COLUMN {col_name} {col_type}"))
                db.session.commit()
            except Exception:
                db.session.rollback() # Column likely already exists

    # When running as a PyInstaller executable or normal script
    # use_reloader=False is crucial to avoid duplicate APScheduler jobs!
    app.run(host=server_host, port=server_port, debug=server_debug, use_reloader=False)
