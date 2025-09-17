"""
Enhanced Khan Academy Question Scraper - Complete Solution
This script integrates the improved mitmproxy addon with browser automation
for unlimited question downloading without manual intervention.

Now includes autonomous scraping capabilities with active batch processing.
"""

import subprocess
import threading
import time
import os
import sys
import logging
import asyncio
from browser_automation import KhanAcademyBrowserAutomation

# Try to import autonomous scraper
try:
    from autonomous_scraper import AutonomousKhanScraper, run_autonomous_scraper
    AUTONOMOUS_AVAILABLE = True
except ImportError:
    AUTONOMOUS_AVAILABLE = False
    print("[WARNING] Autonomous scraper not available, using legacy mode")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedKhanScraper:
    def __init__(self, proxy_port=8080):
        self.proxy_port = proxy_port
        self.mitmproxy_process = None
        self.browser_automation = None
        self.autonomous_mode = AUTONOMOUS_AVAILABLE
        
    def run_autonomous_session(self, exercise_url, max_questions=1000):
        """Run the enhanced autonomous scraping session."""
        if not self.autonomous_mode:
            logger.warning("Autonomous mode not available, falling back to legacy mode")
            return self.run_legacy_session(exercise_url, max_questions)
        
        try:
            logger.info("Starting autonomous scraping session")
            logger.info(f"Exercise URL: {exercise_url}")
            logger.info(f"Target questions: {max_questions}")
            logger.info(f"Proxy port: {self.proxy_port}")
            
            # Start mitmproxy first
            if not self.start_mitmproxy():
                logger.error("Failed to start mitmproxy")
                return False
            
            # Run autonomous scraper
            try:
                result = asyncio.run(run_autonomous_scraper(exercise_url, max_questions, self.proxy_port))
                logger.info(f"Autonomous session completed with result: {result}")
                return result
            except Exception as e:
                logger.error(f"Autonomous session failed: {e}")
                return False
                
        finally:
            self.cleanup()
    
    def run_legacy_session(self, exercise_url, max_questions=1000):
        """Run the legacy scraping session for backward compatibility."""
        try:
            logger.info("Starting legacy scraping session")
            
            # Start mitmproxy
            if not self.start_mitmproxy():
                logger.error("Failed to start mitmproxy")
                return False
            
            # Start browser automation
            self.start_browser_automation(exercise_url, max_questions)
            
            # Wait for completion
            logger.info("Scraping session started. Press Ctrl+C to stop.")
            
            try:
                while True:
                    time.sleep(10)
                    # Could add progress monitoring here
            except KeyboardInterrupt:
                logger.info("Stopping scraper...")
                return True
                
        except Exception as e:
            logger.error(f"Legacy session failed: {e}")
            return False
        finally:
            self.cleanup()
        
    def start_mitmproxy(self):
        """Start mitmproxy with the enhanced addon."""
        try:
            addon_path = os.path.join(os.getcwd(), "capture_khan_json.py")
            
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
        print("Usage: python enhanced_khan_scraper.py <exercise_url> [max_questions] [mode]")
        print()
        print("Arguments:")
        print("  exercise_url     Khan Academy exercise URL (required)")
        print("  max_questions    Maximum questions to capture (default: 1000)")
        print("  mode            Scraping mode: 'autonomous' or 'legacy' (default: autonomous)")
        print()
        print("Modes:")
        print("  autonomous      Full automation with active batch scraping (recommended)")
        print("  legacy          Traditional browser automation only")
        print()
        print("Example:")
        print("  python enhanced_khan_scraper.py https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-functions-equations/x2f8bb11595b61c86:quadratic-formula/e/quadratic_formula 1000 autonomous")
        print()
        print("Requirements:")
        print("  - mitmproxy must be installed and accessible")
        print("  - Chrome browser must be installed")
        print("  - All Python dependencies from requirements.txt")
        print()
        if AUTONOMOUS_AVAILABLE:
            print("✓ Autonomous scraping available")
        else:
            print("⚠ Autonomous scraping not available - will use legacy mode")
        print()
        return
    
    exercise_url = sys.argv[1]
    max_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    mode = sys.argv[3].lower() if len(sys.argv) > 3 else 'autonomous'
    
    # Enhanced URL validation
    if not validate_exercise_url(exercise_url):
        print("❌ Error: Invalid Khan Academy exercise URL")
        print()
        print("Please provide a valid Khan Academy exercise URL that:")
        print("  - Starts with https://www.khanacademy.org/")
        print("  - Contains '/e/' for exercises")
        print("  - Is not a placeholder (no '...' or incomplete paths)")
        print()
        print("Example valid URL:")
        print("  https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-functions-equations/x2f8bb11595b61c86:quadratic-formula/e/quadratic_formula")
        print()
        sys.exit(1)
    
    # Validate mode
    if mode not in ['autonomous', 'legacy']:
        print("Error: Mode must be 'autonomous' or 'legacy'")
        sys.exit(1)
    
    # Create output directory
    output_dir = "khan_academy_json"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

def validate_exercise_url(url):
    """Validate that the URL is a proper Khan Academy exercise URL."""
    try:
        # Check basic URL format
        if not url.startswith("https://www.khanacademy.org/"):
            return False
        
        # Check for placeholder URLs
        if "..." in url:
            return False
        
        # Check for exercise path
        if "/e/" not in url:
            return False
        
        # Check minimum URL length (real URLs are quite long)
        if len(url) < 80:
            return False
        
        # Additional checks for common placeholder patterns
        placeholder_patterns = [
            "exercise_url",
            "example",
            "sample",
            "placeholder"
        ]
        
        for pattern in placeholder_patterns:
            if pattern in url.lower():
                return False
        
        return True
        
    except Exception:
        return False
    os.makedirs("khan_academy_json", exist_ok=True)
    
    # Run the scraper
    scraper = EnhancedKhanScraper()
    
    print("\n" + "=" * 60)
    print("ENHANCED KHAN ACADEMY SCRAPER")
    print("=" * 60)
    print(f"Exercise URL: {exercise_url}")
    print(f"Target questions: {max_questions}")
    print(f"Mode: {mode}")
    if AUTONOMOUS_AVAILABLE and mode == 'autonomous':
        print("Features: UI Automation + Active Batch Scraping + Full Automation")
    else:
        print("Features: UI Automation + Passive Capture")
    print("=" * 60)
    print()
    
    try:
        if mode == 'autonomous' and AUTONOMOUS_AVAILABLE:
            success = scraper.run_autonomous_session(exercise_url, max_questions)
        else:
            if mode == 'autonomous':
                print("Autonomous mode requested but not available, using legacy mode")
            success = scraper.run_legacy_session(exercise_url, max_questions)
        
        print("\n" + "=" * 60)
        if success:
            print("SCRAPING COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            final_count = len([f for f in os.listdir("khan_academy_json") if f.endswith('.json')])
            print(f"Total questions captured: {final_count}")
            print(f"Files saved in: {os.path.abspath('khan_academy_json')}")
            
            # Show efficiency stats for autonomous mode
            if mode == 'autonomous' and AUTONOMOUS_AVAILABLE:
                print("\nAutonomous scraping benefits:")
                print("✓ Eliminated page refreshes with smart UI interactions")
                print("✓ Active batch downloading of pre-loaded questions")
                print("✓ Fully automated question answering and progression")
                print("✓ Comprehensive error recovery and session management")
        else:
            print("SCRAPING FAILED OR INCOMPLETE")
            print("=" * 60)
            print("Please check the logs above for error details.")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nGraceful shutdown requested...")
        print("Cleaning up resources...")
        scraper.cleanup()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()