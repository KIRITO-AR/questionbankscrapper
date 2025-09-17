"""
main.py
Master runner script that orchestrates mitmproxy and Selenium automation.
Based on the technical plan requirements for Part 3.
Enhanced with network resilience and timeout handling.
"""

import subprocess
import time
import sys
import os
import signal
from automate_exercise import run_automation

# --- Configuration ---
MITM_SCRIPT = "capture_khan_json.py"
PROXY_PORT = 8080
DEFAULT_EXERCISE_URL = "https://www.khanacademy.org/math/cc-2nd-grade-math/x3184e0ec:add-and-subtract-within-20/x3184e0ec:add-within-20/e/add-within-20-visually"
DEFAULT_MAX_QUESTIONS = 50  # Reduced for initial testing

# Network resilience settings
MITM_STARTUP_TIMEOUT = 15  # Time to wait for mitmproxy startup
MAX_RETRIES = 3  # Maximum retries for failed operations

def _stream_output(prefix, pipe):
    """Continuously read a subprocess pipe and echo to stdout with a prefix."""
    try:
        for line in iter(pipe.readline, ''):
            if not line:
                break
            try:
                sys.stdout.write(f"{prefix} {line}")
            except Exception:
                # Fallback write without formatting
                try:
                    print(line.rstrip())
                except Exception:
                    pass
    finally:
        try:
            pipe.close()
        except Exception:
            pass

def start_mitmproxy():
    """Start mitmdump as a background process with enhanced error handling."""
    mitm_command = [
        "mitmdump",
        "-s", MITM_SCRIPT,
        "--listen-port", str(PROXY_PORT),
        "--set", "block_global=false",  # Allows traffic to pass through
        "--set", "connection_strategy=lazy",  # Optimize connections
        "--set", "stream_large_bodies=50m",  # Stream large responses
        "--set", "flow_detail=0"  # Reduce logging overhead
    ]
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Starting mitmproxy (attempt {attempt + 1}/{MAX_RETRIES})...")
            
            mitm_process = subprocess.Popen(
                mitm_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Wait for mitmproxy to start and verify it's working
            print("Waiting for mitmproxy to initialize...")
            time.sleep(MITM_STARTUP_TIMEOUT)
            
            if mitm_process.poll() is None:  # Process is still running
                print(f"Mitmproxy started successfully (PID: {mitm_process.pid})")
                # Start streaming threads so addon prints are visible in terminal
                import threading
                threading.Thread(target=_stream_output, args=("[mitmproxy]", mitm_process.stdout), daemon=True).start()
                threading.Thread(target=_stream_output, args=("[mitmproxy-err]", mitm_process.stderr), daemon=True).start()
                return mitm_process
            else:
                print(f"Mitmproxy failed to start (attempt {attempt + 1})")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2)  # Wait before retry
                    
        except FileNotFoundError:
            print("[ERROR] mitmdump not found. Please install mitmproxy: pip install mitmproxy")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to start mitmproxy (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
    
    print("[ERROR] Failed to start mitmproxy after all retries")
    return None

def test_network_connection():
    """Test basic network connectivity before starting scraper."""
    import requests
    
    test_urls = [
        "https://www.google.com",
        "https://www.khanacademy.org"
    ]
    
    print("Testing network connectivity...")
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✓ {url} - OK")
            else:
                print(f"⚠ {url} - HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"✗ {url} - Timeout (slow connection)")
            return False
        except requests.exceptions.RequestException as e:
            print(f"✗ {url} - Error: {e}")
            return False
    
    print("Network connectivity test passed!")
    return True

def cleanup_process(process):
    """Safely terminate a process."""
    if process and process.poll() is None:
        try:
            if os.name == 'nt':  # Windows
                process.send_signal(signal.CTRL_BREAK_EVENT)
            else:  # Unix/Linux/macOS
                process.terminate()
            
            # Wait for graceful termination
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        except Exception as e:
            print(f"[WARNING] Error during cleanup: {e}")
    """Safely terminate a process."""
    if process and process.poll() is None:
        try:
            if os.name == 'nt':  # Windows
                process.send_signal(signal.CTRL_BREAK_EVENT)
            else:  # Unix/Linux/macOS
                process.terminate()
            
            # Wait for graceful termination
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        except Exception as e:
            print(f"[WARNING] Error during cleanup: {e}")

def main(exercise_url=None, max_questions=None):
    """
    Main function that orchestrates the entire scraping process.
    
    Args:
        exercise_url (str): The Khan Academy exercise URL to scrape
        max_questions (int): Maximum number of questions to answer
    """
    if exercise_url is None:
        exercise_url = DEFAULT_EXERCISE_URL
    if max_questions is None:
        max_questions = DEFAULT_MAX_QUESTIONS
    
    print("=" * 60)
    print("Khan Academy Automated Question Scraper")
    print("=" * 60)
    print(f"Exercise URL: {exercise_url}")
    print(f"Max questions: {max_questions}")
    print(f"Proxy port: {PROXY_PORT}")
    print(f"MITM script: {MITM_SCRIPT}")
    print()
    
    mitm_process = None
    
    try:
        # Step 0: Test network connectivity first
        print("[0/4] Testing network connectivity...")
        if not test_network_connection():
            print("[ERROR] Network connectivity test failed. Check your internet connection.")
            print("Possible solutions:")
            print("- Check internet connection")
            print("- Disable VPN if active")
            print("- Check firewall settings")
            return False
        
        # Step 1: Start mitmproxy
        print("[1/4] Starting mitmproxy...")
        mitm_process = start_mitmproxy()
        if not mitm_process:
            print("[ERROR] Failed to start mitmproxy. Exiting.")
            return False
        
        print("[SUCCESS] mitmproxy started successfully")
        
        # Step 2: Run browser automation
        print("[2/4] Starting browser automation...")
        try:
            run_automation(exercise_url, max_questions)
            print("[SUCCESS] Browser automation completed")
        except Exception as e:
            print(f"[ERROR] Browser automation failed: {e}")
            print("This may be due to:")
            print("- Network timeout issues")
            print("- Slow proxy response")
            print("- Website changes")
            return False
        
        # Step 3: Cleanup
        print("[3/4] Cleaning up...")
        
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user. Cleaning up...")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        print("Check the error details above for troubleshooting.")
    finally:
        # Ensure mitmproxy is terminated when the script is done or fails
        if mitm_process:
            print("Terminating mitmproxy...")
            cleanup_process(mitm_process)
        print("Cleanup complete.")
        
    print("\nScraping session finished!")
    return True

if __name__ == "__main__":
    # Parse command line arguments
    exercise_url = None
    max_questions = None
    
    if len(sys.argv) > 1:
        exercise_url = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            max_questions = int(sys.argv[2])
        except ValueError:
            print("[WARNING] Invalid max_questions value. Using default.")
    
    print("Usage: python main.py [exercise_url] [max_questions]")
    print("Example: python main.py https://www.khanacademy.org/math/... 50")
    print()
    
    success = main(exercise_url, max_questions)
    sys.exit(0 if success else 1)