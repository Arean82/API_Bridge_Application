# ==================================================================
# File: bridge_app/services/email_service.py
# Description: Service for dispatching email alerts.
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
import configparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# In-memory dictionary for throttling: { "job_id": datetime_object }
_last_email_sent = {}

def get_config():
    """Load config.ini."""
    from bridge_app.app import current_app_instance
    if current_app_instance:
        base_dir = os.path.dirname(current_app_instance.root_path)
    else:
        # Fallback if outside app context
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
    config = configparser.ConfigParser()
    config_path = os.path.join(base_dir, 'config.ini')
    config.read(config_path)
    return config

def should_throttle(job_id, config):
    """Check if we should throttle the email for this job."""
    try:
        throttle_enabled = config.getboolean('Email', 'throttle_enabled', fallback=False)
        if not throttle_enabled:
            return False
            
        throttle_minutes = config.getint('Email', 'throttle_minutes', fallback=60)
        
        last_sent = _last_email_sent.get(job_id)
        if last_sent:
            now = datetime.now()
            if (now - last_sent) < timedelta(minutes=throttle_minutes):
                return True # Throttle
                
        # If we reach here, we are not throttling. Update timestamp.
        _last_email_sent[job_id] = datetime.now()
        return False
    except Exception as e:
        print(f"Error checking email throttle: {e}")
        return False

def send_failure_alert(job_id, template_name, dest_url, error_msg):
    """Dispatch an email alert if configured."""
    config = get_config()
    mode = config.get('Email', 'mode', fallback='none').lower()
    
    if mode == 'none' or not mode:
        return
        
    if should_throttle(job_id, config):
        print(f"Email alert for Job {job_id} throttled (cooldown active).")
        return
        
    sender = config.get('Email', 'sender_email', fallback='noreply@bridge-app.local')
    recipients_raw = config.get('Email', 'recipient_emails', fallback='')
    recipients = [email.strip() for email in recipients_raw.split(',') if email.strip()]
    
    if not recipients:
        print("Email service is active but no recipients configured.")
        return

    from flask import render_template
    
    subject = f"Alert: Schedule Job {job_id} ({template_name}) Failed"
    
    try:
        html_content = render_template('email/failure_alert.html', 
                                       job_id=job_id, 
                                       template_name=template_name,
                                       dest_url=dest_url,
                                       error_msg=error_msg,
                                       timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        print(f"Error rendering email template: {e}")
        # Fallback raw HTML
        html_content = f"<h2>Schedule Failure Alert</h2><p>Job ID: {job_id}</p><pre>{error_msg}</pre>"

    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)
    msg.attach(MIMEText("Please view this email in an HTML compatible client.", "plain"))
    msg.attach(MIMEText(html_content, "html"))

    if mode == 'local':
        try:
            # Use local system MTA (localhost:25) without auth
            with smtplib.SMTP('localhost', 25) as server:
                server.sendmail(sender, recipients, msg.as_string())
            print(f"Sent local failure alert for Job {job_id}")
        except Exception as e:
            print(f"Failed to send local email alert: {e}")
            
    elif mode == 'smtp':
        try:
            host = config.get('Email', 'smtp_host', fallback='smtp.gmail.com')
            port = config.getint('Email', 'smtp_port', fallback=587)
            user = config.get('Email', 'smtp_user', fallback='')
            password = config.get('Email', 'smtp_password', fallback='')
            
            with smtplib.SMTP(host, port) as server:
                server.starttls()
                if user and password:
                    server.login(user, password)
                server.sendmail(sender, recipients, msg.as_string())
            print(f"Sent SMTP failure alert for Job {job_id}")
        except Exception as e:
            print(f"Failed to send SMTP email alert: {e}")
