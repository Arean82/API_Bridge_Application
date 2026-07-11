# ==================================================================
# File: bridge_app/services/graphql_service.py
# Description: Service for parsing and executing GraphQL queries.
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

def execute_graphql_query(template, query, context_data):
    """
    Executes a GraphQL query against the dynamic schema generated for the template.
    Returns a dict with 'data' and/or 'errors'.
    """
    if not query:
        raise ValueError("No query provided")
        
    field_mapping = json.loads(template.field_mapping_json or '[]')
    schema = generate_graphql_schema_from_mapping(field_mapping)
    
    execution_result = schema.execute(query, context={'payload_data': context_data})
    
    response = {}
    if execution_result.errors:
        response['errors'] = [str(err) for err in execution_result.errors]
    if execution_result.data:
        response['data'] = execution_result.data
        
    return response
