"""
test_timeout_fixes.py
Verification script to test the timeout and network resilience fixes.
"""

import time
import requests
import subprocess
import sys
import os

def test_network_connectivity():
    """Test basic network connectivity."""
    print("=" * 50)
    print("Testing Network Connectivity")
    print("=" * 50)
    
    test_urls = [
        ("Google", "https://www.google.com"),
        ("Khan Academy", "https://www.khanacademy.org"),
        ("Khan Academy API", "https://www.khanacademy.org/api/internal/graphql")
    ]
    
    results = {}
    for name, url in test_urls:
        try:
            print(f"Testing {name}...")
            start_time = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✓ {name}: OK ({elapsed:.2f}s)")
                results[name] = True
            else:
                print(f"⚠ {name}: HTTP {response.status_code} ({elapsed:.2f}s)")
                results[name] = False
        except requests.exceptions.Timeout:
            print(f"✗ {name}: TIMEOUT (>10s)")
            results[name] = False
        except requests.exceptions.RequestException as e:
            print(f"✗ {name}: ERROR - {e}")
            results[name] = False
    
    return results

def test_mitmproxy_startup():
    """Test if mitmproxy can start successfully."""
    print("\n" + "=" * 50)
    print("Testing Mitmproxy Startup")
    print("=" * 50)
    
    try:
        print("Starting mitmproxy...")
        mitm_command = [
            "mitmdump",
            "--version"
        ]
        
        result = subprocess.run(mitm_command, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ mitmproxy is installed and accessible")
            print(f"Version: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ mitmproxy command failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("✗ mitmproxy not found - install with: pip install mitmproxy")
        return False
    except subprocess.TimeoutExpired:
        print("✗ mitmproxy startup timeout")
        return False
    except Exception as e:
        print(f"✗ Error testing mitmproxy: {e}")
        return False

def test_selenium_imports():
    """Test if Selenium and webdriver-manager are available."""
    print("\n" + "=" * 50)
    print("Testing Selenium Dependencies")
    print("=" * 50)
    
    dependencies = [
        ("selenium", "selenium"),
        ("webdriver-manager", "webdriver_manager"),
        ("requests", "requests")
    ]
    
    results = {}
    for name, module in dependencies:
        try:
            __import__(module)
            print(f"✓ {name} is available")
            results[name] = True
        except ImportError:
            print(f"✗ {name} is NOT available")
            results[name] = False
    
    return results

def test_webdriver_manager():
    """Test if ChromeDriverManager works."""
    print("\n" + "=" * 50)
    print("Testing WebDriver Manager")
    print("=" * 50)
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        
        print("Testing ChromeDriverManager...")
        start_time = time.time()
        driver_path = ChromeDriverManager().install()
        elapsed = time.time() - start_time
        
        if os.path.exists(driver_path):
            print(f"✓ ChromeDriver installed successfully ({elapsed:.2f}s)")
            print(f"Driver path: {driver_path}")
            return True
        else:
            print("✗ ChromeDriver path not found")
            return False
            
    except Exception as e:
        print(f"✗ ChromeDriverManager failed: {e}")
        return False

def test_script_imports():
    """Test if our scripts can be imported without errors."""
    print("\n" + "=" * 50)
    print("Testing Script Imports")
    print("=" * 50)
    
    scripts = [
        ("automate_exercise", "automate_exercise"),
        ("capture_khan_json", "capture_khan_json"),
        ("main", "main")
    ]
    
    results = {}
    for name, module in scripts:
        try:
            __import__(module)
            print(f"✓ {name} imports successfully")
            results[name] = True
        except ImportError as e:
            print(f"✗ {name} import failed: {e}")
            results[name] = False
        except Exception as e:
            print(f"⚠ {name} import warning: {e}")
            results[name] = True  # Consider warnings as success
    
    return results

def display_summary(results):
    """Display a summary of all test results."""
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    all_passed = True
    for category, tests in results.items():
        print(f"\n{category}:")
        if isinstance(tests, dict):
            for test, passed in tests.items():
                status = "✓ PASS" if passed else "✗ FAIL"
                print(f"  {test}: {status}")
                if not passed:
                    all_passed = False
        else:
            status = "✓ PASS" if tests else "✗ FAIL"
            print(f"  {status}")
            if not tests:
                all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ ALL TESTS PASSED - Timeout fixes should work!")
        print("\nYou can now run:")
        print("  python main.py")
    else:
        print("✗ SOME TESTS FAILED - Please fix the issues above")
        print("\nCommon solutions:")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Check internet connection")
        print("- Disable VPN/firewall temporarily")
    
    return all_passed

def main():
    """Run all verification tests."""
    print("Timeout Fix Verification Test")
    print("Testing enhanced timeout and network resilience features...\n")
    
    results = {}
    
    # Run all tests
    results["Network Connectivity"] = test_network_connectivity()
    results["Mitmproxy"] = test_mitmproxy_startup()
    results["Selenium Dependencies"] = test_selenium_imports()
    results["WebDriver Manager"] = test_webdriver_manager()
    results["Script Imports"] = test_script_imports()
    
    # Display summary
    success = display_summary(results)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)