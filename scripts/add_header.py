# ==================================================================
# File: scripts/add_header.py
# Description: Automatically adds standard headers to Python files.
# ==================================================================

import os

HEADER_TEMPLATE = """# ==================================================================
# File: {filepath}
# Description: 
# ==================================================================

"""

def add_header_to_file(filepath, relative_path):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if content.startswith("# =================================================================="):
        print(f"Skipping (Header already exists): {relative_path}")
        return
        
    header = HEADER_TEMPLATE.format(filepath=relative_path.replace('\\', '/'))
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header + content)
        
    print(f"Added header to: {relative_path}")

def scan_and_add_headers(root_dir):
    for root, dirs, files in os.walk(root_dir):
        # Skip virtual environments and caches
        dirs[:] = [d for d in dirs if d not in ('venv', 'env', '__pycache__', '.git', 'node_modules')]
        
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                add_header_to_file(full_path, rel_path)

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("Scanning for Python files...")
    scan_and_add_headers(project_root)
    print("Done adding headers.")
