#!/usr/bin/env python3
"""
Test script to verify that the Khan Academy scraper is configured for active mode.
"""

import sys
import os

# Import the capture module
try:
    from capture_khan_json import ENABLE_ACTIVE_SCRAPING, KhanAcademyCapture
    print("✓ Successfully imported capture_khan_json module")
except ImportError as e:
    print(f"✗ Failed to import module: {e}")
    sys.exit(1)

def test_active_mode():
    """Test that active scraping is enabled."""
    print(f"Active scraping enabled: {ENABLE_ACTIVE_SCRAPING}")
    
    if ENABLE_ACTIVE_SCRAPING:
        print("✓ Active scraping is ENABLED")
    else:
        print("✗ Active scraping is DISABLED")
        return False
    
    # Test that the capture class can be instantiated
    try:
        capture = KhanAcademyCapture()
        print("✓ KhanAcademyCapture class instantiated successfully")
        
        # Check that base_headers is initialized as None (will be set from real requests)
        if capture.base_headers is None:
            print("✓ Headers are properly initialized as None (will be set from intercepted requests)")
        else:
            print(f"- Headers pre-initialized: {list(capture.base_headers.keys())}")
            
        return True
    except Exception as e:
        print(f"✗ Failed to instantiate KhanAcademyCapture: {e}")
        return False

def main():
    print("Khan Academy Scraper - Active Mode Test")
    print("=" * 50)
    
    success = test_active_mode()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All tests passed! The scraper is configured for ACTIVE mode.")
        print("\nTo use:")
        print("1. Start the mitmproxy with: mitmdump -s capture_khan_json.py")
        print("2. Configure your browser to use the proxy")
        print("3. Browse Khan Academy exercises")
        print("4. The scraper will actively fetch questions when it detects practice tasks")
    else:
        print("✗ Tests failed! Please check the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()