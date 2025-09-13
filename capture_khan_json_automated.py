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

# Import our new modules
try:
    from active_scraper import ActiveKhanScraper
    from graphql_analyzer import KhanGraphQLAnalyzer
    ACTIVE_SCRAPING_AVAILABLE = True
except ImportError:
    ACTIVE_SCRAPING_AVAILABLE = False
    print("[WARNING] Active scraping modules not available, falling back to passive mode")

# --- Configuration ---
SAVE_DIRECTORY = "khan_academy_json"
REQUEST_DELAY = 1.0  # Delay between automated requests (seconds)
MAX_RETRIES = 5  # Increased retries
BATCH_SIZE = 3  # Reduced batch size for better reliability
MAX_QUESTIONS = 1000  # Remove download limit (set to high number)
ENABLE_ACTIVE_SCRAPING = True  # Enable active batch scraping

# --- Global State ---
questions_to_capture: Set[str] = set()
saved_questions: Set[str] = set()
questions_captured_count = 0
session_cookies: Optional[str] = None
session_headers: Dict[str, str] = {}
base_url = "https://www.khanacademy.org"
all_discovered_questions: Set[str] = set()  # Track all discovered questions
browser_automation_active = False
active_scraper_instance: Optional[ActiveKhanScraper] = None
graphql_analyzer: Optional[KhanGraphQLAnalyzer] = None

class KhanAcademyAutomatedCapture:
    def __init__(self):
        global graphql_analyzer, active_scraper_instance
        
        if not os.path.exists(SAVE_DIRECTORY):
            os.makedirs(SAVE_DIRECTORY)
        self.active_requests = set()
        self.automation_task = None
        self.active_scraping_task = None
        
        # Initialize GraphQL analyzer and active scraper if available
        if ACTIVE_SCRAPING_AVAILABLE:
            graphql_analyzer = KhanGraphQLAnalyzer()
            print("[INFO] GraphQL analyzer initialized")
        
        print("[INFO] Automated Capture addon loaded. Will auto-download all questions...")
        if ENABLE_ACTIVE_SCRAPING and ACTIVE_SCRAPING_AVAILABLE:
            print("[INFO] Active batch scraping enabled")
        else:
            print("[INFO] Using passive scraping mode only")

    def response(self, flow: http.HTTPFlow) -> None:
        # Capture session data for authenticated requests
        self.capture_session_data(flow)
        
        # --- Part 1: Capture the manifest and trigger automation ---
        if ("api/internal/graphql/getOrCreatePracticeTask" in flow.request.pretty_url or
            "api/internal/graphql" in flow.request.pretty_url):
            self.handle_practice_task(flow)

        # --- Part 2: Capture individual question JSONs ---
        if ("api/internal/graphql/getAssessmentItem" in flow.request.pretty_url or
            "getAssessmentItem" in flow.request.pretty_url):
            self.handle_assessment_item(flow)
            
        # --- Part 3: Capture any other question-related responses ---
        if "itemData" in str(flow.response.content) and "question" in str(flow.response.content):
            self.try_extract_question_data(flow)

    def capture_session_data(self, flow: http.HTTPFlow):
        """Capture session cookies and headers for authenticated requests"""
        global session_cookies, session_headers, active_scraper_instance, graphql_analyzer
        
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
            
            # Update active scraper with new session data
            if ACTIVE_SCRAPING_AVAILABLE and active_scraper_instance:
                active_scraper_instance.update_session_data(session_cookies, session_headers)
            
            # Analyze GraphQL requests
            if ACTIVE_SCRAPING_AVAILABLE and graphql_analyzer and "graphql" in flow.request.pretty_url.lower():
                try:
                    request_data = flow.request.content.decode('utf-8', errors='ignore')
                    graphql_analyzer.analyze_question_request(request_data, flow.request.pretty_url)
                except Exception as e:
                    print(f"[DEBUG] Could not analyze GraphQL request: {e}")

    def handle_practice_task(self, flow: http.HTTPFlow):
        """
        Parses the main task response and starts automated question downloading.
        """
        global questions_to_capture, all_discovered_questions
        print("[INFO] Practice Task detected. Starting automated question capture...")
        
        try:
            data = json.loads(flow.response.content)
            
            # Multiple ways to extract question IDs
            new_questions = set()
            
            # Method 1: From practice task reserved items
            if 'data' in data and 'getOrCreatePracticeTask' in data['data']:
                reserved_items = data['data']['getOrCreatePracticeTask']['result']['userTask']['task']['reservedItems']
                for item in reserved_items:
                    # The ID is the part after the '|'
                    item_id = item.split('|')[1]
                    new_questions.add(item_id)
                    all_discovered_questions.add(item_id)
            
            # Method 2: From any GraphQL response with assessment items
            if 'assessmentItem' in str(data):
                # Extract IDs from any assessment item references
                content_str = json.dumps(data)
                item_ids = re.findall(r'"id":\s*"([a-f0-9x]+)"', content_str)
                for item_id in item_ids:
                    if len(item_id) > 10:  # Filter for Khan Academy question IDs
                        new_questions.add(item_id)
                        all_discovered_questions.add(item_id)
            
            # Add only new questions that haven't been saved
            new_unsaved_questions = new_questions - saved_questions
            questions_to_capture.update(new_unsaved_questions)
            
            print(f"[INFO] Found {len(new_unsaved_questions)} new questions to capture automatically.")
            print(f"[INFO] Total questions discovered: {len(all_discovered_questions)}")
            print(f"[INFO] Total questions in queue: {len(questions_to_capture)}")
            
            # Start automated downloading in a separate thread
            if new_unsaved_questions and not self.automation_task:
                self.automation_task = threading.Thread(
                    target=self.start_automated_capture,
                    args=(new_unsaved_questions,),
                    daemon=True
                )
                self.automation_task.start()
            elif new_unsaved_questions and self.automation_task:
                # If automation is already running, the new questions will be picked up
                print(f"[INFO] Automation already running, new questions added to queue.")
            
            # Start active batch scraping if enabled and questions found
            if (ENABLE_ACTIVE_SCRAPING and ACTIVE_SCRAPING_AVAILABLE and 
                new_unsaved_questions and not self.active_scraping_task):
                self.active_scraping_task = threading.Thread(
                    target=self.start_active_batch_processing,
                    args=(new_unsaved_questions,),
                    daemon=True
                )
                self.active_scraping_task.start()
                print(f"[INFO] Started active batch processing for {len(new_unsaved_questions)} questions")

        except (KeyError, TypeError, json.JSONDecodeError) as e:
            print(f"[ERROR] Could not parse practice task. Error: {e}")
            # Try to extract any question data anyway
            self.try_extract_question_data(flow)

    def try_extract_question_data(self, flow: http.HTTPFlow):
        """
        Try to extract question data from any response that might contain it.
        """
        try:
            data = json.loads(flow.response.content)
            
            # Look for itemData in the response
            def find_item_data(obj, path=""):
                if isinstance(obj, dict):
                    if 'itemData' in obj and 'id' in obj:
                        # Found a question item
                        item_id = obj['id']
                        if item_id not in saved_questions:
                            print(f"[INFO] Found question data in response: {item_id}")
                            self.save_question_data_direct(obj, item_id)
                    
                    for key, value in obj.items():
                        find_item_data(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_item_data(item, f"{path}[{i}]")
            
            find_item_data(data)
            
        except (json.JSONDecodeError, TypeError):
            pass

    def save_question_data_direct(self, item_obj: dict, question_id: str) -> bool:
        """
        Save question data directly from item object.
        """
        global saved_questions, questions_captured_count
        
        try:
            if question_id in saved_questions:
                return False
                
            saved_questions.add(question_id)
            
            filename = os.path.join(SAVE_DIRECTORY, f"{question_id}.json")
            
            # Check if itemData is already parsed or needs parsing
            if isinstance(item_obj.get('itemData'), str):
                perseus_data = json.loads(item_obj['itemData'])
            else:
                perseus_data = item_obj.get('itemData', item_obj)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(perseus_data, f, ensure_ascii=False, indent=4)
            
            questions_captured_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"    💾 Saved! {question_id} - Total: {questions_captured_count} ({timestamp})")
            
            # If we're under the limit, continue capturing more
            if questions_captured_count < MAX_QUESTIONS:
                self.trigger_more_questions()
                
            return True
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"  ⚠ Parse error for {question_id}: {e}")
            return False

    def trigger_more_questions(self):
        """
        Trigger loading of more questions by discovering new question IDs.
        """
        # This will be called by browser automation or when we need more questions
        if len(questions_to_capture) < 10:  # If queue is low, try to get more
            print("[INFO] Question queue low, triggering browser to load more questions...")
            # Signal to browser automation to refresh/get more questions
            global browser_automation_active
            browser_automation_active = True

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
        Capture questions in parallel batches with unlimited downloading.
        """
        question_list = list(question_ids)
        total_processed = 0
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),  # Increased timeout
            headers=session_headers,
            cookies=self.parse_cookies()
        ) as session:
            
            # Continue processing until we reach the limit or no more questions
            while total_processed < MAX_QUESTIONS and question_list:
                # Process in batches
                for i in range(0, len(question_list), BATCH_SIZE):
                    if total_processed >= MAX_QUESTIONS:
                        break
                        
                    batch = question_list[i:i + BATCH_SIZE]
                    batch_num = i//BATCH_SIZE + 1
                    total_batches = (len(question_list) + BATCH_SIZE - 1)//BATCH_SIZE
                    
                    print(f"[INFO] Processing batch {batch_num}/{total_batches} (Total processed: {total_processed})")
                    
                    # Create tasks for this batch
                    tasks = [
                        self.fetch_question(session, question_id)
                        for question_id in batch
                    ]
                    
                    # Wait for batch completion
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Count successful captures
                    total_processed += sum(1 for result in results if result is True)
                    
                    # Small delay between batches
                    if i + BATCH_SIZE < len(question_list):
                        await asyncio.sleep(REQUEST_DELAY)
                
                # Check if we need to discover more questions
                if total_processed < MAX_QUESTIONS and len(questions_to_capture) < 5:
                    print(f"[INFO] Captured {total_processed} questions, looking for more...")
                    # Give browser automation time to discover more questions
                    await asyncio.sleep(5)
                    
                    # Add any newly discovered questions to the list
                    new_questions = list(questions_to_capture - set(question_list))
                    if new_questions:
                        question_list.extend(new_questions)
                        print(f"[INFO] Added {len(new_questions)} new questions to queue")
                    else:
                        print("[INFO] No new questions found, completing capture...")
                        break

    async def fetch_question(self, session: aiohttp.ClientSession, question_id: str):
        """
        Fetch a single question JSON with retries.
        """
        if question_id in saved_questions:
            return True
            
        url = f"{base_url}/api/internal/graphql/getAssessmentItem"
        
        # GraphQL query payload with enhanced query
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
                        __typename
                    }
                    __typename
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
                            return True
                        else:
                            print(f"  ⚠ Failed to parse: {question_id} (attempt {attempt + 1})")
                    else:
                        print(f"  ⚠ HTTP {response.status} for {question_id} (attempt {attempt + 1})")
                        
            except Exception as e:
                print(f"  ⚠ Error fetching {question_id} (attempt {attempt + 1}): {e}")
            
            # Wait before retry with exponential backoff
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(REQUEST_DELAY * (2 ** attempt))
        
        print(f"  ✗ Failed to capture {question_id} after {MAX_RETRIES} attempts")
        return False

    def save_question_data(self, data: dict, question_id: str) -> bool:
        """
        Save question data to file. Returns True if successful.
        """
        global saved_questions, questions_captured_count
        
        try:
            # Enhanced data extraction with multiple fallbacks
            item = None
            
            # Method 1: Standard GraphQL response
            if 'data' in data and 'assessmentItem' in data['data'] and data['data']['assessmentItem']:
                item = data['data']['assessmentItem']['item']
            
            # Method 2: Direct item in response
            elif 'item' in data:
                item = data['item']
            
            # Method 3: Look for any object with itemData
            elif 'itemData' in data:
                item = data
                
            if not item:
                print(f"  ⚠ No item data found for {question_id}")
                return False
            
            item_id = item.get('id', question_id)
            
            if item_id != question_id:
                print(f"  ⚠ ID mismatch: expected {question_id}, got {item_id}")
                # Continue anyway, might be a variation
            
            if item_id not in saved_questions:
                saved_questions.add(item_id)
                
                filename = os.path.join(SAVE_DIRECTORY, f"{item_id}.json")
                
                # Handle itemData whether it's string or object
                if 'itemData' in item:
                    if isinstance(item['itemData'], str):
                        perseus_data = json.loads(item['itemData'])
                    else:
                        perseus_data = item['itemData']
                else:
                    # Fallback: save the entire item
                    perseus_data = item
                
                # Validate that this looks like a proper question
                if self.validate_question_data(perseus_data):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(perseus_data, f, ensure_ascii=False, indent=4)
                    
                    questions_captured_count += 1
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"    💾 Saved! Total: {questions_captured_count}/{MAX_QUESTIONS} ({timestamp})")
                    
                    # Remove from capture queue
                    questions_to_capture.discard(item_id)
                    
                    return True
                else:
                    print(f"  ⚠ Invalid question data for {question_id}")
                    saved_questions.discard(item_id)  # Remove from saved since it wasn't valid
                    return False
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"  ⚠ Parse error for {question_id}: {e}")
            
        return False
    
    def validate_question_data(self, data: dict) -> bool:
        """
        Validate that the data contains a proper Khan Academy question.
        """
        try:
            # Check for essential question components
            if not isinstance(data, dict):
                return False
                
            # Should have question content
            if 'question' not in data:
                return False
                
            # Question should have content
            question = data['question']
            if not isinstance(question, dict) or 'content' not in question:
                return False
                
            # Should have some meaningful content (not just empty)
            content = question['content']
            if not content or len(content.strip()) < 10:
                return False
                
            print(f"    ✓ Validated question data: {len(content)} chars, has hints: {'hints' in data}")
            return True
            
        except Exception as e:
            print(f"    ⚠ Validation error: {e}")
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
            
            # Extract question ID and data
            item_id = None
            
            # Multiple ways to get the ID
            if 'data' in data and 'assessmentItem' in data['data'] and data['data']['assessmentItem']:
                item = data['data']['assessmentItem']['item']
                item_id = item['id']
            elif 'id' in data:
                item_id = data['id']
            
            if item_id and item_id not in saved_questions:
                print(f"[INFO] Manual assessment item captured: {item_id}")
                self.save_question_data(data, item_id)
                
                # Add to our discovered questions
                all_discovered_questions.add(item_id)
                
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"[DEBUG] Assessment item parse attempt failed: {e}")
            # Try alternative extraction
            self.try_extract_question_data(flow)
    
    def start_active_batch_processing(self, initial_questions: Set[str]):
        """Start active batch processing using concurrent GraphQL requests."""
        if not ACTIVE_SCRAPING_AVAILABLE:
            print("[WARNING] Active scraping not available, skipping batch processing")
            return
        
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async batch processing
            loop.run_until_complete(self.async_batch_processing(initial_questions))
            
        except Exception as e:
            print(f"[ERROR] Active batch processing failed: {e}")
        finally:
            try:
                loop.close()
            except:
                pass
    
    async def async_batch_processing(self, initial_questions: Set[str]):
        """Async method for batch processing questions."""
        global active_scraper_instance, saved_questions, questions_captured_count
        
        try:
            # Initialize active scraper if not already done
            if not active_scraper_instance:
                active_scraper_instance = ActiveKhanScraper(session_cookies, session_headers)
                await active_scraper_instance.create_session()
                print("[INFO] Active scraper initialized")
            
            # Test connection first
            if not await active_scraper_instance.test_connection():
                print("[WARNING] Active scraper connection test failed, skipping batch processing")
                return
            
            # Process questions in batches
            questions_to_process = list(initial_questions - saved_questions)
            
            if not questions_to_process:
                print("[INFO] No new questions to process actively")
                return
            
            print(f"[INFO] Starting active batch processing for {len(questions_to_process)} questions")
            
            def progress_callback(completed, total, successful):
                print(f"[PROGRESS] Active batch: {completed}/{total} processed, {successful} successful")
            
            # Fetch all questions concurrently
            results = await active_scraper_instance.fetch_batch_with_progress(
                questions_to_process, 
                progress_callback
            )
            
            # Save the results (results now contain Perseus data directly)
            saved_count = 0
            for question_id, perseus_data in results.items():
                if self.save_active_question_data(question_id, perseus_data):
                    saved_count += 1
            
            print(f"[SUCCESS] Active batch processing completed: {saved_count}/{len(questions_to_process)} questions saved")
            print(f"[INFO] 📈 Total questions captured: {questions_captured_count}")
            
        except Exception as e:
            print(f"[ERROR] Async batch processing error: {e}")
        finally:
            if active_scraper_instance:
                await active_scraper_instance.close()
    
    def save_active_question_data(self, question_id: str, perseus_data: Dict) -> bool:
        """Save question data obtained from active scraping in Perseus format."""
        global saved_questions, questions_captured_count
        
        try:
            # The perseus_data should already be in the correct Perseus format from active_scraper
            # Validate that it has the expected structure
            if not self.validate_perseus_data(perseus_data, question_id):
                print(f"[ERROR] Invalid Perseus data structure for {question_id}")
                return False
            
            # Save the Perseus data directly (not wrapped in GraphQL response)
            filename = os.path.join(SAVE_DIRECTORY, f"{question_id}.json")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(perseus_data, f, ensure_ascii=False, indent=4)
            
            # Update tracking
            saved_questions.add(question_id)
            questions_captured_count += 1
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[ACTIVE] 💾 Saved {question_id} via active scraping ({timestamp})")
            print(f"         📊 Total captured: {questions_captured_count}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to save active question data for {question_id}: {e}")
            return False
    
    def validate_perseus_data(self, data: Dict, question_id: str) -> bool:
        """Validate Perseus question data structure."""
        try:
            # Check for required Perseus fields
            required_fields = ["question"]
            
            for field in required_fields:
                if field not in data:
                    print(f"[WARNING] Missing Perseus field '{field}' for {question_id}")
                    return False
            
            # Check question structure
            question = data["question"]
            if not isinstance(question, dict):
                print(f"[WARNING] Invalid question structure for {question_id}")
                return False
            
            if "content" not in question:
                print(f"[WARNING] No content in question for {question_id}")
                return False
            
            # Check content is meaningful
            content = question["content"]
            if not content or len(content.strip()) < 10:
                print(f"[WARNING] Empty or too short content for {question_id}")
                return False
            
            # Optional fields that should be present in good Perseus data
            optional_fields = ["hints", "answerArea", "widgets"]
            found_optional = sum(1 for field in optional_fields if field in data)
            
            if found_optional == 0:
                print(f"[WARNING] No optional Perseus fields found for {question_id} - might be incomplete")
            
            print(f"[VALIDATION] ✓ Perseus data validated for {question_id}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Perseus validation failed for {question_id}: {e}")
            return False

addons = [KhanAcademyAutomatedCapture()]