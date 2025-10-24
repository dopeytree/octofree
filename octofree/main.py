"""
Octofree - Octopus Energy Free Electricity Session Monitor

Main application module that orchestrates session scraping, scheduling,
and Discord notifications for Octopus Energy's free electricity sessions.

Functionality:
- Scrapes octopus.energy/free-electricity/ website hourly
- Optionally scrapes X.com (Twitter) at 11am and 8pm
- Detects new sessions and sends Discord notifications
- Manages session queue with support for multiple concurrent sessions
- Sends reminder notifications (5 min before start/end)
- Tracks session history to prevent duplicate notifications

Environment Variables:
- DISCORD_WEBHOOK_URL: Discord webhook for notifications
- TEST_MODE: Enable test mode (resets notification flags)
- SINGLE_RUN: Run once and exit (vs. continuous loop)
- OUTPUT_DIR: Directory for data files (default: ./output)
- BEARER_TOKEN: Optional X.com API bearer token
- TEST_X_SCRAPER: Force X.com scraper to run (testing only)
"""

import time
import os
import logging
from scraper_website import fetch_page_content, extract_sessions
from scraper_x import fetch_and_extract_sessions
from notifier import check_and_send_notifications, send_discord_notification
from storage import load_scheduled_sessions, save_scheduled_sessions, load_past_scheduled_sessions, save_past_scheduled_sessions, update_last_sent_session, get_last_sent_session, load_last_extracted_sessions, save_last_extracted_sessions, log_x_scraper_data
from utils import parse_session_date, parse_session_to_reminder, parse_session_to_end_reminder, parse_session_end_date
from validator import run_startup_validation
from loading_screen import display_loading_screen, display_static_banner
from datetime import datetime, timedelta

# Logging configuration (match original, but set to DEBUG for more detail)
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
output_dir = os.path.abspath(os.path.expanduser(os.getenv('OUTPUT_DIR', DEFAULT_OUTPUT_DIR)))

# Create output directory with error handling
try:
    os.makedirs(output_dir, exist_ok=True)
except PermissionError:
    print(f"ERROR: Cannot create directory {output_dir} - permission denied")
    print("If running in Docker, ensure the volume is mounted with proper permissions")
    raise

# Configure logging to suppress verbose urllib3/requests debug logs
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

log_file = os.path.join(output_dir, 'octofree.log')
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG to show more logs; revert to INFO if too verbose
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def _log_loaded_settings():
    """Log current configuration settings for debugging."""
    logging.info("⚙️ LOADING SETTINGS")
    logging.info("┌───")
    # Mask webhook URL for security - never log the full URL
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if webhook_url:
        logging.info(f"│ 🔵 DISCORD_WEBHOOK_URL: SET ({len(webhook_url)} chars)")
    else:
        logging.info("│ 🔴 DISCORD_WEBHOOK_URL: NOT SET")
    logging.info(f"│ 🔵 TEST_MODE: {os.getenv('TEST_MODE', 'false')}")
    logging.info(f"│ 🔵 SINGLE_RUN: {os.getenv('SINGLE_RUN', 'false')}")
    logging.info(f"│ 🔵 OUTPUT_DIR: {output_dir}")
    logging.info("└───")

_log_loaded_settings()

def should_check_x():
    """
    Determine if X.com scraper should run based on current time.
    
    X.com scraper is configured to run during specific time windows:
    - 11:00-11:59 (11am window)
    - 20:00-20:59 (8pm window)
    
    This reduces API usage while still catching announcements that typically
    happen at these times. Can be overridden with TEST_X_SCRAPER=true.
    
    Returns:
        bool: True if current hour is 11 or 20, or if TEST_X_SCRAPER is set.
    """
    # Allow override for testing
    if os.getenv('TEST_X_SCRAPER', '').strip().lower() == 'true':
        return True
    
    now = datetime.now()
    hour = now.hour
    # Check if we're in the 11am window (11:00-11:59) or 8pm window (20:00-20:59)
    return hour == 11 or hour == 20

def main():
    """
    Main application loop for Octofree session monitoring.
    
    Workflow:
    1. Run startup validation on historical data
    2. Scrape octopus.energy website for sessions
    3. Optionally scrape X.com during scheduled windows (11am, 8pm)
    4. Compare extracted sessions with previous run
    5. Detect new sessions and add to queue
    6. Send initial notifications for new "next" sessions
    7. Check for and send reminder notifications
    8. Sleep 1 hour and repeat (unless SINGLE_RUN mode)
    
    Supports TEST_MODE for testing notifications without waiting for real sessions.
    Handles multiple concurrent sessions announced within 48 hours.
    """
    # Display loading screen at startup
    try:
        # Try animated loading screen (works in most terminals)
        display_loading_screen(duration=10.0, steps=40)
    except Exception:
        # Fallback to static banner if animation fails (e.g., in some Docker setups)
        display_static_banner()
    
    url = 'https://octopus.energy/free-electricity/'
    single_run = os.getenv('SINGLE_RUN', '').strip().lower() == 'true'
    test_mode = os.getenv('TEST_MODE', '').strip().lower() == 'true'
    x_enabled = bool(os.getenv('BEARER_TOKEN'))
    
    # Run startup validation and correction on historical data
    logging.info("🌀 Created by Ed Stone (Dopeytree) 2025")
    logging.info("────────────────────────────────────────────────────────────────────")
    try:
        run_startup_validation(output_dir)
    except Exception:
        logging.exception("Startup validation encountered an error; continuing")
    
    # BAYESIAN UPDATE: Check stored sessions against current website data immediately
    logging.info("🔄 BAYESIAN UPDATE: Validating stored sessions against current website data")
    try:
        # Immediate website scrape to get current state
        startup_html_content = fetch_page_content(url)
        startup_current_sessions = []
        startup_session_type = None
        
        if startup_html_content:
            logging.debug(f"[STARTUP_SCRAPE] Fetched HTML content length: {len(startup_html_content)}")
            startup_session_type, startup_website_sessions = extract_sessions(startup_html_content)
            startup_current_sessions.extend(startup_website_sessions)
            logging.info(f"🔍 [STARTUP SCRAPE] Fetched HTML ({len(startup_html_content)}KB)")
            logging.info(f"🔵 [STARTUP SCRAPE] Extracted {len(startup_website_sessions)} session(s):")
            for i, session in enumerate(startup_website_sessions):
                prefix = "└─" if i == len(startup_website_sessions) - 1 else "├─"
                logging.info(f"  {prefix} {session}")
            
            # Load current stored sessions
            startup_scheduled_sessions = load_scheduled_sessions()
            startup_past_sessions = load_past_scheduled_sessions()
            
            # Log startup session counts
            total_startup_sessions = len(startup_scheduled_sessions) + len(startup_past_sessions)
            logging.info(f"📅 STARTUP: Loaded {total_startup_sessions} total sessions ({len(startup_scheduled_sessions)} scheduled, {len(startup_past_sessions)} past)")
            
            startup_tracked_strings = set(s['session'] for s in startup_scheduled_sessions)
            startup_past_strings = set(s['session'] for s in startup_past_sessions)
            
            # Check for sessions that exist on website but are missing from stored data
            missing_from_tracking = []
            for session_str in startup_current_sessions:
                if session_str not in startup_tracked_strings and session_str not in startup_past_strings:
                    missing_from_tracking.append(session_str)
            
            # Check for sessions in stored data that no longer exist on website
            website_session_set = set(startup_current_sessions)
            orphaned_scheduled = []
            for session in startup_scheduled_sessions[:]:  # Copy to avoid modification during iteration
                if session['session'] not in website_session_set:
                    # Check if session has already ended (past its end time)
                    end_time = datetime.fromisoformat(session['end_time'])
                    if end_time <= datetime.now():
                        # Session has ended, move to past
                        startup_past_sessions.append(session)
                        startup_scheduled_sessions.remove(session)
                        logging.info(f"✅ [STARTUP CLEANUP] Completed session '{session['session']}' → moved to past")
                    else:
                        # Session still exists but not on website - this is unusual, log it
                        orphaned_scheduled.append(session['session'])
                        logging.warning(f"⚠️ [STARTUP CLEANUP] Session '{session['session']}' exists in scheduled but not on website")
            
            # Add missing sessions
            if missing_from_tracking:
                logging.warning(f"🟠 [STARTUP RECOVERY] Found {len(missing_from_tracking)} session(s) on website but missing from tracking:")
                for i, session in enumerate(missing_from_tracking):
                    prefix = "└─" if i == len(missing_from_tracking) - 1 else "├─"
                    logging.warning(f"  {prefix} {session}")
                
                for session_str in missing_from_tracking:
                    # Parse and add the missing session
                    start_time = parse_session_date(session_str)
                    reminder_time = parse_session_to_reminder(session_str)
                    end_time = parse_session_end_date(session_str)
                    end_reminder_time = parse_session_to_end_reminder(session_str)
                    
                    if start_time and end_time:
                        session_data = {
                            'session': session_str,
                            'start_time': start_time.isoformat(),
                            'reminder_time': reminder_time.isoformat() if reminder_time else None,
                            'end_time': end_time.isoformat(),
                            'end_reminder_time': end_reminder_time.isoformat() if end_reminder_time else None,
                            'notified': False,  # Don't send notification on startup recovery
                            'reminder_sent': False,
                            'end_sent': False
                        }
                        
                        startup_scheduled_sessions.append(session_data)
                        logging.info(f"✅ [STARTUP RECOVERY] Recovered missing session: {session_str}")
                    else:
                        logging.error(f"❌ [STARTUP RECOVERY] Failed to parse times for recovered session: {session_str}")
                
                # Save updated sessions
                save_scheduled_sessions(startup_scheduled_sessions)
                save_past_scheduled_sessions(startup_past_sessions)
                logging.info(f"✅ [STARTUP RECOVERY] Session recovery complete - added {len(missing_from_tracking)} session(s)")
            
            # Summary
            total_stored = len(startup_scheduled_sessions) + len(startup_past_sessions)
            logging.info(f"✅ [STARTUP UPDATE] Bayesian update complete: {len(startup_current_sessions)} on website, {total_stored} total stored ({len(startup_scheduled_sessions)} scheduled, {len(startup_past_sessions)} past)")
            logging.info("────────────────────────────────────────────────────────────────────")
            
        else:
            logging.warning("🔴 [STARTUP SCRAPE] Failed to fetch website data for Bayesian update - proceeding with stored data")
            
    except Exception as e:
        logging.exception(f"🔴 [STARTUP SCRAPE] Error during Bayesian update: {e} - proceeding with stored data")
    
    if x_enabled:
        logging.info("🔍 SCRAPER STATUS")
        logging.info("  X.com scraper ENABLED (checks at 11am/8pm)")
    else:
        logging.info("🔍 SCRAPER STATUS")
        logging.info("  X.com scraper DISABLED (BEARER_TOKEN not configured)")

    logging.info("────────────────────────────────────────────────────────────────────")

    while True:
        # Fetch from Octopus website (scraper_website - always runs)
        html_content = fetch_page_content(url)
        current_sessions = []
        session_type = None
        website_sessions = []
        
        if html_content:
            logging.debug(f"[SCRAPER_WEBSITE] Fetched HTML content length: {len(html_content)}")
            session_type, website_sessions = extract_sessions(html_content)
            current_sessions.extend(website_sessions)
            logging.info(f"🔍 [WEBSITE SCRAPER] Fetched HTML ({len(html_content)}KB)")
            logging.info(f"🔵 [WEBSITE SCRAPER] Extracted {len(website_sessions)} session(s):")
            for i, session in enumerate(website_sessions):
                prefix = "└─" if i == len(website_sessions) - 1 else "├─"
                logging.info(f"  {prefix} {session}")
        else:
            logging.warning("🔴 [WEBSITE SCRAPER] Failed to fetch content from Octopus website")
        
        # Fetch from X.com only during scheduled check times (11am and 8pm) - OPTIONAL
        x_sessions = []
        new_x_sessions = []
        if x_enabled and should_check_x():
            try:
                logging.info("🟣 [X SCRAPER] Check window active - fetching from X.com")
                x_session_type, x_sessions = fetch_and_extract_sessions()
                
                # Only add sessions not already found by scraper_website
                new_x_sessions = [s for s in x_sessions if s not in website_sessions]
                if new_x_sessions:
                    current_sessions.extend(new_x_sessions)
                    logging.info(f"🟢 [X SCRAPER] Found {len(new_x_sessions)} NEW session(s) from X.com:")
                    for i, session in enumerate(new_x_sessions):
                        prefix = "└─" if i == len(new_x_sessions) - 1 else "├─"
                        logging.info(f"  {prefix} {session}")
                else:
                    logging.info(f"🟡 [X SCRAPER] Extracted {len(x_sessions)} session(s) from X.com, but all already found by website scraper")
                
                if x_session_type == 'next':
                    session_type = 'next'  # Override if X has next
                
                # Log X.com scraper data for tracking
                log_x_scraper_data(website_sessions, x_sessions, new_x_sessions)
                    
            except Exception as e:
                logging.warning(f"🔴 [X SCRAPER] Error fetching from X.com (non-critical): {e}")
                logging.info("  └─ Continuing with website data only")
        elif x_enabled:
            logging.debug(f"🔍 [SCRAPER_X] Outside X.com check window (current hour: {datetime.now().hour}). Skipping X.com check.")
        
        # Log summary of what was found
        logging.info(f"📊 SUMMARY")
        logging.info(f"  ├─ Total unique sessions: {len(current_sessions)}")
        logging.info(f"  ├─ Website: {len(website_sessions)} sessions")
        logging.info(f"  ├─ X.com: {len(x_sessions)} sessions")
        logging.info(f"  └─ New from X: {len(new_x_sessions)} sessions")
        
        logging.info("────────────────────────────────────────────────────────────────────")
        
        # Log mode status (TEST_MODE, SINGLE_RUN)
        if test_mode or single_run:
            if test_mode:
                logging.info("🟠 TEST MODE ACTIVE - Processing all sessions for testing")
                logging.info("  ├─ Sessions unchanged will be re-processed for testing")
                logging.info("  ├─ Existing notification flags will be reset")
                logging.info("  └─ All notifications will be sent regardless of prior state")
            if single_run:
                logging.info("🔸 SINGLE RUN MODE - Will exit after this cycle")
            logging.info("────────────────────────────────────────────────────────────────────")
        
        if current_sessions:
            is_next = (session_type == 'next')
            logging.info(f"📋 Total extracted sessions: {current_sessions} (type: {session_type})")
            
            # Check if sessions are the same as last time
            last_sessions = load_last_extracted_sessions()
            
            # Compare sets to see if there are any new sessions
            current_set = set(current_sessions)
            last_set = set(last_sessions)
            new_sessions = current_set - last_set
            
            # Load existing scheduled sessions (needed for all processing)
            scheduled_sessions = load_scheduled_sessions()
            past_sessions = load_past_scheduled_sessions()
            
            # Get list of already tracked session strings for quick lookup
            tracked_session_strings = set(s['session'] for s in scheduled_sessions)
            past_session_strings = set(s['session'] for s in past_sessions)
            
            sessions_added = []
            
            # Process sessions that need to be added (either new or missing from tracking)
            sessions_to_process = []
            
            if new_sessions or test_mode:
                # In normal mode, only process new sessions
                # In test mode, process all sessions for re-notification
                sessions_to_process = current_sessions if test_mode else list(new_sessions)
            else:
                # Check if any currently extracted sessions are missing from tracking
                # This handles cases where sessions were lost from scheduled_sessions.json
                missing_sessions = []
                for session_str in current_sessions:
                    if session_str not in tracked_session_strings and session_str not in past_session_strings:
                        missing_sessions.append(session_str)
                
                if missing_sessions:
                    logging.warning(f"🟠 Found {len(missing_sessions)} session(s) currently on website but missing from tracking:")
                    for i, session in enumerate(missing_sessions):
                        prefix = "└─" if i == len(missing_sessions) - 1 else "├─"
                        logging.warning(f"  {prefix} {session}")
                    sessions_to_process = missing_sessions
                else:
                    logging.info("🟡 No new sessions detected")
            
            # Process any sessions that need to be added
            if sessions_to_process:
                if new_sessions:
                    logging.info(f"🟢 NEW DETECTIONS:")
                    for i, session in enumerate(new_sessions):
                        prefix = "└─" if i == len(new_sessions) - 1 else "├─"
                        logging.info(f"  {prefix} {session}")
                
                # Process each session that needs to be added
                for session_str in sessions_to_process:
                    # In TEST_MODE, allow reprocessing by resetting flags BEFORE checking if tracked
                    if test_mode and session_str in tracked_session_strings:
                        existing = next(s for s in scheduled_sessions if s['session'] == session_str)
                        existing['notified'] = False
                        existing['reminder_sent'] = False
                        existing['end_sent'] = False
                        continue  # Skip adding duplicate, but flags are reset for re-notification
                    
                    # Check if already in scheduled or past (skip in normal mode)
                    if session_str in tracked_session_strings:
                        logging.debug(f"Session already in scheduled: {session_str}")
                        continue
                    
                    if session_str in past_session_strings:
                        logging.debug(f"⏱️ Session already in past: {session_str}")
                        continue
                    
                    # Parse times
                    start_time = parse_session_date(session_str)
                    reminder_time = parse_session_to_reminder(session_str)
                    end_time = parse_session_end_date(session_str)
                    end_reminder_time = parse_session_to_end_reminder(session_str)
                    
                    if not start_time or not end_time:
                        logging.warning(f"Failed to parse times for session: {session_str}")
                        continue
                    
                    # Log extracted times for verification
                    duration_hours = (end_time - start_time).total_seconds() / 3600
                    logging.info(f"🔍 PARSING '{session_str}'")
                    logging.info(f"  ├─ Start: {start_time.strftime('%Y-%m-%d %H:%M')} ({start_time.strftime('%I:%M %p')})")
                    logging.info(f"  ├─ End:   {end_time.strftime('%Y-%m-%d %H:%M')} ({end_time.strftime('%I:%M %p')})")
                    logging.info(f"  └─ Duration: {duration_hours:.1f}h")
                    
                    # Warn if duration seems unusual
                    if duration_hours > 4:
                        logging.warning(f"  ⚠️ Duration seems unusually long ({duration_hours:.1f} hours) - please verify parsing!")
                    elif duration_hours < 0:
                        logging.error(f"  ❌ End time is before start time! Parsing error detected.")
                        continue
                    
                    # Create session dict
                    session_data = {
                        'session': session_str,
                        'start_time': start_time.isoformat(),
                        'reminder_time': reminder_time.isoformat() if reminder_time else None,
                        'end_time': end_time.isoformat(),
                        'end_reminder_time': end_reminder_time.isoformat() if end_reminder_time else None,
                        'notified': False,
                        'reminder_sent': False,
                        'end_sent': False
                    }
                    
                    # Add to scheduled and track
                    scheduled_sessions.append(session_data)
                    tracked_session_strings.add(session_str)
                    sessions_added.append(session_str)
                    logging.info(f"✓ Added new session to queue: {session_str}")
                    
                    # Send initial notification for upcoming sessions OR if in TEST_MODE
                    if is_next or test_mode:
                        # Use the new notification format from notifier.py
                        message = (
                            f"📣 Free Electric Session Scheduled: {session_str}\n"
                            f"- Verify: https://octopus.energy/free-electricity/\n"
                            f"  or https://x.com/savingsessions"
                        )
                        send_discord_notification(message, "date_time")
                        session_data['notified'] = True
                        logging.info(f"📣 NOTIFICATION SENT")
                        logging.info(f"  └─ Free Electric Session: {session_str}")
                        logging.info(f"     Verify: https://octopus.energy/free-electricity/ | https://x.com/savingsessions")
                        logging.info(f"✓ Initial alert dispatched")
                    else:
                        logging.info(f"⏭️ Skipped notification for {session_str} (type: {session_type}, test_mode: {test_mode})")
                    
                    # Update last sent session log
                    update_last_sent_session(session_str)
                
                # Save scheduled sessions
                save_scheduled_sessions(scheduled_sessions)
                save_past_scheduled_sessions(past_sessions)
                
                # Log summary
                if sessions_added:
                    logging.info(f"📊 QUEUE UPDATE")
                    logging.info(f"  ├─ {len(sessions_added)} sessions added")
                    logging.info(f"  └─ Total queued: {len(scheduled_sessions)}")
            
            # Check and send notifications (reminders, end states) - EVERY HOUR
            check_and_send_notifications()
            
            # Show final status of upcoming alerts (moved to end for easy visibility)
            logging.info("────────────────────────────────────────────────────────────────────")
            final_scheduled_sessions = load_scheduled_sessions()
            if final_scheduled_sessions:
                now = datetime.now()
                upcoming_reminders = []
                for session in final_scheduled_sessions:
                    reminder_time = session.get('reminder_time')
                    if reminder_time and not session.get('reminder_sent', False):
                        reminder_dt = datetime.fromisoformat(reminder_time)
                        if reminder_dt > now:
                            upcoming_reminders.append(f"{session['session']} ({reminder_dt.strftime('%m/%d %I:%M%p')})")
                
                if upcoming_reminders:
                    logging.info(f"⏰ UPCOMING REMINDER ALERTS: {len(upcoming_reminders)} pending")
                    for i, reminder in enumerate(upcoming_reminders[:3]):  # Show first 3
                        prefix = "└─" if i == min(2, len(upcoming_reminders) - 1) else "├─"
                        logging.info(f"  {prefix} {reminder}")
                    if len(upcoming_reminders) > 3:
                        logging.info(f"  └─ ... and {len(upcoming_reminders) - 3} more")
                else:
                    logging.info("✅ All scheduled session reminders have been sent")
            
            # Always save current sessions as last extracted (after processing)
            logging.info("────────────────────────────────────────────────────────────────────")
            save_last_extracted_sessions(current_sessions)
            logging.debug(f"💾 [STORAGE] Updated last_extracted_sessions.json with {len(current_sessions)} session(s)")
        
        else:
            logging.error("Failed to fetch HTML content.")
        
        if single_run:
            break
        time.sleep(3600)

if __name__ == "__main__":
    main()