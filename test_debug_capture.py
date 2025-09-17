"""
test_debug_capture.py
Test script to run debug capture and see what's happening.
"""

import subprocess
import time
import sys
import os
import signal

def test_debug_capture():
    """Run a quick test with debug capture to see what requests are being made."""
    
    print("=" * 60)
    print("Debug Capture Test")
    print("=" * 60)
    print("This will start mitmproxy with debug logging and open Khan Academy")
    print("Press Ctrl+C to stop the test")
    print()
    
    # Start mitmproxy with debug script
    mitm_command = [
        "mitmdump",
        "-s", "debug_capture.py",
        "--listen-port", "8080",
        "--set", "block_global=false"
    ]
    
    mitm_process = None
    
    try:
        print("[1/3] Starting mitmproxy with debug capture...")
        mitm_process = subprocess.Popen(
            mitm_command,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        print(f"Mitmproxy started (PID: {mitm_process.pid})")
        print("Waiting for initialization...")
        time.sleep(5)
        
        print("\n[2/3] Starting browser automation...")
        print("The browser will open and try to load Khan Academy")
        print("Watch the console output for debug information...")
        print()
        
        # Import and run a simple automation
        from automate_exercise import run_automation
        
        # Run just a few questions for testing
        run_automation(max_questions=3)
        
        print("\n[3/3] Test completed!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        if mitm_process:
            print("Stopping mitmproxy...")
            try:
                if os.name == 'nt':
                    mitm_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    mitm_process.terminate()
                mitm_process.wait(timeout=5)
            except:
                mitm_process.kill()
        
        # Show debug log
        if os.path.exists("debug_capture.log"):
            print("\n" + "=" * 60)
            print("Debug Log Summary:")
            print("=" * 60)
            with open("debug_capture.log", 'r') as f:
                content = f.read()
                if content:
                    print(content[-1000:])  # Show last 1000 chars
                else:
                    print("Debug log is empty")

if __name__ == "__main__":
    test_debug_capture()