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
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
        
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
                successful_downloads[question_id] = result
                logger.debug(f"Successfully fetched {question_id}")
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