# ==================================================================
# File: bridge_app/services/data_transform.py
# Description: Service for mapping and transforming JSON payloads.
#              value casting used by the pull/push engine.
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
