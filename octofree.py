import requests
import re
import os
import time
from datetime import datetime, timedelta
from dateutil import parser

# Discord webhook URL - read from environment for safety (set DISCORD_WEBHOOK_URL to use)
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')

# File to track the last sent session
LAST_SENT_FILE = 'last_sent_session.txt'

def fetch_page_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def extract_next_session(html_content):
    # Search for pattern like "Next Session: 2-3pm, Thursday 18th September"
    # Adjust regex as needed based on page structure
    match = re.search(r'Next\s+(Free Electricity\s+)?session:\s*(\d+-\d+(am|pm),\s*\w+\s*\d+(st|nd|rd|th)\s*\w+)', html_content, re.IGNORECASE)
    if match:
        return match.group(2)
    return None

def parse_session_date(session_str):
    try:
        # Assume current year if not specified
        current_year = datetime.now().year
        session_str_with_year = f"{session_str} {current_year}"
        dt = parser.parse(session_str_with_year, fuzzy=True)
        return dt.date()
    except Exception as e:
        print(f"Error parsing date: {e}")
        return None

def is_today_or_tomorrow(session_date):
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    return session_date == today or session_date == tomorrow

def get_last_sent_session():
    if os.path.exists(LAST_SENT_FILE):
        with open(LAST_SENT_FILE, 'r') as f:
            return f.read().strip()
    return None

def update_last_sent_session(session_str):
    with open(LAST_SENT_FILE, 'w') as f:
        f.write(session_str)

def send_discord_notification(message):
    data = {
        "content": message,
        "username": "Free Electricity Alert"
    }
    if not DISCORD_WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL not set; skipping sending notification.")
        return
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()
        print("Notification sent successfully.")
    except Exception as e:
        print(f"Error sending notification: {e}")

def main():
    url = 'https://octopus.energy/free-electricity/'
    while True:
        html_content = fetch_page_content(url)
        if html_content:
            session_str = extract_next_session(html_content)
            if session_str:
                print(f"Found session: {session_str}")
                last_sent = get_last_sent_session()
                if session_str != last_sent:
                    session_date = parse_session_date(session_str)
                    if session_date and is_today_or_tomorrow(session_date):
                        message = f"Free Electricity Session Alert: {session_str}"
                        send_discord_notification(message)
                        update_last_sent_session(session_str)
                else:
                    print("Already sent notification for this session.")
            else:
                print("No next session found on the page.")
        else:
            print("Failed to fetch page content.")
        
        # Wait for 1 hour (3600 seconds)
        time.sleep(3600)

        # If SINGLE_RUN is set to '1', exit after one iteration to allow safe one-shot runs
        if os.environ.get('SINGLE_RUN') == '1':
            print('SINGLE_RUN=1 detected, exiting after one loop.')
            break
if __name__ == "__main__":
    main()