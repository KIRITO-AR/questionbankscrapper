"""
Test script for Khan Academy automated scraper improvements.
This script tests each improvement incrementally.
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime

class AutomatedScrapingTest:
    def __init__(self):
        self.test_results = {}
        self.save_directory = "khan_academy_json"
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def test_1_dependency_check(self):
        """Test 1: Check if all dependencies are installed"""
        self.log("Testing dependency installation...")
        
        try:
            # Try virtual environment first
            venv_mitmdump = os.path.join(os.getcwd(), ".venv", "Scripts", "mitmdump.exe")
            if os.path.exists(venv_mitmdump):
                cmd = [venv_mitmdump, '--version']
            else:
                cmd = ['mitmdump', '--version']
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log("✓ mitmproxy is installed")
                mitmproxy_ok = True
            else:
                self.log("✗ mitmproxy not working", "ERROR")
                mitmproxy_ok = False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.log("✗ mitmproxy not found", "ERROR")
            mitmproxy_ok = False
        
        # Test aiohttp
        try:
            import aiohttp
            self.log("✓ aiohttp is available")
            aiohttp_ok = True
        except ImportError:
            self.log("✗ aiohttp not found", "ERROR")
            aiohttp_ok = False
        
        # Test selenium (optional)
        try:
            import selenium
            self.log("✓ selenium is available")
            selenium_ok = True
        except ImportError:
            self.log("⚠ selenium not found (optional)", "WARNING")
            selenium_ok = False
        
        success = mitmproxy_ok and aiohttp_ok
        self.test_results['dependency_check'] = {
            'success': success,
            'mitmproxy': mitmproxy_ok,
            'aiohttp': aiohttp_ok,
            'selenium': selenium_ok
        }
        
        return success
    
    def test_2_file_structure(self):
        """Test 2: Verify all required files exist"""
        self.log("Testing file structure...")
        
        required_files = [
            'capture_khan_json_automated.py',
            'browser_automation.py',
            'automated_scraper.py',
            'requirements.txt'
        ]
        
        missing_files = []
        for file in required_files:
            if os.path.exists(file):
                self.log(f"✓ {file} exists")
            else:
                self.log(f"✗ {file} missing", "ERROR")
                missing_files.append(file)
        
        success = len(missing_files) == 0
        self.test_results['file_structure'] = {
            'success': success,
            'missing_files': missing_files
        }
        
        return success
    
    def test_3_automated_capture_import(self):
        """Test 3: Test if automated capture script can be imported"""
        self.log("Testing automated capture script import...")
        
        try:
            # Try to import without running
            sys.path.insert(0, '.')
            
            # Read the file and check syntax
            with open('capture_khan_json_automated.py', 'r') as f:
                content = f.read()
            
            # Basic syntax check
            compile(content, 'capture_khan_json_automated.py', 'exec')
            self.log("✓ Automated capture script syntax is valid")
            
            success = True
            
        except SyntaxError as e:
            self.log(f"✗ Syntax error in automated capture script: {e}", "ERROR")
            success = False
        except Exception as e:
            self.log(f"✗ Error with automated capture script: {e}", "ERROR")
            success = False
        
        self.test_results['automated_capture_import'] = {'success': success}
        return success
    
    def test_4_browser_automation_import(self):
        """Test 4: Test browser automation script"""
        self.log("Testing browser automation script...")
        
        try:
            # Check if selenium is available for full test
            import selenium
            from browser_automation import KhanAcademyBrowserAutomation
            
            # Create instance (without actually starting browser)
            automation = KhanAcademyBrowserAutomation()
            self.log("✓ Browser automation class can be instantiated")
            
            success = True
            
        except ImportError:
            self.log("⚠ Selenium not available, browser automation will use manual mode", "WARNING")
            success = True  # Not a failure, just falls back to manual mode
            
        except Exception as e:
            self.log(f"✗ Error with browser automation: {e}", "ERROR")
            success = False
        
        self.test_results['browser_automation'] = {'success': success}
        return success
    
    def test_5_directory_setup(self):
        """Test 5: Test directory creation and permissions"""
        self.log("Testing directory setup...")
        
        try:
            # Test creating save directory
            test_dir = "test_" + self.save_directory
            
            if not os.path.exists(test_dir):
                os.makedirs(test_dir)
                self.log(f"✓ Successfully created {test_dir}")
            
            # Test writing to directory
            test_file = os.path.join(test_dir, "test.json")
            with open(test_file, 'w') as f:
                json.dump({"test": "data"}, f)
            self.log("✓ Successfully wrote test file")
            
            # Cleanup
            os.remove(test_file)
            os.rmdir(test_dir)
            self.log("✓ Successfully cleaned up test files")
            
            success = True
            
        except Exception as e:
            self.log(f"✗ Directory setup error: {e}", "ERROR")
            success = False
        
        self.test_results['directory_setup'] = {'success': success}
        return success
    
    def test_6_basic_mitmproxy_start(self):
        """Test 6: Test basic mitmproxy startup (quick test)"""
        self.log("Testing mitmproxy startup...")
        
        try:
            # Try to start mitmproxy with a quick test
            venv_mitmdump = os.path.join(os.getcwd(), ".venv", "Scripts", "mitmdump.exe")
            if os.path.exists(venv_mitmdump):
                cmd = [venv_mitmdump, '--version']
            else:
                cmd = ['mitmdump', '--version']
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log("✓ Mitmproxy can start successfully")
                success = True
            else:
                self.log(f"✗ Mitmproxy startup failed: {result.stderr}", "ERROR")
                success = False
                
        except subprocess.TimeoutExpired:
            self.log("✗ Mitmproxy startup timed out", "ERROR")
            success = False
        except Exception as e:
            self.log(f"✗ Mitmproxy startup error: {e}", "ERROR")
            success = False
        
        self.test_results['mitmproxy_startup'] = {'success': success}
        return success
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("Starting automated scraper testing...")
        self.log("=" * 60)
        
        tests = [
            ("Dependency Check", self.test_1_dependency_check),
            ("File Structure", self.test_2_file_structure),
            ("Automated Capture Import", self.test_3_automated_capture_import),
            ("Browser Automation", self.test_4_browser_automation_import),
            ("Directory Setup", self.test_5_directory_setup),
            ("Mitmproxy Startup", self.test_6_basic_mitmproxy_start)
        ]
        
        results = []
        for test_name, test_func in tests:
            self.log(f"Running: {test_name}")
            try:
                success = test_func()
                results.append((test_name, success))
                
                if success:
                    self.log(f"✓ {test_name} PASSED", "SUCCESS")
                else:
                    self.log(f"✗ {test_name} FAILED", "ERROR")
                    
            except Exception as e:
                self.log(f"✗ {test_name} CRASHED: {e}", "ERROR")
                results.append((test_name, False))
            
            self.log("-" * 40)
        
        # Summary
        self.log("=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "PASS" if success else "FAIL"
            self.log(f"{test_name}: {status}")
        
        self.log(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! Ready for automated scraping.", "SUCCESS")
            return True
        else:
            self.log("⚠ Some tests failed. Check the issues above.", "WARNING")
            return False
    
    def install_missing_dependencies(self):
        """Install missing dependencies"""
        self.log("Installing missing dependencies...")
        
        try:
            # Install requirements
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✓ Dependencies installed successfully")
                return True
            else:
                self.log(f"✗ Dependency installation failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Error installing dependencies: {e}", "ERROR")
            return False

def main():
    tester = AutomatedScrapingTest()
    
    print("Khan Academy Automated Scraper - Test Suite")
    print("=" * 60)
    print("This will test all improvements before running the scraper.")
    print()
    
    # Ask if user wants to install dependencies
    install_deps = input("Install/update dependencies first? (y/n): ").lower().strip() == 'y'
    
    if install_deps:
        if not tester.install_missing_dependencies():
            print("Failed to install dependencies. Please install manually.")
            return
    
    # Run tests
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! You can now run the automated scraper.")
        print("Usage: python automated_scraper.py <exercise_url>")
        print("Or run: run_automated_scraper.bat")
    else:
        print("\n⚠ Some tests failed. Please fix the issues and try again.")
        print("Common fixes:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Install Chrome browser for automation")
        print("- Check that all Python files are present")

if __name__ == "__main__":
    main()