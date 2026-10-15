"""
capture_khan_json.py
Enhanced Khan     def __init_    def __init__(self):
        self.base_headers: Optional[Dict[str, str]] = None
        self.session = requests.Session()  # Persistent session for better auth
        self.active_requests = 0  # Track concurrent requests
        self.request_lock = threading.Lock()  # Thread safety
        self.last_queue_report = 0  # Track when we last reported queue status
        self.last_session_update = 0  # Track when we last updated session headers
        self.session_refresh_interval = 300  # Refresh session every 5 minutes
        self.log(f"[INFO] Khan Academy JSON Capture addon loaded")
        self.log(f"[INFO] Save directory: {SAVE_DIRECTORY}")
        if ENABLE_ACTIVE_SCRAPING:
            self.log(f"[INFO] 🚀 SMART ACTIVE CAPTURE: Session-aware with anti-403 strategies")
            self.log(f"[INFO] Strategy: Persistent session + intelligent retry + passive fallback")
        else:
            self.log(f"[INFO] 📡 PASSIVE CAPTURE MODE: Intercepting browser requests only")
            self.log(f"[INFO] Strategy: Pure passive interception (no active requests)")
        self.log(f"[INFO] Capabilities: Browser request interception + Response parsing")
        
        # Start a periodic queue monitor
        self.start_queue_monitor()     self.base_headers: Optional[Dict[str, str]] = None
        self.session = requests.Session()  # Persistent session for better auth
        self.active_requests = 0  # Track concurrent requests
        self.request_lock = threading.Lock()  # Thread safety
        self.last_queue_report = 0  # Track when we last reported queue status
        self.last_session_update = 0  # Track when we last updated session headers
        self.session_refresh_interval = 300  # Refresh session every 5 minutes
        self.log(f"[INFO] Khan Academy JSON Capture addon loaded")
        self.log(f"[INFO] Save directory: {SAVE_DIRECTORY}")
        if ENABLE_ACTIVE_SCRAPING:
            self.log(f"[INFO] 🚀 SMART ACTIVE CAPTURE: Session-aware with anti-403 strategies")
            self.log(f"[INFO] Strategy: Persistent session + intelligent retry + passive fallback")
        else:
            self.log(f"[INFO] 📡 PASSIVE CAPTURE MODE: Intercepting browser requests only")
            self.log(f"[INFO] Strategy: Pure passive interception (no active requests)")self.log(f"[INFO] Khan Academy JSON Capture addon loaded")
        self.log(f"[INFO] Save directory: {SAVE_DIRECTORY}")
        self.log(f"[INFO] 🚀 ACTIVE CAPTURE MODE: ENABLED with enhanced bypass strategies")
        self.log(f"[INFO] Strategy: Aggressive active fetching with session auth")
        self.log(f"[INFO] Capabilities: Session-aware GraphQL + Enhanced auth bypass")y JSON capture script with active batch scraping.
Based on the technical plan requirements for Part 2.
Optimized for network performance and reduced timeouts.
"""

import json
import os
import requests
from mitmproxy import http, ctx
from datetime import datetime
from typing import Set, Dict, Optional
import threading
import time

# --- Configuration ---
SAVE_DIRECTORY = "khan_academy_json"
REQUEST_DELAY = 0.5  # Reduced delay for better performance
MAX_RETRIES = 3
MAX_QUESTIONS = 1000  # High limit for unlimited scraping
TIMEOUT = 15  # Reduced timeout for faster failure detection

# Performance optimization settings
ENABLE_ACTIVE_SCRAPING = True  # SMART ACTIVE CAPTURE - Session-aware with fallback
MAX_CONCURRENT_REQUESTS = 3  # Reduced for better success rate
PASSIVE_FIRST_MODE = True  # Try passive capture first, active as fallback

# --- Global State ---
questions_to_capture: Set[str] = set()
saved_questions: Set[str] = set()
questions_captured_count = 0

# Ensure save directory exists
if not os.path.exists(SAVE_DIRECTORY):
    os.makedirs(SAVE_DIRECTORY)

class KhanAcademyCapture:
    def __init__(self):
        self.base_headers: Optional[Dict[str, str]] = None
        self.active_requests = 0  # Track concurrent requests
        self.request_lock = threading.Lock()  # Thread safety
        self.last_queue_report = 0  # Track when we last reported queue status
        self.log(f"[INFO] Khan Academy JSON Capture addon loaded")
        self.log(f"[INFO] Save directory: {SAVE_DIRECTORY}")
        self.log(f"[INFO] � PASSIVE CAPTURE MODE: Intercepting browser requests only")
        self.log(f"[INFO] Strategy: Pure passive interception (no active requests)")
        self.log(f"[INFO] Capabilities: Browser request interception + Response parsing")
        
        # Start a periodic queue monitor
        self.start_queue_monitor()

    def start_queue_monitor(self):
        """Start a background thread to monitor the capture queue - intelligent mode."""
        def monitor_queue():
            while True:
                try:
                    time.sleep(60)  # Check every minute for intelligent monitoring
                    current_time = time.time()
                    
                    if len(questions_to_capture) > 0:
                        if current_time - self.last_queue_report > 120:  # Report every 2 minutes
                            session_status = self.check_session_health()
                            self.log(f"[MONITOR] SMART QUEUE: {len(questions_to_capture)} pending questions")
                            self.log(f"[MONITOR] Session status: {session_status}")
                            self.log(f"[MONITOR] Waiting for natural browser requests for: {list(questions_to_capture)[:3]}")
                            self.log(f"[MONITOR] Total saved: {questions_captured_count}")
                            self.last_queue_report = current_time
                            
                            # Only retry if we have good session data and reasonable queue size
                            if (len(questions_to_capture) <= 10 and 
                                self.base_headers and 
                                current_time - self.last_session_update < 600):
                                
                                self.log("[MONITOR] Attempting intelligent retry for small queue")
                                batch_to_try = list(questions_to_capture)[:3]  # Try only 3 at once
                                for i, item_id in enumerate(batch_to_try):
                                    # Longer stagger to avoid rate limiting
                                    threading.Timer(i * 10.0, self.retry_passive_question, args=[item_id]).start()
                            else:
                                self.log("[MONITOR] Waiting for better conditions (browser activity needed)")
                                    
                except Exception as e:
                    self.log(f"[ERROR] Queue monitor error: {e}")
        
        monitor_thread = threading.Thread(target=monitor_queue, daemon=True)
        monitor_thread.start()
        self.log("[INFO] Started intelligent queue monitor for smart capture")

    def log(self, message: str) -> None:
        try:
            print(message, flush=True)
        except Exception:
            pass
        try:
            ctx.log.info(message)
        except Exception:
            pass
        try:
            with open("autonomous_scraper.log", "a", encoding="utf-8") as lf:
                lf.write(message + "\n")
        except Exception:
            pass

    def update_session_from_flow(self, flow: http.HTTPFlow):
        """Update session with fresh authentication data from browser requests."""
        current_time = time.time()
        
        # Only update if enough time has passed or if we don't have headers yet
        if (current_time - self.last_session_update < self.session_refresh_interval and 
            self.base_headers is not None):
            return False
            
        cookie_header = flow.request.headers.get('Cookie', '')
        if not cookie_header:
            return False
            
        # Extract important authentication tokens
        fkey_value = ''
        csrf_token = ''
        try:
            import re
            # Extract fkey
            m = re.search(r'(?i)fkey=([^;]+)', cookie_header)
            if m:
                fkey_value = m.group(1)
            # Extract csrf token if present
            csrf_match = re.search(r'(?i)csrftoken=([^;]+)', cookie_header)
            if csrf_match:
                csrf_token = csrf_match.group(1)
        except Exception:
            pass

        xka = flow.request.headers.get('X-KA-FKey') or flow.request.headers.get('x-ka-fkey') or fkey_value
        referer = flow.request.headers.get('Referer', 'https://www.khanacademy.org/')

        # Update session headers with fresh data
        self.base_headers = {
            'Cookie': cookie_header,
            'User-Agent': flow.request.headers.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
            'X-KA-FKey': xka,
            'x-ka-fkey': xka,
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': flow.request.headers.get('Accept-Language', 'en-US,en;q=0.9'),
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.khanacademy.org',
            'Referer': referer,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        if csrf_token:
            self.base_headers['X-CSRFToken'] = csrf_token
            
        # Update the session cookies
        self.session.headers.update(self.base_headers)
        
        self.last_session_update = current_time
        self.log(f"[SESSION] Updated authentication data (fkey: {fkey_value[:8] if fkey_value else 'none'}...)")
        
        return True

    def check_session_health(self):
        """Check the health of current session data."""
        if not self.base_headers:
            return "No session data"
        
        current_time = time.time()
        age = current_time - self.last_session_update
        
        if age > 600:  # 10 minutes
            return f"Session stale ({age:.0f}s old)"
        elif age > 300:  # 5 minutes
            return f"Session aging ({age:.0f}s old)"
        else:
            return f"Session fresh ({age:.0f}s old)"

    def contains_assessment_data(self, data: dict) -> bool:
        """Check if response data contains assessment item information."""
        try:
            # Check for direct assessmentItem
            if 'data' in data and isinstance(data['data'], dict):
                if 'assessmentItem' in data['data']:
                    return True
            # Check for nested assessmentItem
            if 'assessmentItem' in data:
                return True
            # Check for itemData field
            if 'itemData' in data:
                return True
            return False
        except Exception:
            return False

    def response(self, flow: http.HTTPFlow) -> None:
        """Main response handler for mitmproxy - enhanced passive capture."""

        # Skip processing non-Khan Academy requests to reduce overhead
        if "khanacademy.org" not in flow.request.pretty_host:
            return

        # Update session data from every Khan Academy request for better auth
        self.update_session_from_flow(flow)

        # Only consider GraphQL endpoint; determine operation by inspecting body
        if "/api/internal/graphql" not in flow.request.path:
            return

        operation_name = None
        try:
            # Some KA requests send JSON bodies; parse safely
            req_text = flow.request.get_text(strict=False)
            if req_text:
                body = json.loads(req_text)
                # Body may be a single operation or an array; handle both
                if isinstance(body, list) and body:
                    operation_name = body[0].get("operationName")
                elif isinstance(body, dict):
                    operation_name = body.get("operationName")
        except Exception:
            operation_name = None

        # --- Enhanced Practice Task Detection ---
        if operation_name and operation_name.lower() in {
            "getorcreatepracticetask", "createpracticetask", "practiceitemspreload",
            "practiceitemsforassessment", "getassessmentitemsforexercise",
            "getpracticeitems", "getpracticeitemsforuser", "practicetask"
        }:
            self.log(f"[MITM] Detected practice manifest operation: {operation_name}")
            threading.Thread(target=self.handle_practice_task, args=(flow,), daemon=True).start()

        # --- Enhanced Assessment Item Detection ---
        elif operation_name and operation_name.lower() in {
            "getassessmentitem", "assessmentitem", "itemdata", "questiondata"
        }:
            self.log(f"[MITM] Detected assessmentItem response: {operation_name}")
            threading.Thread(target=self.handle_assessment_item, args=(flow,), daemon=True).start()
        
        # --- Comprehensive Fallback Detection ---
        else:
            # Enhanced fallback: detect any response containing assessment data
            try:
                resp_text = flow.response.get_text(strict=False)
                if resp_text and len(resp_text) > 100:  # Only check substantial responses
                    # Quick string check before JSON parsing
                    if any(keyword in resp_text for keyword in [
                        '"assessmentItem"', '"itemData"', '"perseus"', 
                        '"widgets"', '"content"', '"question"'
                    ]):
                        try:
                            resp_data = json.loads(resp_text)
                            if isinstance(resp_data, dict) and self.contains_assessment_data(resp_data):
                                self.log("[MITM] Fallback: Found assessment data in response")
                                threading.Thread(target=self.handle_assessment_item, args=(flow,), daemon=True).start()
                        except json.JSONDecodeError:
                            pass
            except Exception:
                pass
        
        # --- Additional Detection for Any Khan Academy GraphQL ---
        if flow.request.method == "POST" and "khanacademy.org" in flow.request.pretty_host:
            try:
                resp_text = flow.response.get_text(strict=False)
                if resp_text and ("assessmentItem" in resp_text or "itemData" in resp_text):
                    # Don't parse if we already handled it above
                    if operation_name not in {
                        "getorcreatepracticetask", "createpracticetask", "practiceitemspreload",
                        "getassessmentitem", "assessmentitem"
                    }:
                        try:
                            resp_data = json.loads(resp_text)
                            if isinstance(resp_data, dict) and self.contains_assessment_data(resp_data):
                                self.log("[MITM] Additional: Found assessment data in GraphQL response")
                                threading.Thread(target=self.handle_assessment_item, args=(flow,), daemon=True).start()
                        except json.JSONDecodeError:
                            pass
            except Exception:
                pass

    def handle_practice_task(self, flow: http.HTTPFlow):
        """Handle practice task response and trigger active batch scraping."""
        global questions_to_capture
        self.log("[INFO] Practice Task detected. Building and actively fetching questions...")
        
        try:
            data = json.loads(flow.response.content)
        except json.JSONDecodeError:
            self.log("[ERROR] Could not parse practice task JSON")
            return

        # Store headers from a legitimate flow to use in our forged requests
        cookie_header = flow.request.headers.get('Cookie', '')
        # Extract fkey from cookies if present
        fkey_value = ''
        try:
            import re
            m = re.search(r'(?i)fkey=([^;]+)', cookie_header)
            if m:
                fkey_value = m.group(1)
        except Exception:
            pass

        xka = flow.request.headers.get('X-KA-FKey') or flow.request.headers.get('x-ka-fkey') or fkey_value
        referer = flow.request.headers.get('Referer', 'https://www.khanacademy.org/')

        self.base_headers = {
            'Cookie': cookie_header,
            'User-Agent': flow.request.headers.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
            'X-KA-FKey': xka,
            'x-ka-fkey': xka,
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': flow.request.headers.get('Accept-Language', 'en-US,en;q=0.9'),
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.khanacademy.org',
            'Referer': referer,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        try:
            # Extract question IDs from practice task (handle multiple possible shapes)
            reserved_items = None
            try:
                reserved_items = data['data']['getOrCreatePracticeTask']['result']['userTask']['task']['reservedItems']
            except Exception:
                # Fallbacks: search alternative known response paths
                for path in (
                    ('data', 'practiceItemsPreload', 'reservedItems'),
                    ('data', 'getPracticeItems', 'reservedItems'),
                    ('data', 'getAssessmentItemsForExercise', 'reservedItems'),
                ):
                    ref = data
                    ok = True
                    for key in path:
                        if isinstance(ref, dict) and key in ref:
                            ref = ref[key]
                        else:
                            ok = False
                            break
                    if ok and isinstance(ref, list):
                        reserved_items = ref
                        break

            if not isinstance(reserved_items, list):
                raise KeyError("reservedItems not found")
            new_ids = set()
            
            for item in reserved_items:
                # Extract question ID from format like "assessmentitem|question_id"
                if '|' in item:
                    item_id = item.split('|')[1]
                    if item_id not in questions_to_capture:
                        new_ids.add(item_id)
                        questions_to_capture.add(item_id)

            self.log(f"[MITM] Found {len(new_ids)} new question IDs.")
            
            if ENABLE_ACTIVE_SCRAPING and new_ids:
                self.log(f"[ACTIVE] 🚀 AGGRESSIVE CAPTURE - fetching all {len(new_ids)} questions immediately")
                # Attempt to capture ALL discovered questions
                for item_id in new_ids:
                    # Start active fetch in separate thread
                    threading.Thread(target=self.fetch_assessment_item, args=(item_id,), daemon=True).start()
                    time.sleep(REQUEST_DELAY)  # Standard delay between requests
                self.log(f"[ACTIVE] Started active capture threads for all {len(new_ids)} questions")
            else:
                self.log(f"[INFO] Active scraping disabled - will rely on passive capture only.")
                self.log(f"[INFO] Questions found: {list(new_ids)}")

        except (KeyError, TypeError, IndexError) as e:
            self.log(f"[ERROR] Could not find question IDs in manifest. Error: {e}")
            # Try alternative parsing methods
            self.try_alternative_parsing(data)

    def try_alternative_parsing(self, data: dict):
        """Try alternative methods to extract question IDs."""
        try:
            # Look for any field containing question IDs
            data_str = json.dumps(data)
            import re
            
            # Look for patterns that might be question IDs
            # Prefer IDs that look like Perseus item ids: e.g., x4199a21da4572c96
            patterns = [
                r'assessmentitem\|(x?[a-f0-9]{16})',
                r'"id":\s*"(x?[a-f0-9]{16})"',
                r'"itemId":\s*"(x?[a-f0-9]{16})"',
                r'"contentId":\s*"(x?[a-f0-9]{16})"'
            ]
            
            found_ids = set()
            for pattern in patterns:
                matches = re.findall(pattern, data_str)
                found_ids.update(matches)
            
            if found_ids:
                self.log(f"[INFO] Found {len(found_ids)} questions using alternative parsing")
                self.log(f"[INFO] Active fetching disabled - will wait for passive capture")
                self.log(f"[INFO] Questions discovered: {list(found_ids)}")
                # Store IDs but don't actively fetch due to GraphQL restrictions
                for item_id in found_ids:
                    # Normalize to include 'x' prefix if missing
                    if not item_id.startswith('x'):
                        item_id = 'x' + item_id
                    if item_id not in questions_to_capture:
                        questions_to_capture.add(item_id)
                        
        except Exception as e:
            self.log(f"[ERROR] Alternative parsing failed: {e}")

    def fetch_assessment_item(self, item_id: str):
        """
        SMART ACTIVE capture using session-aware requests with anti-403 strategies.
        """
        # Rate limiting to prevent overloading
        with self.request_lock:
            if self.active_requests >= MAX_CONCURRENT_REQUESTS:
                self.log(f"[INFO] Rate limiting: delaying request for {item_id}")
                time.sleep(REQUEST_DELAY)
            self.active_requests += 1

        try:
            # Check if we have valid session data
            if not self.base_headers:
                self.log(f"[WARNING] No session data available for {item_id} - skipping active capture")
                return False
                
            # Ensure we have fresh session data
            current_time = time.time()
            if current_time - self.last_session_update > 600:  # 10 minutes
                self.log(f"[WARNING] Session data is stale for {item_id} - may fail")

            # Use the main GraphQL endpoint
            graphql_url = "https://www.khanacademy.org/api/internal/graphql"
            
            # STRATEGY: Use simpler, more likely to be whitelisted queries
            payload_options = [
                {
                    "operationName": "getAssessmentItem",
                    "variables": {"itemId": item_id},
                    "query": """query getAssessmentItem($itemId: String!) {
                        assessmentItem(id: $itemId) {
                            id
                            itemData
                            sha
                        }
                    }"""
                },
                {
                    "operationName": "node",
                    "variables": {"id": item_id},
                    "query": """query node($id: ID!) {
                        node(id: $id) {
                            id
                            ... on AssessmentItem {
                                itemData
                                sha
                            }
                        }
                    }"""
                },
                {
                    "operationName": "assessmentItems",
                    "variables": {"ids": [item_id]},
                    "query": """query assessmentItems($ids: [String!]!) {
                        assessmentItems(ids: $ids) {
                            id
                            itemData
                            sha
                        }
                    }"""
                }
            ]

            # Use persistent session with updated headers
            headers = self.base_headers.copy()
            
            # Add minimal additional headers to avoid detection
            headers.update({
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'DNT': '1',
                'Pragma': 'no-cache'
            })

            # Try each payload option until one succeeds
            for i, payload in enumerate(payload_options):
                try:
                    self.log(f"[ACTIVE] Strategy {i+1} for {item_id}: {payload['operationName']}")
                    
                    # Use persistent session instead of requests.post
                    response = self.session.post(
                        graphql_url, 
                        headers=headers, 
                        json=payload,
                        timeout=TIMEOUT
                    )
                    
                    self.log(f"[ACTIVE] Response status: {response.status_code} for strategy {i+1}")
                    
                    if response.status_code == 200:
                        # Success! Parse and save the JSON
                        response_data = response.json()
                        self.save_item_json(response_data)
                        self.log(f"[SUCCESS] ✅ ACTIVE capture successful for {item_id} using strategy {i+1}")
                        return  # Success, exit function
                    elif response.status_code == 403:
                        self.log(f"[WARNING] Strategy {i+1} blocked (403) - trying next strategy")
                        continue
                    else:
                        response_text = response.text[:500]
                        self.log(f"[WARNING] Strategy {i+1} failed with {response.status_code}: {response_text}")
                        continue
                        
                except requests.exceptions.RequestException as e:
                    self.log(f"[ERROR] Strategy {i+1} request failed: {e}")
                    continue
            
            # If all strategies failed, try the ultimate fallback: direct web scraping
            self.log(f"[ACTIVE] All GraphQL strategies failed for {item_id} - trying direct web scraping")
            success = self.fetch_via_web_scraping(item_id, headers)
            if success:
                self.log(f"[SUCCESS] ✅ ACTIVE capture via web scraping for {item_id}")
            else:
                # Try batch operation as final active attempt
                success = self.fetch_via_batch_operation(item_id, headers)
                if success:
                    self.log(f"[SUCCESS] ✅ ACTIVE capture via batch operation for {item_id}")
                else:
                    self.log(f"[FALLBACK] Adding {item_id} to passive capture queue")
                    questions_to_capture.add(item_id)
                    # Schedule aggressive retry attempts
                    threading.Timer(5.0, self.retry_passive_question, args=[item_id]).start()
            
        except Exception as e:
            self.log(f"[ERROR] Active fetch completely failed for {item_id}: {e}")
            # Add to passive capture as last resort
            questions_to_capture.add(item_id)
            # Schedule aggressive retry attempts
            threading.Timer(8.0, self.retry_passive_question, args=[item_id]).start()
        finally:
            # Always decrement the active request counter
            with self.request_lock:
                self.active_requests = max(0, self.active_requests - 1)

    def retry_passive_question(self, item_id: str):
        """Smart retry with passive-first strategy, then intelligent active fallback."""
        global questions_to_capture
        
        # Check if the question was already captured
        if item_id not in questions_to_capture:
            return  # Already captured
        
        self.log(f"[RETRY] Smart retry attempt for {item_id}")
        
        # STRATEGY 1: Wait for passive capture (recommended approach)
        if PASSIVE_FIRST_MODE:
            # Just log that we're waiting - the browser will eventually trigger the request
            self.log(f"[PASSIVE] Waiting for browser to naturally request {item_id}")
            return
        
        # STRATEGY 2: Active capture only if we have fresh session data
        if not self.base_headers:
            self.log(f"[SKIP] No session data for {item_id} - waiting for browser activity")
            return
            
        # Check session freshness
        current_time = time.time()
        if current_time - self.last_session_update > 300:  # 5 minutes
            self.log(f"[SKIP] Session data too old for {item_id} - waiting for fresh auth")
            return
        
        # Try simplified GraphQL strategies with session awareness
        strategies = [
            {
                "operationName": "getAssessmentItem",
                "variables": {"assessmentItemId": item_id},
                "query": "query getAssessmentItem($assessmentItemId: String!) { assessmentItem(id: $assessmentItemId) { item { id itemData } } }"
            },
            {
                "operationName": "node",
                "variables": {"id": item_id},
                "query": "query node($id: String!) { node(id: $id) { ... on AssessmentItem { id itemData } } }"
            },
            {
                "operationName": "assessmentItems",
                "variables": {"ids": [item_id]},
                "query": "query assessmentItems($ids: [String!]!) { assessmentItems(ids: $ids) { id itemData } }"
            }
        ]
        
        for strategy in strategies:
            try:
                headers = self.base_headers.copy()
                
                # Use persistent session
                response = self.session.post(
                    "https://www.khanacademy.org/api/internal/graphql",
                    headers=headers,
                    json=strategy,
                    timeout=10
                )
                
                self.log(f"[RETRY] {strategy['operationName']} status for {item_id}: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    if self.save_item_json(response_data):
                        self.log(f"[SUCCESS] ✅ RETRY successful for {item_id} using {strategy['operationName']}")
                        questions_to_capture.discard(item_id)
                        return
                elif response.status_code != 403:
                    # If not blocked, try next strategy
                    continue
                    
            except Exception as e:
                self.log(f"[RETRY] Strategy {strategy['operationName']} failed: {e}")
                continue
        
        # If all strategies failed, keep trying
        self.log(f"[RETRY] All strategies failed for {item_id} - will retry again later")
        # Schedule another retry in 30 seconds
        threading.Timer(30.0, self.retry_passive_question, args=[item_id]).start()

    def fetch_via_batch_operation(self, item_id: str, headers: dict) -> bool:
        """
        Advanced ACTIVE capture: Use the correct GraphQL query structure.
        """
        try:
            # Ensure headers are properly initialized
            if not headers:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Content-Type': 'application/json',
                    'Origin': 'https://www.khanacademy.org',
                    'Referer': 'https://www.khanacademy.org/'
                }
            
            graphql_url = "https://www.khanacademy.org/api/internal/graphql"
            
            # Use the correct getAssessmentItem query structure
            assessment_item_payload = {
                "operationName": "getAssessmentItem",
                "variables": {
                    "assessmentItemId": item_id,
                    "problemType": None,
                    "showSolutions": False
                },
                "query": """query getAssessmentItem($assessmentItemId: String!, $problemType: String, $showSolutions: Boolean) {
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
                }"""
            }
            
            # Alternative queries to try
            batch_payloads = [
                assessment_item_payload,
                {
                    "operationName": "getOrCreatePracticeTask",
                    "variables": {
                        "exerciseId": f"x{item_id[1:]}",  # Remove 'x' prefix and re-add
                        "itemIds": [item_id],
                        "userId": None
                    },
                    "query": """query getOrCreatePracticeTask($exerciseId: String!, $itemIds: [String!], $userId: String) {
                        getOrCreatePracticeTask(exerciseId: $exerciseId, itemIds: $itemIds, userId: $userId) {
                            result {
                                userTask {
                                    task {
                                        reservedItems
                                    }
                                }
                            }
                        }
                    }"""
                }
            ]
            
            for payload in batch_payloads:
                try:
                    self.log(f"[ACTIVE] Trying batch operation: {payload['operationName']}")
                    response = requests.post(graphql_url, headers=headers, json=payload, timeout=TIMEOUT)
                    
                    self.log(f"[ACTIVE] Batch operation {payload['operationName']} status: {response.status_code}")
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        
                        # Check for GraphQL errors first
                        if "errors" in response_data:
                            self.log(f"[ACTIVE] GraphQL errors: {response_data['errors']}")
                            continue
                        
                        # Enhanced response handling
                        if "data" in response_data:
                            # Try to save the response directly
                            if self.save_item_json(response_data):
                                self.log(f"[SUCCESS] ✅ ACTIVE batch capture successful for {item_id}")
                                return True
                            
                            # If direct save failed, try to extract assessment item data
                            data = response_data.get("data", {})
                            
                            # Handle different response structures
                            if "assessmentItem" in data and data["assessmentItem"]:
                                assessment_item = data["assessmentItem"]
                                if "item" in assessment_item and assessment_item["item"]:
                                    self.log(f"[SUCCESS] ✅ ACTIVE assessment item capture for {item_id}")
                                    return True
                            
                            # Handle practice task responses
                            elif "getOrCreatePracticeTask" in data:
                                task_data = data["getOrCreatePracticeTask"]
                                if task_data and "result" in task_data:
                                    self.log(f"[SUCCESS] ✅ ACTIVE practice task capture for {item_id}")
                                    return True
                        
                        self.log(f"[ACTIVE] Response structure not recognized for {payload['operationName']}")
                        
                    elif response.status_code == 403:
                        self.log(f"[ACTIVE] Batch operation {payload['operationName']} blocked (403)")
                    elif response.status_code == 404:
                        self.log(f"[ACTIVE] Batch operation {payload['operationName']} not found (404)")
                    else:
                        self.log(f"[ACTIVE] Batch operation {payload['operationName']} returned {response.status_code}")
                        # Log response content for debugging
                        try:
                            error_content = response.text[:200]
                            self.log(f"[DEBUG] Response: {error_content}")
                        except:
                            pass
                        
                except requests.exceptions.RequestException as e:
                    self.log(f"[ERROR] Request exception in batch operation {payload['operationName']}: {e}")
                    continue
            
            return False
            
        except Exception as e:
            self.log(f"[ERROR] Batch operation failed for {item_id}: {e}")
            return False

    def fetch_via_web_scraping(self, item_id: str, headers: dict) -> bool:
        """
        Alternative ACTIVE capture method: direct web scraping of exercise pages.
        """
        try:
            # Try to construct exercise URLs that might contain this item
            possible_urls = [
                f"https://www.khanacademy.org/api/internal/assessment_items/{item_id}",
                f"https://www.khanacademy.org/api/internal/exercises/{item_id}",
                f"https://www.khanacademy.org/exercise/{item_id}",
            ]
            
            for url in possible_urls:
                try:
                    self.log(f"[ACTIVE] Trying direct URL: {url}")
                    response = requests.get(url, headers=headers, timeout=TIMEOUT)
                    
                    self.log(f"[ACTIVE] Direct URL {url} status: {response.status_code}")
                    
                    if response.status_code == 200:
                        content = response.text
                        if "itemData" in content or "perseus" in content:
                            # Try to extract JSON data
                            try:
                                if content.startswith('{'):
                                    data = json.loads(content)
                                    if self.save_item_json(data):
                                        self.log(f"[SUCCESS] ✅ Direct URL capture successful for {item_id}")
                                        return True
                                else:
                                    # HTML page - try to extract embedded JSON
                                    import re
                                    json_match = re.search(r'"itemData":\s*"([^"]+)"', content)
                                    if json_match:
                                        item_data = json_match.group(1)
                                        # Decode if needed
                                        item_data = item_data.replace('\\"', '"')
                                        data = json.loads(item_data)
                                        if self.save_item_json({"data": {"assessmentItem": {"id": item_id, "itemData": json.dumps(data)}}}):
                                            self.log(f"[SUCCESS] ✅ HTML extraction successful for {item_id}")
                                            return True
                            except json.JSONDecodeError as e:
                                self.log(f"[ACTIVE] JSON decode error for {url}: {e}")
                                continue
                        else:
                            self.log(f"[ACTIVE] No relevant content found in {url}")
                    elif response.status_code == 403:
                        self.log(f"[ACTIVE] Direct URL {url} blocked (403)")
                    elif response.status_code == 404:
                        self.log(f"[ACTIVE] Direct URL {url} not found (404)")
                    else:
                        self.log(f"[ACTIVE] Direct URL {url} failed with status {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    self.log(f"[ERROR] Request exception for {url}: {e}")
                    continue
            
            return False
            
        except Exception as e:
            self.log(f"[ERROR] Web scraping failed for {item_id}: {e}")
            return False

    def save_item_json(self, data: dict) -> bool:
        """
        Centralized function to handle the saving logic.
        Returns True if successfully saved, False otherwise.
        """
        global saved_questions, questions_captured_count
        
        try:
            # Extract the assessment item data - try multiple possible structures
            assessment_item = None
            item_id = None
            item_data_raw = None
            
            # Method 1: Standard assessment item response
            if 'data' in data and isinstance(data['data'], dict) and 'assessmentItem' in data['data']:
                assessment_item_data = data['data']['assessmentItem']
                if 'item' in assessment_item_data and assessment_item_data['item']:
                    assessment_item = assessment_item_data['item']
                    item_id = assessment_item.get('id')
                    item_data_raw = assessment_item.get('itemData')
                    
            # Method 2: Direct assessment item (no nested data structure)
            elif 'assessmentItem' in data:
                assessment_item = data['assessmentItem']
                if 'item' in assessment_item:
                    assessment_item = assessment_item['item']
                item_id = assessment_item.get('id')
                item_data_raw = assessment_item.get('itemData')
                
            # Method 3: Practice task response with items
            elif 'data' in data and 'getOrCreatePracticeTask' in data['data']:
                task_data = data['data']['getOrCreatePracticeTask']
                if 'result' in task_data and 'userTask' in task_data['result']:
                    user_task = task_data['result']['userTask']
                    if 'task' in user_task and 'reservedItems' in user_task['task']:
                        reserved_items = user_task['task']['reservedItems']
                        if reserved_items and len(reserved_items) > 0:
                            # Extract first item
                            first_item = reserved_items[0]
                            if 'item' in first_item:
                                assessment_item = first_item['item']
                                item_id = assessment_item.get('id')
                                item_data_raw = assessment_item.get('itemData')
                            
            # Method 4: Items array (batch responses)
            elif 'items' in data and isinstance(data['items'], list) and data['items']:
                assessment_item = data['items'][0]
                item_id = assessment_item.get('id')
                item_data_raw = assessment_item.get('itemData')
                
            # Method 5: Preload items array
            elif 'preloadItems' in data and isinstance(data['preloadItems'], list) and data['preloadItems']:
                assessment_item = data['preloadItems'][0]
                item_id = assessment_item.get('id')
                item_data_raw = assessment_item.get('itemData')

            # Validation
            if not item_id or not item_data_raw:
                # Log the data structure for debugging
                self.log(f"[DEBUG] Could not extract item data. Data keys: {list(data.keys())}")
                return False

            # De-dup across session
            if item_id in saved_questions:
                self.log(f"[DEBUG] Question {item_id} already saved, skipping")
                return False
            saved_questions.add(item_id)

            # Parse the Perseus data
            if isinstance(item_data_raw, str):
                perseus_data = json.loads(item_data_raw)
            else:
                perseus_data = item_data_raw

            # Ensure save directory exists
            os.makedirs(SAVE_DIRECTORY, exist_ok=True)

            # Save to file unconditionally so browsing saves all questions
            import re
            # Validate item_id to prevent path traversal (only safe filename characters)
            if not isinstance(item_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', item_id):
                self.log(f"[ERROR] Refusing to save item with unsafe id: {item_id!r}")
                return False
            filename = os.path.join(SAVE_DIRECTORY, f"{item_id}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(perseus_data, f, ensure_ascii=False, indent=4)

            questions_captured_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log(f"[SAVE] ✅ {item_id}.json  Total saved: {questions_captured_count} ({timestamp})")
            
            # Remove from capture queue if it was there
            global questions_to_capture
            questions_to_capture.discard(item_id)
            
            # Check if we've reached our limit
            if questions_captured_count >= MAX_QUESTIONS:
                self.log(f"[INFO] Reached maximum question limit ({MAX_QUESTIONS})")

            return True

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.log(f"[ERROR] Failed to save item data: {e}")
            return False
        except Exception as e:
            self.log(f"[ERROR] Unexpected error in save_item_json: {e}")
            return False

    def handle_assessment_item(self, flow: http.HTTPFlow):
        """
        Active-enhanced capture - intercept browser requests and trigger active fetching.
        """
        global questions_to_capture
        
        try:
            data = json.loads(flow.response.content)
            
            # Try to save any assessment data found
            if self.save_item_json(data):
                # Successfully saved from passive capture
                self.log(f"[PASSIVE] ✅ Captured question from browser response")
                
                # Remove from pending queue if found
                data_str = str(data)
                for item_id in list(questions_to_capture):
                    if item_id in data_str:
                        questions_to_capture.discard(item_id)
                        self.log(f"[PASSIVE] ✅ Removed {item_id} from pending queue")
                        
        except json.JSONDecodeError:
            pass
        
        # Active queue processing - try to capture pending questions
        if len(questions_to_capture) > 0:
            self.log(f"[ACTIVE-QUEUE] {len(questions_to_capture)} questions pending active capture")
            
            # Trigger active capture for some pending questions
            if len(questions_to_capture) <= 15:  # When queue is manageable
                batch_to_try = list(questions_to_capture)[:5]  # Try 5 at a time
                for item_id in batch_to_try:
                    # Start immediate active capture attempt
                    threading.Timer(1.0, self.retry_passive_question, args=[item_id]).start()

    def contains_assessment_data(self, data: dict) -> bool:
        """Enhanced check for assessment item information."""
        try:
            # Check for direct assessmentItem
            if 'data' in data and isinstance(data['data'], dict):
                if 'assessmentItem' in data['data']:
                    return True
                # Also check for practice task responses
                if 'getOrCreatePracticeTask' in data['data']:
                    return True
            
            # Check for nested assessmentItem
            if 'assessmentItem' in data:
                return True
            
            # Check for itemData field (actual question content)
            if 'itemData' in data:
                return True
                
            # Check for Perseus-specific fields
            if 'question' in data and 'content' in data.get('question', {}):
                return True
                
            return False
        except Exception:
            return False

# Create the addon instance
addons = [KhanAcademyCapture()]