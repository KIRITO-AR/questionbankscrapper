"""
Quick Test Script for Simple Khan Academy Capture
"""

import subprocess
import time
import os

def test_simple_capture():
    print("=== TESTING SIMPLE KHAN ACADEMY CAPTURE ===")
    print()
    
    # Kill any existing processes
    try:
        subprocess.run(["taskkill", "/f", "/im", "mitmdump.exe"], capture_output=True)
        subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True)
    except:
        pass
    
    print("1. Starting simple capture proxy...")
    
    # Start mitmproxy with simple capture
    proxy_cmd = [
        "D:/collage/questionbankscrapper/.venv/Scripts/mitmdump.exe",
        "-s", "capture_khan_simple.py",
        "--listen-port", "8084",
        "-q"  # Quiet mode
    ]
    
    proxy_process = subprocess.Popen(proxy_cmd)
    time.sleep(3)
    
    print("2. Starting Chrome with proxy...")
    
    # Start Chrome with proxy
    chrome_cmd = [
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "--proxy-server=http://127.0.0.1:8084",
        "--ignore-certificate-errors",
        "--disable-web-security",
        "--new-window",
        "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:linear-equations-1/x2f8bb11595b61c86:intro-to-linear-equations/e/linear_equations_1"
    ]
    
    chrome_process = subprocess.Popen(chrome_cmd)
    
    print("3. Chrome opened to Khan Academy exercise")
    print("4. Navigate around, answer questions, and check for captures")
    print("5. Press Enter to stop the test...")
    
    input()
    
    # Cleanup
    try:
        proxy_process.terminate()
        chrome_process.terminate()
    except:
        pass
    
    # Check results
    json_dir = "khan_academy_json"
    if os.path.exists(json_dir):
        files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        print(f"\nFinal count: {len(files)} JSON files")
        
        # Show any new files
        import datetime
        recent_files = []
        for f in files:
            filepath = os.path.join(json_dir, f)
            mtime = os.path.getmtime(filepath)
            if time.time() - mtime < 300:  # Last 5 minutes
                recent_files.append(f)
        
        if recent_files:
            print(f"New files captured: {recent_files}")
        else:
            print("No new files captured")

if __name__ == "__main__":
    test_simple_capture()