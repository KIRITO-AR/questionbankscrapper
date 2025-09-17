"""
debug_capture.py
Debug version of the capture script to see what requests are being intercepted.
"""

import json
import os
from mitmproxy import http
from datetime import datetime

# --- Configuration ---
SAVE_DIRECTORY = "khan_academy_json"
DEBUG_LOG = "debug_capture.log"

# Ensure save directory exists
if not os.path.exists(SAVE_DIRECTORY):
    os.makedirs(SAVE_DIRECTORY)

class DebugKhanCapture:
    def __init__(self):
        self.request_count = 0
        self.khan_request_count = 0
        print(f"[DEBUG] Khan Academy Debug Capture addon loaded")
        
        # Clear previous log
        with open(DEBUG_LOG, 'w') as f:
            f.write(f"Debug session started: {datetime.now()}\n")
            f.write("=" * 50 + "\n")

    def response(self, flow: http.HTTPFlow) -> None:
        """Debug response handler - logs all requests."""
        self.request_count += 1
        
        # Log all Khan Academy requests
        if "khanacademy.org" in flow.request.pretty_host:
            self.khan_request_count += 1
            self.log_request(flow)
            
            # Check for specific GraphQL endpoints
            if "graphql" in flow.request.pretty_url:
                self.log_graphql_request(flow)
                
            # Try to save any assessment items
            if "getAssessmentItem" in flow.request.pretty_url:
                self.handle_assessment_item(flow)

    def log_request(self, flow: http.HTTPFlow):
        """Log Khan Academy request details."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] Khan Request #{self.khan_request_count}\n"
        log_entry += f"  URL: {flow.request.pretty_url}\n"
        log_entry += f"  Method: {flow.request.method}\n"
        log_entry += f"  Status: {flow.response.status_code}\n"
        log_entry += f"  Content-Type: {flow.response.headers.get('content-type', 'unknown')}\n"
        log_entry += f"  Content Length: {len(flow.response.content)} bytes\n"
        
        # Check if it's a GraphQL request
        if flow.request.method == "POST" and "graphql" in flow.request.pretty_url:
            try:
                request_data = json.loads(flow.request.content)
                operation_name = request_data.get('operationName', 'unknown')
                log_entry += f"  GraphQL Operation: {operation_name}\n"
            except:
                log_entry += f"  GraphQL: Could not parse request\n"
        
        log_entry += "-" * 30 + "\n"
        
        # Write to log file
        with open(DEBUG_LOG, 'a') as f:
            f.write(log_entry)
        
        # Also print to console
        print(f"[DEBUG] Khan Request: {flow.request.pretty_url}")

    def log_graphql_request(self, flow: http.HTTPFlow):
        """Log detailed GraphQL request information."""
        if flow.request.method == "POST":
            try:
                request_data = json.loads(flow.request.content)
                operation_name = request_data.get('operationName', 'unknown')
                
                print(f"[GraphQL] Operation: {operation_name}")
                
                # Log specific operations we care about
                if operation_name in ['getOrCreatePracticeTask', 'getAssessmentItem']:
                    print(f"[GraphQL] *** IMPORTANT: {operation_name} detected! ***")
                    
                    # Try to log response data
                    if flow.response.content:
                        try:
                            response_data = json.loads(flow.response.content)
                            print(f"[GraphQL] Response data available: {len(str(response_data))} chars")
                        except:
                            print(f"[GraphQL] Could not parse response JSON")
                            
            except json.JSONDecodeError:
                print(f"[GraphQL] Could not parse request JSON")

    def handle_assessment_item(self, flow: http.HTTPFlow):
        """Try to save assessment item if found."""
        try:
            data = json.loads(flow.response.content)
            
            # Check if this looks like an assessment item response
            if 'data' in data and 'assessmentItem' in data['data']:
                assessment_item = data['data']['assessmentItem']
                item_id = assessment_item.get('id', 'unknown')
                
                print(f"[SAVE] Found assessment item: {item_id}")
                
                # Save to file
                filename = os.path.join(SAVE_DIRECTORY, f"debug_{item_id}.json")
                
                if 'itemData' in assessment_item:
                    perseus_data = json.loads(assessment_item['itemData'])
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(perseus_data, f, ensure_ascii=False, indent=4)
                    print(f"[SAVE] *** Successfully saved: {filename} ***")
                else:
                    print(f"[SAVE] No itemData found in assessment item")
                    
        except Exception as e:
            pass  # Ignore errors for now

# Create the addon instance
addons = [DebugKhanCapture()]