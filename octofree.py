import requests
import re
import os
import time

# Discord webhook URL - replace with your own
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1418296940847956070/yg7EVh3Mjur4lGmgms-oxqE1Q1qPLE8KGvXyHURbzdP_e2d5r04uoN0dv803ex6CfvlB'

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
    # Try to extract the session info after 'Next Session:'
    match = re.search(r'Next\s+Session:\s*([^<\n]+)', html_content, re.IGNORECASE)
    if match:
        session_raw = match.group(1).strip()
        # Remove any HTML tags from the session string (defensive)
        session_clean = re.sub(r'<[^>]+>', '', session_raw)
        return session_clean
    else:
        print("No session text found after 'Next Session:'. Regex did not match.")
        return None

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
        "content": f"🕰️ {message}",
        "username": "🐙 Octopus - Free Electric!!! ⚡️"

    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()
        print("Notification sent successfully.")
    except Exception as e:
        print(f"Error sending notification: {e}")

def main():
    url = 'https://octopus.energy/free-electricity/'
    single_run = os.getenv('SINGLE_RUN', '').strip().lower() == 'true'

    html_content = fetch_page_content(url)
    test_mode = os.getenv('TEST_MODE', '').strip().lower() == 'true'
    if html_content:
        session_str = extract_next_session(html_content)
        if session_str:
            print(f"Found session: {session_str}")
            last_sent = get_last_sent_session()
            if test_mode:
                print("TEST_MODE=1: Bypassing last sent session check. Always sending notification.")
                send_discord_notification(session_str)
            elif session_str != last_sent:
                send_discord_notification(session_str)
                update_last_sent_session(session_str)
            else:
                print("Already sent notification for this session.")
        else:
            print("No session text found between 'Next' and 'Next'.")
    else:
        print("Failed to fetch page content.")

    # Exit if SINGLE_RUN is set, otherwise loop every hour
    if not single_run:
        time.sleep(3600)
        main()

if __name__ == "__main__":
    main()