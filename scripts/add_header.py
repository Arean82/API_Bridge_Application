import os
import re

def add_header_to_file(filepath, relative_path):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='utf-16') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"Skipping (Unknown Encoding): {relative_path}")
            return
    except Exception as e:
        print(f"Skipping (Error reading): {relative_path} - {e}")
        return
        
    # Extract description if exists
    desc_pattern = r'^# Description:\s*(.*?)\n'
    desc_match = re.search(desc_pattern, content, flags=re.MULTILINE)
    description = desc_match.group(1) if desc_match else ""
    
    header_pattern = r'^# ==================================================================.*?# ==================================================================\n+'
    new_content = re.sub(header_pattern, '', content, flags=re.DOTALL)
    
    desc_line = f"# Description: {description}\n#\n" if description else ""
    
    HEADER_TEMPLATE = f"""# ==================================================================
# File: {{filepath}}
{desc_line}# Copyright (C) 2026 Arean Narrayan - SynoraStudio
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

"""
    
    header = HEADER_TEMPLATE.format(filepath=relative_path.replace('\\', '/'))
    
    if new_content == content and content.startswith(header.strip()):
        print(f"Skipping (Header already correct): {relative_path}")
        return
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(header + new_content)
        
    print(f"Updated header in: {relative_path}")

def scan_and_add_headers(root_dir):
    for root, dirs, files in os.walk(root_dir):
        # Skip virtual environments and caches
        dirs[:] = [d for d in dirs if d not in ('venv', 'env', '__pycache__', '.git', 'node_modules', 'sample')]
        
        for file in files:
            if file.endswith('.py') and file != 'add_header.py':
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                add_header_to_file(full_path, rel_path)

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("Scanning for Python files...")
    scan_and_add_headers(project_root)
    print("Done adding headers.")
