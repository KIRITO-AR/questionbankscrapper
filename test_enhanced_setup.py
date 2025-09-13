"""
Test script for the Enhanced Khan Academy Question Scraper
This script validates that all components are working properly.
"""

import os
import sys
import time
import subprocess
import threading
import json

def test_mitmproxy_addon():
    """Test that the mitmproxy addon can be loaded."""
    print("Testing mitmproxy addon...")
    
    addon_path = "capture_khan_json_automated.py"
    if not os.path.exists(addon_path):
        print("❌ Addon file not found!")
        return False
    
    try:
        # Try to import the addon as a module
        import importlib.util
        spec = importlib.util.spec_from_file_location("addon", addon_path)
        addon_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(addon_module)
        
        print("✅ Addon loads successfully")
        
        # Check if it has the required class
        if hasattr(addon_module, 'KhanAcademyAutomatedCapture'):
            print("✅ Main capture class found")
        else:
            print("❌ Main capture class missing")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Addon loading failed: {e}")
        return False

def test_browser_automation():
    """Test browser automation import."""
    print("\nTesting browser automation...")
    
    try:
        from browser_automation import KhanAcademyBrowserAutomation
        print("✅ Browser automation imports successfully")
        
        # Test basic initialization
        automation = KhanAcademyBrowserAutomation()
        print("✅ Browser automation can be initialized")
        return True
    except Exception as e:
        print(f"❌ Browser automation failed: {e}")
        return False

def test_dependencies():
    """Test required dependencies."""
    print("\nTesting dependencies...")
    
    required_modules = [
        'mitmproxy',
        'selenium', 
        'aiohttp',
        'asyncio',
        'threading',
        'json'
    ]
    
    all_good = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module} - {e}")
            all_good = False
    
    return all_good

def test_mitmdump_executable():
    """Test that mitmdump is accessible."""
    print("\nTesting mitmdump executable...")
    
    try:
        # Try different possible paths
        possible_paths = [
            os.path.join(os.path.dirname(sys.executable), "mitmdump.exe"),
            os.path.join(os.path.dirname(sys.executable), "Scripts", "mitmdump.exe"),
            "mitmdump",
            "mitmdump.exe"
        ]
        
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    print(f"✅ mitmdump found at: {path}")
                    return True
                # Also try running it to see if it's in PATH
                elif path in ["mitmdump", "mitmdump.exe"]:
                    result = subprocess.run([path, "--version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        print(f"✅ mitmdump accessible via PATH: {path}")
                        return True
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
        
        # Try using Python module
        try:
            result = subprocess.run([sys.executable, "-m", "mitmproxy.tools.mitmdump", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ mitmdump accessible via Python module")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        print("❌ mitmdump not found in any expected location")
        print("   Try: pip install mitmproxy")
        return False
        
    except Exception as e:
        print(f"❌ mitmdump test failed: {e}")
        return False

def test_output_directory():
    """Test output directory creation."""
    print("\nTesting output directory...")
    
    try:
        os.makedirs("khan_academy_json", exist_ok=True)
        
        if os.path.exists("khan_academy_json") and os.path.isdir("khan_academy_json"):
            print("✅ Output directory created/exists")
            return True
        else:
            print("❌ Output directory creation failed")
            return False
    except Exception as e:
        print(f"❌ Output directory test failed: {e}")
        return False

def test_json_validation():
    """Test JSON validation with sample data."""
    print("\nTesting JSON validation...")
    
    try:
        # Sample Perseus question format
        sample_question = {
            "question": {
                "content": "Test question content",
                "widgets": {}
            },
            "hints": [],
            "answerArea": {
                "calculator": False
            }
        }
        
        # Test JSON serialization
        json_str = json.dumps(sample_question, indent=2)
        parsed_back = json.loads(json_str)
        
        if parsed_back == sample_question:
            print("✅ JSON validation working")
            return True
        else:
            print("❌ JSON validation failed")
            return False
    except Exception as e:
        print(f"❌ JSON validation test failed: {e}")
        return False

def main():
    print("Enhanced Khan Academy Question Scraper - Test Suite")
    print("=" * 60)
    
    tests = [
        test_dependencies,
        test_mitmdump_executable,
        test_mitmproxy_addon,
        test_browser_automation,
        test_output_directory,
        test_json_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED! The scraper should work properly.")
        print("\nNext steps:")
        print("1. Find a Khan Academy exercise URL")
        print("2. Run: python enhanced_khan_scraper.py <URL>")
        print("3. Watch the automatic question capture!")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Run: pip install -r requirements.txt")
        print("- Ensure Chrome browser is installed")
        print("- Check that all files are in the correct directory")
    
    print("=" * 60)

if __name__ == "__main__":
    main()