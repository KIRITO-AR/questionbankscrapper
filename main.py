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
MITM_STARTUP_TIMEOUT = 25  # Increased timeout for active scraping initialization
MAX_RETRIES = 3  # Maximum retries for failed operations
ACTIVE_SCRAPING_WAIT = 5  # Additional wait time for active batch fetching

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
        "--set", "flow_detail=0",  # Reduce logging overhead
        "--set", "keep_host_header=true",  # Better for active requests
        "--set", "http2=false"  # Disable HTTP/2 for better compatibility
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
                print("Active scraping mode enabled - will batch-fetch questions automatically")
                # Start streaming threads so addon prints are visible in terminal
                import threading
                threading.Thread(target=_stream_output, args=("[mitmproxy]", mitm_process.stdout), daemon=True).start()
                threading.Thread(target=_stream_output, args=("[mitmproxy-err]", mitm_process.stderr), daemon=True).start()
                
                # Give extra time for active scraping initialization
                print(f"Allowing {ACTIVE_SCRAPING_WAIT}s for active scraping initialization...")
                time.sleep(ACTIVE_SCRAPING_WAIT)
                
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
    print("Khan Academy ACTIVE Question Scraper")
    print("=" * 60)
    print(f"Exercise URL: {exercise_url}")
    print(f"Max questions: {max_questions}")
    print(f"Proxy port: {PROXY_PORT}")
    print(f"MITM script: {MITM_SCRIPT}")
    print(f"Mode: ACTIVE BATCH SCRAPING (auto-fetches all questions)")
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
        print("[2/4] Starting browser automation with ACTIVE question fetching...")
        try:
            run_automation(exercise_url, max_questions)
            print("[SUCCESS] Browser automation completed")
            print("[INFO] Check the khan_academy_json/ folder for actively fetched questions!")
        except Exception as e:
            print(f"[ERROR] Browser automation failed: {e}")
            print("This may be due to:")
            print("- Network timeout issues")
            print("- Slow proxy response")
            print("- Website changes")
            print("- Khan Academy blocking active requests (will fallback to passive)")
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
        
    # Show summary of captured questions
    print("\n" + "=" * 60)
    print("SCRAPING SESSION SUMMARY")
    print("=" * 60)
    
    # Count JSON files in the output directory
    json_dir = "khan_academy_json"
    if os.path.exists(json_dir):
        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        print(f"Total questions captured: {len(json_files)}")
        print(f"Output directory: {json_dir}")
        if json_files:
            print("Recent captures:")
            # Show last 5 files
            for file in sorted(json_files)[-5:]:
                print(f"  - {file}")
    else:
        print("No questions captured (output directory not found)")
        
    print("=" * 60)
    print("Scraping session finished!")
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