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

import json

def get_theme():
    config_ini.read(config_path)
    if not config_ini.has_section('UI'):
        return json.dumps({"theme": "default", "colorMode": "auto"})
    
    theme_val = config_ini.get('UI', 'theme', fallback='default')
    color_mode = config_ini.get('UI', 'colorMode', fallback='auto')
    return json.dumps({"theme": theme_val, "colorMode": color_mode})

def set_theme(theme_name, color_mode):
    if not config_ini.has_section('UI'):
        config_ini.add_section('UI')
    config_ini.set('UI', 'theme', theme_name)
    config_ini.set('UI', 'colorMode', color_mode)
    with open(config_path, 'w') as configfile:
        config_ini.write(configfile)

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
    
    # Logging Configuration
    LOG_DIR = config_ini.get('Logging', 'log_dir', fallback='logs')
    LOG_ROTATION = config_ini.get('Logging', 'rotation', fallback='midnight')
    if LOG_ROTATION.lower() == 'daily':
        LOG_ROTATION = 'midnight'
    LOG_BACKUP_COUNT = config_ini.getint('Logging', 'backup_count', fallback=30)
