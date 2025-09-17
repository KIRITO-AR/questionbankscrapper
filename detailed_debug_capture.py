"""
Enhanced debug version of capture script to see exact response structure
"""
import json
import os
from datetime import datetime
from mitmproxy import http
from mitmproxy.tools.main import mitmdump

# Directory to save captured JSON files
SAVE_DIRECTORY = "khan_academy_json"
DEBUG_LOG_FILE = "detailed_debug_capture.log"

# Ensure the save directory exists
os.makedirs(SAVE_DIRECTORY, exist_ok=True)

class DetailedDebugKhanCaptureAddon:
    def __init__(self):
        self.captured_count = 0
        self.log_file = open(DEBUG_LOG_FILE, 'w', encoding='utf-8')
        
    def __del__(self):
        if hasattr(self, 'log_file'):
            self.log_file.close()

    def request(self, flow: http.HTTPFlow):
        """Called when a request is made."""
        if self.is_khan_request(flow):
            self.log_request(flow)

    def response(self, flow: http.HTTPFlow):
        """Called when a response is received."""
        if self.is_khan_graphql_request(flow):
            self.log_graphql_response(flow)
            
            # Check for assessment item
            if self.is_get_assessment_item(flow):
                self.detailed_assessment_debug(flow)

    def is_khan_request(self, flow: http.HTTPFlow) -> bool:
        """Check if this is a Khan Academy request."""
        return "khanacademy.org" in flow.request.pretty_host

    def is_khan_graphql_request(self, flow: http.HTTPFlow) -> bool:
        """Check if this is a Khan Academy GraphQL request."""
        return (self.is_khan_request(flow) and 
                "/graphql/" in flow.request.path)

    def is_get_assessment_item(self, flow: http.HTTPFlow) -> bool:
        """Check if this is a getAssessmentItem request."""
        return "getAssessmentItem" in flow.request.path

    def log_request(self, flow: http.HTTPFlow):
        """Log basic request information."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {flow.request.method} {flow.request.pretty_url}\n"
        
        self.log_file.write(log_entry)
        self.log_file.flush()

    def log_graphql_response(self, flow: http.HTTPFlow):
        """Log detailed GraphQL response information."""
        if flow.request.method == "POST" or flow.request.method == "GET":
            timestamp = datetime.now().strftime("%H:%M:%S")
            operation_name = "unknown"
            
            # Try to extract operation name from URL
            if "getAssessmentItem" in flow.request.path:
                operation_name = "getAssessmentItem"
            elif "getOrCreatePracticeTask" in flow.request.path:
                operation_name = "getOrCreatePracticeTask"
            
            print(f"[{timestamp}] GraphQL Operation: {operation_name}")
            
            if operation_name in ['getOrCreatePracticeTask', 'getAssessmentItem']:
                print(f"[{timestamp}] *** IMPORTANT: {operation_name} detected! ***")

    def detailed_assessment_debug(self, flow: http.HTTPFlow):
        """Detailed debugging of assessment item responses."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        try:
            if not flow.response.content:
                print(f"[{timestamp}] No response content")
                return
                
            # Parse response
            response_text = flow.response.content.decode('utf-8')
            print(f"[{timestamp}] Raw response length: {len(response_text)} chars")
            
            # Try to parse as JSON
            try:
                data = json.loads(response_text)
                print(f"[{timestamp}] JSON parsed successfully")
                
                # Show the structure
                print(f"[{timestamp}] Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Look for assessment item data
                if isinstance(data, dict):
                    if 'data' in data:
                        print(f"[{timestamp}] Data section keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else 'Data not a dict'}")
                        
                        if isinstance(data['data'], dict) and 'assessmentItem' in data['data']:
                            assessment_item = data['data']['assessmentItem']
                            print(f"[{timestamp}] Assessment item keys: {list(assessment_item.keys()) if isinstance(assessment_item, dict) else 'Assessment item not a dict'}")
                            
                            if isinstance(assessment_item, dict):
                                item_id = assessment_item.get('id', 'unknown')
                                print(f"[{timestamp}] Assessment item ID: {item_id}")
                                
                                # Check for Perseus data
                                if 'itemData' in assessment_item:
                                    print(f"[{timestamp}] *** FOUND itemData! ***")
                                    self.save_assessment_item(assessment_item, item_id, timestamp)
                                elif 'item' in assessment_item:
                                    print(f"[{timestamp}] Found 'item' field instead of 'itemData'")
                                    print(f"[{timestamp}] Item keys: {list(assessment_item['item'].keys()) if isinstance(assessment_item['item'], dict) else 'Item not a dict'}")
                                else:
                                    print(f"[{timestamp}] No itemData or item field found")
                                    # Show what we do have
                                    for key, value in assessment_item.items():
                                        if isinstance(value, str) and len(value) > 100:
                                            print(f"[{timestamp}] Key '{key}': Long string ({len(value)} chars)")
                                        else:
                                            print(f"[{timestamp}] Key '{key}': {type(value).__name__}")
                        else:
                            print(f"[{timestamp}] No assessmentItem in data")
                    else:
                        print(f"[{timestamp}] No 'data' section in response")
                else:
                    print(f"[{timestamp}] Response is not a dict: {type(data)}")
                    
            except json.JSONDecodeError as e:
                print(f"[{timestamp}] JSON parse error: {e}")
                print(f"[{timestamp}] First 200 chars: {response_text[:200]}")
                
        except Exception as e:
            print(f"[{timestamp}] Error in detailed debug: {e}")

    def save_assessment_item(self, assessment_item, item_id, timestamp):
        """Save the assessment item to a file."""
        try:
            filename = os.path.join(SAVE_DIRECTORY, f"detailed_debug_{item_id}.json")
            
            if 'itemData' in assessment_item:
                # Try to parse itemData as JSON
                try:
                    perseus_data = json.loads(assessment_item['itemData'])
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(perseus_data, f, ensure_ascii=False, indent=4)
                    print(f"[{timestamp}] *** SUCCESSFULLY SAVED: {filename} ***")
                    self.captured_count += 1
                except json.JSONDecodeError:
                    # If itemData is not JSON, save the whole assessment item
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(assessment_item, f, ensure_ascii=False, indent=4)
                    print(f"[{timestamp}] *** SAVED RAW ASSESSMENT ITEM: {filename} ***")
                    self.captured_count += 1
            else:
                # Save what we have
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(assessment_item, f, ensure_ascii=False, indent=4)
                print(f"[{timestamp}] *** SAVED AVAILABLE DATA: {filename} ***")
                self.captured_count += 1
                
        except Exception as e:
            print(f"[{timestamp}] Error saving file: {e}")

# Create the addon instance
addons = [DetailedDebugKhanCaptureAddon()]

if __name__ == "__main__":
    # Run mitmproxy with this addon
    mitmdump(["-s", __file__, "--listen-port", "8080"])