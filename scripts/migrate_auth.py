import os
import sys
import json
import sqlite3

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bridge_app.app import create_app
from bridge_app.extensions import db
from bridge_app.models import SwaggerConnection
from bridge_app.services.encryption import decrypt_token, encrypt_token

def run_migration():
    app = create_app()
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"Connecting to database at {db_path}...")
        
        # 1. Add columns via raw SQLite (idempotent)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(swagger_connections)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'auth_type' not in columns:
            print("Adding auth_type column...")
            cursor.execute("ALTER TABLE swagger_connections ADD COLUMN auth_type VARCHAR(50) DEFAULT 'none'")
        
        if 'auth_config' not in columns:
            print("Adding auth_config column...")
            cursor.execute("ALTER TABLE swagger_connections ADD COLUMN auth_config TEXT")
            
        if 'custom_headers' not in columns:
            print("Adding custom_headers column...")
            cursor.execute("ALTER TABLE swagger_connections ADD COLUMN custom_headers TEXT")
            
        if 'schema_source' not in columns:
            print("Adding schema_source column...")
            cursor.execute("ALTER TABLE swagger_connections ADD COLUMN schema_source VARCHAR(50) DEFAULT 'introspection'")
            
        conn.commit()
        conn.close()
        print("Schema migration complete.")

        # 2. Data Migration: convert _auth_token to auth_config
        connections = SwaggerConnection.query.all()
        migrated_count = 0
        
        for conn in connections:
            # If the connection has a legacy auth token but NO new auth_config
            if conn._auth_token and not conn._auth_config:
                print(f"Migrating legacy token for connection '{conn.name}' (ID: {conn.id})...")
                
                # Decrypt the old token
                decrypted_token = decrypt_token(conn._auth_token)
                
                if decrypted_token:
                    # Create the new JSON structure
                    new_config = {
                        "token": decrypted_token
                    }
                    
                    # Encrypt the JSON and save it
                    conn._auth_config = encrypt_token(json.dumps(new_config))
                    conn.auth_type = 'bearer'
                    
                    migrated_count += 1
                else:
                    print(f"Warning: Could not decrypt legacy token for connection ID {conn.id}.")
            
            # If no legacy token but auth_type is missing, set it to none
            if not conn.auth_type:
                conn.auth_type = 'none'
                
            if not conn.schema_source:
                conn.schema_source = 'introspection'

        db.session.commit()
        print(f"Data migration complete. Migrated {migrated_count} connections.")

if __name__ == "__main__":
    run_migration()
