"""
Main orchestrator for fully automated Khan Academy question scraping.
This script coordinates mitmproxy interception with browser automation.
"""

import os
import sys
import subprocess
import threading
import time
import signal
import argparse
from datetime import datetime
import json

class KhanAcademyFullAutomation:
    def __init__(self, proxy_port=8080):
        self.proxy_port = proxy_port
        self.mitm_process = None
        self.browser_thread = None
        self.running = False
        self.questions_captured = 0
        self.save_directory = "khan_academy_json"
        
    def setup_directories(self):
        """Create necessary directories."""
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)
            print(f"[INFO] Created directory: {self.save_directory}")
    
    def start_mitmproxy(self):
        """Start mitmproxy with the automated capture script."""
        try:
            # Try to find mitmdump in virtual environment first
            venv_mitmdump = os.path.join(os.getcwd(), ".venv", "Scripts", "mitmdump.exe")
            if os.path.exists(venv_mitmdump):
                mitmdump_cmd = venv_mitmdump
            else:
                mitmdump_cmd = "mitmdump"
            
            cmd = [
                mitmdump_cmd,
                "-s", "capture_khan_json_automated.py",
                "-p", str(self.proxy_port),
                "--set", "confdir=~/.mitmproxy"
            ]
            
            print(f"[INFO] Starting mitmproxy on port {self.proxy_port}...")
            print(f"[INFO] Using: {mitmdump_cmd}")
            self.mitm_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Give mitmproxy time to start
            time.sleep(3)
            
            if self.mitm_process.poll() is None:
                print("[INFO] Mitmproxy started successfully")
                return True
            else:
                print("[ERROR] Mitmproxy failed to start")
                return False
                
        except Exception as e:
            print(f"[ERROR] Failed to start mitmproxy: {e}")
            return False
    
    def start_browser_automation(self, exercise_url):
        """Start browser automation in a separate thread."""
        def automation_worker():
            try:
                # Import here to avoid issues if selenium isn't installed
                from browser_automation import run_automation
                
                print("[INFO] Starting browser automation...")
                time.sleep(5)  # Wait for mitmproxy to be fully ready
                
                success = run_automation(exercise_url, self.proxy_port)
                if success:
                    print("[INFO] Browser automation completed successfully")
                else:
                    print("[WARNING] Browser automation encountered issues")
                    
            except ImportError:
                print("[WARNING] Selenium not available, running manual browser instructions")
                self.print_manual_instructions(exercise_url)
            except Exception as e:
                print(f"[ERROR] Browser automation failed: {e}")
                self.print_manual_instructions(exercise_url)
        
        self.browser_thread = threading.Thread(target=automation_worker, daemon=True)
        self.browser_thread.start()
    
    def print_manual_instructions(self, exercise_url):
        """Print manual instructions if automation fails."""
        print("\n" + "="*60)
        print("MANUAL BROWSER SETUP REQUIRED")
        print("="*60)
        print("Since browser automation is not available, please follow these steps:")
        print(f"1. Open Chrome with proxy settings:")
        print(f"   --proxy-server=http://127.0.0.1:{self.proxy_port}")
        print("2. Navigate to Khan Academy and login if needed")
        print(f"3. Go to this exercise: {exercise_url}")
        print("4. Start the exercise and let it load questions")
        print("5. Refresh the page periodically to load new question sets")
        print("6. The questions will be automatically captured")
        print("="*60 + "\n")
    
    def monitor_progress(self):
        """Monitor and report progress."""
        last_count = 0
        
        while self.running:
            try:
                # Count captured files
                if os.path.exists(self.save_directory):
                    current_count = len([f for f in os.listdir(self.save_directory) 
                                       if f.endswith('.json')])
                    
                    if current_count > last_count:
                        print(f"[PROGRESS] {current_count} questions captured (+{current_count - last_count})")
                        last_count = current_count
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"[ERROR] Progress monitoring error: {e}")
                time.sleep(10)
    
    def run_full_automation(self, exercise_url):
        """Run the complete automated scraping process."""
        print("Khan Academy Automated Question Scraper")
        print("="*50)
        print(f"Target exercise: {exercise_url}")
        print(f"Proxy port: {self.proxy_port}")
        print(f"Save directory: {self.save_directory}")
        print()
        
        # Setup
        self.setup_directories()
        
        # Start mitmproxy
        if not self.start_mitmproxy():
            return False
        
        self.running = True
        
        try:
            # Start browser automation
            self.start_browser_automation(exercise_url)
            
            # Start progress monitoring
            monitor_thread = threading.Thread(target=self.monitor_progress, daemon=True)
            monitor_thread.start()
            
            print("[INFO] Automation is running. Press Ctrl+C to stop.")
            print("[INFO] Questions will be automatically captured as they load.")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[INFO] Stopping automation...")
            self.running = False
            
        finally:
            self.cleanup()
        
        return True
    
    def cleanup(self):
        """Clean up all processes and threads."""
        print("[INFO] Cleaning up...")
        self.running = False
        
        if self.mitm_process:
            try:
                self.mitm_process.terminate()
                self.mitm_process.wait(timeout=5)
                print("[INFO] Mitmproxy stopped")
            except subprocess.TimeoutExpired:
                self.mitm_process.kill()
                print("[INFO] Mitmproxy killed")
            except Exception as e:
                print(f"[WARNING] Error stopping mitmproxy: {e}")
        
        # Final count
        if os.path.exists(self.save_directory):
            final_count = len([f for f in os.listdir(self.save_directory) 
                            if f.endswith('.json')])
            print(f"[FINAL] Total questions captured: {final_count}")
        
        print("[INFO] Cleanup complete")

def main():
    parser = argparse.ArgumentParser(description='Automated Khan Academy Question Scraper')
    parser.add_argument('exercise_url', nargs='?', help='Khan Academy exercise URL to scrape')
    parser.add_argument('--port', type=int, default=8080, help='Proxy port (default: 8080)')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    
    args = parser.parse_args()
    
    if args.check_deps:
        check_dependencies()
        return
    
    if not args.exercise_url:
        print("[ERROR] Please provide a Khan Academy exercise URL")
        parser.print_help()
        return
    
    # Validate URL
    if 'khanacademy.org' not in args.exercise_url:
        print("[ERROR] Please provide a valid Khan Academy exercise URL")
        return
    
    # Run automation
    automation = KhanAcademyFullAutomation(args.port)
    automation.run_full_automation(args.exercise_url)

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("Checking dependencies...")
    
    # Check mitmproxy
    try:
        result = subprocess.run(['mitmdump', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ mitmproxy is installed")
        else:
            print("✗ mitmproxy not found")
    except FileNotFoundError:
        print("✗ mitmproxy not found - install with: pip install mitmproxy")
    
    # Check selenium (optional)
    try:
        import selenium
        print("✓ selenium is available")
        
        # Check for Chrome
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            options = Options()
            options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)
            driver.quit()
            print("✓ Chrome WebDriver is working")
        except Exception:
            print("✗ Chrome WebDriver not working - may need chromedriver")
            
    except ImportError:
        print("⚠ selenium not found - will use manual browser mode")
        print("  Install with: pip install selenium")
    
    # Check aiohttp for async requests
    try:
        import aiohttp
        print("✓ aiohttp is available")
    except ImportError:
        print("⚠ aiohttp not found - install with: pip install aiohttp")
    
    print("\nDependency check complete.")

if __name__ == "__main__":
    main()