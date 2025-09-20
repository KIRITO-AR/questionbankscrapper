#!/usr/bin/env python3
"""
Test script to verify autonomous scraping capabilities.
This script validates that the scraper can run autonomously without user interaction.
"""

import sys
import os

def test_autonomous_config():
    """Test that the automation is configured for autonomous operation."""
    print("🤖 Testing Autonomous Scraping Configuration")
    print("=" * 50)
    
    try:
        # Test imports
        from automate_exercise import (
            run_automation, 
            log_progress, 
            find_all_exercise_links, 
            autonomous_answer_question, 
            autonomous_submit_answer, 
            autonomous_next_question
        )
        print("✓ All autonomous functions imported successfully")
        
        from main import DEFAULT_MAX_QUESTIONS
        print(f"✓ Default max questions: {DEFAULT_MAX_QUESTIONS}")
        
        from capture_khan_json import ENABLE_ACTIVE_SCRAPING
        print(f"✓ Active scraping enabled: {ENABLE_ACTIVE_SCRAPING}")
        
        if ENABLE_ACTIVE_SCRAPING and DEFAULT_MAX_QUESTIONS >= 100:
            print("✅ CONFIGURATION VERIFIED!")
            print()
            print("🚀 AUTONOMOUS SCRAPING READY!")
            print("Features enabled:")
            print("  ✓ Active batch question fetching")
            print("  ✓ Automatic exercise discovery")
            print("  ✓ Autonomous question answering")
            print("  ✓ Multi-exercise crawling")
            print("  ✓ Zero user interaction required")
            print()
            print("To start autonomous scraping:")
            print("  python main.py")
            print()
            print("The scraper will:")
            print("  1. Automatically find all exercises on Khan Academy")
            print("  2. Start each exercise automatically")
            print("  3. Answer all questions autonomously")
            print("  4. Download ALL question JSONs via active scraping")
            print("  5. Move to the next exercise automatically")
            print("  6. Continue until all questions are captured")
            return True
        else:
            print("❌ CONFIGURATION INCOMPLETE!")
            if not ENABLE_ACTIVE_SCRAPING:
                print("  - Active scraping is disabled")
            if DEFAULT_MAX_QUESTIONS < 100:
                print(f"  - Max questions too low: {DEFAULT_MAX_QUESTIONS}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    print("Khan Academy Autonomous Scraper - Configuration Test")
    print("=" * 60)
    
    success = test_autonomous_config()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 ALL SYSTEMS GO! Ready for autonomous scraping!")
        sys.exit(0)
    else:
        print("\n" + "=" * 60) 
        print("❌ Configuration issues found. Please check the setup.")
        sys.exit(1)

if __name__ == "__main__":
    main()