import json
import yaml
import requests
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from openapi_spec_validator import validate
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

class OpenAPISecurityError(Exception):
    pass

class OpenAPIParseError(Exception):
    pass

@dataclass
class NormalizedOperation:
    operation_id: str
    path: str
    method: str
    summary: Optional[str]
    parameters: list
    request_body: Optional[Any]
    responses: dict
    security: list
    tags: List[str]

class OpenAPIValidator:
    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
    TIMEOUT_SECONDS = 10
    MAX_REDIRECTS = 3

    def __init__(self):
        self.session = requests.Session()
        self.session.max_redirects = self.MAX_REDIRECTS

    def _check_ssrf(self, url: str) -> bool:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        # Basic SSRF prevention (MVP level)
        forbidden_hosts = ['localhost', '127.0.0.1', '169.254.169.254', '::1', '0.0.0.0']
        if hostname.lower() in forbidden_hosts:
            return False
        return True

    def fetch_from_url(self, url: str, auth_headers: dict = None) -> str:
        if not self._check_ssrf(url):
            raise OpenAPISecurityError("URL rejected due to SSRF protection.")
            
        headers = auth_headers or {}
        
        try:
            response = self.session.get(url, headers=headers, timeout=self.TIMEOUT_SECONDS, stream=True)
            response.raise_for_status()
            
            # Check content length before reading
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > self.MAX_SIZE_BYTES:
                raise OpenAPISecurityError("Specification file exceeds maximum allowed size.")
                
            content = response.content
            if len(content) > self.MAX_SIZE_BYTES:
                raise OpenAPISecurityError("Specification file exceeds maximum allowed size.")
                
            return content.decode('utf-8')
        except requests.exceptions.RequestException as e:
            raise OpenAPIParseError(f"Failed to fetch specification from URL: {str(e)}")

    def parse_content(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise OpenAPIParseError(f"Failed to parse content as JSON or YAML: {str(e)}")

    def detect_version(self, spec_dict: dict) -> str:
        if 'swagger' in spec_dict:
            return f"Swagger {spec_dict['swagger']}"
        elif 'openapi' in spec_dict:
            return f"OpenAPI {spec_dict['openapi']}"
        else:
            raise OpenAPIParseError("Could not detect Swagger or OpenAPI version field.")

    def validate_spec(self, spec_dict: dict):
        try:
            # openapi-spec-validator validates complete documents against standard schemas
            validate(spec_dict)
        except OpenAPIValidationError as e:
            raise OpenAPIParseError(f"OpenAPI validation failed: {str(e)}")
        except Exception as e:
            raise OpenAPIParseError(f"Validation error: {str(e)}")

    def resolve_refs(self, spec_dict: dict) -> dict:
        # MVP: Simple custom controlled resolver (shallow/internal only for now)
        # Deep resolution and external file resolution would go here.
        # Returning original for now as a placeholder for the translation engine.
        return spec_dict

    def normalize(self, resolved_spec: dict) -> List[NormalizedOperation]:
        operations = []
        paths = resolved_spec.get('paths', {})
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method, details in methods.items():
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                    continue
                    
                op_id = details.get('operationId', f"{method}_{path}")
                operations.append(NormalizedOperation(
                    operation_id=op_id,
                    path=path,
                    method=method.upper(),
                    summary=details.get('summary'),
                    parameters=details.get('parameters', []),
                    request_body=details.get('requestBody'),
                    responses=details.get('responses', {}),
                    security=details.get('security', []),
                    tags=details.get('tags', [])
                ))
        return operations

    def analyze(self, spec_dict: dict, normalized_ops: List[NormalizedOperation]) -> dict:
        info = spec_dict.get('info', {})
        version = self.detect_version(spec_dict)
        
        schema_count = 0
        if 'components' in spec_dict and 'schemas' in spec_dict['components']:
            schema_count = len(spec_dict['components']['schemas'])
        elif 'definitions' in spec_dict: # Swagger 2.0
            schema_count = len(spec_dict['definitions'])
            
        return {
            'success': True,
            'title': info.get('title', 'Unknown API'),
            'api_version': info.get('version', 'Unknown'),
            'spec_version': version,
            'operation_count': len(normalized_ops),
            'schema_count': schema_count
        }

    def process_and_validate(self, content: str = None, url: str = None, auth_headers: dict = None) -> dict:
        try:
            if url:
                content = self.fetch_from_url(url, auth_headers)
                
            if not content:
                raise OpenAPIParseError("No specification content provided.")
                
            spec_dict = self.parse_content(content)
            self.detect_version(spec_dict) # Just to assert it exists
            
            self.validate_spec(spec_dict)
            
            resolved = self.resolve_refs(spec_dict)
            normalized_ops = self.normalize(resolved)
            
            return self.analyze(resolved, normalized_ops)
            
        except (OpenAPISecurityError, OpenAPIParseError) as e:
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"An unexpected error occurred: {str(e)}"
            }
