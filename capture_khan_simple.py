"""
Simple Khan Academy Question Scraper - Manual Approach
This version captures questions by detecting ANY Khan Academy JSON that contains question data
"""

import json
import os
from mitmproxy import http
from datetime import datetime
import re

SAVE_DIRECTORY = "khan_academy_json"
saved_questions = set()

class SimpleKhanCapture:
    def __init__(self):
        os.makedirs(SAVE_DIRECTORY, exist_ok=True)
        print("[SIMPLE] Khan Academy Simple Capture loaded")
        print("[SIMPLE] Will capture ANY response containing question data")

    def response(self, flow: http.HTTPFlow) -> None:
        # Only process Khan Academy requests
        if "khanacademy.org" not in flow.request.pretty_host:
            return
            
        # Log the request for debugging
        print(f"[SIMPLE] Khan Request: {flow.request.method} {flow.request.path_components[-1] if flow.request.path_components else 'root'}")
        
        # Try to find question data in ANY response
        try:
            if flow.response.content:
                content = flow.response.content.decode('utf-8', errors='ignore')
                
                # Look for Perseus question structure in JSON
                if '"question"' in content and '"hints"' in content:
                    print(f"[SIMPLE] Found potential question data in response")
                    
                    try:
                        # Try to parse as complete JSON
                        data = json.loads(content)
                        self.extract_questions_from_data(data)
                    except json.JSONDecodeError:
                        # Try to extract JSON fragments
                        self.extract_json_fragments(content)
                
                # Also look for itemData specifically
                elif '"itemData"' in content:
                    print(f"[SIMPLE] Found itemData in response")
                    try:
                        data = json.loads(content)
                        self.extract_itemdata_from_response(data)
                    except json.JSONDecodeError:
                        pass
        
        except Exception as e:
            print(f"[SIMPLE] Error processing response: {e}")

    def extract_questions_from_data(self, data):
        """Extract question data from any JSON structure."""
        def search_recursive(obj, path=""):
            if isinstance(obj, dict):
                # Check if this is a Perseus question
                if 'question' in obj and 'hints' in obj:
                    question_id = self.generate_question_id(obj)
                    if question_id:
                        self.save_question(obj, question_id)
                
                # Check for itemData
                if 'itemData' in obj:
                    item_data = obj['itemData']
                    if isinstance(item_data, str):
                        try:
                            parsed_data = json.loads(item_data)
                            if 'question' in parsed_data:
                                question_id = self.generate_question_id(parsed_data)
                                if question_id:
                                    self.save_question(parsed_data, question_id)
                        except json.JSONDecodeError:
                            pass
                    elif isinstance(item_data, dict) and 'question' in item_data:
                        question_id = self.generate_question_id(item_data)
                        if question_id:
                            self.save_question(item_data, question_id)
                
                # Recurse into nested objects
                for key, value in obj.items():
                    search_recursive(value, f"{path}.{key}")
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_recursive(item, f"{path}[{i}]")
        
        search_recursive(data)

    def extract_itemdata_from_response(self, data):
        """Specifically look for itemData in GraphQL responses."""
        if isinstance(data, dict):
            # Check for getAssessmentItem response
            if 'data' in data and isinstance(data['data'], dict):
                if 'assessmentItem' in data['data']:
                    assessment_item = data['data']['assessmentItem']
                    if 'item' in assessment_item and 'itemData' in assessment_item['item']:
                        question_id = assessment_item.get('id', self.generate_random_id())
                        item_data = assessment_item['item']['itemData']
                        
                        if isinstance(item_data, str):
                            try:
                                parsed_data = json.loads(item_data)
                                self.save_question(parsed_data, question_id)
                            except json.JSONDecodeError:
                                pass

    def extract_json_fragments(self, content):
        """Try to extract JSON fragments that contain question data."""
        # Look for Perseus-like structures
        pattern = r'\{[^{}]*"question"[^{}]*"content"[^{}]*\}'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            try:
                # Try to find a larger JSON structure around this match
                start = content.find(match)
                # Expand backwards and forwards to find complete JSON
                json_str = self.expand_to_complete_json(content, start, len(match))
                if json_str:
                    data = json.loads(json_str)
                    if 'question' in data:
                        question_id = self.generate_question_id(data)
                        if question_id:
                            self.save_question(data, question_id)
            except (json.JSONDecodeError, Exception):
                continue

    def expand_to_complete_json(self, content, start, length):
        """Try to expand a JSON fragment to complete JSON."""
        # Simple approach: find balanced braces
        end = start + length
        open_braces = content[:end].count('{') - content[:end].count('}')
        
        # Expand forward to balance braces
        pos = end
        while pos < len(content) and open_braces > 0:
            if content[pos] == '{':
                open_braces += 1
            elif content[pos] == '}':
                open_braces -= 1
            pos += 1
        
        if open_braces == 0:
            return content[start:pos]
        return None

    def generate_question_id(self, question_data):
        """Generate a unique ID for a question."""
        # Try to find an existing ID in the data
        content_str = json.dumps(question_data)
        
        # Look for existing question IDs
        id_match = re.search(r'"id":\s*"([a-f0-9x]{10,})"', content_str)
        if id_match:
            return id_match.group(1)
        
        # Generate ID from question content hash
        if 'question' in question_data and 'content' in question_data['question']:
            import hashlib
            content = question_data['question']['content']
            hash_obj = hashlib.md5(content.encode())
            return f"x{hash_obj.hexdigest()[:16]}"
        
        return None

    def generate_random_id(self):
        """Generate a random question ID."""
        import random
        return f"x{''.join(random.choice('0123456789abcdef') for _ in range(16))}"

    def save_question(self, question_data, question_id):
        """Save a question to file."""
        global saved_questions
        
        if question_id in saved_questions:
            return False
        
        # Validate it's a real question
        if not self.validate_question(question_data):
            return False
        
        try:
            filename = os.path.join(SAVE_DIRECTORY, f"{question_id}.json")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(question_data, f, ensure_ascii=False, indent=4)
            
            saved_questions.add(question_id)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[SUCCESS] 🎉 CAPTURED! {question_id} ({timestamp})")
            
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to save {question_id}: {e}")
            return False

    def validate_question(self, data):
        """Validate that this is a real question."""
        if not isinstance(data, dict):
            return False
        
        # Must have question content
        if 'question' not in data:
            return False
        
        question = data['question']
        if not isinstance(question, dict) or 'content' not in question:
            return False
        
        # Must have some actual content
        content = question['content']
        if not isinstance(content, str) or len(content.strip()) < 10:
            return False
        
        return True

# Create addon
addons = [SimpleKhanCapture()]