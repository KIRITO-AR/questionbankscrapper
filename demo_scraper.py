"""
Demo script to test the automated scraper with a sample Khan Academy exercise.
This demonstrates the first improvement: automated question downloading.
"""

import subprocess
import time
import os
from datetime import datetime

def demo_automated_scraping():
    """
    Demo the automated scraping functionality.
    """
    print("Khan Academy Automated Scraper - Demo")
    print("=" * 50)
    
    # Sample exercise URL (Khan Academy Algebra)
    test_url = "https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-functions-equations/x2f8bb11595b61c86:quadratic-formula/e/quadratic_formula"
    
    print(f"Demo URL: {test_url}")
    print()
    print("This demo will:")
    print("1. Start the automated scraper")
    print("2. Run for 30 seconds to capture some questions")
    print("3. Stop and show results")
    print()
    
    # Check if user wants to continue
    response = input("Run the demo? (y/n): ").strip().lower()
    if response != 'y':
        print("Demo cancelled.")
        return
    
    print("\n[INFO] Starting automated scraper demo...")
    
    # Start the automated scraper
    venv_python = os.path.join(os.getcwd(), ".venv", "Scripts", "python.exe")
    
    try:
        process = subprocess.Popen([
            venv_python, 
            "automated_scraper.py", 
            test_url
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            universal_newlines=True, bufsize=1)
        
        print("[INFO] Scraper started, running for 30 seconds...")
        print("[INFO] (In a real scenario, you would let it run longer)")
        print()
        
        # Let it run for 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            # Read output if available
            if process.poll() is not None:
                break
                
            time.sleep(1)
            
            # Show progress
            if os.path.exists("khan_academy_json"):
                count = len([f for f in os.listdir("khan_academy_json") 
                           if f.endswith('.json')])
                if count > 0:
                    print(f"[PROGRESS] {count} questions captured so far...")
        
        # Stop the process
        print("\n[INFO] Stopping demo...")
        process.terminate()
        
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
        # Show final results
        print("\n[RESULTS] Demo completed!")
        
        if os.path.exists("khan_academy_json"):
            files = [f for f in os.listdir("khan_academy_json") if f.endswith('.json')]
            print(f"Total questions captured: {len(files)}")
            
            if files:
                print("\nCaptured files:")
                for i, file in enumerate(files[:5]):  # Show first 5
                    print(f"  {i+1}. {file}")
                if len(files) > 5:
                    print(f"  ... and {len(files) - 5} more")
            else:
                print("No questions captured in this short demo.")
                print("Note: The demo needs longer to establish connections and capture questions.")
        else:
            print("No questions directory created.")
    
    except Exception as e:
        print(f"[ERROR] Demo failed: {e}")
    
    print("\n[INFO] Demo finished. The automated scraper is ready for real use!")
    print("For real usage, run: python automated_scraper.py <exercise_url>")

if __name__ == "__main__":
    demo_automated_scraping()