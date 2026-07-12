# ==================================================================
# File: bridge_app/services/data_transform.py
# Description: Service for mapping and transforming JSON payloads.
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

import re


def cast_value(val, type_str):
    """Cast a value to the specified type string ('int', 'string')."""
    if type_str == 'int':
        try:
            return int(val)
        except (ValueError, TypeError):
            return val
    elif type_str == 'string':
        return str(val)
    return val


def build_nested_payload(mapping, source_data):
    """
    Constructs a dynamic nested JSON payload based on dot/bracket notation paths.
    E.g. path 'gps_data[0].latitude' mapped to source field 'lat'
    """
    payload = {}
    
    # Mapping is now a list of dicts: [{'source': 'field', 'target': 'path.to.field'}]
    for map_item in mapping:
        if not isinstance(map_item, dict):
            continue
        client_path = map_item.get('target')
        source_field = map_item.get('source')
        if not client_path or not source_field:
            continue
            
        # Get the value from the source data
        value = source_data.get(source_field)
        
        # Apply value mapping if present
        value_mapping = map_item.get('value_mapping')
        if value_mapping and isinstance(value_mapping, list):
            for vm in value_mapping:
                src_val = cast_value(vm.get('source_val'), vm.get('source_type'))
                # Strict or string comparison
                if value == src_val or str(value) == str(src_val):
                    value = cast_value(vm.get('target_val'), vm.get('target_type'))
                    break
        
        parts = client_path.split('.')
        current = payload
        
        for i, part in enumerate(parts):
            array_match = re.match(r'(.+)\[(\d*)\]', part)
            if array_match:
                key = array_match.group(1)
                idx_str = array_match.group(2)
                idx = int(idx_str) if idx_str else 0
                
                if key not in current:
                    current[key] = []
                while len(current[key]) <= idx:
                    current[key].append({})
                    
                if i == len(parts) - 1:
                    current[key][idx] = value
                else:
                    current = current[key][idx]
            else:
                key = part
                if i == len(parts) - 1:
                    current[key] = value
                else:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                    
    return payload
