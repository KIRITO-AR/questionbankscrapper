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

# --- Configuration ---
SAVE_DIRECTORY = "khan_academy_json"
REQUEST_DELAY = 0.5  # Delay between automated requests (seconds)
MAX_RETRIES = 3
BATCH_SIZE = 5  # Number of concurrent requests

# --- Global State ---
questions_to_capture: Set[str] = set()
saved_questions: Set[str] = set()
questions_captured_count = 0
session_cookies: Optional[str] = None
session_headers: Dict[str, str] = {}
base_url = "https://www.khanacademy.org"

class KhanAcademyAutomatedCapture:
    def __init__(self):
        if not os.path.exists(SAVE_DIRECTORY):
            os.makedirs(SAVE_DIRECTORY)
        self.active_requests = set()
        self.automation_task = None
        print("[INFO] Automated Capture addon loaded. Will auto-download all questions...")

    def response(self, flow: http.HTTPFlow) -> None:
        # Capture session data for authenticated requests
        self.capture_session_data(flow)
        
        # --- Part 1: Capture the manifest and trigger automation ---
        if "api/internal/graphql/getOrCreatePracticeTask" in flow.request.pretty_url:
            self.handle_practice_task(flow)

        # --- Part 2: Capture individual question JSONs ---
        if "api/internal/graphql/getAssessmentItem" in flow.request.pretty_url:
            self.handle_assessment_item(flow)

    def capture_session_data(self, flow: http.HTTPFlow):
        """Capture session cookies and headers for authenticated requests"""
        global session_cookies, session_headers
        
        if "khanacademy.org" in flow.request.pretty_host:
            # Capture cookies from request headers
            if 'Cookie' in flow.request.headers:
                session_cookies = flow.request.headers['Cookie']
            
            # Capture essential headers
            session_headers.update({
                'User-Agent': flow.request.headers.get('User-Agent', ''),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': flow.request.headers.get('Accept-Language', 'en-US,en;q=0.9'),
                'Referer': flow.request.headers.get('Referer', ''),
                'Origin': 'https://www.khanacademy.org'
            })

    def handle_practice_task(self, flow: http.HTTPFlow):
        """
        Parses the main task response and starts automated question downloading.
        """
        global questions_to_capture
        print("[INFO] Practice Task detected. Starting automated question capture...")
        
        try:
            data = json.loads(flow.response.content)
            reserved_items = data['data']['getOrCreatePracticeTask']['result']['userTask']['task']['reservedItems']
            
            new_questions = set()
            for item in reserved_items:
                # The ID is the part after the '|'
                item_id = item.split('|')[1]
                if item_id not in saved_questions:
                    new_questions.add(item_id)
            
            questions_to_capture.update(new_questions)
            
            print(f"[INFO] Found {len(new_questions)} new questions to capture automatically.")
            print(f"[INFO] Total questions in queue: {len(questions_to_capture)}")
            
            # Start automated downloading in a separate thread
            if new_questions and not self.automation_task:
                self.automation_task = threading.Thread(
                    target=self.start_automated_capture,
                    args=(new_questions,),
                    daemon=True
                )
                self.automation_task.start()

        except (KeyError, TypeError) as e:
            print(f"[ERROR] Could not parse practice task. Error: {e}")

    def start_automated_capture(self, question_ids: Set[str]):
        """
        Start automated capture of all questions in batches.
        """
        print(f"[INFO] Starting automated capture of {len(question_ids)} questions...")
        
        # Create event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self.capture_questions_batch(question_ids))
        except Exception as e:
            print(f"[ERROR] Automated capture failed: {e}")
        finally:
            loop.close()
            self.automation_task = None

    async def capture_questions_batch(self, question_ids: Set[str]):
        """
        Capture questions in parallel batches.
        """
        question_list = list(question_ids)
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=session_headers,
            cookies=self.parse_cookies()
        ) as session:
            
            # Process in batches
            for i in range(0, len(question_list), BATCH_SIZE):
                batch = question_list[i:i + BATCH_SIZE]
                print(f"[INFO] Processing batch {i//BATCH_SIZE + 1}/{(len(question_list) + BATCH_SIZE - 1)//BATCH_SIZE}")
                
                # Create tasks for this batch
                tasks = [
                    self.fetch_question(session, question_id)
                    for question_id in batch
                ]
                
                # Wait for batch completion
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Small delay between batches
                if i + BATCH_SIZE < len(question_list):
                    await asyncio.sleep(REQUEST_DELAY)

    async def fetch_question(self, session: aiohttp.ClientSession, question_id: str):
        """
        Fetch a single question JSON with retries.
        """
        if question_id in saved_questions:
            return
            
        url = f"{base_url}/api/internal/graphql/getAssessmentItem"
        
        # GraphQL query payload
        payload = {
            "operationName": "getAssessmentItem",
            "variables": {
                "assessmentItemId": question_id,
                "kaLocale": "en"
            },
            "query": """
            query getAssessmentItem($assessmentItemId: String!, $kaLocale: String) {
                assessmentItem(id: $assessmentItemId, kaLocale: $kaLocale) {
                    id
                    item {
                        id
                        itemData
                        problem_type
                        sha1
                    }
                }
            }
            """
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process the response
                        if self.save_question_data(data, question_id):
                            print(f"  ✓ Auto-captured: {question_id} (attempt {attempt + 1})")
                            return
                        else:
                            print(f"  ⚠ Failed to parse: {question_id} (attempt {attempt + 1})")
                    else:
                        print(f"  ⚠ HTTP {response.status} for {question_id} (attempt {attempt + 1})")
                        
            except Exception as e:
                print(f"  ⚠ Error fetching {question_id} (attempt {attempt + 1}): {e}")
            
            # Wait before retry
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(REQUEST_DELAY * (attempt + 1))
        
        print(f"  ✗ Failed to capture {question_id} after {MAX_RETRIES} attempts")

    def save_question_data(self, data: dict, question_id: str) -> bool:
        """
        Save question data to file. Returns True if successful.
        """
        global saved_questions, questions_captured_count
        
        try:
            item = data['data']['assessmentItem']['item']
            item_id = item['id']
            
            if item_id != question_id:
                print(f"  ⚠ ID mismatch: expected {question_id}, got {item_id}")
                return False
            
            if item_id not in saved_questions:
                saved_questions.add(item_id)
                
                filename = os.path.join(SAVE_DIRECTORY, f"{item_id}.json")
                perseus_json_str = item['itemData']
                perseus_data = json.loads(perseus_json_str)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(perseus_data, f, ensure_ascii=False, indent=4)
                
                questions_captured_count += 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"    💾 Saved! Total: {questions_captured_count}/{len(questions_to_capture)} ({timestamp})")
                return True
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"  ⚠ Parse error for {question_id}: {e}")
            
        return False

    def parse_cookies(self) -> dict:
        """Parse cookie string into dictionary."""
        if not session_cookies:
            return {}
        
        cookies = {}
        for cookie in session_cookies.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                cookies[key] = value
        return cookies

    def handle_assessment_item(self, flow: http.HTTPFlow):
        """
        Handle manually triggered assessment item responses (fallback).
        """
        global saved_questions, questions_captured_count
        
        try:
            data = json.loads(flow.response.content)
            item = data['data']['assessmentItem']['item']
            item_id = item['id']
            
            # Only save if we haven't already saved it
            if item_id in questions_to_capture and item_id not in saved_questions:
                self.save_question_data(data, item_id)
                
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

addons = [KhanAcademyAutomatedCapture()]