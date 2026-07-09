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
    import sys
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        
    config_ini = configparser.ConfigParser()
    config_path = os.path.join(base_dir, 'config.ini')
    config_ini.read(config_path)

    # Read variables with fallbacks
    server_host = config_ini.get('Server', 'host', fallback='0.0.0.0')
    server_port = config_ini.getint('Server', 'port', fallback=5000)
    server_debug = config_ini.getboolean('Server', 'debug', fallback=False)



    # When running as a PyInstaller executable or normal script
    # use_reloader=False is crucial to avoid duplicate APScheduler jobs!
    app.run(host=server_host, port=server_port, debug=server_debug, use_reloader=False)
