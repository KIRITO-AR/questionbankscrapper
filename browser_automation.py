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
        
        # Comprehensive SSL/Certificate handling for mitmproxy
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
        
        # Additional options for automation
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Optional: Run in headless mode (comment out for debugging)
        # chrome_options.add_argument('--headless')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set longer timeouts for better reliability
            self.driver.set_page_load_timeout(60)  # 60 seconds
            self.driver.implicitly_wait(15)  # 15 seconds
            
            self.wait = WebDriverWait(self.driver, 30)  # Increased to 30 seconds
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
        """Simulate minimal interaction to trigger question loading."""
        try:
            # Look for question elements to interact with
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
    
    def wait_for_questions_to_load(self, timeout=30):
        """Wait for questions to be loaded and captured."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if new questions have been loaded
            # This would be coordinated with the mitmproxy addon
            time.sleep(2)
            
            # Simulate some interaction to keep questions loading
            self.simulate_question_interaction()
        
        return True
    
    def automate_exercise_session(self, exercise_url, refresh_interval=60):
        """
        Run a full automated session for an exercise.
        
        Args:
            exercise_url: URL of the Khan Academy exercise
            refresh_interval: How often to refresh (seconds)
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
            
            # Wait for initial questions to load
            self.wait_for_questions_to_load()
            
            # Periodic refresh to get more questions
            refresh_count = 0
            while refresh_count < 5:  # Limit refreshes to avoid infinite loop
                logger.info(f"Refresh cycle {refresh_count + 1}/5")
                
                if not self.refresh_page():
                    break
                
                self.wait_for_questions_to_load()
                refresh_count += 1
                
                # Wait before next refresh
                time.sleep(refresh_interval)
            
            logger.info("Automated session completed")
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