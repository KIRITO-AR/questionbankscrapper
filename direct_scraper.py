#!/usr/bin/env python3
"""
Direct Khan Academy Question Scraper
Bypasses proxy issues by directly extracting data from page content
"""

import json
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import re
from datetime import datetime

# Configuration
SAVE_DIRECTORY = "khan_academy_json"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectKhanAcademyScraper:
    def __init__(self):
        """Initialize the direct scraper"""
        self.driver = None
        self.wait = None
        self.questions_saved = 0
        
        if not os.path.exists(SAVE_DIRECTORY):
            os.makedirs(SAVE_DIRECTORY)
    
    def setup_browser(self):
        """Setup Chrome browser without proxy"""
        options = Options()
        
        # No proxy - direct connection
        # Just basic automation settings
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Performance settings
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 30)
            logger.info("Browser setup complete - direct connection (no proxy)")
            return True
        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            return False
    
    def extract_perseus_data(self):
        """Extract Perseus JSON data directly from the page"""
        try:
            # Wait a bit for JavaScript to load
            time.sleep(2)
            
            # Method 1: Check for Perseus global variables
            perseus_data = self.driver.execute_script("""
                // Look for Perseus data in global scope
                if (typeof Perseus !== 'undefined' && Perseus.itemData) {
                    return Perseus.itemData;
                }
                
                if (typeof window.Perseus !== 'undefined' && window.Perseus.itemData) {
                    return window.Perseus.itemData;
                }
                
                // Look for exercise data in KA global
                if (typeof KA !== 'undefined' && KA.exerciseData) {
                    return KA.exerciseData;
                }
                
                if (typeof window.KA !== 'undefined' && window.KA.exerciseData) {
                    return window.KA.exerciseData;
                }
                
                // Look for React props or state
                var reactElements = document.querySelectorAll('[data-reactroot], [data-react-class]');
                for (var i = 0; i < reactElements.length; i++) {
                    var elem = reactElements[i];
                    for (var key in elem) {
                        if (key.startsWith('__reactInternalInstance') || key.startsWith('_reactInternalFiber')) {
                            var reactData = elem[key];
                            if (reactData && reactData.memoizedProps && reactData.memoizedProps.itemData) {
                                return reactData.memoizedProps.itemData;
                            }
                        }
                    }
                }
                
                return null;
            """)
            
            if perseus_data:
                logger.info("✅ Found Perseus data via JavaScript globals")
                return perseus_data
            
            # Method 2: Extract from script tags
            try:
                script_elements = self.driver.find_elements(By.TAG_NAME, "script")
                for script in script_elements:
                    script_content = script.get_attribute("innerHTML")
                    if script_content and ("Perseus" in script_content or "itemData" in script_content):
                        # Look for various patterns
                        patterns = [
                            r'Perseus\.itemData\s*=\s*({.*?});',
                            r'"itemData"\s*:\s*({.*?})',
                            r'"perseus_item"\s*:\s*({.*?})',
                            r'itemData:\s*({.*?})',
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, script_content, re.DOTALL)
                            if matches:
                                try:
                                    data = json.loads(matches[0])
                                    logger.info("✅ Found Perseus data in script tags")
                                    return data
                                except:
                                    continue
            except Exception as e:
                logger.debug(f"Script extraction failed: {e}")
            
            # Method 3: Look for data attributes
            try:
                data_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "[data-perseus-item], [data-exercise], [data-item], [data-perseus-json]")
                
                for element in data_elements:
                    for attr in ['data-perseus-item', 'data-exercise', 'data-item', 'data-perseus-json']:
                        data = element.get_attribute(attr)
                        if data:
                            try:
                                parsed_data = json.loads(data)
                                logger.info(f"✅ Found Perseus data in {attr}")
                                return parsed_data
                            except:
                                continue
            except Exception as e:
                logger.debug(f"Data attribute extraction failed: {e}")
            
            # Method 4: Look for exercise containers and extract any JSON
            try:
                exercise_containers = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".exercise, .problem, .question, .perseus-widget, [class*='exercise'], [class*='question']")
                
                for container in exercise_containers:
                    # Check if container has data attributes
                    for attr in container.get_property('attributes'):
                        attr_name = attr['name']
                        if 'data' in attr_name:
                            attr_value = container.get_attribute(attr_name)
                            if attr_value and ('{' in attr_value):
                                try:
                                    data = json.loads(attr_value)
                                    logger.info(f"✅ Found Perseus data in {attr_name}")
                                    return data
                                except:
                                    continue
            except Exception as e:
                logger.debug(f"Container extraction failed: {e}")
            
            # Method 5: Try to extract any JSON from page that looks like Perseus data
            try:
                page_source = self.driver.page_source
                
                # Look for JSON objects that contain exercise-related keywords
                json_pattern = r'{[^{}]*(?:"(?:question|content|problem|exercise|perseus|item)"[^{}]*)*}'
                potential_json = re.findall(json_pattern, page_source)
                
                for json_str in potential_json:
                    try:
                        data = json.loads(json_str)
                        # Check if it looks like Perseus data
                        if any(key in str(data).lower() for key in ['question', 'content', 'problem', 'exercise', 'perseus']):
                            logger.info("✅ Found Perseus-like data in page source")
                            return data
                    except:
                        continue
            except Exception as e:
                logger.debug(f"Page source extraction failed: {e}")
            
            logger.warning("❌ No Perseus data found using any method")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting Perseus data: {e}")
            return None
    
    def save_question_data(self, data, question_id=None):
        """Save question data to file"""
        if not data:
            return False
        
        try:
            # Generate question ID if not provided
            if not question_id:
                question_id = f"direct_{int(time.time())}_{self.questions_saved:04d}"
            
            filename = f"{question_id}.json"
            filepath = os.path.join(SAVE_DIRECTORY, filename)
            
            # Add metadata
            enriched_data = {
                "capture_method": "direct_extraction",
                "timestamp": datetime.now().isoformat(),
                "question_id": question_id,
                "data": data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(enriched_data, f, indent=2, ensure_ascii=False)
            
            self.questions_saved += 1
            logger.info(f"✅ Saved question data: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save question data: {e}")
            return False
    
    def navigate_and_extract(self, url):
        """Navigate to URL and extract question data"""
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(5)  # Wait for JavaScript to load
            
            # Try to find and click on practice/exercise buttons
            try:
                practice_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "button[data-test-id*='practice'], a[href*='practice'], .practice-button, [data-testid*='practice']")
                
                if practice_buttons:
                    logger.info("Found practice button, clicking...")
                    practice_buttons[0].click()
                    time.sleep(3)
            except:
                pass
            
            # Extract current question data
            data = self.extract_perseus_data()
            if data:
                self.save_question_data(data)
                return True
            else:
                logger.warning("No Perseus data found on this page")
                return False
                
        except Exception as e:
            logger.error(f"Failed to navigate and extract: {e}")
            return False
    
    def auto_navigate_exercises(self, base_url, max_questions=10):
        """Automatically navigate through exercises and extract questions"""
        logger.info(f"Starting auto-navigation from: {base_url}")
        
        try:
            # Start with the base URL
            if not self.navigate_and_extract(base_url):
                logger.warning("No data found on initial page")
            
            questions_found = 0
            
            # Look for more exercises or practice questions
            while questions_found < max_questions:
                try:
                    # Look for "Next" or "Continue" buttons with better selectors
                    next_buttons = self.driver.find_elements(By.XPATH, 
                        "//button[contains(text(), 'Next') or contains(text(), 'Continue') or contains(text(), 'Check') or contains(@data-testid, 'next')]")
                    
                    if not next_buttons:
                        # Try CSS selectors
                        next_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                            "button[data-testid*='next'], button[data-testid*='continue'], .next-button, .continue-button")
                    
                    if not next_buttons:
                        # Try common Khan Academy button patterns
                        next_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                            "button[class*='next'], button[class*='continue'], button[class*='check']")
                    
                    if next_buttons:
                        logger.info("Clicking next question...")
                        next_buttons[0].click()
                        time.sleep(3)
                        
                        # Extract data from new question
                        data = self.extract_perseus_data()
                        if data:
                            self.save_question_data(data)
                            questions_found += 1
                        
                    else:
                        logger.info("No more next buttons found, ending auto-navigation")
                        break
                        
                except Exception as e:
                    logger.error(f"Error during auto-navigation: {e}")
                    break
            
            logger.info(f"Auto-navigation complete. Found {questions_found} additional questions.")
            
        except Exception as e:
            logger.error(f"Auto-navigation failed: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        logger.info(f"Scraping complete. Total questions saved: {self.questions_saved}")

def main():
    import sys
    
    # Default URL if none provided
    default_url = "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:foundation/x2f8bb11595b61c86:intro-variables/a/intro-to-variables"
    
    url = sys.argv[1] if len(sys.argv) > 1 else default_url
    max_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    print("🔍 Direct Khan Academy Question Scraper")
    print("=" * 50)
    print(f"Target URL: {url}")
    print(f"Max questions: {max_questions}")
    print(f"Save directory: {SAVE_DIRECTORY}")
    print("=" * 50)
    
    scraper = DirectKhanAcademyScraper()
    
    try:
        if scraper.setup_browser():
            scraper.auto_navigate_exercises(url, max_questions)
        else:
            print("❌ Failed to setup browser")
            
    except KeyboardInterrupt:
        print("\\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()