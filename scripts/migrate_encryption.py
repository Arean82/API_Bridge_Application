import os
import sys
import base64
import secrets

# Add project root to python path so we can import bridge_app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bridge_app.app import create_app
from bridge_app.extensions import db
from sqlalchemy import text
from bridge_app.models.swagger_connection import SwaggerConnection
from bridge_app.services.encryption import encrypt_token

def generate_env_key_if_missing():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    
    # Check if ENCRYPTION_KEY exists in file
    key_exists = False
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('ENCRYPTION_KEY='):
                    key_exists = True
                    break
                    
    if not key_exists:
        # Generate 256-bit AES-GCM key (32 bytes)
        new_key = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
        with open(env_path, 'a') as f:
            f.write(f"\nENCRYPTION_KEY={new_key}\n")
        print("Generated new ENCRYPTION_KEY in .env file.")
        
        # Reload dotenv so os.environ is updated for the rest of the script
        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)

def run_migration():
    app = create_app()
    with app.app_context():
        # Step 1: Schema Migration (Add missing columns)
        print("Checking database schema...")
        columns_to_add = {
            "auth_token": "VARCHAR(1000)",
            "sync_schedule": "VARCHAR(100)",
            "environments": "TEXT"
        }
        for col_name, col_type in columns_to_add.items():
            try:
                db.session.execute(text(f"ALTER TABLE swagger_connections ADD COLUMN {col_name} {col_type}"))
                db.session.commit()
                print(f"Added column {col_name}.")
            except Exception:
                db.session.rollback()
                
        # Step 2: Data Migration (Encrypt legacy tokens)
        print("Scanning existing connections for unencrypted tokens...")
        connections = SwaggerConnection.query.all()
        encrypted_count = 0
        
        for conn in connections:
            raw_token = conn._auth_token
            if raw_token:
                # Check if it looks like a valid base64 token of minimum 28 bytes
                is_legacy = False
                try:
                    decoded = base64.b64decode(raw_token.encode('utf-8'))
                    if len(decoded) < 28:
                        is_legacy = True
                except Exception:
                    is_legacy = True
                    
                if is_legacy:
                    # Encrypt the plain text and save it to the raw column
                    conn._auth_token = encrypt_token(raw_token)
                    encrypted_count += 1
                    
        if encrypted_count > 0:
            db.session.commit()
            print(f"Successfully encrypted {encrypted_count} legacy tokens!")
        else:
            print("No unencrypted legacy tokens found. Data is secure.")

if __name__ == '__main__':
    print("Starting migration...")
    generate_env_key_if_missing()
    run_migration()
    print("Migration complete!")
