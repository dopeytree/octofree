import requests
import re
import os
import time
from datetime import datetime, timedelta
import threading
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

def fetch_page_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Error fetching page: {e}")
        return None

def extract_next_session(html_content):
    # Try to extract the session info after 'Next Session:' (now includes optional words like 'TWO HOUR')
    match = re.search(r'Next(?:\s+\w+)*\s+Session:\s*([^<\n]+)', html_content, re.IGNORECASE)
    if match:
        session_raw = match.group(1).strip()
        # Remove any HTML tags from the session string (defensive)
        session_clean = re.sub(r'<[^>]+>', '', session_raw)
        return session_clean
    else:
        logging.warning("No session text found after 'Next Session:'. Regex did not match.")
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

def update_last_sent_session(session_str):
    with open(LAST_SESSION_LOG, 'a') as f:
        f.write(session_str + "\n")

# Discord notification function

def send_discord_notification(message):
    if not DISCORD_WEBHOOK_URL:
        logging.error("ERROR: DISCORD_WEBHOOK_URL environment variable must be set.")
        return
    data = {
        "content": f"🕰️ {message}",
        "username": "🐙 Octopus - Free Electric!!! ⚡️"
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()
        logging.info("Notification sent successfully.")
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
    
    # Extract start time (before the dash)
    start_time_str = time_part.split('-')[0].strip()  # e.g., '12pm'
    match = re.match(r'(\d+)(am|pm)', start_time_str.lower())
    if not match:
        return None
    hour = int(match.group(1))
    ampm = match.group(2)
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

# Loop settings

def main():
    url = 'https://octopus.energy/free-electricity/'
    single_run = os.getenv('SINGLE_RUN', '').strip().lower() == 'true'

    html_content = fetch_page_content(url)
    test_mode = os.getenv('TEST_MODE', '').strip().lower() == 'true'
    if html_content:
        session_str = extract_next_session(html_content)
        if session_str:
            logging.info(f"Found session: {session_str}")
            last_sent = get_last_sent_session()
            if test_mode:
                logging.info("TEST_MODE=1: Bypassing last sent session check. Always sending notification.")
                send_discord_notification(session_str)
                # In test mode, send the reminder immediately as a one-off for quick verification
                logging.info("TEST_MODE: Sending immediate reminder notification for testing.")
                send_discord_notification(f"📣 T- 5mins till free electricity session starts!{session_str}")
            elif session_str != last_sent:
                send_discord_notification(session_str)
                update_last_sent_session(session_str)
                # Schedule reminder for new session
                reminder_time = parse_session_to_reminder(session_str)
                if reminder_time:
                    logging.info(f"Reminder scheduled for {reminder_time} (5 minutes before session start).")
                    threading.Thread(target=lambda: (
                        time.sleep(max(0, (reminder_time - datetime.now()).total_seconds())),
                        send_discord_notification(f" 📣 T- 5mins till free electricity session starts!{session_str}")
                    )).start()
            else:
                logging.info("Already sent notification for this session.")
        else:
            logging.warning("No session text found between 'Next' and 'Next'.")
    else:
        logging.error("Failed to fetch page content.")

    # Exit if SINGLE_RUN is set, otherwise loop every hour
    if not single_run:
        time.sleep(3600)
        main()

if __name__ == "__main__":
    main()