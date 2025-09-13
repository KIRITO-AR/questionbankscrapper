import json
import os
from datetime import datetime

# Test script to analyze why questions aren't being captured
def analyze_capture_issue():
    print("=== KHAN ACADEMY CAPTURE ANALYSIS ===")
    print()
    
    # Check current state
    json_dir = "khan_academy_json"
    if os.path.exists(json_dir):
        files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        print(f"Current JSON files: {len(files)}")
        for f in files:
            filepath = os.path.join(json_dir, f)
            mtime = os.path.getmtime(filepath)
            timestamp = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {f} - Modified: {timestamp}")
    else:
        print("No khan_academy_json directory found")
    
    print()
    print("=== POTENTIAL ISSUES ===")
    print("1. Browser is not triggering the correct GraphQL requests")
    print("2. Khan Academy changed their API endpoints")
    print("3. mitmproxy is not intercepting the requests properly")
    print("4. Questions are being served from cache instead of API")
    print()
    
    print("=== DEBUGGING STEPS ===")
    print("1. Check if mitmproxy is seeing ANY Khan Academy requests")
    print("2. Verify the GraphQL endpoint URLs are still correct")
    print("3. Test with manual question navigation")
    print("4. Check browser developer tools for network activity")

if __name__ == "__main__":
    analyze_capture_issue()