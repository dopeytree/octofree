import time
import os
import logging
from scraper_website import fetch_page_content, extract_sessions
from scraper_x import fetch_and_extract_sessions
from notifier import check_and_send_notifications, send_discord_notification
from storage import load_scheduled_sessions, save_scheduled_sessions, load_past_scheduled_sessions, save_past_scheduled_sessions, update_last_sent_session, get_last_sent_session, load_last_extracted_sessions, save_last_extracted_sessions, log_x_scraper_data
from utils import parse_session_date, parse_session_to_reminder, parse_session_to_end_reminder, parse_session_end_date
from validator import run_startup_validation
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
    logging.info("Loaded settings:")
    logging.info(f"  DISCORD_WEBHOOK_URL={os.getenv('DISCORD_WEBHOOK_URL')}")
    logging.info(f"  TEST_MODE={os.getenv('TEST_MODE')}")
    logging.info(f"  SINGLE_RUN={os.getenv('SINGLE_RUN')}")
    logging.info(f"  OUTPUT_DIR={output_dir}")

_log_loaded_settings()

def should_check_x():
    """
    Check if current time is during scheduled X.com check windows.
    Returns True at 11am or 8pm (UTC or local time based on system).
    Allows a 1-hour window for each check to avoid missing if script runs slightly off-time.
    Can be overridden by setting TEST_X_SCRAPER=true for testing.
    """
    # Allow override for testing
    if os.getenv('TEST_X_SCRAPER', '').strip().lower() == 'true':
        return True
    
    now = datetime.now()
    hour = now.hour
    # Check if we're in the 11am window (11:00-11:59) or 8pm window (20:00-20:59)
    return hour == 11 or hour == 20

def main():
    url = 'https://octopus.energy/free-electricity/'
    single_run = os.getenv('SINGLE_RUN', '').strip().lower() == 'true'
    test_mode = os.getenv('TEST_MODE', '').strip().lower() == 'true'
    x_enabled = bool(os.getenv('BEARER_TOKEN'))
    
    # Run startup validation and correction on historical data
    logging.info("")
    try:
        run_startup_validation(output_dir)
    except Exception:
        logging.exception("Startup validation encountered an error; continuing")
    logging.info("")
    
    if x_enabled:
        logging.info("X.com scraper (scraper_x) is ENABLED - will check X.com at 11am and 8pm")
    else:
        logging.info("X.com scraper (scraper_x) is DISABLED - BEARER_TOKEN not configured")

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
            logging.info(f"[SCRAPER_WEBSITE] Extracted {len(website_sessions)} session(s) from Octopus website: {website_sessions} (type: {session_type})")
        else:
            logging.warning("[SCRAPER_WEBSITE] Failed to fetch content from Octopus website")
        
        # Fetch from X.com only during scheduled check times (11am and 8pm) - OPTIONAL
        x_sessions = []
        new_x_sessions = []
        if x_enabled and should_check_x():
            try:
                logging.info("[SCRAPER_X] X.com check window - fetching from X.com")
                x_session_type, x_sessions = fetch_and_extract_sessions()
                
                # Only add sessions not already found by scraper_website
                new_x_sessions = [s for s in x_sessions if s not in website_sessions]
                if new_x_sessions:
                    current_sessions.extend(new_x_sessions)
                    logging.info(f"[SCRAPER_X] Found {len(new_x_sessions)} NEW session(s) from X.com: {new_x_sessions}")
                else:
                    logging.info(f"[SCRAPER_X] Extracted {len(x_sessions)} session(s) from X.com, but all already found by website scraper")
                
                if x_session_type == 'next':
                    session_type = 'next'  # Override if X has next
                
                # Log X.com scraper data for tracking
                log_x_scraper_data(website_sessions, x_sessions, new_x_sessions)
                    
            except Exception as e:
                logging.warning(f"[SCRAPER_X] Error fetching from X.com (non-critical): {e}")
                logging.info("[SCRAPER_X] Continuing with website data only")
        elif x_enabled:
            logging.debug(f"[SCRAPER_X] Outside X.com check window (current hour: {datetime.now().hour}). Skipping X.com check.")
        
        # Log summary of what was found
        logging.info(f"SUMMARY: Total {len(current_sessions)} unique session(s) to process (Website: {len(website_sessions)}, X.com: {len(x_sessions)}, New from X.com: {len(new_x_sessions)})")
        
        if current_sessions:
            is_next = (session_type == 'next')
            logging.debug(f"Total extracted sessions: {current_sessions} (type: {session_type})")
            
            # Check if sessions are the same as last time
            last_sessions = load_last_extracted_sessions()
            
            # Compare sets to see if there are any new sessions
            current_set = set(current_sessions)
            last_set = set(last_sessions)
            new_sessions = current_set - last_set
            
            if not new_sessions and not test_mode:
                logging.info("No new session planned")
            else:
                if test_mode and not new_sessions:
                    logging.info("[TEST_MODE] Sessions unchanged, but will process anyway for testing")
                elif new_sessions:
                    logging.info(f"New session(s) detected: {list(new_sessions)}")
                
                # Load existing scheduled sessions
                scheduled_sessions = load_scheduled_sessions()
                past_sessions = load_past_scheduled_sessions()
                
                # Get list of already tracked session strings for quick lookup
                tracked_session_strings = set(s['session'] for s in scheduled_sessions)
                past_session_strings = set(s['session'] for s in past_sessions)
                
                sessions_added = []
                
                # Process each extracted session
                for session_str in current_sessions:
                    # Check if already in scheduled or past
                    if session_str in tracked_session_strings:
                        logging.debug(f"Session already in scheduled: {session_str}")
                        continue
                    
                    if session_str in past_session_strings:
                        logging.debug(f"Session already in past: {session_str}")
                        continue
                    
                    # In TEST_MODE, allow reprocessing by resetting flags
                    if test_mode and session_str in tracked_session_strings:
                        logging.info(f"[TEST_MODE] Resetting notification flags for: {session_str}")
                        existing = next(s for s in scheduled_sessions if s['session'] == session_str)
                        existing['notified'] = False
                        existing['reminder_sent'] = False
                        existing['end_sent'] = False
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
                    logging.info(f"PARSED TIMES for '{session_str}':")
                    logging.info(f"  Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ({start_time.strftime('%I:%M %p')})")
                    logging.info(f"  End:   {end_time.strftime('%Y-%m-%d %H:%M:%S')} ({end_time.strftime('%I:%M %p')})")
                    logging.info(f"  Duration: {duration_hours:.1f} hours")
                    
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
                        if test_mode:
                            logging.info(f"[TEST_MODE] Initial notification sent for {session_str}")
                        else:
                            logging.info(f"✓ Initial notification sent for {session_str}")
                    else:
                        logging.info(f"Skipped notification for {session_str} (type: {session_type}, test_mode: {test_mode})")
                    
                    # Update last sent session log
                    update_last_sent_session(session_str)
                
                # Save scheduled sessions
                save_scheduled_sessions(scheduled_sessions)
                save_past_scheduled_sessions(past_sessions)
                
                # Log summary
                if sessions_added:
                    logging.info(f"✓ Session queue updated: {len(sessions_added)} session(s) added")
                    logging.info(f"✓ Total queued sessions: {len(scheduled_sessions)}")
                
                # Check and send notifications (reminders, end states)
                check_and_send_notifications()
            
            # Always save current sessions as last extracted (after processing)
            save_last_extracted_sessions(current_sessions)
            logging.debug(f"[STORAGE] Updated last_extracted_sessions.json with {len(current_sessions)} session(s)")
        
        else:
            logging.error("Failed to fetch HTML content.")
        
        if single_run:
            break
        time.sleep(3600)

if __name__ == "__main__":
    main()