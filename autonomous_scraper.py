"""
Autonomous Khan Academy Scraper - Full Automation Controller
This module combines active batch scraping with intelligent UI automation
for fully autonomous question downloading.
"""

import asyncio
import threading
import time
import logging
import os
import signal
import sys
from typing import Set, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

# Import our components
from browser_automation import KhanAcademyBrowserAutomation
from active_scraper import ActiveKhanScraper
from graphql_analyzer import KhanGraphQLAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class ScrapingStats:
    """Statistics for the scraping session."""
    discovered_questions: int = 0
    downloaded_questions: int = 0
    questions_in_progress: int = 0
    ui_progressions: int = 0
    active_batches_processed: int = 0
    session_start_time: float = 0
    last_discovery_time: float = 0

class AutonomousKhanScraper:
    def __init__(self, exercise_url: str, proxy_port: int = 8080, max_questions: int = 1000):
        self.exercise_url = exercise_url
        self.proxy_port = proxy_port
        self.max_questions = max_questions
        
        # Components
        self.browser_automation = None
        self.active_scraper = None
        self.graphql_analyzer = None
        
        # State tracking
        self.discovered_questions: Set[str] = set()
        self.downloaded_questions: Set[str] = set()
        self.questions_in_progress: Set[str] = set()
        
        # Configuration
        self.batch_size = 10  # Increased for better download throughput
        self.ui_progression_interval = 20  # Faster UI progressions
        self.max_consecutive_failures = 3  # Quicker failure detection
        self.session_timeout = 7200  # 2 hours max session
        
        # Statistics
        self.stats = ScrapingStats()
        
        # Control flags
        self.running = False
        self.stop_requested = False
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging for the autonomous scraper."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f"autonomous_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            ]
        )
        
    async def run_autonomous_session(self) -> bool:
        """Main autonomous scraping loop."""
        try:
            self.running = True
            self.stats.session_start_time = time.time()
            
            logger.info(f"Starting autonomous scraping session for {self.exercise_url}")
            logger.info(f"Target: {self.max_questions} questions, Proxy port: {self.proxy_port}")
            
            # Phase 1: Initialize all components
            if not await self.initialize_components():
                logger.error("Failed to initialize components")
                return False
            
            # Phase 2: Main scraping loop
            cycle_count = 0
            consecutive_failures = 0
            last_download_cycle = 0
            
            while (len(self.downloaded_questions) < self.max_questions and 
                   consecutive_failures < self.max_consecutive_failures and
                   not self.stop_requested and
                   not self.session_timeout_reached()):
                
                cycle_count += 1
                logger.info(f"=== Autonomous Cycle {cycle_count} ===")
                logger.info(f"Progress: {len(self.downloaded_questions)}/{self.max_questions} downloaded, {len(self.discovered_questions)} discovered")
                
                cycle_success = False
                
                try:
                    # Step 1: Always prioritize downloading discovered questions
                    batch_results = await self.perform_active_batch_scraping()
                    if batch_results > 0:
                        cycle_success = True
                        consecutive_failures = 0
                        last_download_cycle = cycle_count
                    
                    # Step 2: UI progression to discover new questions 
                    # - Always do UI progression if we haven't discovered enough questions
                    # - Also do it if we haven't had successful downloads recently
                    needs_ui_progression = (
                        len(self.discovered_questions) < self.max_questions or
                        batch_results == 0 or
                        (cycle_count - last_download_cycle) > 3
                    )
                    
                    if needs_ui_progression:
                        ui_results = await self.perform_ui_progression()
                        if ui_results > 0:
                            cycle_success = True
                            consecutive_failures = 0
                    
                    # Step 3: Session management and health checks
                    await self.handle_session_management()
                    
                    # Step 4: Progress reporting
                    self.report_progress()
                    
                    if not cycle_success:
                        consecutive_failures += 1
                        logger.warning(f"Cycle {cycle_count} unsuccessful (failure #{consecutive_failures})")
                    
                    # Step 5: Adaptive pause - shorter if we're downloading successfully
                    if batch_results > 0:
                        await asyncio.sleep(2)  # Short pause when downloading
                    else:
                        await asyncio.sleep(5)  # Normal pause otherwise
                    
                except Exception as e:
                    logger.error(f"Error in autonomous cycle {cycle_count}: {e}")
                    consecutive_failures += 1
                    await asyncio.sleep(10)  # Longer pause after errors
            
            # Session completion
            return await self.finalize_session(cycle_count, consecutive_failures)
            
        except Exception as e:
            logger.error(f"Autonomous session failed: {e}")
            return False
        finally:
            await self.cleanup_components()
            self.running = False
    
    async def initialize_components(self) -> bool:
        """Initialize all scraping components."""
        try:
            logger.info("Initializing components...")
            
            # Initialize browser automation
            self.browser_automation = KhanAcademyBrowserAutomation(self.proxy_port)
            
            if not self.browser_automation.setup_browser():
                logger.error("Failed to setup browser")
                return False
            
            if not self.browser_automation.navigate_to_exercise(self.exercise_url):
                logger.error("Failed to navigate to exercise")
                return False
            
            if not self.browser_automation.start_exercise():
                logger.warning("Could not start exercise, continuing anyway...")
            
            # Initialize active scraper components
            self.graphql_analyzer = KhanGraphQLAnalyzer()
            self.active_scraper = ActiveKhanScraper()
            
            # Give some time for session data to be captured
            await asyncio.sleep(5)
            
            logger.info("Components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            return False
    
    async def perform_active_batch_scraping(self) -> int:
        """Perform active batch scraping of discovered questions."""
        try:
            # Get questions that need downloading
            pending_questions = self.discovered_questions - self.downloaded_questions - self.questions_in_progress
            
            if not pending_questions:
                logger.debug("No pending questions for active scraping")
                return 0
            
            # Process in batches - take ALL pending questions if reasonable size
            question_list = list(pending_questions)
            if len(question_list) > self.batch_size * 2:
                question_list = question_list[:self.batch_size]
            
            self.questions_in_progress.update(question_list)
            
            logger.info(f"Starting active batch scraping for {len(question_list)} questions (total pending: {len(pending_questions)})")
            
            # Initialize active scraper session if needed
            if not self.active_scraper.session:
                await self.active_scraper.create_session()
            
            results = await self.active_scraper.fetch_question_batch(question_list)
            
            # Process results
            successful_downloads = 0
            for question_id, data in results.items():
                if data and self.save_question_safely(question_id, data):
                    self.downloaded_questions.add(question_id)
                    successful_downloads += 1
                    logger.debug(f"Successfully downloaded question {question_id}")
                else:
                    logger.warning(f"Failed to download or save question {question_id}")
                
                self.questions_in_progress.discard(question_id)
            
            self.stats.active_batches_processed += 1
            logger.info(f"Active batch scraping completed: {successful_downloads}/{len(question_list)} successful")
            
            # If we have more pending questions, immediately schedule another batch
            remaining_pending = len(pending_questions) - len(question_list)
            if remaining_pending > 0:
                logger.info(f"Still have {remaining_pending} questions pending for download")
            
            return successful_downloads
            
        except Exception as e:
            logger.error(f"Active batch scraping failed: {e}")
            # Reset in-progress tracking on error
            for q_id in question_list:
                self.questions_in_progress.discard(q_id)
            return 0
    
    async def perform_ui_progression(self) -> int:
        """Use browser automation to progress and discover new questions."""
        try:
            logger.info("Performing UI progression to discover new questions")
            
            initial_discovered = len(self.discovered_questions)
            progression_count = 0
            max_progressions = 5
            
            # Perform multiple question progressions
            while progression_count < max_progressions:
                success = await asyncio.get_event_loop().run_in_executor(
                    None, self.browser_automation.progress_to_next_question
                )
                
                if success:
                    progression_count += 1
                    self.stats.ui_progressions += 1
                    
                    # Allow time for new data to be captured
                    await asyncio.sleep(3)
                    
                    # Update discovered questions from global state (captured by mitmproxy)
                    self.update_discovered_questions_from_global_state()
                    
                else:
                    logger.warning("UI progression failed, will retry")
                    break
            
            newly_discovered = len(self.discovered_questions) - initial_discovered
            if newly_discovered > 0:
                self.stats.last_discovery_time = time.time()
            
            logger.info(f"UI progression completed: {progression_count} progressions, {newly_discovered} new questions discovered")
            return newly_discovered
            
        except Exception as e:
            logger.error(f"UI progression error: {e}")
            return 0
    
    def update_discovered_questions_from_global_state(self):
        """Update discovered questions from mitmproxy global state."""
        try:
            # Import global state from mitmproxy addon
            import capture_khan_json_automated as capture_module
            
            global_discovered = getattr(capture_module, 'all_discovered_questions', set())
            global_saved = getattr(capture_module, 'saved_questions', set())
            
            # Update our local state
            old_count = len(self.discovered_questions)
            self.discovered_questions.update(global_discovered)
            self.downloaded_questions.update(global_saved)
            
            new_count = len(self.discovered_questions)
            if new_count > old_count:
                logger.debug(f"Updated discovered questions: {old_count} -> {new_count}")
                
        except Exception as e:
            logger.debug(f"Could not update from global state: {e}")
    
    async def handle_session_management(self):
        """Handle session interruptions and maintain scraping continuity."""
        try:
            # Check for completion dialogs
            if await self.check_exercise_completion():
                logger.info("Exercise completed, restarting...")
                await self.restart_exercise()
            
            # Check for connection health
            if await self.check_connection_health():
                logger.debug("Connection health check passed")
            else:
                logger.warning("Connection issues detected, attempting recovery")
                await self.recover_connection()
            
            # Check for rate limiting indicators
            if await self.check_rate_limiting():
                logger.info("Rate limiting detected, implementing backoff")
                await asyncio.sleep(30)  # Backoff period
        
        except Exception as e:
            logger.error(f"Session management error: {e}")
    
    async def check_exercise_completion(self) -> bool:
        """Check if the current exercise is completed."""
        try:
            completion_indicators = [
                "Congratulations",
                "Practice complete", 
                "You've mastered",
                "Exercise finished"
            ]
            
            for indicator in completion_indicators:
                if await asyncio.get_event_loop().run_in_executor(
                    None, self.browser_automation.handle_exercise_interruptions
                ):
                    return True
            return False
            
        except Exception as e:
            logger.debug(f"Error checking completion: {e}")
            return False
    
    async def restart_exercise(self):
        """Restart the exercise when completion is detected."""
        try:
            success = await asyncio.get_event_loop().run_in_executor(
                None, self.browser_automation.navigate_to_exercise, self.exercise_url
            )
            
            if success:
                await asyncio.sleep(5)  # Allow page to load
                await asyncio.get_event_loop().run_in_executor(
                    None, self.browser_automation.start_exercise
                )
                logger.info("Exercise successfully restarted")
            else:
                logger.error("Failed to restart exercise")
                
        except Exception as e:
            logger.error(f"Exercise restart error: {e}")
    
    async def check_connection_health(self) -> bool:
        """Check if connections are healthy."""
        try:
            # Test browser health
            browser_ok = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.browser_automation.driver is not None
            )
            
            # Test active scraper health
            active_scraper_ok = await self.active_scraper.test_connection()
            
            return browser_ok and active_scraper_ok
            
        except Exception as e:
            logger.debug(f"Connection health check error: {e}")
            return False
    
    async def check_rate_limiting(self) -> bool:
        """Check for rate limiting indicators."""
        try:
            # Check if we've been making too many requests
            current_time = time.time()
            if hasattr(self.active_scraper, 'rate_limit_delay'):
                return self.active_scraper.rate_limit_delay > 2.0
            return False
            
        except Exception as e:
            logger.debug(f"Rate limiting check error: {e}")
            return False
    
    async def recover_connection(self):
        """Recover from connection issues."""
        try:
            logger.info("Attempting connection recovery...")
            
            # Restart active scraper session
            if self.active_scraper and self.active_scraper.session:
                await self.active_scraper.close()
                await asyncio.sleep(5)
                await self.active_scraper.create_session()
            
            # Check browser and refresh if needed
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.browser_automation.refresh_page
                )
                await asyncio.sleep(10)  # Allow page to settle
            except Exception as e:
                logger.warning(f"Browser refresh during recovery failed: {e}")
            
            logger.info("Connection recovery completed")
            
        except Exception as e:
            logger.error(f"Recovery process error: {e}")
    
    def save_question_safely(self, question_id: str, data: Dict) -> bool:
        """Safely save question data in Perseus format."""
        try:
            save_directory = "khan_academy_json"
            if not os.path.exists(save_directory):
                os.makedirs(save_directory)
            
            filename = os.path.join(save_directory, f"{question_id}.json")
            
            # Save in Perseus format directly (data should already be Perseus format from active_scraper)
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Saved question {question_id} in Perseus format")
            return True
            
        except Exception as e:
            logger.error(f"Error saving question {question_id}: {e}")
            return False
    
    def session_timeout_reached(self) -> bool:
        """Check if session timeout has been reached."""
        return (time.time() - self.stats.session_start_time) > self.session_timeout
    
    def report_progress(self):
        """Report current scraping progress and statistics."""
        self.stats.discovered_questions = len(self.discovered_questions)
        self.stats.downloaded_questions = len(self.downloaded_questions)
        self.stats.questions_in_progress = len(self.questions_in_progress)
        
        completion_rate = (self.stats.downloaded_questions / self.max_questions) * 100 if self.max_questions > 0 else 0
        discovery_rate = (self.stats.discovered_questions / self.max_questions) * 100 if self.max_questions > 0 else 0
        
        elapsed_time = time.time() - self.stats.session_start_time
        elapsed_minutes = elapsed_time / 60
        
        logger.info(f"""
        === AUTONOMOUS SCRAPING PROGRESS ===
        Discovered: {self.stats.discovered_questions} questions ({discovery_rate:.1f}%)
        Downloaded: {self.stats.downloaded_questions} questions ({completion_rate:.1f}%)
        In Progress: {self.stats.questions_in_progress} questions
        Remaining: {self.max_questions - self.stats.downloaded_questions} questions
        
        Session Stats:
        - UI Progressions: {self.stats.ui_progressions}
        - Active Batches: {self.stats.active_batches_processed}
        - Session Time: {elapsed_minutes:.1f} minutes
        ====================================
        """)
    
    async def finalize_session(self, cycle_count: int, consecutive_failures: int) -> bool:
        """Finalize the scraping session and report results."""
        try:
            final_stats = {
                "total_cycles": cycle_count,
                "discovered_questions": len(self.discovered_questions),
                "downloaded_questions": len(self.downloaded_questions),
                "ui_progressions": self.stats.ui_progressions,
                "active_batches_processed": self.stats.active_batches_processed,
                "session_duration_minutes": (time.time() - self.stats.session_start_time) / 60,
                "consecutive_failures": consecutive_failures
            }
            
            logger.info("=== SESSION COMPLETION SUMMARY ===")
            for key, value in final_stats.items():
                logger.info(f"{key}: {value}")
            
            success = (consecutive_failures < self.max_consecutive_failures and 
                      len(self.downloaded_questions) > 0)
            
            if success:
                logger.info("Autonomous scraping session completed successfully!")
            else:
                logger.warning("Session ended due to errors or timeout")
            
            return success
            
        except Exception as e:
            logger.error(f"Error finalizing session: {e}")
            return False
    
    async def cleanup_components(self):
        """Clean up all components."""
        try:
            logger.info("Cleaning up components...")
            
            if self.active_scraper:
                await self.active_scraper.close()
            
            if self.browser_automation:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.browser_automation.cleanup
                )
            
            logger.info("Component cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def stop(self):
        """Request the scraper to stop gracefully."""
        self.stop_requested = True
        logger.info("Stop requested - will finish current cycle and exit")

# Helper function for running the autonomous scraper
async def run_autonomous_scraper(exercise_url: str, max_questions: int = 1000, proxy_port: int = 8080) -> bool:
    """Run the autonomous scraper with the given parameters."""
    scraper = AutonomousKhanScraper(exercise_url, proxy_port, max_questions)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        scraper.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    return await scraper.run_autonomous_session()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python autonomous_scraper.py <exercise_url> [max_questions] [proxy_port]")
        sys.exit(1)
    
    exercise_url = sys.argv[1]
    max_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    proxy_port = int(sys.argv[3]) if len(sys.argv) > 3 else 8080
    
    print(f"Starting autonomous scraper for: {exercise_url}")
    print(f"Target questions: {max_questions}, Proxy port: {proxy_port}")
    
    try:
        result = asyncio.run(run_autonomous_scraper(exercise_url, max_questions, proxy_port))
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\nGraceful shutdown completed")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)