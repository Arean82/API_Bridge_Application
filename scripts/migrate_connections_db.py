import os
import sys

# Add parent directory to path to allow importing app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bridge_app.app import create_app
from bridge_app.extensions import db
from sqlalchemy import text

app = create_app()

def migrate():
    with app.app_context():
        # Check current schema
        engine = db.engine
        
        # Determine if sqlite or postgres
        is_sqlite = 'sqlite' in engine.url.drivername
        
        try:
            with engine.connect() as conn:
                print("Checking table columns...")
                if is_sqlite:
                    # SQLite: ALTER TABLE ADD COLUMN
                    try:
                        conn.execute(text("ALTER TABLE swagger_connections ADD COLUMN spec_auth_type VARCHAR(50) DEFAULT 'none'"))
                        print("Added spec_auth_type")
                    except Exception as e:
                        print(f"Skipping spec_auth_type (might exist): {e}")
                        
                    try:
                        conn.execute(text("ALTER TABLE swagger_connections ADD COLUMN spec_auth_config TEXT"))
                        print("Added spec_auth_config")
                    except Exception as e:
                        print(f"Skipping spec_auth_config (might exist): {e}")
                        
                    try:
                        conn.execute(text("ALTER TABLE swagger_connections ADD COLUMN spec_custom_headers TEXT"))
                        print("Added spec_custom_headers")
                    except Exception as e:
                        print(f"Skipping spec_custom_headers (might exist): {e}")
                else:
                    # Postgres
                    try:
                        conn.execute(text("ALTER TABLE swagger_connections ADD COLUMN spec_auth_type VARCHAR(50) DEFAULT 'none'"))
                        print("Added spec_auth_type")
                    except Exception as e:
                        print(f"Skipping spec_auth_type (might exist): {e}")
                        
                    try:
                        conn.execute(text("ALTER TABLE swagger_connections ADD COLUMN spec_auth_config TEXT"))
                        print("Added spec_auth_config")
                    except Exception as e:
                        print(f"Skipping spec_auth_config (might exist): {e}")
                        
                    try:
                        conn.execute(text("ALTER TABLE swagger_connections ADD COLUMN spec_custom_headers TEXT"))
                        print("Added spec_custom_headers")
                    except Exception as e:
                        print(f"Skipping spec_custom_headers (might exist): {e}")
                        
                conn.commit()
                print("Migration completed successfully!")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == '__main__':
    migrate()
