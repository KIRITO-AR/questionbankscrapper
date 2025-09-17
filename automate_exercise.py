"""
automate_exercise.py
Simple exercise automation script based on the technical plan requirements.
This script provides automated browser control for Khan Academy exercises.
Enhanced with improved timeout handling and network resilience.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

# --- Configuration ---
PROXY_PORT = "8080"
EXERCISE_URL = "https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:add-and-subtract-within-20/x3184e0ec:add-within-20/e/add-within-20-visually"  # Example URL

# Enhanced timeout settings for network resilience
PAGE_LOAD_TIMEOUT = 90  # Increased from default
IMPLICIT_WAIT = 20      # Increased from default
EXPLICIT_WAIT = 45      # Increased for slow network connections
ELEMENT_WAIT = 30       # For individual elements
POPUP_WAIT = 3          # Short wait for popups

def run_automation(exercise_url=None, max_questions=20):
    """
    Main automation function that controls the browser and answers questions.
    
    Args:
        exercise_url (str): The Khan Academy exercise URL to scrape
        max_questions (int): Maximum number of questions to answer
    """
    if exercise_url is None:
        exercise_url = EXERCISE_URL
    
    # Configure Chrome with proxy settings
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--proxy-server=http://127.0.0.1:{PROXY_PORT}')
    
    # Essential SSL/Certificate handling for mitmproxy
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--allow-insecure-localhost')
    
    # Performance optimizations to reduce timeouts
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')  # Speed up loading
    # Do NOT disable JavaScript; Khan Academy SPA requires JS to render
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Network optimization
    chrome_options.add_argument('--aggressive-cache-discard')
    chrome_options.add_argument('--disable-background-networking')
    chrome_options.add_argument('--disable-sync')
    
    # Initialize WebDriver with enhanced timeouts
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Set enhanced timeouts
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(IMPLICIT_WAIT)
    
    try:
        # Navigate to exercise page with retry logic
        print(f"Navigating to exercise page: {exercise_url}")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Navigation attempt {attempt + 1}/{max_retries}")
                driver.get(exercise_url)
                print("Page load initiated, waiting for content...")
                
                # Wait for basic page structure to ensure successful load
                WebDriverWait(driver, EXPLICIT_WAIT).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.TAG_NAME, "body")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id]"))
                    )
                )
                print("Page loaded successfully!")
                break
                
            except TimeoutException:
                print(f"Page load timeout on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    print("Failed to load page after all retries")
                    return
                time.sleep(5)  # Wait before retry
        
        print("Starting automation...")

        # Try to click Start/Practice once after load so GraphQL batch prefetch triggers
        try:
            start_buttons = [
                'button[data-test-id="start-button"]',
                'button[data-test-id="practice-button"]',
                'a[data-test-id="start-practice"]',
            ]
            clicked = False
            for sel in start_buttons:
                try:
                    btn = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                    )
                    btn.click()
                    print(f"Clicked start button: {sel}")
                    time.sleep(2)
                    clicked = True
                    break
                except TimeoutException:
                    continue
            if not clicked:
                # Fallback to text-based find via JS
                btn = driver.execute_script(
                    "return Array.from(document.querySelectorAll('button,a')).find(el => /start|practice/i.test(el.textContent));"
                )
                if btn:
                    driver.execute_script("arguments[0].click();", btn)
                    print("Clicked start via text match")
                    time.sleep(2)
        except Exception:
            pass

        # Wait longer for GraphQL calls to complete after starting practice
        print("Waiting for GraphQL calls to complete...")
        time.sleep(8)

        # If current page is a curriculum/section page, iterate all exercise links
        try:
            links = driver.execute_script(
                "return Array.from(document.querySelectorAll('a[href*="/e/"]')).map(a => a.href);"
            )
            # Deduplicate while preserving order
            seen = set()
            exercise_links = []
            for href in links:
                if href and href not in seen:
                    seen.add(href)
                    exercise_links.append(href)
            if exercise_links:
                print(f"Found {len(exercise_links)} exercise links on this page. Beginning batch scrape...")
                scraped = 0
                for href in exercise_links:
                    try:
                        print(f"Opening exercise: {href}")
                        driver.get(href)
                        # Wait for page body
                        WebDriverWait(driver, EXPLICIT_WAIT).until(
                            EC.presence_of_element_located((By.TAG_NAME, 'body'))
                        )
                        time.sleep(2)
                        # Click Start/Practice if present to trigger practice task
                        started = False
                        for sel in [
                            'button[data-test-id="start-button"]',
                            'button[data-test-id="practice-button"]',
                            'a[data-test-id="start-practice"]',
                        ]:
                            try:
                                btn = WebDriverWait(driver, 6).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                                )
                                btn.click(); started = True; print("Started exercise")
                                break
                            except TimeoutException:
                                continue
                        if not started:
                            # Text-based fallback
                            btn = driver.execute_script(
                                "return Array.from(document.querySelectorAll('button,a')).find(el => /start|practice/i.test(el.textContent));"
                            )
                            if btn:
                                driver.execute_script("arguments[0].click();", btn)
                                started = True
                        # Allow mitm addon to capture manifest and download items
                        print("Waiting for GraphQL calls to complete...")
                        time.sleep(8)
                        scraped += 1
                        if scraped >= max_questions:
                            break
                    except Exception as e:
                        print(f"Error opening {href}: {e}")
                print("Batch scrape over exercises complete. Returning.")
                return
        except Exception:
            pass
        
        # Loop to answer a set number of questions
        for i in range(max_questions):
            print(f"--- Answering Question {i+1} ---")
            
            # Handle potential pop-ups before each question
            try:
                # Look for a common modal pop-up and a continue button
                continue_button = WebDriverWait(driver, POPUP_WAIT).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test-id="skill-mastery-modal-continue-button"]'))
                )
                print("Found and clicked a skill mastery pop-up.")
                continue_button.click()
                time.sleep(2)
            except TimeoutException:
                pass  # No pop-up found, continue as normal
            
            # 1. Wait for interactable elements instead of relying on a specific question container
            try:
                WebDriverWait(driver, ELEMENT_WAIT).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="radio"]')),
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]')),
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]')),
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test-id="check-answer-button"]'))
                    )
                )
            except TimeoutException:
                # Try pressing Next/Continue to advance if current screen not ready
                advanced = False
                for sel in [
                    'button[data-test-id="next-question-button"]',
                    'button[data-test-id*="next"]',
                    'button[data-test-id*="continue"]'
                ]:
                    try:
                        btn = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                        btn.click(); time.sleep(2)
                        advanced = True
                        break
                    except TimeoutException:
                        continue
                if not advanced:
                    print("No interactable elements found; skipping this iteration")
                    continue
            
            # 2. Answer the question (simple logic)
            # Try to find a radio button first
            try:
                first_radio_button = driver.find_element(By.CSS_SELECTOR, 'input[type="radio"]')
                first_radio_button.click()
                print("Selected a radio button.")
            except:
                # If no radio button, try to find a numeric input
                try:
                    numeric_input = driver.find_element(By.CSS_SELECTOR, 'input[type="text"]')
                    numeric_input.clear()
                    numeric_input.send_keys("1")
                    print("Entered '1' into a numeric input.")
                except:
                    # Try other input types
                    try:
                        # Try number input
                        number_input = driver.find_element(By.CSS_SELECTOR, 'input[type="number"]')
                        number_input.clear()
                        number_input.send_keys("1")
                        print("Entered '1' into a number input.")
                    except:
                        # Try any clickable option
                        try:
                            clickable_option = driver.find_element(By.CSS_SELECTOR, '[data-test-id*="choice"], .choice, button[data-test-id*="option"]')
                            clickable_option.click()
                            print("Clicked a choice option.")
                        except:
                            print("Could not find a standard answer input.")
                            pass
            
            # 3. Click the "Check" button with enhanced timeout
            try:
                check_button = WebDriverWait(driver, ELEMENT_WAIT).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test-id="check-answer-button"]'))
                )
                check_button.click()
                print("Clicked 'Check'.")
                time.sleep(3)
            except TimeoutException:
                # Try alternative check button selectors (avoid unsupported CSS pseudo)
                try:
                    # Search by text with JS
                    js_btn = driver.execute_script(
                        "return Array.from(document.querySelectorAll('button')).find(el => /check|submit/i.test(el.textContent));"
                    )
                    if js_btn:
                        driver.execute_script("arguments[0].click();", js_btn)
                        print("Clicked alternative 'Check' via text.")
                        time.sleep(3)
                    else:
                        print("Could not find check button after extended wait.")
                except Exception:
                    print("Could not find check button after extended wait.")
            
            # 4. Click the "Next question" button with enhanced timeout
            try:
                next_button = WebDriverWait(driver, ELEMENT_WAIT).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test-id="next-question-button"]'))
                )
                next_button.click()
                print("Clicked 'Next question'.")
            except TimeoutException:
                # Try alternative next button via text search
                try:
                    js_next = driver.execute_script(
                        "return Array.from(document.querySelectorAll('button')).find(el => /next|continue/i.test(el.textContent));"
                    )
                    if js_next:
                        driver.execute_script("arguments[0].click();", js_next)
                        print("Clicked alternative 'Next' via text.")
                    else:
                        print("Could not find next button after extended wait, may have completed exercise.")
                        break
                except Exception:
                    print("Could not find next button after extended wait, may have completed exercise.")
                    break
            
            time.sleep(5)  # Increased wait for next question to start loading
    
    except TimeoutException as e:
        print(f"Timeout error occurred during automation: {e}")
        print("This may be due to slow network connection or proxy issues.")
    except WebDriverException as e:
        print(f"WebDriver error occurred during automation: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during automation: {e}")
    finally:
        print("Automation finished.")
        try:
            driver.quit()
        except:
            pass  # Ignore errors during cleanup

if __name__ == '__main__':
    # This allows running the script directly for testing
    run_automation()