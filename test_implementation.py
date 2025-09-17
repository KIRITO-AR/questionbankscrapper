"""
test_implementation.py
Simple test script to verify the implementation works correctly.
"""

import os
import sys

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import automate_exercise
        print("✓ automate_exercise module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import automate_exercise: {e}")
        return False
    
    try:
        from capture_khan_json import KhanAcademyCapture
        print("✓ capture_khan_json module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import capture_khan_json: {e}")
        return False
    
    try:
        import main
        print("✓ main module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import main: {e}")
        return False
    
    return True

def test_dependencies():
    """Test that all dependencies are available."""
    print("\nTesting dependencies...")
    
    dependencies = [
        'selenium',
        'webdriver_manager',
        'requests',
        'mitmproxy'
    ]
    
    all_available = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} is available")
        except ImportError:
            print(f"✗ {dep} is NOT available")
            all_available = False
    
    return all_available

def test_file_structure():
    """Test that all required files exist."""
    print("\nTesting file structure...")
    
    required_files = [
        'requirements.txt',
        'automate_exercise.py',
        'capture_khan_json.py',
        'main.py'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} is missing")
            all_exist = False
    
    return all_exist

def test_configuration():
    """Test basic configuration and setup."""
    print("\nTesting configuration...")
    
    # Test that save directory can be created
    save_dir = "khan_academy_json"
    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
            print(f"✓ Created save directory: {save_dir}")
        except Exception as e:
            print(f"✗ Failed to create save directory: {e}")
            return False
    else:
        print(f"✓ Save directory already exists: {save_dir}")
    
    return True

def main():
    """Run all tests."""
    print("=" * 50)
    print("Khan Academy Scraper Implementation Test")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_imports,
        test_dependencies,
        test_configuration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if all(results):
        print("✓ All tests passed! Implementation appears to be working correctly.")
        print("\nTo run the scraper:")
        print("python main.py [exercise_url] [max_questions]")
        return True
    else:
        print("✗ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)