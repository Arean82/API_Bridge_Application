# ==================================================================
# File: bridge_app/services/graphql_service.py
# Description: Service for parsing and executing GraphQL queries.
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

import json
import graphene
import re

def generate_graphql_schema_from_mapping(field_mapping):
    """
    Dynamically generates a Graphene GraphQL schema based on the provided field mapping.
    """
    # We dynamically create attributes for our ObjectType based on the field_mapping targets
    attrs = {}
    for mapping in field_mapping:
        target = mapping.get("target")
        if target:
            # Clean up the target name for GraphQL (replace dots, brackets with underscores)
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', target)
            attrs[safe_name] = graphene.String()
            
    # Create the dynamic type
    DynamicType = type("DynamicPayload", (graphene.ObjectType,), attrs)
    
    class Query(graphene.ObjectType):
        payload = graphene.Field(DynamicType)
        
        def resolve_payload(self, info):
            # The data will be passed in through context
            data = info.context.get('payload_data', {})
            
            def get_nested_value(current_data, path):
                import re
                parts = path.split('.')
                current = current_data
                for part in parts:
                    array_match = re.match(r'(.+)\[(\d*)\]', part)
                    if array_match:
                        key = array_match.group(1)
                        idx_str = array_match.group(2)
                        idx = int(idx_str) if idx_str else 0
                        if isinstance(current, dict) and key in current:
                            current = current[key]
                            if isinstance(current, list) and len(current) > idx:
                                current = current[idx]
                            else:
                                return None
                        else:
                            return None
                    else:
                        if isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            return None
                return current

            # Map the clean names back to the data we have
            resolver_data = {}
            for mapping in field_mapping:
                target = mapping.get("target")
                if target:
                    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', target)
                    resolver_data[safe_name] = get_nested_value(data, target)
                    
            return DynamicType(**resolver_data)
            
    return graphene.Schema(query=Query)

def execute_graphql_query(template, dest_slug, query, context_data):
    """
    Executes a GraphQL query against the dynamic schema generated for the template and destination.
    Returns a dict with 'data' and/or 'errors'.
    """
    if not query:
        raise ValueError("No query provided")
        
    t_dict = template.to_dict()
    destinations = t_dict.get('destinations', [])
    field_mapping = []
    
    if dest_slug:
        for d in destinations:
            d_slug = re.sub(r'[^a-z0-9]', '_', d.get('name', '').lower())
            if d_slug == dest_slug:
                field_mapping = d.get('field_mapping', [])
                break
    elif destinations:
        field_mapping = destinations[0].get('field_mapping', [])
        
    schema = generate_graphql_schema_from_mapping(field_mapping)
    
    execution_result = schema.execute(query, context={'payload_data': context_data})
    
    response = {}
    if execution_result.errors:
        response['errors'] = [str(err) for err in execution_result.errors]
    if execution_result.data:
        response['data'] = execution_result.data
        
    return response
