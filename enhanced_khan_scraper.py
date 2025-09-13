"""
Enhanced Khan Academy Question Scraper - Complete Solution
This script integrates the improved mitmproxy addon with browser automation
for unlimited question downloading without manual intervention.
"""

import subprocess
import threading
import time
import os
import sys
import logging
from browser_automation import KhanAcademyBrowserAutomation

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedKhanScraper:
    def __init__(self, proxy_port=8080):
        self.proxy_port = proxy_port
        self.mitmproxy_process = None
        self.browser_automation = None
        
    def start_mitmproxy(self):
        """Start mitmproxy with the enhanced addon."""
        try:
            addon_path = os.path.join(os.getcwd(), "capture_khan_json_automated.py")
            
            if not os.path.exists(addon_path):
                logger.error(f"Addon file not found: {addon_path}")
                return False
            
            # Try different mitmproxy command variations
            mitmproxy_commands = [
                ["mitmdump"],
                [sys.executable, "-m", "mitmproxy.tools.mitmdump"],
                [os.path.join(os.path.dirname(sys.executable), "Scripts", "mitmdump.exe")],
                [os.path.join(os.path.dirname(sys.executable), "mitmdump.exe")]
            ]
            
            for cmd_base in mitmproxy_commands:
                try:
                    cmd = cmd_base + [
                        "-s", addon_path,
                        "--set", f"listen_port={self.proxy_port}",
                        "--set", "confdir=~/.mitmproxy",
                        "--set", "web_open_browser=false"
                    ]
                    
                    logger.info(f"Trying mitmproxy command: {' '.join(cmd)}")
                    
                    self.mitmproxy_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    
                    # Give mitmproxy time to start
                    time.sleep(5)
                    
                    if self.mitmproxy_process.poll() is None:
                        logger.info("Mitmproxy started successfully")
                        return True
                    else:
                        stdout, stderr = self.mitmproxy_process.communicate(timeout=5)
                        logger.warning(f"Command failed. stdout: {stdout}, stderr: {stderr}")
                        continue
                        
                except FileNotFoundError:
                    logger.debug(f"Command not found: {' '.join(cmd_base)}")
                    continue
                except Exception as e:
                    logger.debug(f"Command failed: {e}")
                    continue
            
            logger.error("Failed to start mitmproxy with any available command")
            logger.error("Please ensure mitmproxy is installed: pip install mitmproxy")
            return False
                
        except Exception as e:
            logger.error(f"Failed to start mitmproxy: {e}")
            return False
    
    def start_browser_automation(self, exercise_url, max_questions=1000):
        """Start browser automation in a separate thread."""
        def run_automation():
            try:
                self.browser_automation = KhanAcademyBrowserAutomation(self.proxy_port)
                success = self.browser_automation.automate_exercise_session(
                    exercise_url, 
                    max_questions=max_questions,
                    refresh_interval=90  # Refresh every 90 seconds if no progress
                )
                if success:
                    logger.info("Browser automation completed successfully")
                else:
                    logger.error("Browser automation failed")
            except Exception as e:
                logger.error(f"Browser automation error: {e}")
        
        automation_thread = threading.Thread(target=run_automation, daemon=True)
        automation_thread.start()
        return automation_thread
    
    def run_comprehensive_scrape(self, exercise_url, max_questions=1000, timeout_minutes=60):
        """
        Run a comprehensive scraping session.
        
        Args:
            exercise_url: Khan Academy exercise URL
            max_questions: Maximum number of questions to capture
            timeout_minutes: Maximum time to run (minutes)
        """
        logger.info("=" * 60)
        logger.info("ENHANCED KHAN ACADEMY QUESTION SCRAPER")
        logger.info("=" * 60)
        logger.info(f"Target URL: {exercise_url}")
        logger.info(f"Max Questions: {max_questions}")
        logger.info(f"Timeout: {timeout_minutes} minutes")
        logger.info("=" * 60)
        
        try:
            # Step 1: Start mitmproxy
            logger.info("Step 1: Starting mitmproxy addon...")
            if not self.start_mitmproxy():
                logger.error("Failed to start mitmproxy. Please check your installation.")
                return False
            
            # Step 2: Start browser automation
            logger.info("Step 2: Starting browser automation...")
            automation_thread = self.start_browser_automation(exercise_url, max_questions)
            
            # Step 3: Monitor progress
            logger.info("Step 3: Monitoring progress...")
            start_time = time.time()
            timeout_seconds = timeout_minutes * 60
            
            while time.time() - start_time < timeout_seconds:
                # Check if we've reached our goal
                json_files = [f for f in os.listdir("khan_academy_json") if f.endswith('.json')]
                current_count = len(json_files)
                
                logger.info(f"Progress: {current_count}/{max_questions} questions captured")
                
                if current_count >= max_questions:
                    logger.info(f"Target reached! Captured {current_count} questions.")
                    break
                
                # Wait before next check
                time.sleep(30)  # Check every 30 seconds
            
            else:
                logger.info(f"Timeout reached after {timeout_minutes} minutes")
            
            # Final status
            final_count = len([f for f in os.listdir("khan_academy_json") if f.endswith('.json')])
            logger.info(f"Session completed. Total questions captured: {final_count}")
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
            return False
        except Exception as e:
            logger.error(f"Scraping session failed: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up resources...")
        
        # Stop browser automation
        if self.browser_automation:
            try:
                self.browser_automation.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up browser: {e}")
        
        # Stop mitmproxy
        if self.mitmproxy_process:
            try:
                self.mitmproxy_process.terminate()
                try:
                    self.mitmproxy_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.mitmproxy_process.kill()
                logger.info("Mitmproxy stopped")
            except Exception as e:
                logger.error(f"Error stopping mitmproxy: {e}")

def main():
    """Main entry point."""
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h', 'help']:
        print("Enhanced Khan Academy Question Scraper")
        print("=" * 50)
        print()
        print("Usage: python enhanced_khan_scraper.py <exercise_url> [max_questions] [timeout_minutes]")
        print()
        print("Arguments:")
        print("  exercise_url     Khan Academy exercise URL (required)")
        print("  max_questions    Maximum questions to capture (default: 1000)")
        print("  timeout_minutes  Maximum time to run in minutes (default: 60)")
        print()
        print("Example:")
        print("  python enhanced_khan_scraper.py https://www.khanacademy.org/math/algebra/... 1000 60")
        print()
        print("Requirements:")
        print("  - mitmproxy must be installed and accessible")
        print("  - Chrome browser must be installed")
        print("  - All Python dependencies from requirements.txt")
        print()
        return
    
    exercise_url = sys.argv[1]
    max_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    timeout_minutes = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    
    # Validate URL
    if not exercise_url.startswith("http"):
        print("Error: Please provide a valid HTTP/HTTPS URL")
        sys.exit(1)
    
    # Create output directory
    os.makedirs("khan_academy_json", exist_ok=True)
    
    # Run the scraper
    scraper = EnhancedKhanScraper()
    success = scraper.run_comprehensive_scrape(exercise_url, max_questions, timeout_minutes)
    
    if success:
        print("\n" + "=" * 60)
        print("SCRAPING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        final_count = len([f for f in os.listdir("khan_academy_json") if f.endswith('.json')])
        print(f"Total questions captured: {final_count}")
        print(f"Files saved in: {os.path.abspath('khan_academy_json')}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("SCRAPING FAILED OR INCOMPLETE")
        print("=" * 60)
        print("Please check the logs above for error details.")
        print("=" * 60)

if __name__ == "__main__":
    main()