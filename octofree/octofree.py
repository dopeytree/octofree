import requests
import re
import os
import time
from datetime import datetime, timedelta
import threading
import json  # Added for JSON handling
from dotenv import load_dotenv
import logging


# Load environment variables from .env file in project root or octofree folder
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), 'settings.env'))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Discord webhook URL from environment
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')


# Set up logging to file and console in octofree/output/
# Allow overriding the output directory via environment (useful for Docker bind-mounts)
# If OUTPUT_DIR is not set, default to the repository's ./output folder to preserve
# existing behavior when running locally.
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
output_dir = os.getenv('OUTPUT_DIR', DEFAULT_OUTPUT_DIR)

# Expand user (~) and resolve relative paths to absolute paths
output_dir = os.path.abspath(os.path.expanduser(output_dir))
os.makedirs(output_dir, exist_ok=True)
log_file = os.path.join(output_dir, 'octofree.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Log the loaded configuration so the Docker image (or any run) records what was used
def _log_loaded_settings():
    try:
        # Read the key settings we care about
        discord = os.getenv('DISCORD_WEBHOOK_URL')
        test_mode = os.getenv('TEST_MODE')
        single_run = os.getenv('SINGLE_RUN')

        # Use logging.info so it goes to both console and the log file
        logging.info(f"DISCORD_WEBHOOK_URL={discord}")
        logging.info(f"TEST_MODE={test_mode}")
        logging.info(f"SINGLE_RUN={single_run}")
        logging.info(f"OUTPUT_DIR={output_dir}")
        # Rely on the configured logging handlers to write these values to the log file/console.
    except Exception as e:
        logging.error(f"Failed to log loaded settings: {e}")

# Immediately log settings on module load/startup
_log_loaded_settings()

# File to track the last session(s)
LAST_SESSION_LOG = os.path.join(output_dir, 'last_sent_session.txt')

# New file for tracking scheduled sessions
SCHEDULED_SESSIONS_FILE = os.path.join(output_dir, 'scheduled_sessions.json')

# New file for tracking past scheduled sessions
PAST_SCHEDULED_SESSIONS_FILE = os.path.join(output_dir, 'past_scheduled_sessions.json')

def fetch_page_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Error fetching page: {e}")
        return None

# Read the last session from the log file

def get_last_sent_session():
    if os.path.exists(LAST_SESSION_LOG):
        # Read the history file and return the most recent non-empty line
        with open(LAST_SESSION_LOG, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if lines:
                return lines[-1]
    return None

def parse_session_date(session_str):
    """
    Parse the session string to extract a datetime for sorting.
    Assumes format like '12-2pm, Saturday 4th October'.
    Returns a datetime object, or None if parsing fails.
    """
    parts = session_str.split(',')
    if len(parts) != 2:
        return None
    time_part = parts[0].strip()  # e.g., '12-2pm'
    date_part = parts[1].strip()  # e.g., 'Saturday 4th October'
    
    # Remove ordinal suffix from date
    date_part = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_part, flags=re.IGNORECASE)
    
    # Extract start time (before the dash)
    start_time_str = time_part.split('-')[0].strip()  # e.g., '12'
    match = re.match(r'(\d+)(am|pm)?', start_time_str.lower())
    if not match:
        return None
    hour = int(match.group(1))
    ampm = match.group(2) or ('pm' if hour == 12 else 'am')
    if ampm == 'pm' and hour != 12:
        hour += 12
    elif ampm == 'am' and hour == 12:
        hour = 0
    minute = 0  # Assume on the hour
    
    # Parse date with current year
    current_year = datetime.now().year
    date_str_full = f"{date_part} {current_year}"
    try:
        date_obj = datetime.strptime(date_str_full, '%A %d %B %Y')
    except ValueError:
        return None
    
    # Combine into session start datetime
    return date_obj.replace(hour=hour, minute=minute)

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
        dt = parse_session_date(s)
        return dt if dt else datetime.min  # Unparseable go to the end
    
    sessions.sort(key=sort_key, reverse=True)
    
    # Rewrite the file
    with open(LAST_SESSION_LOG, 'w') as f:
        for session in sessions:
            f.write(session + '\n')

# Discord notification function
def send_discord_notification(message, notification_type="general"):
    if not DISCORD_WEBHOOK_URL:
        logging.error("ERROR: DISCORD_WEBHOOK_URL environment variable must be set.")
        return
    data = {
        "content": message,  # Removed the automatic 🕰️ prefix
        "username": "🐙 Octopus - Free Electric!!! ⚡️"
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        logging.info(f"{notification_type} notification sent successfully: {message}")
    except Exception as e:
        logging.error(f"Error sending notification: {e}")

def parse_session_to_reminder(session_str):
    """
    Parse the session string to extract the reminder time (5 minutes before start).
    Assumes format like '12-2pm, Saturday 4th October'.
    Returns a datetime object for the reminder, or None if parsing fails or time is past.
    """
    parts = session_str.split(',')
    if len(parts) != 2:
        return None
    time_part = parts[0].strip()  # e.g., '12-2pm'
    date_part = parts[1].strip()  # e.g., 'Saturday 4th October'
    
    # Remove ordinal suffix from date
    date_part = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_part, flags=re.IGNORECASE)
    
    # Extract start time (before the dash)
    start_time_str = time_part.split('-')[0].strip()  # e.g., '12'
    match = re.match(r'(\d+)(am|pm)?', start_time_str.lower())
    if not match:
        return None
    hour = int(match.group(1))
    ampm = match.group(2) or ('pm' if hour == 12 else 'am')
    if ampm == 'pm' and hour != 12:
        hour += 12
    elif ampm == 'am' and hour == 12:
        hour = 0
    minute = 0  # Assume on the hour
    
    # Parse date with current year
    current_year = datetime.now().year
    date_str_full = f"{date_part} {current_year}"
    try:
        date_obj = datetime.strptime(date_str_full, '%A %d %B %Y')
    except ValueError:
        return None
    
    # Combine into session start datetime
    session_start = date_obj.replace(hour=hour, minute=minute)
    now = datetime.now()
    if session_start <= now:
        return None  # Session already started or in past
    reminder_time = session_start - timedelta(minutes=5)
    if reminder_time <= now:
        return None  # Reminder time already past
    return reminder_time

def parse_session_to_end_reminder(session_str):
    """
    Parse the session string to extract the end reminder time (5 minutes before end).
    Assumes format like '12-2pm, Saturday 4th October'.
    Returns a datetime object for the end reminder, or None if parsing fails or time is past.
    """
    parts = session_str.split(',')
    if len(parts) != 2:
        return None
    time_part = parts[0].strip()  # e.g., '12-2pm'
    date_part = parts[1].strip()  # e.g., 'Saturday 4th October'
    
    # Remove ordinal suffix from date
    date_part = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_part, flags=re.IGNORECASE)
    
    # Extract end time (after the dash)
    end_time_str = time_part.split('-')[1].strip()  # e.g., '2pm'
    match = re.match(r'(\d+)(am|pm)?', end_time_str.lower())
    if not match:
        return None
    hour = int(match.group(1))
    ampm = match.group(2) or ('pm' if hour == 12 else 'am')
    if ampm == 'pm' and hour != 12:
        hour += 12
    elif ampm == 'am' and hour == 12:
        hour = 0
    minute = 0  # Assume on the hour
    
    # Parse date with current year
    current_year = datetime.now().year
    date_str_full = f"{date_part} {current_year}"
    try:
        date_obj = datetime.strptime(date_str_full, '%A %d %B %Y')
    except ValueError:
        return None
    
    # Combine into session end datetime
    session_end = date_obj.replace(hour=hour, minute=minute)
    now = datetime.now()
    if session_end <= now:
        return None
    end_reminder_time = session_end - timedelta(minutes=5)
    if end_reminder_time <= now:
        return None
    return end_reminder_time

def parse_session_end_date(session_str):
    """
    Parse the session string to extract the end datetime.
    Assumes format like '12-2pm, Saturday 4th October'.
    Returns a datetime object for the end time, or None if parsing fails.
    """
    parts = session_str.split(',')
    if len(parts) != 2:
        return None
    time_part = parts[0].strip()  # e.g., '12-2pm'
    date_part = parts[1].strip()  # e.g., 'Saturday 4th October'
    
    # Remove ordinal suffix from date
    date_part = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_part, flags=re.IGNORECASE)
    
    # Extract end time (after the dash)
    end_time_str = time_part.split('-')[1].strip()  # e.g., '2pm'
    match = re.match(r'(\d+)(am|pm)?', end_time_str.lower())
    if not match:
        return None
    hour = int(match.group(1))
    ampm = match.group(2) or ('pm' if hour == 12 else 'am')
    if ampm == 'pm' and hour != 12:
        hour += 12
    elif ampm == 'am' and hour == 12:
        hour = 0
    minute = 0  # Assume on the hour
    
    # Parse date with current year
    current_year = datetime.now().year
    date_str_full = f"{date_part} {current_year}"
    try:
        date_obj = datetime.strptime(date_str_full, '%A %d %B %Y')
    except ValueError:
        return None
    
    # Combine into session end datetime
    return date_obj.replace(hour=hour, minute=minute)

def load_scheduled_sessions():
    if os.path.exists(SCHEDULED_SESSIONS_FILE):
        try:
            with open(SCHEDULED_SESSIONS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            # If file is empty or invalid, return empty list
            logging.warning(f"Invalid or empty JSON in {SCHEDULED_SESSIONS_FILE}. Treating as empty.")
            return []
    return []

def save_scheduled_sessions(sessions):
    with open(SCHEDULED_SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f, default=str)  # Use default=str for datetime serialization

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
    with open(PAST_SCHEDULED_SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f, default=str)

def extract_sessions(html_content):
    sessions = []
    # Try to find "Next Sessions:" first (for multiple)
    match = re.search(r'Next\s+Sessions?:', html_content, re.IGNORECASE)
    if match:
        start_pos = match.end()
        # Find the end of this section (next heading or double newline or end)
        end_match = re.search(r'<h\d[^>]*>', html_content[start_pos:], re.IGNORECASE)
        end_pos = end_match.start() if end_match else len(html_content) - start_pos
        block = html_content[start_pos:start_pos + end_pos]
        # Replace <br> with \n to handle line breaks
        block = re.sub(r'<br\s*/?>', '\n', block, flags=re.IGNORECASE)
        # Remove HTML tags
        text_block = re.sub(r'<[^>]+>', '', block).strip()
        # Split by newlines or common separators to avoid concatenation
        potential_sessions = re.split(r'\n|Next|Power Tower', text_block)
        for part in potential_sessions:
            part = part.strip()
            if part:
                # Use regex findall to extract valid session strings from each part
                found = re.findall(r'\d+(?:am|pm)?-\d+(?:am|pm)?,\s*\w+\s*\d+(?:st|nd|rd|th)?\s*\w+', part, re.IGNORECASE)
                sessions.extend(found)
    else:
        # Fallback to old single session logic
        match = re.search(r'Next(?:\s+\w+)*\s+Sessions?:\s*([^<\n]+)', html_content, re.IGNORECASE)
        if match:
            session_raw = match.group(1).strip()
            session_clean = re.sub(r'<[^>]+>', '', session_raw)
            # Split if multiple are concatenated
            found = re.findall(r'\d+(?:am|pm)?-\d+(?:am|pm)?,\s*\w+\s*\d+(?:st|nd|rd|th)?\s*\w+', session_clean, re.IGNORECASE)
            sessions.extend(found)
    # Remove duplicates and clean
    sessions = list(set(sessions))
    return sessions

# Loop settings

active_timers = []  # Global list to keep references to active timers

import threading

# Lock for thread-safe JSON access
json_lock = threading.Lock()

def get_start_time_str(session_str):
    """
    Extract the start time string from the session string.
    Assumes format like '12-2pm, Saturday 4th October'.
    Returns the start time string, e.g., '12pm', or None if parsing fails.
    """
    parts = session_str.split(',')
    if len(parts) != 2:
        return None
    time_part = parts[0].strip()  # e.g., '12-2pm'
    start_time_str = time_part.split('-')[0].strip()  # e.g., '12pm'
    return start_time_str

def get_end_time_str(session_str):
    """
    Extract the end time string from the session string.
    Assumes format like '12-2pm, Saturday 4th October'.
    Returns the end time string, e.g., '2pm', or None if parsing fails.
    """
    parts = session_str.split(',')
    if len(parts) != 2:
        return None
    time_part = parts[0].strip()  # e.g., '12-2pm'
    end_time_str = time_part.split('-')[1].strip()  # e.g., '2pm'
    return end_time_str

def check_and_send_notifications():
    """Check and send pending notifications based on current time."""
    sessions = load_scheduled_sessions()
    now = datetime.now()
    for session in sessions:
        # Initial notification
        if not session['notified']:
            send_and_update(session, sessions, 'notified', f"🕰️ {session['session']}", "date_time")
        
        # Reminder notification
        if session.get('reminder_time') and not session['reminder_sent']:
            try:
                reminder_dt = datetime.strptime(session['reminder_time'], '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                try:
                    reminder_dt = datetime.strptime(session['reminder_time'], '%y-%m-%dT%H:%M:%S')
                except ValueError:
                    logging.error(f"Invalid reminder_time format for session {session['session']}: {session['reminder_time']}")
                    continue
            if now >= reminder_dt:
                start_time_str = None
                if session.get('start_time'):
                    try:
                        start_dt = datetime.strptime(session['start_time'], '%Y-%m-%dT%H:%M:%S')
                        start_time_str = start_dt.strftime('%-I%p').lower()
                    except ValueError:
                        pass
                message = f"📣 T-5mins to Delta! - {start_time_str}" if start_time_str else "📣 T-5mins to Delta!"
                send_and_update(session, sessions, 'reminder_sent', message, "5min_delta")
        
        # End notification
        if session.get('end_reminder_time') and not session['end_sent']:
            try:
                end_dt = datetime.strptime(session['end_reminder_time'], '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                try:
                    end_dt = datetime.strptime(session['end_reminder_time'], '%y-%m-%dT%H:%M:%S')
                except ValueError:
                    logging.error(f"Invalid end_reminder_time format for session {session['session']}: {session['end_reminder_time']}")
                    continue
            if now >= end_dt and now - end_dt <= timedelta(minutes=5):
                # Send only if within 5 minutes
                end_time_str = None
                if session.get('end_time'):
                    try:
                        end_dt_parsed = datetime.strptime(session['end_time'], '%Y-%m-%dT%H:%M:%S')
                        end_time_str = end_dt_parsed.strftime('%-I%p').lower()
                    except ValueError:
                        pass
                message = f"🐰 End State - {end_time_str}" if end_time_str else "🐰 End State"
                send_and_update(session, sessions, 'end_sent', message, "end_state")

def send_and_update(session, sessions_list, flag_key, message, notification_type):
    """Send notification and update/save the session flag."""
    send_discord_notification(message, notification_type)
    session[flag_key] = True
    with json_lock:
        save_scheduled_sessions(sessions_list)

def main():
    url = 'https://octopus.energy/free-electricity/'
    single_run = os.getenv('SINGLE_RUN', '').strip().lower() == 'true'
    test_mode = os.getenv('TEST_MODE', '').strip().lower() == 'true'

    while True:
        html_content = fetch_page_content(url)
        if html_content:
            logging.debug(f"Fetched HTML content length: {len(html_content)}")  # Debug log for fetch success
            current_sessions = extract_sessions(html_content)
            logging.debug(f"Extracted sessions: {current_sessions}")  # Debug log for extraction results
            stored_sessions = load_scheduled_sessions()
            stored_session_strs = {s['session'] for s in stored_sessions}
            
            # Validate and re-parse times for existing sessions if invalid, and add missing start_time/end_time/reminder_times
            now = datetime.now()
            for session in stored_sessions:
                session_str = session['session']
                start_time = None
                end_time = None
                if session.get('start_time'):
                    try:
                        start_time = datetime.strptime(session['start_time'], '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        pass
                if session.get('end_time'):
                    try:
                        end_time = datetime.strptime(session['end_time'], '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        pass
                if not start_time:
                    start_time = parse_session_date(session_str)
                    if start_time:
                        session['start_time'] = start_time.strftime('%Y-%m-%dT%H:%M:%S')
                if not end_time:
                    end_time = parse_session_end_date(session_str)
                    if end_time:
                        session['end_time'] = end_time.strftime('%Y-%m-%dT%H:%M:%S')
        
                # Calculate reminder_time as start_time - 5 mins if not present or invalid
                if start_time and (not session.get('reminder_time') or session['reminder_time'] is None):
                    reminder_time = start_time - timedelta(minutes=5)
                    if reminder_time > now:
                        session['reminder_time'] = reminder_time.strftime('%Y-%m-%dT%H:%M:%S')
                    else:
                        session['reminder_time'] = None
        
                # Calculate end_reminder_time as end_time - 5 mins if not present or invalid
                if end_time and (not session.get('end_reminder_time') or session['end_reminder_time'] is None):
                    end_reminder_time = end_time - timedelta(minutes=5)
                    if end_reminder_time > now:
                        session['end_reminder_time'] = end_reminder_time.strftime('%Y-%m-%dT%H:%M:%S')
                    else:
                        session['end_reminder_time'] = None
    
            save_scheduled_sessions(stored_sessions)
            
            new_sessions_added = False
            for session_str in current_sessions:
                if session_str not in stored_session_strs:
                    # New session: parse times and add to tracking
                    reminder_time = parse_session_to_reminder(session_str)
                    end_reminder_time = parse_session_to_end_reminder(session_str)
                    start_time = parse_session_date(session_str)
                    end_time = parse_session_end_date(session_str)
                    new_session = {
                        'session': session_str,
                        'notified': False,
                        'reminder_sent': False,
                        'end_sent': False,
                        'reminder_time': reminder_time.strftime('%Y-%m-%dT%H:%M:%S') if reminder_time else None,
                        'end_reminder_time': end_reminder_time.strftime('%Y-%m-%dT%H:%M:%S') if end_reminder_time else None,
                        'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S') if start_time else None,
                        'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S') if end_time else None
                    }
                    stored_sessions.append(new_session)
                    logging.info(f"New session added: {session_str}")
                    update_last_sent_session(session_str)  # Update the log file for each new session
                    new_sessions_added = True
            save_scheduled_sessions(stored_sessions)
            
            # Log status if no new sessions but existing ones are monitored
            if not new_sessions_added and stored_sessions:
                logging.info("No new sessions detected, but existing sessions are being monitored.")
            
            # Log notification statuses for all stored sessions
            for session in stored_sessions:
                session_str = session['session']
                reminder_time_str = "not scheduled"
                end_time_str = "not scheduled"
                if session.get('reminder_time'):
                    try:
                        reminder_dt = datetime.strptime(session['reminder_time'], '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        try:
                            reminder_dt = datetime.strptime(session['reminder_time'], '%y-%m-%dT%H:%M:%S')
                        except ValueError:
                            reminder_time_str = "invalid format"
                            continue
                    reminder_time_str = reminder_dt.strftime('%Y-%m-%d %H:%M:%S')
                if session.get('end_reminder_time'):
                    try:
                        end_dt = datetime.strptime(session['end_reminder_time'], '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        try:
                            end_dt = datetime.strptime(session['end_reminder_time'], '%y-%m-%dT%H:%M:%S')
                        except ValueError:
                            end_time_str = "invalid format"
                            continue
                    end_time_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')
                logging.info(f"Session '{session_str}': Delta notification scheduled for {reminder_time_str}, end state notification scheduled for {end_time_str}")
            
            # Move past sessions to past_scheduled_sessions.json instead of deleting
            now = datetime.now()
            past_sessions = load_past_scheduled_sessions()
            sessions_to_remove = []
            for session in stored_sessions:
                if session.get('end_time'):
                    try:
                        end_dt = datetime.strptime(session['end_time'], '%Y-%m-%dT%H:%M:%S')
                        if end_dt < now:
                            # Fill in any null reminder times for complete history
                            if not session.get('reminder_time') and session.get('start_time'):
                                try:
                                    start_dt = datetime.strptime(session['start_time'], '%Y-%m-%dT%H:%M:%S')
                                    reminder_time = start_dt - timedelta(minutes=5)
                                    session['reminder_time'] = reminder_time.strftime('%Y-%m-%dT%H:%M:%S')
                                except ValueError:
                                    pass
                            if not session.get('end_reminder_time') and session.get('end_time'):
                                try:
                                    end_dt_parsed = datetime.strptime(session['end_time'], '%Y-%m-%dT%H:%M:%S')
                                    end_reminder_time = end_dt_parsed - timedelta(minutes=5)
                                    session['end_reminder_time'] = end_reminder_time.strftime('%Y-%m-%dT%H:%M:%S')
                                except ValueError:
                                    pass
                            past_sessions.append(session)
                            sessions_to_remove.append(session)
                    except ValueError:
                        logging.warning(f"Invalid end_time for session {session['session']}, skipping move to past.")
            for session in sessions_to_remove:
                stored_sessions.remove(session)
            save_past_scheduled_sessions(past_sessions)
            save_scheduled_sessions(stored_sessions)
        else:
            logging.error("Failed to fetch HTML content.")  # Explicit error if fetch fails
        
        if single_run:
            break
        time.sleep(3600)

if __name__ == "__main__":
    main()