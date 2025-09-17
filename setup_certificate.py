#!/usr/bin/env python3
"""
Certificate Setup Helper for Khan Academy Scraper

This script helps set up the mitmproxy certificate for proper HTTPS interception.
"""

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

def main():
    print("=" * 60)
    print("Khan Academy Scraper - Certificate Setup Helper")
    print("=" * 60)
    print()
    
    print("To fix the 403 errors and TLS handshake failures, you need to:")
    print("1. Trust the mitmproxy certificate in your browser")
    print("2. Make sure you're logged into Khan Academy")
    print()
    
    # Check if mitmproxy is running
    try:
        result = subprocess.run(['mitmdump', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ mitmproxy is installed")
        else:
            print("✗ mitmproxy not found. Please install it first:")
            print("  pip install mitmproxy")
            return
    except Exception:
        print("✗ mitmproxy not found. Please install it first:")
        print("  pip install mitmproxy")
        return
    
    print()
    print("STEP 1: Trust the mitmproxy certificate")
    print("-" * 40)
    print("1. Start the scraper: python main.py")
    print("2. Open your browser and go to: http://mitm.it")
    print("3. Download the Windows certificate")
    print("4. Install it in 'Trusted Root Certification Authorities'")
    print("5. Restart your browser")
    print()
    
    print("STEP 2: Login to Khan Academy")
    print("-" * 40)
    print("1. After starting the scraper, login to Khan Academy in the browser")
    print("2. Keep the browser window open during scraping")
    print()
    
    print("STEP 3: Test the scraper")
    print("-" * 40)
    print("1. Navigate to a Khan Academy section (e.g., Math > Class 1)")
    print("2. Click on an exercise")
    print("3. Watch the terminal for [MITM] and [SAVE] messages")
    print()
    
    # Try to open mitm.it in browser
    try:
        print("Opening http://mitm.it in your browser...")
        webbrowser.open("http://mitm.it")
        print("✓ Browser opened")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print("Please manually open: http://mitm.it")
    
    print()
    print("After completing these steps, run: python main.py")
    print("You should see [SAVE] messages when questions are downloaded!")

if __name__ == "__main__":
    main()
