"""
Test script for detailed debug capture
"""
import subprocess
import time
import threading
import signal
import os
import sys

def run_detailed_debug_capture():
    """Run the detailed debug capture script"""
    print("Starting detailed debug mitmproxy...")
    process = subprocess.Popen([
        sys.executable, "-m", "mitmproxy.tools.mitmdump", 
        "-s", "detailed_debug_capture.py",
        "--listen-port", "8080"
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    return process

def run_browser_automation():
    """Run browser automation to trigger requests"""
    time.sleep(3)  # Wait for mitmproxy to start
    
    print("Starting browser automation...")
    try:
        result = subprocess.run([
            sys.executable, "automate_exercise.py"
        ], capture_output=True, text=True, timeout=120)
        
        print("Browser automation output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("Browser automation timed out")
    except Exception as e:
        print(f"Error running browser automation: {e}")

def main():
    # Start mitmproxy
    mitm_process = run_detailed_debug_capture()
    
    try:
        # Start browser automation in a separate thread
        browser_thread = threading.Thread(target=run_browser_automation)
        browser_thread.start()
        
        # Wait for browser thread to complete
        browser_thread.join()
        
        print("\nDetailed debug test completed!")
        
    finally:
        # Stop mitmproxy
        print("Stopping detailed debug mitmproxy...")
        mitm_process.terminate()
        
        try:
            mitm_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            mitm_process.kill()
            mitm_process.wait()
    
    # Show any new files created
    if os.path.exists("khan_academy_json"):
        json_files = [f for f in os.listdir("khan_academy_json") if f.startswith("detailed_debug_")]
        if json_files:
            print(f"\nNew debug files created: {json_files}")
        else:
            print("\nNo new debug files were created")
    
    # Show debug log if it exists
    if os.path.exists("detailed_debug_capture.log"):
        print("\nDetailed debug log file created")

if __name__ == "__main__":
    main()