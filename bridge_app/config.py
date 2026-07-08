# ==================================================================
# File: bridge_app/config.py
# Description: Application configuration, secrets, and database paths.
# ==================================================================

import os
from dotenv import load_dotenv

load_dotenv()

import configparser

load_dotenv()

# Load config.ini
config_ini = configparser.ConfigParser()
config_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'config.ini')
config_ini.read(config_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Check if a custom URI is provided in config.ini
    custom_uri = config_ini.get('Database', 'uri', fallback='')
    if custom_uri.strip():
        SQLALCHEMY_DATABASE_URI = custom_uri
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'bridge.db')
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCHEDULER_API_ENABLED = True
