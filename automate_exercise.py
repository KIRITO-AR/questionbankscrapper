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

def log_progress(message):
    """Log progress with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def find_all_exercise_links(driver):
    """Find all exercise links on the current page automatically."""
    try:
        # JavaScript to find all exercise links
        exercise_links = driver.execute_script("""
            var links = [];
            // Find direct exercise links (containing /e/)
            document.querySelectorAll('a[href*="/e/"]').forEach(function(link) {
                if (link.href && link.href.includes('/e/') && link.href.includes('khanacademy.org')) {
                    links.push(link.href);
                }
            });
            
            // Find practice links
            document.querySelectorAll('a[href*="practice"]').forEach(function(link) {
                if (link.href && link.href.includes('practice') && link.href.includes('khanacademy.org')) {
                    links.push(link.href);
                }
            });
            
            // Remove duplicates
            return [...new Set(links)];
        """)
        
        log_progress(f"Found {len(exercise_links)} exercise links on current page")
        return exercise_links
        
    except Exception as e:
        log_progress(f"Error finding exercise links: {e}")
        return []

def find_section_links(driver):
    """Find section/topic links for deeper navigation."""
    try:
        section_links = driver.execute_script("""
            var links = [];
            // Find topic/section links
            document.querySelectorAll('a[href*="/math/"], a[href*="/science/"]').forEach(function(link) {
                if (link.href && !link.href.includes('/e/') && !link.href.includes('#') && link.href.includes('khanacademy.org')) {
                    links.push(link.href);
                }
            });
            return [...new Set(links)];
        """)
        
        log_progress(f"Found {len(section_links)} section links on current page")
        return section_links[:20]  # Limit to prevent infinite crawling
        
    except Exception as e:
        log_progress(f"Error finding section links: {e}")
        return []

def autonomous_answer_question(driver):
    """Autonomously answer the current question without user interaction."""
    answered = False
    
    # Try radio buttons first
    try:
        radio_buttons = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"], [role="radio"]')
        if radio_buttons and radio_buttons[0].is_displayed():
            driver.execute_script("arguments[0].click();", radio_buttons[0])
            log_progress("✓ Selected radio button answer")
            answered = True
    except Exception as e:
        log_progress(f"Radio button error: {e}")
    
    # Try text/number inputs
    if not answered:
        try:
            input_selectors = [
                'input[type="text"]',
                'input[type="number"]', 
                'input[aria-label*="answer"]',
                'input[placeholder*="answer"]',
                '.perseus-input input',
                '.simple-text-input input',
                'input[data-test-id*="input"]'
            ]
            
            for selector in input_selectors:
                try:
                    inputs = driver.find_elements(By.CSS_SELECTOR, selector)
                    for input_found in inputs:
                        if input_found.is_displayed() and input_found.is_enabled():
                            input_found.clear()
                            # Use simple answers that are often correct
                            import random
                            answers = ["1", "2", "5", "10", "0", "x", "y"]
                            input_found.send_keys(random.choice(answers))
                            log_progress(f"✓ Entered answer in input field: {selector}")
                            answered = True
                            break
                    if answered:
                        break
                except:
                    continue
        except Exception as e:
            log_progress(f"Input field error: {e}")
    
    # Try clickable choices
    if not answered:
        try:
            choice_selectors = [
                '[data-test-id*="choice"]',
                '.choice',
                'button[data-test-id*="option"]',
                '[role="button"][aria-label*="choice"]',
                '.multiple-choice li button',
                '.perseus-widget-radio .perseus-widget-radio-option',
                '[data-test-id="radio-choice"]'
            ]
            
            for selector in choice_selectors:
                try:
                    choices = driver.find_elements(By.CSS_SELECTOR, selector)
                    if choices and choices[0].is_displayed() and choices[0].is_enabled():
                        driver.execute_script("arguments[0].click();", choices[0])
                        log_progress(f"✓ Clicked choice option: {selector}")
                        answered = True
                        break
                except:
                    continue
        except Exception as e:
            log_progress(f"Choice option error: {e}")
    
    return answered

def autonomous_submit_answer(driver):
    """Submit answer autonomously."""
    try:
        # Try multiple check button selectors
        check_selectors = [
            'button[data-test-id="check-answer-button"]',
            'button[data-test-id="submit-answer-button"]'
        ]
        
        for selector in check_selectors:
            try:
                check_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                check_button.click()
                log_progress("✓ Submitted answer")
                time.sleep(3)
                return True
            except TimeoutException:
                continue
        
        # JavaScript fallback
        button = driver.execute_script("""
            return Array.from(document.querySelectorAll('button')).find(el => 
                /check|submit/i.test(el.textContent)
            );
        """)
        if button:
            driver.execute_script("arguments[0].click();", button)
            log_progress("✓ Submitted answer via JavaScript")
            time.sleep(3)
            return True
            
    except Exception as e:
        log_progress(f"Error submitting answer: {e}")
    
    return False

def autonomous_next_question(driver):
    """Move to next question autonomously."""
    try:
        # Try multiple next button selectors
        next_selectors = [
            'button[data-test-id="next-question-button"]',
            'button[data-test-id*="next"]',
            'button[data-test-id*="continue"]'
        ]
        
        for selector in next_selectors:
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                next_button.click()
                log_progress("✓ Moved to next question")
                time.sleep(5)
                return True
            except TimeoutException:
                continue
        
        # JavaScript fallback
        button = driver.execute_script("""
            return Array.from(document.querySelectorAll('button')).find(el => 
                /next|continue/i.test(el.textContent)
            );
        """)
        if button:
            driver.execute_script("arguments[0].click();", button)
            log_progress("✓ Moved to next question via JavaScript")
            time.sleep(5)
            return True
            
    except Exception as e:
        log_progress(f"Error moving to next question: {e}")
    
    return False

def run_automation(exercise_url=None, max_questions=1000):
    """
    Main automation function that autonomously scrapes ALL questions.
    
    Args:
        exercise_url (str): The Khan Academy exercise URL to scrape
        max_questions (int): Maximum number of questions to answer (increased default)
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
        log_progress("🚀 Starting AUTONOMOUS Khan Academy scraping...")
        
        # Navigate to exercise page with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                log_progress(f"Navigation attempt {attempt + 1}/{max_retries} to: {exercise_url}")
                driver.get(exercise_url)
                
                # Wait for basic page structure
                WebDriverWait(driver, EXPLICIT_WAIT).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.TAG_NAME, "body")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id]"))
                    )
                )
                log_progress("✓ Page loaded successfully!")
                break
                
            except TimeoutException:
                log_progress(f"⚠ Page load timeout on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    log_progress("❌ Failed to load page after all retries")
                    return
                time.sleep(5)
        
        # Start comprehensive autonomous scraping
        total_questions_processed = 0
        visited_exercises = set()
        
        # Check if this is a section page with multiple exercises
        time.sleep(3)
        exercise_links = find_all_exercise_links(driver)
        section_links = find_section_links(driver)
        
        # If we found exercise links, scrape them all
        if exercise_links:
            log_progress(f"📚 Found {len(exercise_links)} exercises to scrape autonomously")
            
            all_exercises_to_scrape = exercise_links.copy()
            
            # Add exercises from section links too
            for section_url in section_links[:10]:  # Limit section depth
                try:
                    log_progress(f"🔍 Exploring section: {section_url}")
                    driver.get(section_url)
                    time.sleep(3)
                    more_exercises = find_all_exercise_links(driver)
                    for ex in more_exercises:
                        if ex not in all_exercises_to_scrape:
                            all_exercises_to_scrape.append(ex)
                except:
                    continue
            
            log_progress(f"📝 Total exercises to scrape: {len(all_exercises_to_scrape)}")
            
            # Scrape each exercise autonomously
            for i, exercise_url in enumerate(all_exercises_to_scrape):
                if exercise_url in visited_exercises:
                    continue
                    
                if total_questions_processed >= max_questions:
                    log_progress(f"🎯 Reached maximum questions limit: {max_questions}")
                    break
                
                visited_exercises.add(exercise_url)
                
                try:
                    log_progress(f"📖 [{i+1}/{len(all_exercises_to_scrape)}] Scraping exercise: {exercise_url}")
                    driver.get(exercise_url)
                    time.sleep(3)
                    
                    # Try to start the exercise
                    started = False
                    start_selectors = [
                        'button[data-test-id="start-button"]',
                        'button[data-test-id="practice-button"]',
                        'a[data-test-id="start-practice"]',
                    ]
                    
                    for sel in start_selectors:
                        try:
                            btn = WebDriverWait(driver, 8).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                            )
                            btn.click()
                            log_progress(f"✓ Started exercise using: {sel}")
                            time.sleep(3)
                            started = True
                            break
                        except TimeoutException:
                            continue
                    
                    if not started:
                        # JavaScript fallback
                        btn = driver.execute_script("""
                            return Array.from(document.querySelectorAll('button,a')).find(el => 
                                /start|practice/i.test(el.textContent)
                            );
                        """)
                        if btn:
                            driver.execute_script("arguments[0].click();", btn)
                            log_progress("✓ Started exercise via JavaScript")
                            time.sleep(3)
                    
                    # Wait for GraphQL calls to complete
                    log_progress("⏳ Waiting for question data to load...")
                    time.sleep(8)
                    
                    # Enhanced: Navigate through the exercise more thoroughly to trigger more requests
                    log_progress("🔄 Enhanced passive capture - navigating through exercise thoroughly")
                    
                    # Try to load a few questions to trigger more GraphQL calls
                    for warmup in range(3):
                        try:
                            # Wait for question to load
                            time.sleep(2)
                            
                            # Try to answer quickly to move to next question
                            if autonomous_answer_question(driver):
                                if autonomous_submit_answer(driver):
                                    if autonomous_next_question(driver):
                                        log_progress(f"🔥 Warmup question {warmup+1} - triggered more GraphQL calls")
                                    else:
                                        break
                                else:
                                    break
                            else:
                                # Even if we can't answer, try to advance
                                autonomous_next_question(driver)
                        except:
                            break
                    
                    # Reset back to start if possible or just continue with main loop
                    log_progress("✅ Enhanced capture warmup complete, starting main question loop")
                    
                    # Autonomous question answering loop for this exercise
                    exercise_questions = 0
                    consecutive_failures = 0
                    max_questions_per_exercise = 50  # Limit per exercise
                    
                    for q in range(max_questions_per_exercise):
                        if total_questions_processed >= max_questions:
                            break
                            
                        log_progress(f"🔢 Question {q+1} in current exercise...")
                        
                        # Handle pop-ups
                        try:
                            continue_button = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test-id="skill-mastery-modal-continue-button"]'))
                            )
                            continue_button.click()
                            log_progress("✓ Dismissed skill mastery pop-up")
                            time.sleep(2)
                        except TimeoutException:
                            pass
                        
                        # Wait for question to load
                        try:
                            WebDriverWait(driver, ELEMENT_WAIT).until(
                                EC.any_of(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="radio"]')),
                                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]')),
                                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]')),
                                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id*="choice"]')),
                                    EC.presence_of_element_located((By.CSS_SELECTOR, '.perseus-widget-container')),
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test-id="check-answer-button"]'))
                                )
                            )
                        except TimeoutException:
                            # Try to advance if stuck
                            if not autonomous_next_question(driver):
                                consecutive_failures += 1
                                if consecutive_failures >= 3:
                                    log_progress("⚠ Too many failures, moving to next exercise")
                                    break
                            continue
                        
                        # Answer the question autonomously
                        if autonomous_answer_question(driver):
                            # Submit the answer
                            if autonomous_submit_answer(driver):
                                # Move to next question
                                if autonomous_next_question(driver):
                                    exercise_questions += 1
                                    total_questions_processed += 1
                                    consecutive_failures = 0
                                    log_progress(f"✅ Processed question {exercise_questions} (Total: {total_questions_processed})")
                                else:
                                    log_progress("✅ Exercise complete - no more questions")
                                    break
                            else:
                                consecutive_failures += 1
                        else:
                            log_progress("❌ Could not answer question")
                            consecutive_failures += 1
                        
                        # Break if too many consecutive failures
                        if consecutive_failures >= 5:
                            log_progress("⚠ Too many consecutive failures, moving to next exercise")
                            break
                        
                        time.sleep(2)  # Brief pause between questions
                    
                    log_progress(f"✅ Completed exercise: {exercise_questions} questions processed")
                    time.sleep(3)  # Brief pause between exercises
                    
                except Exception as e:
                    log_progress(f"❌ Error in exercise {exercise_url}: {e}")
                    continue
            
            log_progress(f"🎉 AUTONOMOUS SCRAPING COMPLETE!")
            log_progress(f"📊 Total exercises visited: {len(visited_exercises)}")
            log_progress(f"📊 Total questions processed: {total_questions_processed}")
            
        else:
            # Single exercise mode - scrape this one exercise thoroughly
            log_progress("📖 Single exercise mode - scraping current exercise thoroughly")
            
            # Try to start the exercise
            started = False
            start_selectors = [
                'button[data-test-id="start-button"]',
                'button[data-test-id="practice-button"]',
                'a[data-test-id="start-practice"]',
            ]
            
            for sel in start_selectors:
                try:
                    btn = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                    )
                    btn.click()
                    log_progress(f"✓ Started exercise using: {sel}")
                    time.sleep(3)
                    started = True
                    break
                except TimeoutException:
                    continue
            
            if not started:
                btn = driver.execute_script("""
                    return Array.from(document.querySelectorAll('button,a')).find(el => 
                        /start|practice/i.test(el.textContent)
                    );
                """)
                if btn:
                    driver.execute_script("arguments[0].click();", btn)
                    log_progress("✓ Started exercise via JavaScript")
                    time.sleep(3)
            
            # Wait for GraphQL calls
            log_progress("⏳ Waiting for question data to load...")
            time.sleep(8)
            
            # Answer questions autonomously
            for i in range(max_questions):
                log_progress(f"🔢 Autonomous Question {i+1}/{max_questions}")
                
                # Handle pop-ups
                try:
                    continue_button = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test-id="skill-mastery-modal-continue-button"]'))
                    )
                    continue_button.click()
                    time.sleep(2)
                except TimeoutException:
                    pass
                
                # Wait for question to load
                try:
                    WebDriverWait(driver, ELEMENT_WAIT).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="radio"]')),
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]')),
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="number"]')),
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id*="choice"]')),
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.perseus-widget-container')),
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test-id="check-answer-button"]'))
                        )
                    )
                except TimeoutException:
                    if not autonomous_next_question(driver):
                        log_progress("❌ Could not advance - may be end of exercise")
                        break
                    continue
                
                # Process question autonomously
                if autonomous_answer_question(driver):
                    if autonomous_submit_answer(driver):
                        if not autonomous_next_question(driver):
                            log_progress("✅ Exercise complete - no more questions")
                            break
                        total_questions_processed += 1
                    else:
                        log_progress("❌ Could not submit answer")
                else:
                    log_progress("❌ Could not answer question")
                
                time.sleep(2)
            
            log_progress(f"✅ Single exercise complete: {total_questions_processed} questions processed")
    
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