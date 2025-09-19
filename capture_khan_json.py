"""
capture_khan_json.py
Enhanced Khan Academy JSON capture script with active batch scraping.
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
ENABLE_ACTIVE_SCRAPING = True  # Enable active batch scraping
MAX_CONCURRENT_REQUESTS = 3  # Limit concurrent requests to avoid overload

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
        self.log(f"[INFO] Khan Academy JSON Capture addon loaded")
        self.log(f"[INFO] Save directory: {SAVE_DIRECTORY}")
        self.log(f"[INFO] Active batch scraping: {'ENABLED' if ENABLE_ACTIVE_SCRAPING else 'DISABLED'}")
        self.log(f"[INFO] Performance mode: Optimized for reduced timeouts")

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
        """Main response handler for mitmproxy - optimized for performance."""

        # Skip processing non-Khan Academy requests to reduce overhead
        if "khanacademy.org" not in flow.request.pretty_host:
            return

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

        # --- Part 1: Capture the manifest and trigger active scraping ---
        if operation_name and operation_name.lower() in {
            "getorcreatepracticetask", "createpracticetask", "practiceitemspreload",
            "practiceitemsforassessment", "getassessmentitemsforexercise",
            "getpracticeitems", "getpracticeitemsforuser"
        }:
            self.log(f"[MITM] Detected practice manifest operation: {operation_name}")
            if ENABLE_ACTIVE_SCRAPING:
                threading.Thread(target=self.handle_practice_task, args=(flow,), daemon=True).start()
            else:
                self.handle_practice_task(flow)

        # --- Part 2: Capture individual question JSONs (passive backup) ---
        elif operation_name and operation_name.lower() in {"getassessmentitem", "assessmentitem"}:
            self.log("[MITM] Detected assessmentItem response; saving passively")
            threading.Thread(target=self.handle_assessment_item, args=(flow,), daemon=True).start()
        else:
            # Fallback: attempt to detect assessmentItem directly from response body
            try:
                # Mitm may stream; ensure bytes -> JSON safely
                resp_text = flow.response.get_text(strict=False)
                resp_data = json.loads(resp_text) if resp_text else None
                if isinstance(resp_data, dict) and 'data' in resp_data and isinstance(resp_data['data'], dict) and 'assessmentItem' in resp_data['data']:
                    self.log("[MITM] Fallback matched assessmentItem in response body")
                    threading.Thread(target=self.handle_assessment_item, args=(flow,), daemon=True).start()
            except Exception:
                pass
        
        # Additional check for any Khan Academy response that might contain assessment data
        if flow.request.method == "POST" and "khanacademy.org" in flow.request.pretty_host:
            try:
                resp_text = flow.response.get_text(strict=False)
                if resp_text and ("assessmentItem" in resp_text or "itemData" in resp_text):
                    resp_data = json.loads(resp_text)
                    if isinstance(resp_data, dict) and self.contains_assessment_data(resp_data):
                        self.log("[MITM] Found assessment data in response, attempting to save")
                        threading.Thread(target=self.handle_assessment_item, args=(flow,), daemon=True).start()
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
                self.log(f"[INFO] Active scraping enabled - fetching {len(new_ids)} questions")
                for item_id in new_ids:
                    threading.Thread(target=self.fetch_assessment_item, args=(item_id,), daemon=True).start()
                    time.sleep(REQUEST_DELAY)  # Rate limit between requests
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
        Actively sends a request to the getAssessmentItem GraphQL endpoint.
        Optimized with rate limiting and better error handling.
        """
        # Rate limiting to prevent overloading
        with self.request_lock:
            if self.active_requests >= MAX_CONCURRENT_REQUESTS:
                self.log(f"[INFO] Rate limiting: delaying request for {item_id}")
                time.sleep(REQUEST_DELAY)
            self.active_requests += 1

        try:
            if not self.base_headers:
                self.log("[WARNING] No headers available for active requests")
                return

            # Use the standard GraphQL endpoint that matches intercepted requests
            graphql_url = "https://www.khanacademy.org/api/internal/graphql"
            
            # Updated GraphQL query payload with simplified structure
            payload = {
                "operationName": "getAssessmentItem",
                "variables": {"id": item_id},
                "query": """query getAssessmentItem($id: String!) {
                    assessmentItem(id: $id) {
                        id
                        itemData
                        item {
                            id
                            itemData
                            sha
                        }
                    }
                }"""
            }

            # Enhanced headers with better authentication
            headers = self.base_headers.copy()
            headers.update({
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Accept-Encoding': 'gzip, deflate, br',
                'X-Requested-With': 'XMLHttpRequest',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            })

            # Make request with reduced timeout
            self.log(f"[MITM] Active fetch: {item_id}")
            self.log(f"[DEBUG] Request URL: {graphql_url}")
            self.log(f"[DEBUG] Payload: {json.dumps(payload)}")
            self.log(f"[DEBUG] Headers keys: {list(headers.keys())}")
            
            response = requests.post(
                graphql_url, 
                headers=headers, 
                json=payload,
                timeout=TIMEOUT
            )
            
            self.log(f"[DEBUG] Response status: {response.status_code}")
            
            if response.status_code != 200:
                response_text = response.text[:1000]  # First 1000 chars
                self.log(f"[DEBUG] Response body: {response_text}")
            
            response.raise_for_status()
            
            # Parse and save the JSON
            response_data = response.json()
            self.save_item_json(response_data)
            self.log(f"[SUCCESS] Actively fetched question: {item_id}")
            
        except requests.exceptions.Timeout:
            self.log(f"[ERROR] Timeout fetching {item_id} (network may be slow)")
        except requests.exceptions.HTTPError as e:
            # Detailed logging for HTTP errors, especially 400s and 403s
            status_code = getattr(e.response, 'status_code', 'unknown')
            response_text = getattr(e.response, 'text', '')
            if callable(response_text):
                response_text = response_text()
            self.log(f"[ERROR] HTTP {status_code} for {item_id}")
            self.log(f"[ERROR] Response: {response_text[:500]}")
            
            if status_code == 400:
                self.log(f"[ERROR] 400 Bad Request - likely payload or authentication issue")
            elif status_code == 403:
                self.log(f"[WARNING] 403 Forbidden - Khan Academy may be blocking active requests")
                self.log(f"[INFO] Falling back to passive capture for {item_id}")
                # Add to passive capture queue
                questions_to_capture.add(item_id)
            elif status_code == 429:
                self.log(f"[WARNING] 429 Rate Limited - slowing down requests")
                time.sleep(REQUEST_DELAY * 2)  # Double the delay
        except requests.exceptions.RequestException as e:
            self.log(f"[ERROR] Active fetch failed for {item_id}. Error: {e}")
        except json.JSONDecodeError:
            self.log(f"[ERROR] Invalid JSON response for {item_id}")
        finally:
            # Always decrement the active request counter
            with self.request_lock:
                self.active_requests = max(0, self.active_requests - 1)

    def save_item_json(self, data: dict):
        """
        Centralized function to handle the saving logic.
        """
        global saved_questions, questions_captured_count
        
        try:
            # Extract the assessment item data - try multiple possible structures
            assessment_item = None
            if 'data' in data and isinstance(data['data'], dict) and 'assessmentItem' in data['data']:
                assessment_item = data['data']['assessmentItem']
            elif 'assessmentItem' in data:
                assessment_item = data['assessmentItem']
            
            if not assessment_item:
                return

            # The actual question data might be in the 'item' field
            actual_item = assessment_item.get('item', assessment_item)
            
            item_id = actual_item.get('id')
            item_data_raw = actual_item.get('itemData')

            if not item_id or not item_data_raw:
                return

            # De-dup across session
            if item_id in saved_questions:
                return
            saved_questions.add(item_id)

            # Parse the Perseus data
            perseus_data = json.loads(item_data_raw)

            # Save to file unconditionally so browsing saves all questions
            filename = os.path.join(SAVE_DIRECTORY, f"{item_id}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(perseus_data, f, ensure_ascii=False, indent=4)

            questions_captured_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log(f"[SAVE] {item_id}.json  Total saved: {questions_captured_count} ({timestamp})")
            
            # Check if we've reached our limit
            if questions_captured_count >= MAX_QUESTIONS:
                self.log(f"[INFO] Reached maximum question limit ({MAX_QUESTIONS})")

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # Ignore if the JSON is not what we expect
            pass

    def handle_assessment_item(self, flow: http.HTTPFlow):
        """
        Handle assessment item responses (passive backup).
        This function now just acts as a passive backup.
        """
        try:
            data = json.loads(flow.response.content)
            self.save_item_json(data)
        except json.JSONDecodeError:
            pass

# Create the addon instance
addons = [KhanAcademyCapture()]