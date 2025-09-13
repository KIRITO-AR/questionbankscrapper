"""
GraphQL Request Analyzer for Khan Academy
This module analyzes captured GraphQL requests to understand structure and create reusable templates.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

class KhanGraphQLAnalyzer:
    def __init__(self):
        self.session_cookies = None
        self.base_headers = {}
        self.discovered_endpoints = {}
        self.request_templates = {}
    
    def analyze_question_request(self, flow_data: str, request_url: str = None) -> Dict:
        """Analyze captured GraphQL request to understand structure."""
        try:
            # Extract GraphQL query structure
            if "getAssessmentItem" in flow_data:
                return self.parse_assessment_item_request(flow_data, request_url)
            elif "getOrCreatePracticeTask" in flow_data:
                return self.parse_practice_task_request(flow_data, request_url)
            else:
                return self.parse_generic_graphql_request(flow_data, request_url)
        except Exception as e:
            logger.error(f"Failed to analyze GraphQL request: {e}")
        return {}
    
    def parse_assessment_item_request(self, flow_data: str, request_url: str = None) -> Dict:
        """Parse getAssessmentItem request structure."""
        try:
            # Extract the GraphQL query and variables
            query_template = self.extract_request_template(flow_data)
            
            # Store the template for reuse
            self.request_templates['getAssessmentItem'] = query_template
            
            logger.info("Parsed getAssessmentItem request template")
            return query_template
            
        except Exception as e:
            logger.error(f"Error parsing assessment item request: {e}")
            return {}
    
    def parse_practice_task_request(self, flow_data: str, request_url: str = None) -> Dict:
        """Parse getOrCreatePracticeTask request structure."""
        try:
            query_template = self.extract_request_template(flow_data)
            
            # Store the template for reuse
            self.request_templates['getOrCreatePracticeTask'] = query_template
            
            logger.info("Parsed getOrCreatePracticeTask request template")
            return query_template
            
        except Exception as e:
            logger.error(f"Error parsing practice task request: {e}")
            return {}
    
    def parse_generic_graphql_request(self, flow_data: str, request_url: str = None) -> Dict:
        """Parse any GraphQL request to extract structure."""
        try:
            query_template = self.extract_request_template(flow_data)
            
            # Try to identify operation name
            operation_name = self.extract_operation_name(flow_data)
            if operation_name:
                self.request_templates[operation_name] = query_template
                logger.info(f"Parsed {operation_name} request template")
            
            return query_template
            
        except Exception as e:
            logger.error(f"Error parsing generic GraphQL request: {e}")
            return {}
    
    def extract_request_template(self, raw_request: str) -> Dict:
        """Extract reusable request template from captured request."""
        try:
            # Parse the GraphQL query structure
            query_pattern = r'"query":\s*"([^"]+)"'
            variables_pattern = r'"variables":\s*(\{[^}]*\})'
            operation_pattern = r'"operationName":\s*"([^"]*)"'
            
            query_match = re.search(query_pattern, raw_request)
            variables_match = re.search(variables_pattern, raw_request)
            operation_match = re.search(operation_pattern, raw_request)
            
            # Clean up the query string (handle escaped quotes)
            query = query_match.group(1).replace('\\"', '"') if query_match else None
            
            # Parse variables
            variables = {}
            if variables_match:
                try:
                    variables = json.loads(variables_match.group(1))
                except json.JSONDecodeError:
                    logger.warning("Could not parse variables JSON")
            
            template = {
                "query": query,
                "variables_template": variables,
                "operationName": operation_match.group(1) if operation_match else None,
                "endpoint": self.extract_endpoint(raw_request)
            }
            
            return template
            
        except Exception as e:
            logger.error(f"Error extracting request template: {e}")
            return {}
    
    def extract_operation_name(self, raw_request: str) -> Optional[str]:
        """Extract GraphQL operation name."""
        try:
            operation_pattern = r'"operationName":\s*"([^"]*)"'
            match = re.search(operation_pattern, raw_request)
            return match.group(1) if match else None
        except Exception as e:
            logger.debug(f"Could not extract operation name: {e}")
            return None
    
    def extract_endpoint(self, raw_request: str) -> Optional[str]:
        """Extract API endpoint from request."""
        try:
            # Look for URL patterns in the request
            url_patterns = [
                r'POST\s+(https?://[^\s]+)',
                r'"url":\s*"([^"]+)"',
                r'https://www\.khanacademy\.org/api/[^\s"]+'
            ]
            
            for pattern in url_patterns:
                match = re.search(pattern, raw_request)
                if match:
                    return match.group(1) if match.groups() else match.group(0)
            
            # Default endpoint for Khan Academy GraphQL
            return "https://www.khanacademy.org/api/internal/graphql"
            
        except Exception as e:
            logger.debug(f"Could not extract endpoint: {e}")
            return "https://www.khanacademy.org/api/internal/graphql"
    
    def create_assessment_item_query(self, question_id: str) -> Dict:
        """Create a GraphQL query for a specific assessment item."""
        try:
            # Use stored template if available
            if 'getAssessmentItem' in self.request_templates:
                template = self.request_templates['getAssessmentItem']
                query = template.get('query')
                variables = template.get('variables_template', {}).copy()
            else:
                # Fallback to standard query
                query = '''
                    query getAssessmentItem($assessmentItemId: String!, $problemType: String, $showSolutions: Boolean) {
                        assessmentItem(id: $assessmentItemId, problemType: $problemType, showSolutions: $showSolutions) {
                            __typename
                            ... on AssessmentItemOrError {
                                error {
                                    __typename
                                    ... on SingleMessageError {
                                        message
                                    }
                                }
                                item {
                                    __typename
                                    id
                                    itemData
                                    problemType
                                    sha
                                }
                            }
                        }
                    }
                '''
                variables = {}
            
            # Set the specific question ID
            variables.update({
                "assessmentItemId": question_id,
                "problemType": None,
                "showSolutions": False
            })
            
            return {
                "operationName": "getAssessmentItem",
                "variables": variables,
                "query": query.strip()
            }
            
        except Exception as e:
            logger.error(f"Error creating assessment item query: {e}")
            return {}
    
    def get_endpoint_for_operation(self, operation_name: str) -> str:
        """Get the appropriate endpoint for a given operation."""
        try:
            if operation_name in self.request_templates:
                return self.request_templates[operation_name].get('endpoint', 
                    "https://www.khanacademy.org/api/internal/graphql")
            
            # Default endpoints for known operations
            operation_endpoints = {
                "getAssessmentItem": "https://www.khanacademy.org/api/internal/graphql/getAssessmentItem",
                "getOrCreatePracticeTask": "https://www.khanacademy.org/api/internal/graphql/getOrCreatePracticeTask"
            }
            
            return operation_endpoints.get(operation_name, "https://www.khanacademy.org/api/internal/graphql")
            
        except Exception as e:
            logger.error(f"Error getting endpoint for operation {operation_name}: {e}")
            return "https://www.khanacademy.org/api/internal/graphql"
    
    def analyze_response_structure(self, response_data: str) -> Dict:
        """Analyze GraphQL response to understand data structure."""
        try:
            if isinstance(response_data, str):
                data = json.loads(response_data)
            else:
                data = response_data
            
            analysis = {
                "has_errors": "errors" in data,
                "has_data": "data" in data,
                "operations": [],
                "question_ids": set(),
                "item_data_found": False
            }
            
            # Extract operation names and question IDs
            if "data" in data:
                self._analyze_data_section(data["data"], analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing response structure: {e}")
            return {}
    
    def _analyze_data_section(self, data_section: Dict, analysis: Dict):
        """Helper method to analyze the data section of a GraphQL response."""
        try:
            for key, value in data_section.items():
                analysis["operations"].append(key)
                
                # Look for assessment items and question IDs
                if isinstance(value, dict):
                    if "item" in value and isinstance(value["item"], dict):
                        item = value["item"]
                        if "id" in item:
                            analysis["question_ids"].add(item["id"])
                        if "itemData" in item:
                            analysis["item_data_found"] = True
                    
                    # Recursively search nested structures
                    self._analyze_data_section(value, analysis)
                
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self._analyze_data_section(item, analysis)
                            
        except Exception as e:
            logger.debug(f"Error analyzing data section: {e}")