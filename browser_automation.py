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
        """Setup Chrome browser with proxy configuration."""
        chrome_options = Options()
        
        # Configure proxy
        chrome_options.add_argument(f'--proxy-server=http://127.0.0.1:{self.proxy_port}')
        
        # Enhanced SSL/Certificate handling for mitmproxy
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--ignore-certificate-errors-spki-list')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--ignore-urlfetcher-cert-requests')
        chrome_options.add_argument('--disable-cert-verification')
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Network and timeout improvements
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-default-apps')
        
        # Additional network optimizations
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Speed up loading
        # Removed --disable-javascript as Khan Academy needs it
        
        # Additional options for automation
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Optional: Run in headless mode (comment out for debugging)
        # chrome_options.add_argument('--headless')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set shorter timeouts for faster operation and better error handling
            self.driver.set_page_load_timeout(20)  # Reduced from 30
            self.driver.implicitly_wait(5)  # Reduced from 10
            
            self.wait = WebDriverWait(self.driver, 15)  # Reduced from 20
            logger.info("Browser setup complete with enhanced proxy and SSL configuration")
            return True
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            return False
    
    def navigate_to_exercise(self, exercise_url):
        """Navigate to a Khan Academy exercise."""
        try:
            logger.info(f"Navigating to exercise: {exercise_url}")
            
            # Try to load the page with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver.get(exercise_url)
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Navigation attempt {attempt + 1} failed, retrying: {e}")
                        time.sleep(5)
                    else:
                        raise e
            
            self.current_exercise_url = exercise_url
            
            # Wait for page to load with better error handling and shorter timeouts
            try:
                # Use shorter timeout for initial page load check
                short_wait = WebDriverWait(self.driver, 10)
                short_wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info("Basic page structure loaded")
                
                # Wait for Khan Academy specific elements with even shorter timeout
                khan_wait = WebDriverWait(self.driver, 5)
                try:
                    # Look for any Khan Academy content indicators
                    khan_wait.until(lambda driver: 
                        driver.find_elements(By.CSS_SELECTOR, "[data-test-id], .exercise, .problem, [class*='khan'], [class*='exercise']") or
                        "khanacademy" in driver.current_url.lower()
                    )
                    logger.info("Khan Academy content detected")
                except:
                    logger.info("Khan Academy content check timeout, but URL suggests we're on the right page")
                
                # Give time for JavaScript to initialize
                time.sleep(3)
                logger.info("Page loaded successfully")
                
            except Exception as e:
                logger.warning(f"Page load wait failed, but continuing: {e}")
                # Even if the wait fails, we might still be on the page - check URL
                try:
                    current_url = self.driver.current_url
                    if "khanacademy" in current_url.lower():
                        logger.info(f"On Khan Academy page despite timeout: {current_url}")
                    else:
                        logger.warning(f"Not on expected page: {current_url}")
                except:
                    logger.warning("Could not verify current URL")
            
            return True
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
        """Progress to next question using UI buttons instead of refresh."""
        try:
            logger.info("Starting question progression sequence")
            
            # Step 1: Try to answer the current question (non-blocking)
            try:
                self.auto_answer_question()
                logger.info("Question answered (or attempted)")
            except Exception as e:
                logger.warning(f"Auto-answer failed, continuing: {e}")
            
            # Step 2: Look for and click "Check Answer" button
            check_selectors = [
                "button[data-test-id='check-answer']",
                "button[data-test-id='check']", 
                "button.check-answer-button",
                ".check-button",
                "button:contains('Check')",
                "[data-test-id*='check']"
            ]
            
            check_clicked = False
            for selector in check_selectors:
                try:
                    if ":contains" in selector:
                        # Handle text-based selectors
                        element = self.driver.execute_script("""
                            return Array.from(document.querySelectorAll('button')).find(el => 
                                el.textContent.toLowerCase().includes('check'));
                        """)
                        if element:
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info("Clicked check button via JavaScript")
                            check_clicked = True
                            break
                    else:
                        check_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        check_button.click()
                        logger.info(f"Clicked check button: {selector}")
                        check_clicked = True
                        break
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"Check button {selector} failed: {e}")
                    continue
            
            if check_clicked:
                time.sleep(2)  # Wait for answer validation
                logger.info("Check button clicked, waiting for result")
            else:
                logger.warning("No check button found, trying to proceed")
            
            # Step 3: Look for and click "Next Question" button
            next_selectors = [
                "button[data-test-id='next-question']",
                "button[data-test-id='next']",
                "button.next-question-button", 
                ".next-button",
                "button:contains('Next')",
                "[data-test-id*='next']"
            ]
            
            next_clicked = False
            for selector in next_selectors:
                try:
                    if ":contains" in selector:
                        element = self.driver.execute_script("""
                            return Array.from(document.querySelectorAll('button')).find(el => 
                                el.textContent.toLowerCase().includes('next'));
                        """)
                        if element:
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info("Clicked next button via JavaScript")
                            next_clicked = True
                            break
                    else:
                        next_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        next_button.click()
                        logger.info(f"Clicked next button: {selector}")
                        next_clicked = True
                        break
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"Next button {selector} failed: {e}")
                    continue
            
            if next_clicked:
                # Step 4: Wait for new question to load
                time.sleep(3)  # Give time for navigation
                logger.info("Next button clicked, waiting for new question")
                return self.wait_for_question_load()
            else:
                logger.warning("No next button found - trying page refresh fallback")
                return self.refresh_page()
            
        except Exception as e:
            logger.error(f"Error progressing to next question: {e}")
            # Fallback to page refresh
            try:
                logger.info("Attempting fallback refresh")
                return self.refresh_page()
            except Exception as refresh_error:
                logger.error(f"Fallback refresh also failed: {refresh_error}")
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