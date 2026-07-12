# ==================================================================
# File: bridge_app/config.py
# Description: Application configuration, secrets, and database paths.
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
from dotenv import load_dotenv
import configparser
import json

load_dotenv()

# Load config.ini
import sys
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

config_ini = configparser.ConfigParser()
config_path = os.path.join(base_dir, 'config.ini')
config_ini.read(config_path)

def get_theme():
    config_ini.read(config_path)
    if not config_ini.has_section('UI'):
        return json.dumps({"theme": "default", "colorMode": "auto"})
    
    theme_val = config_ini.get('UI', 'theme', fallback='default')
    color_mode = config_ini.get('UI', 'colorMode', fallback='auto')
    return json.dumps({"theme": theme_val, "colorMode": color_mode})

def set_theme(theme_name, color_mode):
    import re
    with open(config_path, 'r') as f:
        content = f.read()
        
    if not '[UI]' in content:
        content += f"\n[UI]\ntheme = {theme_name}\ncolormode = {color_mode}\n"
    else:
        content = re.sub(r'theme\s*=\s*.*', f'theme = {theme_name}', content)
        content = re.sub(r'colormode\s*=\s*.*', f'colormode = {color_mode}', content)
        
    with open(config_path, 'w') as f:
        f.write(content)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    raw_env = config_ini.get('Server', 'environment', fallback='development')
    env = raw_env.split('#')[0].strip().strip('"').strip("'").lower()
    
    # Check if a custom URI is provided in config.ini
    custom_uri = config_ini.get('Database', 'uri', fallback='')
    if custom_uri.strip():
        SQLALCHEMY_DATABASE_URI = custom_uri
    elif env == 'production':
        pg_host = config_ini.get('POSTGRES', 'host', fallback='localhost')
        pg_port = config_ini.get('POSTGRES', 'port', fallback='5432')
        pg_db = config_ini.get('POSTGRES', 'database', fallback='bridge_db')
        pg_user = config_ini.get('POSTGRES', 'username', fallback='postgres')
        pg_pass = config_ini.get('POSTGRES', 'password', fallback='')
        SQLALCHEMY_DATABASE_URI = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    else:
        # Get sqlite path and name from config.ini
        sqlite_path = config_ini.get('SQLITE', 'path', fallback='instance')
        sqlite_db_name = config_ini.get('SQLITE', 'database', fallback='bridge_app.db')
        
        if not os.path.isabs(sqlite_path):
            sqlite_path = os.path.join(os.path.dirname(basedir), sqlite_path)
            
        os.makedirs(sqlite_path, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(sqlite_path, sqlite_db_name)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenTelemetry configuration
    OTLP_ENDPOINT = config_ini.get('OPENTELEMETRY', 'otlp_endpoint', fallback='http://localhost:4318/v1/traces')
    SCHEDULER_API_ENABLED = True
    
    # Timezone & Formatting
    APP_TIMEZONE = config_ini.get('Server', 'timezone', fallback='Asia/Kolkata')
    UI_DATE_FORMAT = config_ini.get('UI', 'date_format', fallback='DD/MM/YYYY HH:mm:ss')
    
    # Logging Configuration
    LOG_DIR = config_ini.get('Logging', 'log_dir', fallback='logs')
    LOG_ROTATION = config_ini.get('Logging', 'rotation', fallback='midnight')
    if LOG_ROTATION.lower() == 'daily':
        LOG_ROTATION = 'midnight'
    LOG_BACKUP_COUNT = config_ini.getint('Logging', 'backup_count', fallback=30)
    
    # Retry Queue Configuration
    RETRY_QUEUE_RETENTION_MINUTES = config_ini.getint('RetryQueue', 'retention_minutes', fallback=60)
    
    # Swagger Configuration
    SWAGGER_REFRESH_INTERVAL = config_ini.getint('Swagger', 'refresh_interval', fallback=1)
    SWAGGER_REFRESH_UNIT = config_ini.get('Swagger', 'refresh_unit', fallback='hours')
    
    # Scheduler Execution & Scale-Out Configuration
    from apscheduler.executors.pool import ThreadPoolExecutor
    from apscheduler.jobstores.memory import MemoryJobStore
    
    SCHEDULER_EXECUTORS = {
        'default': ThreadPoolExecutor(max_workers=200)
    }
    
    # Optional Redis configuration for multi-node locking
    REDIS_URL = config_ini.get('Server', 'redis_url', fallback='')
    
    if REDIS_URL.strip():
        from apscheduler.jobstores.redis import RedisJobStore
        import urllib.parse
        parsed = urllib.parse.urlparse(REDIS_URL.strip())
        connect_args = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 6379,
            'db': int(parsed.path.lstrip('/') or '0')
        }
        if parsed.password:
            connect_args['password'] = parsed.password
            
        SCHEDULER_JOBSTORES = {
            'default': RedisJobStore(jobs_key='bridge_jobs', run_times_key='bridge_run_times', **connect_args)
        }
    else:
        SCHEDULER_JOBSTORES = {
            'default': MemoryJobStore()
        }
