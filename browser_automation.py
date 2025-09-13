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
        chrome_options.add_argument('--no-proxy-server')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Speed up loading
        chrome_options.add_argument('--disable-javascript')  # We don't need JS for our purpose
        
        # Additional options for automation
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Optional: Run in headless mode (comment out for debugging)
        # chrome_options.add_argument('--headless')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set more aggressive timeouts for faster operation
            self.driver.set_page_load_timeout(30)  # Reduced from 60
            self.driver.implicitly_wait(10)  # Reduced from 15
            
            self.wait = WebDriverWait(self.driver, 20)  # Reduced from 30
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
            
            # Wait for page to load with better error handling
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(5)  # Additional wait for full page load and JS execution
                logger.info("Page loaded successfully")
            except Exception as e:
                logger.warning(f"Page load wait failed, but continuing: {e}")
            
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

    def attempt_to_answer_question(self):
        """
        Attempt to answer the current question to trigger progression.
        """
        try:
            # Try to fill in simple numeric answers
            numeric_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='number']")
            for input_elem in numeric_inputs:
                try:
                    # Put a simple answer to trigger progression
                    input_elem.clear()
                    input_elem.send_keys("1")
                    time.sleep(0.5)
                except Exception:
                    continue
            
            # Try to select first radio button option
            radio_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            if radio_buttons:
                try:
                    self.driver.execute_script("arguments[0].click();", radio_buttons[0])
                    time.sleep(0.5)
                except Exception:
                    pass
            
            # Try to submit the answer
            submit_selectors = [
                "button[data-test-id='check-answer']",
                "button:contains('Check')",
                "button:contains('Submit')",
                ".btn-primary"
            ]
            
            for selector in submit_selectors:
                try:
                    if ":contains" in selector:
                        element = self.driver.execute_script(f"""
                            return Array.from(document.querySelectorAll('button')).find(el => 
                                el.textContent.toLowerCase().includes('{selector.split("'")[1].lower()}'));
                        """)
                        if element:
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info("Submitted answer to progress")
                            time.sleep(2)
                            return True
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element.is_enabled():
                            element.click()
                            logger.info(f"Submitted answer: {selector}")
                            time.sleep(2)
                            return True
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Could not answer question: {e}")
        
        return False
    
    def wait_for_questions_to_load(self, timeout=30):
        """Wait for questions to be loaded and captured."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Interact with the page to trigger question loading
            self.simulate_question_interaction()
            
            # Small wait between interactions
            time.sleep(3)
            
            # Try to progress to next question periodically
            if (time.time() - start_time) % 10 < 3:  # Every 10 seconds
                self.attempt_to_progress_to_next_question()
        
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
    
    def automate_exercise_session(self, exercise_url, max_questions=1000, refresh_interval=120):
        """
        Run a comprehensive automated session for an exercise.
        
        Args:
            exercise_url: URL of the Khan Academy exercise
            max_questions: Maximum number of questions to capture
            refresh_interval: How often to refresh if no progress (seconds)
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
            
            # Main loop for question capture
            total_cycles = 0
            max_cycles = max_questions // 5  # Assume ~5 questions per cycle
            last_refresh_time = time.time()
            
            while total_cycles < max_cycles:
                cycle_start = time.time()
                logger.info(f"Question capture cycle {total_cycles + 1}/{max_cycles}")
                
                # Try to progress through questions
                progress_made = False
                for attempt in range(10):  # Try to progress through up to 10 questions per cycle
                    # Wait and interact with current question
                    self.wait_for_questions_to_load(timeout=15)
                    
                    # Try to progress to next question
                    if self.attempt_to_progress_to_next_question():
                        progress_made = True
                        time.sleep(2)  # Brief pause between questions
                    else:
                        # If we can't progress, try answering the current question
                        if self.attempt_to_answer_question():
                            time.sleep(2)
                            if self.attempt_to_progress_to_next_question():
                                progress_made = True
                        break
                
                # If no progress made or it's been too long, refresh
                current_time = time.time()
                if not progress_made or (current_time - last_refresh_time) > refresh_interval:
                    logger.info("Refreshing page to get fresh questions...")
                    if not self.refresh_page():
                        logger.error("Failed to refresh page")
                        break
                    last_refresh_time = current_time
                
                total_cycles += 1
                
                # Brief pause between cycles
                time.sleep(3)
            
            logger.info(f"Automated session completed after {total_cycles} cycles")
            return True
            
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