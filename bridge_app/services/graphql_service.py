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
    Dynamically generates a Graphene GraphQL schema with proper nesting based on the provided field mapping.
    """
    def build_schema_dict(mapping_list):
        schema_dict = {}
        for mapping in mapping_list:
            target = mapping.get("target")
            if not target: continue
            
            parts = []
            for part in target.split('.'):
                array_match = re.match(r'(.+)\[(\d*)\]', part)
                if array_match:
                    key = array_match.group(1)
                    parts.append((re.sub(r'[^a-zA-Z0-9_]', '_', key), True))
                else:
                    parts.append((re.sub(r'[^a-zA-Z0-9_]', '_', part), False))

            current = schema_dict
            for i, (key, is_list) in enumerate(parts):
                if key not in current:
                    current[key] = {'_is_list': is_list}
                else:
                    current[key]['_is_list'] = current[key]['_is_list'] or is_list

                if i == len(parts) - 1:
                    current[key]['_type'] = "String"
                else:
                    current = current[key]
        return schema_dict

    def create_graphene_type(name, s_dict):
        attrs = {}
        for key, value in s_dict.items():
            if key.startswith('_'): continue
            
            is_list = value.get('_is_list', False)
            if '_type' in value:
                field = graphene.String
            else:
                field = create_graphene_type(f"{name}_{key}", value)
                
            if is_list:
                attrs[key] = graphene.List(field)
            else:
                attrs[key] = graphene.Field(field) if not hasattr(field, 'parse_literal') else field()
                
        return type(name, (graphene.ObjectType,), attrs)

    schema_dict = build_schema_dict(field_mapping)
    DynamicType = create_graphene_type("DynamicPayload", schema_dict)
    
    def clean_dict_keys(data):
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.items():
                safe_k = re.sub(r'[^a-zA-Z0-9_]', '_', k)
                new_data[safe_k] = clean_dict_keys(v)
            return new_data
        elif isinstance(data, list):
            return [clean_dict_keys(item) for item in data]
        return data

    class Query(graphene.ObjectType):
        payload = graphene.Field(DynamicType)
        
        def resolve_payload(self, info):
            # The data is already nested via data_transform.py. We just need to sanitize keys.
            data = info.context.get('payload_data', {})
            clean_data = clean_dict_keys(data)
            
            # Helper to convert dicts to Graphene types
            def dict_to_graphene(data_dict, graphene_type):
                if not data_dict or not isinstance(data_dict, dict):
                    return None
                kwargs = {}
                for key, val in data_dict.items():
                    if hasattr(graphene_type, key):
                        field_type = getattr(graphene_type, key).type
                        
                        # Handle lists
                        if isinstance(val, list):
                            if hasattr(field_type, 'of_type') and hasattr(field_type.of_type, '_meta'):
                                kwargs[key] = [dict_to_graphene(item, field_type.of_type) for item in val]
                            else:
                                kwargs[key] = val
                        # Handle nested objects
                        elif isinstance(val, dict) and hasattr(field_type, '_meta'):
                            kwargs[key] = dict_to_graphene(val, field_type)
                        else:
                            kwargs[key] = val
                return graphene_type(**kwargs)
                
            return dict_to_graphene(clean_data, DynamicType)
            
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

import requests

def fetch_from_graphql_source(url, query, auth_token=None):
    """Executes a GraphQL query against an external source."""
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
        
    response = requests.post(url, json={"query": query}, headers=headers, timeout=15)
    response.raise_for_status()
    result = response.json()
    if 'errors' in result:
        raise ValueError(f"GraphQL Source returned errors: {result['errors']}")
    return result.get('data', {})

def introspect_graphql_endpoint(url, auth_token=None):
    """Fetches the Introspection schema from an external GraphQL endpoint."""
    introspection_query = '''
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        types { ...FullType }
      }
    }
    fragment FullType on __Type {
      kind
      name
      fields(includeDeprecated: true) {
        name
        args { ...InputValue }
        type { ...TypeRef }
      }
      inputFields { ...InputValue }
      interfaces { ...TypeRef }
      enumValues(includeDeprecated: true) { name }
      possibleTypes { ...TypeRef }
    }
    fragment InputValue on __InputValue {
      name
      type { ...TypeRef }
    }
    fragment TypeRef on __Type {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
          }
        }
      }
    }
    '''
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
        
    response = requests.post(url, json={"query": introspection_query}, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()
