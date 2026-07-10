# ==================================================================
# File: bridge_app/services/swagger_utils.py
# Description: Swagger/OpenAPI utilities — URL fixing, JSON fetching,
#              and background connection refresh.
# ==================================================================

import requests
import re
import json
from urllib.parse import urlparse, urljoin


def fix_swagger_urls(data, source_url):
    """Fix relative URLs in Swagger/OpenAPI spec to use the source URL's base."""
    parsed = urlparse(source_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    if 'servers' in data:
        for server in data['servers']:
            if server.get('url', '').startswith('/'):
                server['url'] = base_url + server['url']
    elif 'host' not in data:
        data['host'] = parsed.netloc
        if 'schemes' not in data:
            data['schemes'] = [parsed.scheme]
            
    if 'info' in data and isinstance(data['info'], dict) and data['info'].get('description'):
        desc = data['info']['description']
        # Fix relative markdown links
        desc = re.sub(
            r'\[([^\]]+)\]\((/[^)]+)\)',
            lambda m: f'[{m.group(1)}]({base_url}{m.group(2)})',
            desc
        )
        data['info']['description'] = desc
        
    return data


def fetch_swagger_json(url):
    """
    Fetch Swagger/OpenAPI JSON from a URL.
    If the URL returns HTML instead of JSON, attempt to extract
    the spec URL from the HTML and fetch that instead.
    Returns (json_text, actual_url) tuple.
    """
    resp = requests.get(url, timeout=10)
    if not resp.ok:
        raise ValueError(f"HTTP {resp.status_code}")
        
    try:
        data = resp.json()
        return fix_swagger_urls(data, url), url
    except Exception:
        html = resp.text
        match = re.search(r'url:\s*["\']([^"\']+)["\']', html)
        if match:
            json_url = urljoin(url, match.group(1))
            resp2 = requests.get(json_url, timeout=10)
            if not resp2.ok:
                raise ValueError(f"Extracted JSON URL {json_url} but got HTTP {resp2.status_code}")
            try:
                data = resp2.json()
                return fix_swagger_urls(data, json_url), json_url
            except Exception:
                pass
        raise ValueError("URL does not return valid JSON and no Swagger URL could be extracted.")


def update_swagger_connections():
    """Background job to refresh Swagger JSON content for remote connections."""
    from bridge_app.app import current_app_instance
    if not current_app_instance:
        from bridge_app.app import create_app
        current_app_instance = create_app()
    with current_app_instance.app_context():
        from bridge_app.models import SwaggerConnection
        from bridge_app.extensions import db
        from datetime import datetime
    
        from bridge_app.services.file_logger import get_connection_logger
    
        # Get connections that are remote and URL is not null
        conns = SwaggerConnection.query.filter_by(is_local_file=False).all()
        for conn in conns:
            if not conn.url:
                continue
            
            # Respect individual sync_schedule
            if conn.sync_schedule:
                from datetime import timedelta
                now = datetime.utcnow()
                if conn.sync_schedule == 'hourly' and conn.last_updated and (now - conn.last_updated) < timedelta(hours=1):
                    continue
                elif conn.sync_schedule == 'daily' and conn.last_updated and (now - conn.last_updated) < timedelta(days=1):
                    continue
                elif conn.sync_schedule == 'weekly' and conn.last_updated and (now - conn.last_updated) < timedelta(weeks=1):
                    continue
        
            logger = get_connection_logger(conn.name)
            logger.info(f"Starting sync for SwaggerConnection: {conn.name} (URL: {conn.url})")
        
            try:
                resp = requests.get(conn.url, timeout=10)
                if resp.ok:
                    conn.json_content = resp.text
                    conn.last_updated = datetime.utcnow()
                    db.session.commit()
                    msg = f"Successfully updated SwaggerConnection {conn.name} (ID: {conn.id})"
                    print(msg)
                    logger.info(msg)
                else:
                    msg = f"Failed to update SwaggerConnection {conn.name} (ID: {conn.id}): HTTP {resp.status_code}"
                    print(msg)
                    logger.error(msg)
            except Exception as e:
                msg = f"Error updating SwaggerConnection {conn.name} (ID: {conn.id}): {e}"
                print(msg)
                logger.error(msg)
