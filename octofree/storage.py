"""
Storage module for managing session data persistence.

This module handles all file I/O operations for the Octofree application,
including loading and saving scheduled sessions, past sessions, and tracking
scraped data. All file operations are thread-safe using a global lock.
"""

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
    """
    Load scheduled sessions from JSON file with validation and deduplication.
    
    Thread-safe operation that reads the scheduled_sessions.json file,
    validates each entry, removes duplicates, and filters out malformed data.
    Logs warnings for any data quality issues found.
    
    Returns:
        list: List of unique, validated session dictionaries. Each dict contains:
            - session (str): Session description (e.g., "9-10pm, Friday 24th October")
            - start_time (str): ISO format start datetime
            - end_time (str): ISO format end datetime
            - reminder_time (str): ISO format reminder datetime
            - end_reminder_time (str): ISO format end reminder datetime
            - notified (bool): Whether initial notification was sent
            - reminder_sent (bool): Whether reminder notification was sent
            - end_sent (bool): Whether end notification was sent
            Returns empty list if file doesn't exist or is invalid.
    """
    if os.path.exists(SCHEDULED_SESSIONS_FILE):
        with json_lock:  # Ensure atomic read with respect to writes
            try:
                with open(SCHEDULED_SESSIONS_FILE, 'r') as f:
                    sessions = json.load(f)
                    
                    # Validate and deduplicate sessions
                    seen = set()
                    unique_sessions = []
                    malformed_count = 0
                    
                    for i, session in enumerate(sessions):
                        # Defensive validation: ensure entry is a dict with 'session' key
                        if not isinstance(session, dict):
                            logging.debug(f"[STORAGE] Skipping malformed entry at index {i}: not a dict")
                            malformed_count += 1
                            continue
                        
                        session_str = session.get('session', '')
                        if not session_str or not isinstance(session_str, str):
                            logging.debug(f"[STORAGE] Skipping entry at index {i}: missing or invalid 'session' key")
                            malformed_count += 1
                            continue
                        
                        # Deduplicate based on session string
                        if session_str not in seen:
                            seen.add(session_str)
                            unique_sessions.append(session)
                        else:
                            logging.debug(f"[STORAGE] Removing duplicate session during load: {session_str}")
                    
                    # Log summary of cleanup
                    duplicates_removed = len(sessions) - len(unique_sessions) - malformed_count
                    if malformed_count > 0:
                        logging.warning(f"[STORAGE] Removed {malformed_count} malformed entry/entries from scheduled_sessions.json")
                    if duplicates_removed > 0:
                        logging.warning(f"[STORAGE] Deduplicated {duplicates_removed} duplicate session(s) from scheduled_sessions.json")
                    
                    return unique_sessions
            except (json.JSONDecodeError, ValueError) as e:
                logging.warning(f"Invalid or empty JSON in {SCHEDULED_SESSIONS_FILE}: {e}. Treating as empty.")
                return []
    return []

def save_scheduled_sessions(sessions):
    """
    Save scheduled sessions to JSON file in a thread-safe manner.
    
    Args:
        sessions (list): List of session dictionaries to save.
            Each dictionary should contain session metadata and notification states.
    """
    with json_lock:
        with open(SCHEDULED_SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, default=str)

def load_past_scheduled_sessions():
    """
    Load past (completed) sessions from JSON file with validation and deduplication.
    
    Thread-safe operation that reads the past_scheduled_sessions.json file,
    validates each entry, removes duplicates, and filters out malformed data.
    Past sessions are retained for historical tracking and preventing re-notification.
    
    Returns:
        list: List of unique, validated past session dictionaries with same structure
            as load_scheduled_sessions(). Returns empty list if file doesn't exist
            or is invalid.
    """
    if os.path.exists(PAST_SCHEDULED_SESSIONS_FILE):
        with json_lock:  # Ensure atomic read with respect to writes
            try:
                with open(PAST_SCHEDULED_SESSIONS_FILE, 'r') as f:
                    sessions = json.load(f)
                    
                    # Validate and deduplicate sessions
                    seen = set()
                    unique_sessions = []
                    malformed_count = 0
                    
                    for i, session in enumerate(sessions):
                        # Defensive validation: ensure entry is a dict with 'session' key
                        if not isinstance(session, dict):
                            logging.debug(f"[STORAGE] Skipping malformed entry at index {i} in past sessions: not a dict")
                            malformed_count += 1
                            continue
                        
                        session_str = session.get('session', '')
                        if not session_str or not isinstance(session_str, str):
                            logging.debug(f"[STORAGE] Skipping entry at index {i} in past sessions: missing or invalid 'session' key")
                            malformed_count += 1
                            continue
                        
                        # Deduplicate based on session string
                        if session_str not in seen:
                            seen.add(session_str)
                            unique_sessions.append(session)
                        else:
                            logging.debug(f"[STORAGE] Removing duplicate past session during load: {session_str}")
                    
                    # Log summary of cleanup
                    duplicates_removed = len(sessions) - len(unique_sessions) - malformed_count
                    if malformed_count > 0:
                        logging.warning(f"[STORAGE] Removed {malformed_count} malformed entry/entries from past_scheduled_sessions.json")
                    if duplicates_removed > 0:
                        logging.warning(f"[STORAGE] Deduplicated {duplicates_removed} duplicate past session(s) from past_scheduled_sessions.json")
                    
                    return unique_sessions
            except (json.JSONDecodeError, ValueError) as e:
                logging.warning(f"Invalid or empty JSON in {PAST_SCHEDULED_SESSIONS_FILE}: {e}. Treating as empty.")
                return []
    return []

def save_past_scheduled_sessions(sessions):
    """
    Save past sessions to JSON file in a thread-safe manner.
    
    Args:
        sessions (list): List of completed session dictionaries to archive.
    """
    with json_lock:
        with open(PAST_SCHEDULED_SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, default=str)

def get_last_sent_session():
    """
    Get the most recently sent session from the log file.
    
    Reads the last_sent_session.txt file and returns the last (most recent) line.
    Used for tracking notification history and preventing duplicate notifications.
    
    Returns:
        str or None: The last session string that was notified, or None if file
            doesn't exist or is empty.
    """
    if os.path.exists(LAST_SESSION_LOG):
        with open(LAST_SESSION_LOG, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if lines:
                return lines[-1]
    return None

def update_last_sent_session(session_str):
    """
    Update the last sent session log file with a new session.
    
    Adds the session to the log if not already present, sorts all sessions
    by date (newest first), and rewrites the file. Thread-safe operation.
    
    Args:
        session_str (str): Session description to add to the log
            (e.g., "9-10pm, Friday 24th October").
    """
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
    """
    Load the list of sessions extracted during the last scraper run.
    
    Thread-safe operation that reads last_extracted_sessions.json and validates
    that it contains a list of non-empty strings. Used for detecting new sessions
    by comparing current extraction results with previous results.
    
    Returns:
        list: List of session strings from the last extraction. Returns empty list
            if file doesn't exist, is invalid, or contains malformed data.
    """
    if os.path.exists(LAST_EXTRACTED_SESSIONS_FILE):
        with json_lock:  # Ensure atomic read with respect to writes
            try:
                with open(LAST_EXTRACTED_SESSIONS_FILE, 'r') as f:
                    sessions = json.load(f)
                    
                    # Validate that it's a list of strings
                    if not isinstance(sessions, list):
                        logging.warning(f"[STORAGE] {LAST_EXTRACTED_SESSIONS_FILE} is not a list. Treating as empty.")
                        return []
                    
                    # Filter and validate entries
                    valid_sessions = []
                    for i, session in enumerate(sessions):
                        if isinstance(session, str) and session.strip():
                            valid_sessions.append(session)
                        else:
                            logging.debug(f"[STORAGE] Skipping invalid entry at index {i} in last_extracted_sessions: {type(session).__name__}")
                    
                    if len(valid_sessions) < len(sessions):
                        logging.warning(f"[STORAGE] Removed {len(sessions) - len(valid_sessions)} invalid entry/entries from last_extracted_sessions.json")
                    
                    return valid_sessions
            except (json.JSONDecodeError, ValueError) as e:
                logging.warning(f"Invalid or empty JSON in {LAST_EXTRACTED_SESSIONS_FILE}: {e}. Treating as empty.")
                return []
    return []

def save_last_extracted_sessions(sessions):
    """
    Save the current extraction results to track for next run comparison.
    
    Thread-safe operation that writes the list of currently extracted sessions
    to last_extracted_sessions.json for use in detecting new sessions on
    subsequent runs.
    
    Args:
        sessions (list): List of session strings extracted in current run.
    """
    with json_lock:
        with open(LAST_EXTRACTED_SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, default=str)

def log_x_scraper_data(website_sessions, x_sessions, new_sessions_found):
    """
    Log X.com scraper activity for performance tracking and comparison.
    
    Records each X.com scraper run to x_scraper_log.json, tracking what sessions
    were found on both the website and X.com, and whether X.com provided any
    unique data. Maintains a rolling log of the last 100 entries to prevent
    unlimited file growth.
    
    Args:
        website_sessions (list): Sessions found on octopus.energy website.
        x_sessions (list): Sessions found on X.com (Twitter).
        new_sessions_found (list): Sessions found on X.com that weren't on website.
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