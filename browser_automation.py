"""
Enhanced Khan Academy Question Scraper with Browser Automation
This module provides automated browser control to trigger question loading
and refresh the page when needed.
"""

import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import threading
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KhanAcademyBrowserAutomation:
    def __init__(self, proxy_port=8080):
        self.proxy_port = proxy_port
        self.driver = None
        self.wait = None
        self.current_exercise_url = None
        self.questions_loaded = set()
        
    def setup_browser(self):
        """Setup Chrome browser with proxy configuration - ENHANCED VERSION with better timeouts."""
        chrome_options = Options()
        
        # Configure proxy
        chrome_options.add_argument(f'--proxy-server=http://127.0.0.1:{self.proxy_port}')
        
        # ESSENTIAL: SSL/Certificate handling for mitmproxy
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--ignore-certificate-errors-spki-list')
        chrome_options.add_argument('--ignore-urlfetcher-cert-requests')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-insecure-localhost')
        
        # PERFORMANCE: Improve loading speed
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Speed up loading
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')  # Reduce resource usage
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-translate')
        
        # AUTOMATION: Better detection avoidance
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # WINDOW: Start with reasonable size
        chrome_options.add_argument('--window-size=1280,720')  # Smaller for better performance
        
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # ENHANCED: More generous timeouts for slow connections
            self.driver.set_page_load_timeout(60)  # Increased to 60 seconds
            self.driver.implicitly_wait(15)  # Increased implicit wait
            
            self.wait = WebDriverWait(self.driver, 30)  # Increased explicit wait
            logger.info("Browser setup complete with enhanced configuration")
            return True
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            return False
    
    def navigate_to_exercise(self, exercise_url):
        """Navigate to a Khan Academy exercise with enhanced error handling."""
        try:
            logger.info(f"Navigating to exercise: {exercise_url}")
            
            # Validate URL format first
            if not self._validate_url_accessibility(exercise_url):
                logger.error("URL validation failed")
                return False
            
            # Navigate with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Navigation attempt {attempt + 1}/{max_retries}")
                    self.driver.get(exercise_url)
                    logger.info("Page load initiated successfully")
                    
                    # Wait for basic page structure with timeout
                    time.sleep(5)  # Initial wait
                    
                    self.current_exercise_url = exercise_url
                    
                    # Check if page loaded successfully
                    if self._verify_page_loaded():
                        logger.info("Page loaded and verified successfully")
                        return self._wait_for_page_ready()
                    else:
                        logger.warning(f"Page verification failed on attempt {attempt + 1}")
                        if attempt < max_retries - 1:
                            time.sleep(5)  # Wait before retry
                            continue
                        else:
                            return False
                            
                except Exception as e:
                    logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                    else:
                        raise e
            
            return False
            
        except Exception as e:
            logger.error(f"Navigation completely failed: {e}")
            return False

    def _validate_url_accessibility(self, url):
        """Validate that the URL is accessible before attempting navigation."""
        try:
            # Basic URL structure validation
            if not url.startswith("https://www.khanacademy.org/"):
                logger.error("URL is not a Khan Academy URL")
                return False
            
            # Check for placeholder URLs
            if "..." in url or len(url) < 80:
                logger.error("URL appears to be a placeholder or incomplete")
                return False
            
            logger.info("URL validation passed")
            return True
            
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False

    def _verify_page_loaded(self):
        """Verify that the page loaded successfully."""
        try:
            # Check current URL
            current_url = self.driver.current_url
            logger.info(f"Current URL: {current_url}")
            
            # Check if we're on Khan Academy
            if "khanacademy.org" not in current_url.lower():
                logger.error("Not on Khan Academy domain")
                return False
            
            # Check if page has basic content
            page_source = self.driver.page_source
            if len(page_source) < 1000:  # Very basic check
                logger.error("Page content appears minimal")
                return False
            
            # Check for common error indicators
            error_indicators = ["404", "not found", "error", "blocked"]
            page_text = page_source.lower()
            for indicator in error_indicators:
                if indicator in page_text and "error" in page_text[:2000]:  # Check early in page
                    logger.error(f"Page contains error indicator: {indicator}")
                    return False
            
            logger.info("Page verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Page verification error: {e}")
            return False

    def _check_partial_page_load(self):
        """Check if a partial page load has enough content to be useful."""
        try:
            # Step 1: Check for basic page structure
            body = self.driver.find_element(By.TAG_NAME, "body")
            if not body:
                logger.info("No body element found")
                return False
            
            # Step 2: Check current URL contains khanacademy
            current_url = self.driver.current_url.lower()
            if "khanacademy" not in current_url:
                logger.info(f"Not on Khan Academy: {current_url}")
                return False
            
            logger.info(f"On Khan Academy URL: {current_url}")
            
            # Step 3: Check for ANY content - be very lenient
            try:
                # Look for any div, span, or content elements
                content_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "div, span, p, h1, h2, h3, article, section, main")
                
                if len(content_elements) > 5:  # Very low bar - just need some elements
                    logger.info(f"Found {len(content_elements)} content elements")
                    return True
                    
                # Also check for any text content
                page_text = self.driver.execute_script("return document.body.innerText || '';")
                if len(page_text.strip()) > 20:  # Any reasonable amount of text
                    logger.info(f"Found {len(page_text)} characters of text content")
                    return True
                    
                logger.info("Insufficient content found")
                return False
                
            except Exception as e:
                logger.warning(f"Error checking content: {e}")
                # If we can't check content but we're on the right URL, assume it's okay
                return True
                
        except Exception as e:
            logger.warning(f"Error in partial page check: {e}")
            return False

    def _wait_for_page_ready(self):
        """Wait for Khan Academy page to be ready with proper content detection."""
        try:
            logger.info("Waiting for Khan Academy page to be ready...")
            
            # Step 1: Wait for basic DOM
            try:
                basic_wait = WebDriverWait(self.driver, 15)
                basic_wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info("Basic DOM structure loaded")
            except TimeoutException:
                logger.warning("Basic DOM timeout")
                return False
            
            # Step 2: Wait for Khan Academy specific content
            try:
                ka_wait = WebDriverWait(self.driver, 20)
                # Look for Khan Academy app or exercise content
                ka_wait.until(EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#application")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id]")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".exercise")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".problem")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='khan']"))
                ))
                logger.info("Khan Academy content detected")
            except TimeoutException:
                logger.warning("Khan Academy content timeout, checking URL...")
                # If we're on the right URL, continue anyway
                if "khanacademy" in self.driver.current_url.lower():
                    logger.info("On Khan Academy URL, proceeding despite timeout")
                else:
                    return False
            
            # Step 3: Wait a bit more for JavaScript to initialize
            logger.info("Waiting for JavaScript initialization...")
            time.sleep(10)  # Give time for Khan Academy's JS to load
            
            # Step 4: Check if we have actual content
            if self._check_khan_academy_content():
                logger.info("Khan Academy page is ready with content")
                return True
            else:
                logger.warning("Khan Academy page loaded but content not detected")
                return True  # Continue anyway - might work
                
        except Exception as e:
            logger.error(f"Error waiting for page ready: {e}")
            return False

    def _check_khan_academy_content(self):
        """Check if Khan Academy content is properly loaded."""
        try:
            # Check URL
            current_url = self.driver.current_url.lower()
            if "khanacademy" not in current_url:
                return False
            
            # Check for content elements
            content_selectors = [
                "#application",
                "[data-test-id]", 
                ".exercise",
                ".problem",
                ".question",
                "[class*='khan']",
                "div[role='main']",
                "main"
            ]
            
            content_found = 0
            for selector in content_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        content_found += len(elements)
                        logger.info(f"Found {len(elements)} elements for selector: {selector}")
                except:
                    continue
            
            # Check for text content
            try:
                page_text = self.driver.execute_script("return document.body.innerText || '';")
                text_length = len(page_text.strip())
                logger.info(f"Page contains {text_length} characters of text")
                
                if text_length > 100:  # Reasonable amount of text
                    content_found += 1
            except:
                pass
            
            logger.info(f"Total content indicators found: {content_found}")
            return content_found > 0
            
        except Exception as e:
            logger.warning(f"Error checking Khan Academy content: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to navigate to exercise: {e}")
            return False
    
    def start_exercise(self):
        """Start the exercise to trigger question loading."""
        try:
            # Look for various start buttons
            start_selectors = [
                "button[data-test-id='start-button']",
                "button[data-test-id='practice-button']",
                "a[data-test-id='start-practice']",
                ".btn:contains('Start')",
                ".btn:contains('Practice')",
                "button:contains('Start')",
                "button:contains('Practice')"
            ]
            
            for selector in start_selectors:
                try:
                    if ":contains" in selector:
                        # Handle jQuery-style selectors with JavaScript
                        element = self.driver.execute_script(f"""
                            return Array.from(document.querySelectorAll('button')).find(el => 
                                el.textContent.includes('{selector.split("'")[1]}'));
                        """)
                        if element:
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info(f"Clicked start button using JavaScript: {selector}")
                            break
                    else:
                        element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        element.click()
                        logger.info(f"Clicked start button: {selector}")
                        break
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            # Wait for exercise to load
            time.sleep(5)
            return True
            
        except Exception as e:
            logger.error(f"Failed to start exercise: {e}")
            return False
    
    def refresh_page(self):
        """Refresh the current page to get fresh questions."""
        try:
            logger.info("Refreshing page to load new questions...")
            self.driver.refresh()
            time.sleep(3)
            
            # Restart the exercise after refresh
            self.start_exercise()
            return True
        except Exception as e:
            logger.error(f"Failed to refresh page: {e}")
            return False
    
    def simulate_question_interaction(self):
        """Simulate interaction to trigger question loading and progression."""
        try:
            # Method 1: Try to find and click next question button
            next_selectors = [
                "button[data-test-id='next-question']",
                "button:contains('Next')",
                ".next-button",
                "button[aria-label*='Next']",
                "button[title*='Next']"
            ]
            
            for selector in next_selectors:
                try:
                    if ":contains" in selector:
                        element = self.driver.execute_script(f"""
                            return Array.from(document.querySelectorAll('button')).find(el => 
                                el.textContent.toLowerCase().includes('next'));
                        """)
                        if element:
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info("Clicked next question button")
                            time.sleep(2)
                            return True
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element.is_enabled():
                            element.click()
                            logger.info(f"Clicked next question: {selector}")
                            time.sleep(2)
                            return True
                except Exception:
                    continue
            
            # Method 2: Try to answer current question to progress
            self.attempt_to_answer_question()
            
            # Method 3: Look for question elements to interact with
            interactive_selectors = [
                "input[type='text']",
                "input[type='number']", 
                ".radio input",
                ".multiple-choice input",
                "button[data-test-id='check-answer']",
                ".btn-primary"
            ]
            
            for selector in interactive_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # Just focus on the element to trigger any lazy loading
                        self.driver.execute_script("arguments[0].focus();", elements[0])
                        time.sleep(0.5)
                        break
                except Exception:
                    continue
                    
            return True
        except Exception as e:
            logger.error(f"Failed to simulate interaction: {e}")
            return False

    def detect_question_type(self):
        """Detect the type of question being displayed."""
        try:
            selectors = {
                "numeric_input": "input[type='text'], input[data-test-id='numeric-input'], input[type='number']",
                "multiple_choice": "input[type='radio'], .multiple-choice",
                "expression": "input[data-test-id='expression-input']",
                "graph": ".graphie, .interactive-graph",
                "dropdown": "select, .dropdown"
            }
            
            for question_type, selector in selectors.items():
                if self.driver.find_elements(By.CSS_SELECTOR, selector):
                    logger.info(f"Detected question type: {question_type}")
                    return question_type
            return "generic"
        except Exception as e:
            logger.debug(f"Error detecting question type: {e}")
            return "generic"
    
    def auto_answer_question(self):
        """Automatically answer the current question based on its type."""
        try:
            # Wait a moment for page to settle
            time.sleep(2)
            
            # Check if there's any content to work with
            try:
                # Look for any exercise/question content with more lenient selectors
                content_selectors = [
                    "[data-test-id='exercise-content']",
                    ".problem-content", 
                    ".question-content",
                    ".exercise-content",
                    ".problem",
                    ".question",
                    "[class*='question']",
                    "[class*='problem']",
                    "[class*='exercise']"
                ]
                
                content_found = False
                for selector in content_selectors:
                    if self.driver.find_elements(By.CSS_SELECTOR, selector):
                        content_found = True
                        break
                
                if not content_found:
                    logger.warning("No question content found - page may not be ready")
                    return False
                    
            except Exception as e:
                logger.warning(f"Error checking for content: {e}")
                return False
            
            # Detect question type and answer appropriately
            question_type = self.detect_question_type()
            
            if question_type == "numeric_input":
                return self.answer_numeric_question()
            elif question_type == "multiple_choice":
                return self.answer_multiple_choice()
            elif question_type == "expression":
                return self.answer_expression_question()
            else:
                return self.answer_generic_question()
                
        except Exception as e:
            logger.error(f"Failed to auto-answer question: {e}")
            return False
    
    def answer_numeric_question(self):
        """Answer numeric input questions."""
        try:
            numeric_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number'], input[data-test-id='numeric-input']")
            for input_elem in numeric_inputs:
                if input_elem.is_displayed() and input_elem.is_enabled():
                    input_elem.clear()
                    # Use a simple answer that's likely to be wrong but will trigger progression
                    input_elem.send_keys("1")
                    logger.info("Filled numeric input with test value")
                    time.sleep(0.5)
                    return True
            return False
        except Exception as e:
            logger.debug(f"Error answering numeric question: {e}")
            return False
    
    def answer_multiple_choice(self):
        """Answer multiple choice questions."""
        try:
            radio_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            if radio_buttons:
                # Select the first option
                first_radio = radio_buttons[0]
                if first_radio.is_displayed() and first_radio.is_enabled():
                    self.driver.execute_script("arguments[0].click();", first_radio)
                    logger.info("Selected first multiple choice option")
                    time.sleep(0.5)
                    return True
            return False
        except Exception as e:
            logger.debug(f"Error answering multiple choice: {e}")
            return False
    
    def answer_expression_question(self):
        """Answer expression input questions."""
        try:
            expression_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[data-test-id='expression-input'], .math-input")
            for input_elem in expression_inputs:
                if input_elem.is_displayed() and input_elem.is_enabled():
                    input_elem.clear()
                    input_elem.send_keys("x")
                    logger.info("Filled expression input with test value")
                    time.sleep(0.5)
                    return True
            return False
        except Exception as e:
            logger.debug(f"Error answering expression question: {e}")
            return False
    
    def answer_generic_question(self):
        """Fallback method for unknown question types."""
        try:
            # Try to fill any visible text inputs
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            for input_elem in text_inputs:
                if input_elem.is_displayed() and input_elem.is_enabled():
                    input_elem.clear()
                    input_elem.send_keys("1")
                    time.sleep(0.5)
            
            # Try to click first radio button if available
            radio_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            if radio_buttons:
                self.driver.execute_script("arguments[0].click();", radio_buttons[0])
                time.sleep(0.5)
            
            logger.info("Applied generic answer strategy")
            return True
        except Exception as e:
            logger.debug(f"Error with generic answer strategy: {e}")
            return False
    
    def attempt_to_answer_question(self):
        """
        Legacy method maintained for compatibility - now uses auto_answer_question.
        """
        return self.auto_answer_question()
    def wait_for_question_load(self, timeout=30):
        """Wait for a new question to fully load with multiple indicators."""
        try:
            # Wait for exercise content
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='exercise-content'], .problem-content, .question-content")))
            
            # Wait for question content to be visible
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".question-content, .problem-content, .exercise-content")))
            
            # Wait for input elements to be interactable
            input_selectors = [
                "input[type='text']",
                "input[type='radio']", 
                "input[type='number']",
                "button[data-test-id='check-answer']"
            ]
            
            for selector in input_selectors:
                try:
                    WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
                    
            # Additional wait for JavaScript to settle
            time.sleep(2)
            logger.info("Question loaded successfully")
            return True
            
        except TimeoutException:
            logger.warning("Question load timeout - continuing anyway")
            return False
        except Exception as e:
            logger.error(f"Error waiting for question load: {e}")
            return False
    
    def progress_to_next_question(self):
        """Progress to next question using UI buttons instead of refresh - ENHANCED VERSION."""
        try:
            logger.info("Starting intelligent question progression sequence")
            
            # Step 1: Wait for page stability and detect question type
            if not self._wait_for_stable_page():
                logger.warning("Page not stable, but continuing...")
            
            question_type = self.detect_question_type()
            logger.info(f"Detected question type: {question_type}")
            
            # Step 2: Answer the question intelligently based on Perseus format
            try:
                success = self._answer_question_by_type(question_type)
                if success:
                    logger.info("Question answered successfully")
                else:
                    logger.warning("Could not answer question, will still try to progress")
            except Exception as e:
                logger.warning(f"Auto-answer failed: {e}")
            
            # Step 3: Submit answer with enhanced detection
            if not self._submit_answer_with_retry():
                logger.error("Failed to submit answer")
                return False
            
            # Step 4: Wait for feedback and continue to next question
            if not self._continue_to_next_question():
                logger.error("Failed to progress to next question")
                return False
                
            logger.info("Question progression completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Question progression failed: {e}")
            return False

    def _wait_for_stable_page(self):
        """Wait for Khan Academy page to stabilize after navigation."""
        try:
            # Wait for loading indicators to disappear
            loading_selectors = [
                ".loading-spinner", "[data-test-id*='loading']", 
                ".skeleton-loader", "[aria-label*='loading']",
                ".spinner", ".loader"
            ]
            
            for selector in loading_selectors:
                try:
                    WebDriverWait(self.driver, 3).until_not(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                except TimeoutException:
                    pass
            
            # Wait for interactive content to be available
            interactive_selectors = [
                "input[type='text']", "input[type='number']", 
                "input[type='radio']", "button[data-test-id*='check']",
                "[data-test-id*='numeric-input']"
            ]
            
            for selector in interactive_selectors:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Interactive content ready: {selector}")
                    time.sleep(1)  # Brief pause for JS to initialize
                    return True
                except TimeoutException:
                    continue
            
            logger.warning("No interactive content detected, but proceeding")
            return True
            
        except Exception as e:
            logger.error(f"Error waiting for stable page: {e}")
            return False

    def _answer_question_by_type(self, question_type):
        """Answer question based on detected type and Perseus format."""
        try:
            if question_type == "numeric_input":
                return self._answer_numeric_inputs()
            elif question_type == "multiple_choice":
                return self._answer_multiple_choice_enhanced()
            elif question_type == "expression":
                return self._answer_expression_enhanced()
            else:
                return self._answer_generic_enhanced()
        except Exception as e:
            logger.error(f"Error answering question type {question_type}: {e}")
            return False

    def _answer_numeric_inputs(self):
        """Handle numeric input questions (like the seals example)."""
        try:
            # Look for numeric input fields with Perseus-style data attributes
            numeric_selectors = [
                "[data-test-id*='numeric-input']",
                "input[type='number']",
                "input[type='text'][data-test-id*='input']",
                ".perseus-widget-numeric-input input",
                "input[aria-label*='answer']"
            ]
            
            inputs_filled = 0
            for selector in numeric_selectors:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for input_elem in inputs:
                        if input_elem.is_displayed() and input_elem.is_enabled():
                            # Clear and fill with a reasonable test value
                            input_elem.clear()
                            time.sleep(0.3)
                            
                            # Use different values for different inputs
                            test_values = ["5", "35", "7", "42", "10"]
                            value = test_values[inputs_filled % len(test_values)]
                            
                            input_elem.send_keys(value)
                            logger.info(f"Filled numeric input with: {value}")
                            inputs_filled += 1
                            time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"Error with numeric input {selector}: {e}")
                    continue
            
            return inputs_filled > 0
            
        except Exception as e:
            logger.error(f"Error answering numeric inputs: {e}")
            return False

    def _submit_answer_with_retry(self):
        """Submit answer with multiple retry strategies."""
        try:
            # Enhanced check button detection
            check_selectors = [
                "button[data-test-id='check-answer-button']",
                "button[data-test-id='check-answer']",
                "button[data-test-id='check']",
                ".perseus-widget-interaction button:contains('Check')",
                "button.check-answer-button",
                "button:contains('Check')",
                "button:contains('Submit')",
                "[data-test-id*='check'] button"
            ]
            
            for attempt in range(3):  # 3 attempts
                for selector in check_selectors:
                    try:
                        if ":contains" in selector:
                            # Handle text-based selectors with JavaScript
                            element = self.driver.execute_script("""
                                return Array.from(document.querySelectorAll('button')).find(el => 
                                    el.textContent.toLowerCase().includes('check') ||
                                    el.textContent.toLowerCase().includes('submit'));
                            """)
                            if element and element.is_enabled():
                                self.driver.execute_script("arguments[0].click();", element)
                                logger.info("Submitted answer via JavaScript")
                                time.sleep(2)  # Wait for submission processing
                                return True
                        else:
                            check_button = WebDriverWait(self.driver, 2).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            check_button.click()
                            logger.info(f"Submitted answer: {selector}")
                            time.sleep(2)
                            return True
                    except TimeoutException:
                        continue
                    except Exception as e:
                        logger.debug(f"Submit attempt failed for {selector}: {e}")
                        continue
                
                if attempt < 2:  # Don't sleep on last attempt
                    logger.info(f"Submit attempt {attempt + 1} failed, retrying...")
                    time.sleep(1)
            
            logger.warning("All submit attempts failed")
            return False
            
        except Exception as e:
            logger.error(f"Error submitting answer: {e}")
            return False

    def _continue_to_next_question(self):
        """Continue to next question after answer submission."""
        try:
            # Wait a moment for feedback to appear
            time.sleep(2)
            
            # Look for next question / continue buttons
            next_selectors = [
                "button[data-test-id='next-question']",
                "button[data-test-id='continue']",
                "button:contains('Next')",
                "button:contains('Continue')",
                "button:contains('Next question')",
                ".next-question-button",
                "[data-test-id*='next'] button",
                "[data-test-id*='continue'] button"
            ]
            
            for selector in next_selectors:
                try:
                    if ":contains" in selector:
                        element = self.driver.execute_script("""
                            return Array.from(document.querySelectorAll('button')).find(el => 
                                el.textContent.toLowerCase().includes('next') ||
                                el.textContent.toLowerCase().includes('continue'));
                        """)
                        if element and element.is_enabled():
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info("Continued to next question via JavaScript")
                            time.sleep(3)  # Wait for next question to load
                            return True
                    else:
                        next_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        next_button.click()
                        logger.info(f"Continued to next question: {selector}")
                        time.sleep(3)
                        return True
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"Next button {selector} failed: {e}")
                    continue
            
            logger.warning("No next/continue button found")
            return False
            
        except Exception as e:
            logger.error(f"Error continuing to next question: {e}")
            return False

    def _answer_multiple_choice_enhanced(self):
        """Enhanced multiple choice answering."""
        try:
            radio_selectors = [
                "input[type='radio']",
                ".multiple-choice input",
                "[data-test-id*='choice'] input",
                ".answer-choice input"
            ]
            
            for selector in radio_selectors:
                try:
                    radio_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if radio_buttons:
                        # Select the first visible and enabled option
                        for radio in radio_buttons:
                            if radio.is_displayed() and radio.is_enabled():
                                self.driver.execute_script("arguments[0].click();", radio)
                                logger.info("Selected multiple choice option")
                                return True
                except Exception as e:
                    logger.debug(f"Error with radio selector {selector}: {e}")
                    continue
            
            return False
        except Exception as e:
            logger.error(f"Error answering multiple choice: {e}")
            return False

    def _answer_expression_enhanced(self):
        """Enhanced expression input answering."""
        try:
            expression_selectors = [
                "input[data-test-id*='expression']",
                ".math-input input",
                "[data-test-id*='math'] input"
            ]
            
            for selector in expression_selectors:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for input_elem in inputs:
                        if input_elem.is_displayed() and input_elem.is_enabled():
                            input_elem.clear()
                            input_elem.send_keys("x")
                            logger.info("Filled expression input")
                            return True
                except Exception as e:
                    logger.debug(f"Error with expression selector {selector}: {e}")
                    continue
            
            return False
        except Exception as e:
            logger.error(f"Error answering expression: {e}")
            return False

    def _answer_generic_enhanced(self):
        """Enhanced generic question answering."""
        try:
            # Try any visible input fields
            generic_selectors = [
                "input[type='text']:not([readonly])",
                "input[type='number']:not([readonly])",
                "input[type='radio']",
                "textarea:not([readonly])"
            ]
            
            answered = False
            for selector in generic_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            if elem.get_attribute('type') == 'radio':
                                self.driver.execute_script("arguments[0].click();", elem)
                                answered = True
                                break
                            else:
                                elem.clear()
                                elem.send_keys("1")
                                answered = True
                            time.sleep(0.3)
                except Exception as e:
                    logger.debug(f"Error with generic selector {selector}: {e}")
                    continue
            
            if answered:
                logger.info("Applied generic answer strategy")
            return answered
            
        except Exception as e:
            logger.error(f"Error with generic answer strategy: {e}")
            return False
    
    def refresh_page(self):
        """Refresh the current page to get fresh questions."""
        try:
            logger.info("Refreshing page to load new questions...")
            self.driver.refresh()
            time.sleep(3)
            
            # Restart the exercise after refresh
            self.start_exercise()
            return True
        except Exception as e:
            logger.error(f"Failed to refresh page: {e}")
            return False
    
    def handle_exercise_interruptions(self):
        """Handle pop-ups, completion dialogs, and other interruptions."""
        try:
            interruption_handlers = [
                ("Practice complete", self.handle_completion_dialog),
                ("Congratulations", self.handle_completion_dialog),
                ("Streak", self.handle_streak_popup),
                ("Hint", self.handle_hint_dialog),
                ("Error", self.handle_error_dialog),
                ("Try again", self.handle_retry_dialog)
            ]
            
            page_text = self.driver.page_source.lower()
            
            for text, handler in interruption_handlers:
                if text.lower() in page_text:
                    logger.info(f"Handling interruption: {text}")
                    return handler()
            return True
        except Exception as e:
            logger.error(f"Error handling interruptions: {e}")
            return True  # Continue anyway
    
    def handle_completion_dialog(self):
        """Handle exercise completion dialogs."""
        try:
            # Look for restart or continue buttons
            restart_selectors = [
                "button[data-test-id='restart']",
                "button:contains('Start over')",
                "button:contains('Restart')",
                "a[href*='restart']"
            ]
            
            for selector in restart_selectors:
                try:
                    if ":contains" in selector:
                        element = self.driver.execute_script(f"""
                            return Array.from(document.querySelectorAll('button, a')).find(el => 
                                el.textContent.toLowerCase().includes('{selector.split("'")[1].lower()}'));
                        """)
                        if element:
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info("Restarted exercise from completion dialog")
                            return True
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        element.click()
                        logger.info("Restarted exercise from completion dialog")
                        return True
                except Exception:
                    continue
            
            # If no restart button, refresh the page
            logger.info("No restart button found, refreshing page")
            return self.refresh_page()
        except Exception as e:
            logger.error(f"Error handling completion dialog: {e}")
            return False
    
    def handle_streak_popup(self):
        """Handle streak celebration popups."""
        try:
            # Look for continue or dismiss buttons
            dismiss_selectors = [
                "button[data-test-id='continue']",
                "button[data-test-id='dismiss']",
                ".modal button",
                "button:contains('Continue')"
            ]
            
            for selector in dismiss_selectors:
                try:
                    if ":contains" in selector:
                        element = self.driver.execute_script(f"""
                            return Array.from(document.querySelectorAll('button')).find(el => 
                                el.textContent.toLowerCase().includes('continue'));
                        """)
                        if element:
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info("Dismissed streak popup")
                            return True
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        element.click()
                        logger.info("Dismissed streak popup")
                        return True
                except Exception:
                    continue
            
            return True  # Continue even if can't dismiss
        except Exception as e:
            logger.debug(f"Error handling streak popup: {e}")
            return True
    
    def handle_hint_dialog(self):
        """Handle hint dialogs."""
        try:
            # Look for close or skip hint buttons
            close_selectors = [
                "button[data-test-id='close-hint']",
                "button[data-test-id='skip-hint']", 
                ".hint-dialog button",
                "button:contains('Skip')"
            ]
            
            for selector in close_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    element.click()
                    logger.info("Closed hint dialog")
                    return True
                except Exception:
                    continue
            
            return True
        except Exception as e:
            logger.debug(f"Error handling hint dialog: {e}")
            return True
    
    def handle_error_dialog(self):
        """Handle error dialogs."""
        try:
            # Look for OK or dismiss buttons
            ok_selectors = [
                "button[data-test-id='ok']",
                "button[data-test-id='dismiss']",
                ".error-dialog button",
                "button:contains('OK')"
            ]
            
            for selector in ok_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    element.click()
                    logger.info("Dismissed error dialog")
                    return True
                except Exception:
                    continue
            
            return True
        except Exception as e:
            logger.debug(f"Error handling error dialog: {e}")
            return True
    
    def handle_retry_dialog(self):
        """Handle retry/try again dialogs."""
        try:
            # Look for try again or continue buttons
            retry_selectors = [
                "button[data-test-id='try-again']",
                "button[data-test-id='retry']",
                "button:contains('Try again')",
                "button:contains('Continue')"
            ]
            
            for selector in retry_selectors:
                try:
                    if ":contains" in selector:
                        element = self.driver.execute_script(f"""
                            return Array.from(document.querySelectorAll('button')).find(el => 
                                el.textContent.toLowerCase().includes('{selector.split("'")[1].lower()}'));
                        """)
                        if element:
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info("Clicked try again")
                            return True
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        element.click()
                        logger.info("Clicked try again")
                        return True
                except Exception:
                    continue
            
            return True
        except Exception as e:
            logger.debug(f"Error handling retry dialog: {e}")
            return True
    
    def attempt_to_progress_to_next_question(self):
        """
        Try various methods to progress to the next question.
        """
        try:
            # Method 1: Look for "Next" or "Continue" buttons
            progress_selectors = [
                "button[data-test-id='next-question']",
                "button[data-test-id='continue']",
                "a[data-test-id='next-question']",
                "button:contains('Next')",
                "button:contains('Continue')",
                ".next-button",
                ".continue-button"
            ]
            
            for selector in progress_selectors:
                try:
                    if ":contains" in selector:
                        element = self.driver.execute_script(f"""
                            return Array.from(document.querySelectorAll('button, a')).find(el => 
                                el.textContent.toLowerCase().includes('{selector.split("'")[1].lower()}'));
                        """)
                        if element and element.is_displayed():
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info(f"Progressed using: {selector}")
                            time.sleep(3)
                            return True
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            logger.info(f"Progressed using: {selector}")
                            time.sleep(3)
                            return True
                except Exception:
                    continue
            
            # Method 2: If we can't find progress buttons, try refreshing to get new questions
            logger.info("No progress buttons found, will refresh to get new questions")
            return False
            
        except Exception as e:
            logger.debug(f"Could not progress to next question: {e}")
            return False
    
    def automate_exercise_session(self, exercise_url, max_questions=1000, refresh_interval=300):
        """
        Run a comprehensive automated session for an exercise with improved UI interactions.
        
        Args:
            exercise_url: URL of the Khan Academy exercise
            max_questions: Maximum number of questions to capture
            refresh_interval: How often to refresh if no progress (seconds) - increased default
        """
        if not self.setup_browser():
            return False

        try:
            # Navigate to exercise
            if not self.navigate_to_exercise(exercise_url):
                return False

            # Start the exercise
            if not self.start_exercise():
                logger.warning("Could not start exercise, continuing anyway...")

            # Main loop for question capture with improved progression
            questions_progressed = 0
            max_questions_per_session = max_questions
            last_refresh_time = time.time()
            consecutive_failures = 0
            
            logger.info(f"Starting automated session - target: {max_questions} questions")

            while questions_progressed < max_questions_per_session and consecutive_failures < 5:
                cycle_start = time.time()
                logger.info(f"Question {questions_progressed + 1}/{max_questions_per_session}")

                # Handle any interruptions first
                if not self.handle_exercise_interruptions():
                    logger.warning("Failed to handle interruptions")

                # Wait for current question to load
                if not self.wait_for_question_load():
                    logger.warning("Question load timeout, attempting to continue")

                # Try to progress to next question using improved UI interactions
                if self.progress_to_next_question():
                    questions_progressed += 1
                    consecutive_failures = 0
                    logger.info(f"Successfully progressed to question {questions_progressed + 1}")
                    
                    # Brief pause between questions to allow for data capture
                    time.sleep(3)
                else:
                    consecutive_failures += 1
                    logger.warning(f"Failed to progress (failure #{consecutive_failures})")
                    
                    # If we've had several failures, try refresh as fallback
                    current_time = time.time()
                    if consecutive_failures >= 3 or (current_time - last_refresh_time) > refresh_interval:
                        logger.info("Multiple failures detected, refreshing page as fallback...")
                        if self.refresh_page():
                            last_refresh_time = current_time
                            consecutive_failures = 0
                            time.sleep(5)  # Allow page to settle after refresh
                        else:
                            logger.error("Failed to refresh page")
                            break

                # Progress reporting every 5 questions
                if questions_progressed % 5 == 0 and questions_progressed > 0:
                    elapsed = time.time() - cycle_start
                    logger.info(f"Progress update: {questions_progressed} questions completed")

            if consecutive_failures >= 5:
                logger.error("Too many consecutive failures, stopping session")
            else:
                logger.info(f"Automated session completed successfully - {questions_progressed} questions processed")
            
            return questions_progressed > 0

        except Exception as e:
            logger.error(f"Automation session failed: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up browser resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser cleanup completed")
            except Exception as e:
                logger.error(f"Error during browser cleanup: {e}")

def run_automation(exercise_url, proxy_port=8080):
    """
    Run browser automation for question extraction.
    
    Args:
        exercise_url: Khan Academy exercise URL
        proxy_port: Port where mitmproxy is running
    """
    automation = KhanAcademyBrowserAutomation(proxy_port)
    return automation.automate_exercise_session(exercise_url)

if __name__ == "__main__":
    # Example usage
    example_url = "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-functions-equations/x2f8bb11595b61c86:quadratic-formula/e/quadratic_formula"
    run_automation(example_url)