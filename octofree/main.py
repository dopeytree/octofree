import time
import os
import logging
from scraper import fetch_page_content, extract_sessions
from notifier import check_and_send_notifications, send_discord_notification
from storage import load_scheduled_sessions, save_scheduled_sessions, load_past_scheduled_sessions, save_past_scheduled_sessions, update_last_sent_session, get_last_sent_session
from utils import parse_session_date, parse_session_to_reminder, parse_session_to_end_reminder, parse_session_end_date
from datetime import datetime, timedelta

# Logging configuration (match original, but set to DEBUG for more detail)
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
output_dir = os.path.abspath(os.path.expanduser(os.getenv('OUTPUT_DIR', DEFAULT_OUTPUT_DIR)))
os.makedirs(output_dir, exist_ok=True)
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

def main():
    url = 'https://octopus.energy/free-electricity/'
    single_run = os.getenv('SINGLE_RUN', '').strip().lower() == 'true'
    test_mode = os.getenv('TEST_MODE', '').strip().lower() == 'true'

    while True:
        html_content = fetch_page_content(url)
        if html_content:
            logging.debug(f"Fetched HTML content length: {len(html_content)}")
            current_sessions = extract_sessions(html_content)
            logging.debug(f"Extracted sessions: {current_sessions}")
            
            # Load existing scheduled sessions
            scheduled_sessions = load_scheduled_sessions()
            past_sessions = load_past_scheduled_sessions()
            
            # Process each extracted session
            for session_str in current_sessions:
                # Check if already in scheduled or past
                existing = next((s for s in scheduled_sessions if s['session'] == session_str), None)
                past_existing = next((s for s in past_sessions if s['session'] == session_str), None)
                
                if existing or past_existing:
                    logging.info(f"Session already tracked: {session_str}")
                    continue
                
                # Parse times
                start_time = parse_session_date(session_str)
                reminder_time = parse_session_to_reminder(session_str)
                end_time = parse_session_end_date(session_str)
                end_reminder_time = parse_session_to_end_reminder(session_str)
                
                if not start_time or not end_time:
                    logging.warning(f"Failed to parse times for session: {session_str}")
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
                
                # Add to scheduled
                scheduled_sessions.append(session_data)
                logging.info(f"Added new session: {session_str}")
                
                # Send initial notification (unless TEST_MODE)
                if not test_mode:
                    message = f"📣 Free Electric Session Scheduled: {session_str}"
                    send_discord_notification(message, "date_time")
                    session_data['notified'] = True
                    logging.info(f"Initial notification sent for {session_str}")
                else:
                    logging.info(f"TEST_MODE: Skipped notification for {session_str}")
                
                # Update last sent session log
                update_last_sent_session(session_str)
            
            # Save scheduled sessions
            save_scheduled_sessions(scheduled_sessions)
            save_past_scheduled_sessions(past_sessions)
            
            # Check and send notifications (reminders, end states)
            check_and_send_notifications()
            
        else:
            logging.error("Failed to fetch HTML content.")
        
        if single_run:
            break
        time.sleep(3600)

if __name__ == "__main__":
    main()