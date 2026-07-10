# ==================================================================
# File: bridge_app/extensions.py
# Description: Flask extensions initialization (db, scheduler, etc).
# ==================================================================

from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

db = SQLAlchemy()
scheduler = APScheduler()
