"""
Active Khan Academy Scraper
This module actively generates GraphQL requests to download question data concurrently.
"""

import asyncio
import aiohttp
import json
import time
from typing import List, Set, Dict, Optional, Tuple
import logging
from urllib.parse import urlencode
from graphql_analyzer import KhanGraphQLAnalyzer

logger = logging.getLogger(__name__)

class ActiveKhanScraper:
    def __init__(self, session_cookies: str = None, base_headers: Dict = None):
        self.session_cookies = session_cookies or ""
        self.base_headers = base_headers or {}
        self.session = None
        self.analyzer = KhanGraphQLAnalyzer()
        self.rate_limit_delay = 0.5  # Delay between requests
        self.max_retries = 3
        self.timeout = 30
        
    async def create_session(self):
        """Create aiohttp session with proper headers and cookies."""
        try:
            cookies = self.parse_cookies(self.session_cookies)
            
            # Default headers for Khan Academy API
            default_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/json',
                'Origin': 'https://www.khanacademy.org',
                'Referer': 'https://www.khanacademy.org/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }
            
            # Merge with provided headers
            headers = {**default_headers, **self.base_headers}
            
            connector = aiohttp.TCPConnector(
                limit=10, 
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=10)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers,
                cookies=cookies
            )
            
            logger.info("Created active scraper session")
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def parse_cookies(self, cookie_string: str) -> Dict[str, str]:
        """Parse cookie string into dictionary."""
        try:
            if not cookie_string:
                return {}
            
            cookies = {}
            for cookie in cookie_string.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
            
            return cookies
        except Exception as e:
            logger.error(f"Error parsing cookies: {e}")
            return {}
    
    async def fetch_question_batch(self, question_ids: List[str]) -> Dict[str, Dict]:
        """Actively fetch multiple questions concurrently."""
        if not self.session:
            await self.create_session()
        
        logger.info(f"Starting batch fetch for {len(question_ids)} questions")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(5)  # Increased from 3 to 5
        
        tasks = []
        for question_id in question_ids:
            task = asyncio.create_task(
                self.fetch_single_question_with_retry(question_id, semaphore)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_downloads = {}
        failed_downloads = []
        
        for question_id, result in zip(question_ids, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {question_id}: {result}")
                failed_downloads.append(question_id)
            elif result is not None:
                # Extract Perseus data from the GraphQL response
                perseus_data = self.extract_perseus_data(result, question_id)
                if perseus_data:
                    successful_downloads[question_id] = perseus_data
                    logger.debug(f"Successfully fetched and processed {question_id}")
                else:
                    logger.warning(f"Could not extract Perseus data for {question_id}")
                    failed_downloads.append(question_id)
            else:
                failed_downloads.append(question_id)
        
        logger.info(f"Batch fetch completed: {len(successful_downloads)} successful, {len(failed_downloads)} failed")
        return successful_downloads
    
    async def fetch_single_question_with_retry(self, question_id: str, semaphore: asyncio.Semaphore) -> Optional[Dict]:
        """Fetch a single question with retry logic."""
        async with semaphore:
            for attempt in range(self.max_retries):
                try:
                    result = await self.fetch_single_question(question_id)
                    if result:
                        return result
                    
                    # If no result, wait before retry
                    if attempt < self.max_retries - 1:
                        wait_time = (attempt + 1) * 2  # Exponential backoff
                        logger.debug(f"Retry {attempt + 1} for {question_id} in {wait_time}s")
                        await asyncio.sleep(wait_time)
                        
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed for {question_id}: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep((attempt + 1) * 2)
            
            logger.error(f"All attempts failed for question {question_id}")
            return None
    
    async def fetch_single_question(self, question_id: str) -> Optional[Dict]:
        """Fetch a single question using the reverse-engineered GraphQL query."""
        try:
            # Create the GraphQL request
            graphql_query = self.analyzer.create_assessment_item_query(question_id)
            
            if not graphql_query:
                logger.error(f"Could not create query for {question_id}")
                return None
            
            # Get the appropriate endpoint
            endpoint = self.analyzer.get_endpoint_for_operation("getAssessmentItem")
            
            # Add delay to avoid rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            logger.debug(f"Fetching question {question_id} from {endpoint}")
            
            async with self.session.post(
                endpoint,
                json=graphql_query,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate the response structure
                    if self.validate_response(data, question_id):
                        logger.debug(f"Successfully fetched question {question_id}")
                        return data
                    else:
                        logger.warning(f"Invalid response structure for {question_id}")
                        return None
                        
                elif response.status == 429:  # Rate limited
                    logger.warning(f"Rate limited for {question_id}, increasing delay")
                    self.rate_limit_delay = min(self.rate_limit_delay * 2, 5.0)
                    return None
                    
                else:
                    logger.error(f"HTTP {response.status} for question {question_id}")
                    response_text = await response.text()
                    logger.debug(f"Response: {response_text[:500]}")
                    return None
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching question {question_id}")
            return None
        except Exception as e:
            logger.error(f"Exception fetching question {question_id}: {e}")
            return None
    
    def extract_perseus_data(self, graphql_response: Dict, question_id: str) -> Optional[Dict]:
        """Extract Perseus question data from GraphQL response."""
        try:
            # Navigate through the GraphQL response structure
            if "data" not in graphql_response:
                logger.warning(f"No data field in GraphQL response for {question_id}")
                return None
            
            assessment_item = graphql_response["data"].get("assessmentItem")
            if not assessment_item:
                logger.warning(f"No assessmentItem in GraphQL response for {question_id}")
                return None
            
            item = assessment_item.get("item")
            if not item:
                logger.warning(f"No item in assessmentItem for {question_id}")
                return None
            
            item_data = item.get("itemData")
            if not item_data:
                logger.warning(f"No itemData for {question_id}")
                return None
            
            # Parse itemData (it might be a string or already parsed)
            if isinstance(item_data, str):
                try:
                    perseus_data = json.loads(item_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse itemData JSON for {question_id}: {e}")
                    return None
            else:
                perseus_data = item_data
            
            # Validate Perseus structure
            if not self.validate_perseus_structure(perseus_data, question_id):
                return None
            
            logger.debug(f"Successfully extracted Perseus data for {question_id}")
            return perseus_data
            
        except Exception as e:
            logger.error(f"Error extracting Perseus data for {question_id}: {e}")
            return None
    
    def validate_perseus_structure(self, data: Dict, question_id: str) -> bool:
        """Validate that the data has proper Perseus structure - ENHANCED VERSION."""
        try:
            # Check for required Perseus fields
            required_fields = ["question"]
            optional_fields = ["hints", "answerArea", "itemDataVersion"]
            
            # Must have at least the question field
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required Perseus field '{field}' for {question_id}")
                    return False
            
            # Count optional fields for confidence scoring
            optional_found = sum(1 for field in optional_fields if field in data)
            
            # Check question structure
            question = data["question"]
            if not isinstance(question, dict):
                logger.warning(f"Invalid question structure for {question_id}")
                return False
            
            if "content" not in question:
                logger.warning(f"No content in question for {question_id}")
                return False
            
            # Check content is not empty
            content = question["content"]
            if not content or len(content.strip()) < 5:
                logger.warning(f"Empty or too short content for {question_id}")
                return False
            
            # Enhanced validation: check for widgets (interactive elements)
            widgets_found = 0
            if "widgets" in question and isinstance(question["widgets"], dict):
                widgets_found = len(question["widgets"])
                logger.debug(f"Found {widgets_found} widgets in question {question_id}")
            
            # Check hints structure if present
            hints_valid = True
            if "hints" in data:
                hints = data["hints"]
                if isinstance(hints, list) and len(hints) > 0:
                    logger.debug(f"Found {len(hints)} hints for {question_id}")
                else:
                    hints_valid = False
            
            # Calculate confidence score
            confidence_score = optional_found + (1 if widgets_found > 0 else 0) + (1 if hints_valid else 0)
            
            logger.debug(f"Perseus validation for {question_id}: confidence_score={confidence_score}, widgets={widgets_found}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating Perseus structure for {question_id}: {e}")
            return False

    def validate_response(self, data: Dict, question_id: str) -> bool:
        """Validate that the response contains valid question data."""
        try:
            # Check for GraphQL errors
            if "errors" in data:
                logger.warning(f"GraphQL errors in response for {question_id}: {data['errors']}")
                return False
            
            # Check for data structure
            if "data" not in data:
                logger.warning(f"No data field in response for {question_id}")
                return False
            
            # Check for assessment item
            if "assessmentItem" not in data["data"]:
                logger.warning(f"No assessmentItem in response for {question_id}")
                return False
            
            assessment_item = data["data"]["assessmentItem"]
            
            # Check for errors in assessment item
            if assessment_item.get("error"):
                logger.warning(f"Assessment item error for {question_id}: {assessment_item['error']}")
                return False
            
            # Check for item data
            if "item" not in assessment_item:
                logger.warning(f"No item data for {question_id}")
                return False
            
            item = assessment_item["item"]
            if not item.get("itemData"):
                logger.warning(f"No itemData for {question_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating response for {question_id}: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test if the active scraper can make requests successfully."""
        try:
            if not self.session:
                await self.create_session()
            
            # Test with a simple GraphQL introspection query
            test_query = {
                "query": "{ __schema { queryType { name } } }",
                "variables": {}
            }
            
            async with self.session.post(
                "https://www.khanacademy.org/api/internal/graphql",
                json=test_query,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status in [200, 400]:  # 400 might be expected for introspection
                    logger.info("Active scraper connection test successful")
                    return True
                else:
                    logger.warning(f"Connection test returned status {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def fetch_batch_with_progress(self, question_ids: List[str], progress_callback=None) -> Dict[str, Dict]:
        """Fetch questions with progress reporting."""
        if not question_ids:
            return {}
        
        total_questions = len(question_ids)
        completed = 0
        successful_downloads = {}
        
        # Process in smaller batches to provide progress updates
        batch_size = 5
        for i in range(0, total_questions, batch_size):
            batch = question_ids[i:i + batch_size]
            
            try:
                batch_results = await self.fetch_question_batch(batch)
                successful_downloads.update(batch_results)
                completed += len(batch)
                
                if progress_callback:
                    progress_callback(completed, total_questions, len(batch_results))
                
                logger.info(f"Progress: {completed}/{total_questions} questions processed")
                
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                completed += len(batch)  # Count as processed even if failed
        
        return successful_downloads
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            logger.info("Closed active scraper session")
    
    def update_session_data(self, cookies: str, headers: Dict):
        """Update session cookies and headers."""
        self.session_cookies = cookies
        self.base_headers.update(headers)
        logger.info("Updated session data for active scraper")

    def save_perseus_question(self, question_id: str, perseus_data: Dict, save_directory: str = "khan_academy_json") -> bool:
        """Save Perseus JSON data to file with enhanced metadata."""
        try:
            import os
            # Ensure directory exists
            os.makedirs(save_directory, exist_ok=True)
            
            # Create filename with question ID
            filename = f"{question_id}.json"
            filepath = os.path.join(save_directory, filename)
            
            # Add metadata to the Perseus data
            enhanced_data = {
                **perseus_data,
                "_metadata": {
                    "question_id": question_id,
                    "capture_timestamp": time.time(),
                    "capture_method": "active_scraper",
                    "format_version": "perseus_json"
                }
            }
            
            # Save to file with pretty formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, indent=4, ensure_ascii=False)
            
            logger.debug(f"Saved Perseus data for {question_id} to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving Perseus data for {question_id}: {e}")
            return False

    def analyze_perseus_content(self, perseus_data: Dict) -> Dict:
        """Analyze Perseus content to understand question structure."""
        try:
            analysis = {
                "question_type": "unknown",
                "widget_types": [],
                "has_hints": False,
                "hint_count": 0,
                "content_length": 0,
                "complexity_score": 0
            }
            
            # Analyze question content
            if "question" in perseus_data:
                question = perseus_data["question"]
                if "content" in question:
                    analysis["content_length"] = len(question["content"])
                
                # Analyze widgets (like in your sample JSON)
                if "widgets" in question and isinstance(question["widgets"], dict):
                    widgets = question["widgets"]
                    for widget_id, widget_data in widgets.items():
                        if "type" in widget_data:
                            widget_type = widget_data["type"]
                            analysis["widget_types"].append(widget_type)
                            
                            # Determine question type based on widgets
                            if widget_type == "numeric-input":
                                analysis["question_type"] = "numeric_input"
                            elif widget_type == "radio":
                                analysis["question_type"] = "multiple_choice"
                            elif widget_type == "expression":
                                analysis["question_type"] = "expression"
                            elif widget_type == "image":
                                if analysis["question_type"] == "unknown":
                                    analysis["question_type"] = "image_based"
            
            # Analyze hints
            if "hints" in perseus_data and isinstance(perseus_data["hints"], list):
                analysis["has_hints"] = True
                analysis["hint_count"] = len(perseus_data["hints"])
            
            # Calculate complexity score
            complexity = 0
            complexity += min(analysis["content_length"] // 100, 5)  # Content length factor
            complexity += len(analysis["widget_types"])  # Widget complexity
            complexity += analysis["hint_count"] // 2  # Hint complexity
            analysis["complexity_score"] = complexity
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing Perseus content: {e}")
            return {"error": str(e)}