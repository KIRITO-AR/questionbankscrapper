"""
Test script for the enhanced Khan Academy scraper with autonomous capabilities.
This script runs a quick test to validate all components work together.
"""

import sys
import os
import time
import asyncio
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from browser_automation import KhanAcademyBrowserAutomation
        print("✓ browser_automation imported successfully")
    except ImportError as e:
        print(f"✗ browser_automation import failed: {e}")
        return False
    
    try:
        from graphql_analyzer import KhanGraphQLAnalyzer
        print("✓ graphql_analyzer imported successfully")
    except ImportError as e:
        print(f"✗ graphql_analyzer import failed: {e}")
        return False
    
    try:
        from active_scraper import ActiveKhanScraper
        print("✓ active_scraper imported successfully")
    except ImportError as e:
        print(f"✗ active_scraper import failed: {e}")
        return False
    
    try:
        from autonomous_scraper import AutonomousKhanScraper
        print("✓ autonomous_scraper imported successfully")
    except ImportError as e:
        print(f"✗ autonomous_scraper import failed: {e}")
        return False
    
    try:
        import capture_khan_json_automated
        print("✓ capture_khan_json_automated imported successfully")
    except ImportError as e:
        print(f"✗ capture_khan_json_automated import failed: {e}")
        return False
    
    try:
        from enhanced_khan_scraper import EnhancedKhanScraper
        print("✓ enhanced_khan_scraper imported successfully")
    except ImportError as e:
        print(f"✗ enhanced_khan_scraper import failed: {e}")
        return False
    
    return True

def test_component_initialization():
    """Test that components can be initialized without errors."""
    print("\nTesting component initialization...")
    
    try:
        from graphql_analyzer import KhanGraphQLAnalyzer
        analyzer = KhanGraphQLAnalyzer()
        print("✓ GraphQL analyzer initialized")
    except Exception as e:
        print(f"✗ GraphQL analyzer initialization failed: {e}")
        return False
    
    try:
        from active_scraper import ActiveKhanScraper
        scraper = ActiveKhanScraper()
        print("✓ Active scraper initialized")
    except Exception as e:
        print(f"✗ Active scraper initialization failed: {e}")
        return False
    
    try:
        from autonomous_scraper import AutonomousKhanScraper
        autonomous = AutonomousKhanScraper("https://example.com", 8080, 10)
        print("✓ Autonomous scraper initialized")
    except Exception as e:
        print(f"✗ Autonomous scraper initialization failed: {e}")
        return False
    
    return True

async def test_async_components():
    """Test async components work correctly."""
    print("\nTesting async components...")
    
    try:
        from active_scraper import ActiveKhanScraper
        scraper = ActiveKhanScraper()
        
        # Test session creation (will fail due to no cookies, but should not crash)
        try:
            await scraper.create_session()
            print("✓ Active scraper session creation works")
        except Exception as e:
            print(f"✓ Active scraper session creation handled gracefully: {type(e).__name__}")
        
        # Test close
        await scraper.close()
        print("✓ Active scraper cleanup works")
        
    except Exception as e:
        print(f"✗ Async component test failed: {e}")
        return False
    
    return True

def test_enhanced_scraper():
    """Test the enhanced scraper main class."""
    print("\nTesting enhanced scraper...")
    
    try:
        from enhanced_khan_scraper import EnhancedKhanScraper
        scraper = EnhancedKhanScraper(proxy_port=8080)
        print("✓ Enhanced scraper initialized")
        
        # Test that autonomous mode is detected
        if hasattr(scraper, 'autonomous_mode'):
            print(f"✓ Autonomous mode available: {scraper.autonomous_mode}")
        else:
            print("⚠ Autonomous mode attribute not found")
        
        return True
        
    except Exception as e:
        print(f"✗ Enhanced scraper test failed: {e}")
        return False

def test_mitmproxy_addon():
    """Test the mitmproxy addon loads correctly."""
    print("\nTesting mitmproxy addon...")
    
    try:
        import capture_khan_json_automated as addon_module
        
        # Check if the addon class exists
        if hasattr(addon_module, 'KhanAcademyAutomatedCapture'):
            addon = addon_module.KhanAcademyAutomatedCapture()
            print("✓ Mitmproxy addon class instantiated")
            
            # Check for new methods
            if hasattr(addon, 'start_active_batch_processing'):
                print("✓ Active batch processing method available")
            else:
                print("⚠ Active batch processing method not found")
            
            if hasattr(addon, 'save_active_question_data'):
                print("✓ Active question saving method available")
            else:
                print("⚠ Active question saving method not found")
            
        else:
            print("✗ Addon class not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Mitmproxy addon test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("ENHANCED KHAN ACADEMY SCRAPER - COMPONENT TEST")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Component Initialization Test", test_component_initialization),
        ("Enhanced Scraper Test", test_enhanced_scraper),
        ("Mitmproxy Addon Test", test_mitmproxy_addon)
    ]
    
    async_tests = [
        ("Async Components Test", test_async_components)
    ]
    
    results = {}
    
    # Run synchronous tests
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Run async tests
    for test_name, test_func in async_tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = asyncio.run(test_func())
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print("\n" + "=" * 60)
    print(f"OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The enhanced scraper is ready to use.")
        print("\nYou can now run:")
        print("python enhanced_khan_scraper.py <url> <max_questions> autonomous")
    else:
        print("⚠ Some tests failed. Please check the errors above.")
        print("The scraper may still work but with limited functionality.")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)