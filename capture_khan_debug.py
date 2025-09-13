import json
import os
import asyncio
import aiohttp
import time
from mitmproxy import http
from datetime import datetime
from typing import Set, Dict, Optional
import threading
from urllib.parse import urlparse, parse_qs
import re

# --- Configuration ---
SAVE_DIRECTORY = "khan_academy_json"
REQUEST_DELAY = 1.0
MAX_RETRIES = 3
BATCH_SIZE = 2
MAX_QUESTIONS = 1000

# --- Global State ---
questions_to_capture: Set[str] = set()
saved_questions: Set[str] = set()
questions_captured_count = 0
session_cookies: Optional[str] = None
session_headers: Dict[str, str] = {}
base_url = "https://www.khanacademy.org"
all_discovered_questions: Set[str] = set()

class KhanAcademyDebugCapture:
    def __init__(self):
        if not os.path.exists(SAVE_DIRECTORY):
            os.makedirs(SAVE_DIRECTORY)
        self.active_requests = set()
        self.automation_task = None
        print("[DEBUG] Enhanced Debug Capture addon loaded")
        print("[DEBUG] Will log ALL Khan Academy requests for debugging")

    def response(self, flow: http.HTTPFlow) -> None:
        # Log ALL Khan Academy requests for debugging
        if "khanacademy.org" in flow.request.pretty_host:
            print(f"[DEBUG] Khan Academy Request: {flow.request.method} {flow.request.pretty_url}")
            print(f"[DEBUG] Response Status: {flow.response.status_code}")
            
            # Check for any JSON response
            try:
                if flow.response.content:
                    content_str = flow.response.content.decode('utf-8', errors='ignore')
                    
                    # Look for any question-related content
                    if any(keyword in content_str.lower() for keyword in ['question', 'itemdata', 'perseus', 'assessment']):
                        print(f"[DEBUG] Found question-related content in response")
                        
                        # Try to parse as JSON
                        try:
                            data = json.loads(content_str)
                            self.analyze_response_for_questions(data, flow.request.pretty_url)
                        except json.JSONDecodeError:
                            print(f"[DEBUG] Response contains question keywords but is not valid JSON")
                    
                    # Look for GraphQL responses specifically
                    if 'graphql' in flow.request.pretty_url.lower():
                        print(f"[DEBUG] GraphQL response detected")
                        try:
                            data = json.loads(content_str)
                            self.handle_graphql_response(data, flow.request.pretty_url)
                        except json.JSONDecodeError:
                            print(f"[DEBUG] GraphQL response is not valid JSON")
                
            except Exception as e:
                print(f"[DEBUG] Error analyzing response: {e}")
        
        # Original capture logic
        self.capture_session_data(flow)
        
        # Enhanced detection for practice tasks
        if any(endpoint in flow.request.pretty_url for endpoint in [
            "getOrCreatePracticeTask",
            "getAssessmentItem", 
            "graphql",
            "api/internal"
        ]):
            self.handle_api_response(flow)

    def analyze_response_for_questions(self, data: dict, url: str):
        """Analyze any response that might contain question data."""
        print(f"[DEBUG] Analyzing response from: {url}")
        
        # Look for question IDs in various formats
        content_str = json.dumps(data)
        
        # Pattern 1: Standard question IDs (x followed by hex)
        question_ids = re.findall(r'"(?:id|assessmentItemId)":\s*"(x[a-f0-9]{16})"', content_str)
        
        # Pattern 2: Any long hex-like IDs
        hex_ids = re.findall(r'"id":\s*"([a-f0-9]{16,})"', content_str)
        
        # Pattern 3: Assessment item references
        assessment_refs = re.findall(r'"assessmentItem".*?"id":\s*"([^"]+)"', content_str)
        
        all_ids = set(question_ids + hex_ids + assessment_refs)
        
        if all_ids:
            print(f"[DEBUG] Found {len(all_ids)} potential question IDs: {list(all_ids)[:5]}...")
            for qid in all_ids:
                if len(qid) > 10:  # Filter for substantial IDs
                    all_discovered_questions.add(qid)
                    if qid not in saved_questions:
                        questions_to_capture.add(qid)
        
        # Look for immediate question data to save
        self.extract_immediate_question_data(data)

    def extract_immediate_question_data(self, data: dict):
        """Extract and save question data found directly in responses."""
        def search_for_questions(obj, path=""):
            if isinstance(obj, dict):
                # Check if this object contains itemData
                if 'itemData' in obj and ('id' in obj or 'assessmentItemId' in obj):
                    question_id = obj.get('id') or obj.get('assessmentItemId')
                    if question_id:
                        print(f"[DEBUG] Found question data for ID: {question_id}")
                        self.save_question_data_direct(obj, question_id)
                
                # Check if this is a Perseus question structure
                if 'question' in obj and 'hints' in obj:
                    # This looks like Perseus data, try to find an ID
                    parent_id = self.find_question_id_in_context(data, obj)
                    if parent_id:
                        print(f"[DEBUG] Found Perseus data for ID: {parent_id}")
                        self.save_perseus_data(obj, parent_id)
                
                # Recurse into nested objects
                for key, value in obj.items():
                    search_for_questions(value, f"{path}.{key}")
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_for_questions(item, f"{path}[{i}]")
        
        search_for_questions(data)

    def find_question_id_in_context(self, full_data: dict, perseus_obj: dict) -> Optional[str]:
        """Try to find the question ID associated with Perseus data."""
        content_str = json.dumps(full_data)
        
        # Look for IDs near the Perseus data
        question_ids = re.findall(r'"(?:id|assessmentItemId)":\s*"(x[a-f0-9]{16})"', content_str)
        
        if question_ids:
            return question_ids[0]  # Return the first found ID
        
        return None

    def save_perseus_data(self, perseus_data: dict, question_id: str) -> bool:
        """Save Perseus question data directly."""
        global saved_questions, questions_captured_count
        
        try:
            if question_id in saved_questions:
                return False
            
            # Validate this looks like Perseus data
            if not ('question' in perseus_data and 'hints' in perseus_data):
                return False
            
            saved_questions.add(question_id)
            
            filename = os.path.join(SAVE_DIRECTORY, f"{question_id}.json")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(perseus_data, f, ensure_ascii=False, indent=4)
            
            questions_captured_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[SUCCESS] 💾 Saved Perseus data! {question_id} - Total: {questions_captured_count} ({timestamp})")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to save Perseus data for {question_id}: {e}")
            return False

    def handle_graphql_response(self, data: dict, url: str):
        """Handle GraphQL responses specifically."""
        print(f"[DEBUG] Processing GraphQL response from: {url}")
        
        # Check for getAssessmentItem responses
        if 'data' in data and 'assessmentItem' in data['data']:
            assessment_item = data['data']['assessmentItem']
            if 'item' in assessment_item and 'itemData' in assessment_item['item']:
                question_id = assessment_item['id']
                print(f"[DEBUG] Found getAssessmentItem response for: {question_id}")
                self.save_question_data_direct(assessment_item, question_id)
        
        # Check for practice task responses
        elif 'data' in data and 'getOrCreatePracticeTask' in data['data']:
            print(f"[DEBUG] Found practice task response")
            self.handle_practice_task_response(data)

    def handle_practice_task_response(self, data: dict):
        """Handle practice task responses to extract question IDs."""
        try:
            task_data = data['data']['getOrCreatePracticeTask']['result']['userTask']['task']
            
            if 'reservedItems' in task_data:
                reserved_items = task_data['reservedItems']
                new_questions = set()
                
                for item in reserved_items:
                    # Extract ID after the pipe
                    if '|' in item:
                        question_id = item.split('|')[1]
                        new_questions.add(question_id)
                        all_discovered_questions.add(question_id)
                
                print(f"[DEBUG] Extracted {len(new_questions)} question IDs from practice task")
                
                # Add to capture queue
                new_unsaved = new_questions - saved_questions
                questions_to_capture.update(new_unsaved)
                
                print(f"[DEBUG] Added {len(new_unsaved)} new questions to capture queue")
        
        except Exception as e:
            print(f"[DEBUG] Error processing practice task: {e}")

    def handle_api_response(self, flow: http.HTTPFlow):
        """Handle API responses (original logic with debug)."""
        print(f"[DEBUG] API Response: {flow.request.pretty_url}")
        
        try:
            data = json.loads(flow.response.content)
            
            # Handle different types of responses
            if "getOrCreatePracticeTask" in flow.request.pretty_url:
                print("[DEBUG] Practice task detected")
                self.handle_practice_task_response(data)
            
            elif "getAssessmentItem" in flow.request.pretty_url:
                print("[DEBUG] Assessment item detected")
                self.handle_assessment_item(flow)
            
            else:
                print("[DEBUG] Other API response")
                self.extract_immediate_question_data(data)
        
        except json.JSONDecodeError:
            print("[DEBUG] Non-JSON API response")
        except Exception as e:
            print(f"[DEBUG] Error handling API response: {e}")

    def capture_session_data(self, flow: http.HTTPFlow):
        """Capture session cookies and headers."""
        global session_cookies, session_headers
        
        if "khanacademy.org" in flow.request.pretty_host:
            if 'Cookie' in flow.request.headers:
                session_cookies = flow.request.headers['Cookie']
            
            session_headers.update({
                'User-Agent': flow.request.headers.get('User-Agent', ''),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': flow.request.headers.get('Accept-Language', 'en-US,en;q=0.9'),
                'Referer': flow.request.headers.get('Referer', ''),
                'Origin': 'https://www.khanacademy.org'
            })

    def handle_assessment_item(self, flow: http.HTTPFlow):
        """Handle assessment item responses."""
        try:
            data = json.loads(flow.response.content)
            
            if 'data' in data and 'assessmentItem' in data['data']:
                assessment_item = data['data']['assessmentItem']
                question_id = assessment_item.get('id')
                
                if question_id and 'item' in assessment_item:
                    print(f"[DEBUG] Processing assessment item: {question_id}")
                    self.save_question_data_direct(assessment_item, question_id)
        
        except Exception as e:
            print(f"[DEBUG] Error handling assessment item: {e}")

    def save_question_data_direct(self, item_obj: dict, question_id: str) -> bool:
        """Save question data directly from item object."""
        global saved_questions, questions_captured_count
        
        try:
            if question_id in saved_questions:
                print(f"[DEBUG] Question {question_id} already saved")
                return False
            
            print(f"[DEBUG] Attempting to save question: {question_id}")
            
            # Extract the actual question data
            question_data = None
            
            # Method 1: Direct itemData
            if 'item' in item_obj and 'itemData' in item_obj['item']:
                item_data = item_obj['item']['itemData']
                if isinstance(item_data, str):
                    question_data = json.loads(item_data)
                else:
                    question_data = item_data
            
            # Method 2: Direct itemData in object
            elif 'itemData' in item_obj:
                item_data = item_obj['itemData']
                if isinstance(item_data, str):
                    question_data = json.loads(item_data)
                else:
                    question_data = item_data
            
            # Method 3: Object is already Perseus data
            elif 'question' in item_obj and 'hints' in item_obj:
                question_data = item_obj
            
            if question_data and self.validate_question_data(question_data):
                saved_questions.add(question_id)
                
                filename = os.path.join(SAVE_DIRECTORY, f"{question_id}.json")
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(question_data, f, ensure_ascii=False, indent=4)
                
                questions_captured_count += 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[SUCCESS] 🎉 SAVED! {question_id} - Total: {questions_captured_count} ({timestamp})")
                
                return True
            else:
                print(f"[WARNING] Invalid question data for {question_id}")
                return False
        
        except Exception as e:
            print(f"[ERROR] Failed to save {question_id}: {e}")
            return False

    def validate_question_data(self, data: dict) -> bool:
        """Validate that data contains a proper question."""
        return (
            isinstance(data, dict) and
            ('question' in data or 'problem' in data) and
            ('hints' in data or 'answerArea' in data)
        )

# Create the addon instance
addons = [KhanAcademyDebugCapture()]