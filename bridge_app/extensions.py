# ==================================================================
# File: bridge_app/extensions.py
# Description: Initializes Flask extensions like SQLAlchemy and APScheduler.
# ==================================================================

from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

db = SQLAlchemy()
scheduler = APScheduler()
