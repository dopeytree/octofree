import json
import os
import logging
import threading
from datetime import datetime, timedelta
from utils import parse_session_date  # Import from utils instead of notifier

# Define file paths (use the same logic as in octofree.py)
output_dir = os.path.abspath(os.path.expanduser(os.getenv('OUTPUT_DIR', os.path.join(os.path.dirname(__file__), 'output'))))
SCHEDULED_SESSIONS_FILE = os.path.join(output_dir, 'scheduled_sessions.json')
PAST_SCHEDULED_SESSIONS_FILE = os.path.join(output_dir, 'past_scheduled_sessions.json')
LAST_SESSION_LOG = os.path.join(output_dir, 'last_sent_session.txt')
LAST_EXTRACTED_SESSIONS_FILE = os.path.join(output_dir, 'last_extracted_sessions.json')
X_SCRAPER_LOG = os.path.join(output_dir, 'x_scraper_log.json')

json_lock = threading.Lock()

def load_scheduled_sessions():
    if os.path.exists(SCHEDULED_SESSIONS_FILE):
        try:
            with open(SCHEDULED_SESSIONS_FILE, 'r') as f:
                sessions = json.load(f)
                # Deduplicate sessions based on session string
                seen = set()
                unique_sessions = []
                for session in sessions:
                    session_str = session.get('session', '')
                    if session_str and session_str not in seen:
                        seen.add(session_str)
                        unique_sessions.append(session)
                    elif session_str in seen:
                        logging.debug(f"[STORAGE] Removing duplicate session during load: {session_str}")
                
                if len(unique_sessions) < len(sessions):
                    logging.warning(f"[STORAGE] Deduplicated {len(sessions) - len(unique_sessions)} duplicate session(s) from scheduled_sessions.json")
                
                return unique_sessions
        except (json.JSONDecodeError, ValueError):
            logging.warning(f"Invalid or empty JSON in {SCHEDULED_SESSIONS_FILE}. Treating as empty.")
            return []
    return []

def save_scheduled_sessions(sessions):
    with json_lock:
        with open(SCHEDULED_SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, default=str)

def load_past_scheduled_sessions():
    if os.path.exists(PAST_SCHEDULED_SESSIONS_FILE):
        try:
            with open(PAST_SCHEDULED_SESSIONS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            logging.warning(f"Invalid or empty JSON in {PAST_SCHEDULED_SESSIONS_FILE}. Treating as empty.")
            return []
    return []

def save_past_scheduled_sessions(sessions):
    with json_lock:
        with open(PAST_SCHEDULED_SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, default=str)

def get_last_sent_session():
    if os.path.exists(LAST_SESSION_LOG):
        with open(LAST_SESSION_LOG, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if lines:
                return lines[-1]
    return None

def update_last_sent_session(session_str):
    # Load existing sessions
    sessions = []
    if os.path.exists(LAST_SESSION_LOG):
        with open(LAST_SESSION_LOG, 'r') as f:
            sessions = [line.strip() for line in f.readlines() if line.strip()]
    
    # Add new session if not already present
    if session_str not in sessions:
        sessions.append(session_str)
    
    # Sort by parsed date (newest first), ignoring unparseable ones
    def sort_key(s):
        parsed = parse_session_date(s)
        return parsed if parsed else datetime.min
    
    sessions.sort(key=sort_key, reverse=True)
    
    # Rewrite the file
    with json_lock:
        with open(LAST_SESSION_LOG, 'w') as f:
            for s in sessions:
                f.write(f"{s}\n")

def load_last_extracted_sessions():
    if os.path.exists(LAST_EXTRACTED_SESSIONS_FILE):
        try:
            with open(LAST_EXTRACTED_SESSIONS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            logging.warning(f"Invalid or empty JSON in {LAST_EXTRACTED_SESSIONS_FILE}. Treating as empty.")
            return []
    return []

def save_last_extracted_sessions(sessions):
    with json_lock:
        with open(LAST_EXTRACTED_SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, default=str)

def log_x_scraper_data(website_sessions, x_sessions, new_sessions_found):
    """
    Log X.com scraper activity to a separate JSON file for tracking and comparison.
    This helps monitor scraper_x performance over time.
    """
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'website_sessions': website_sessions,
        'x_sessions': x_sessions,
        'new_sessions_from_x': new_sessions_found,
        'x_provided_unique_data': len(new_sessions_found) > 0
    }
    
    # Load existing log entries
    log_entries = []
    if os.path.exists(X_SCRAPER_LOG):
        try:
            with open(X_SCRAPER_LOG, 'r') as f:
                log_entries = json.load(f)
        except (json.JSONDecodeError, ValueError):
            logging.warning(f"Invalid JSON in {X_SCRAPER_LOG}. Starting fresh.")
            log_entries = []
    
    # Add new entry
    log_entries.append(log_entry)
    
    # Keep only last 100 entries to prevent file from growing too large
    log_entries = log_entries[-100:]
    
    # Save
    with json_lock:
        with open(X_SCRAPER_LOG, 'w') as f:
            json.dump(log_entries, f, indent=2, default=str)
    
    logging.debug(f"[SCRAPER_X] Logged activity to {X_SCRAPER_LOG}")