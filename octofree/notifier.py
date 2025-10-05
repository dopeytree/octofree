import requests
import os
import logging
import threading
from datetime import datetime, timedelta
from storage import load_scheduled_sessions, save_scheduled_sessions, load_past_scheduled_sessions, save_past_scheduled_sessions, update_last_sent_session
from utils import parse_session_date, parse_session_to_reminder, parse_session_to_end_reminder, parse_session_end_date  # Import from utils

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def send_discord_notification(message, notification_type="general"):
    if not DISCORD_WEBHOOK_URL:
        logging.error("ERROR: DISCORD_WEBHOOK_URL environment variable must be set.")
        return
    data = {
        "content": message,
        "username": "🐙 Octopus - Free Electric!!! ⚡️"
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        logging.info(f"{notification_type} notification sent successfully: {message}")
    except Exception as e:
        logging.error(f"Error sending notification: {e}")

active_timers = []  # Global list to keep references to active timers

def check_and_send_notifications():
    # Load scheduled sessions
    scheduled_sessions = load_scheduled_sessions()
    past_sessions = load_past_scheduled_sessions()
    now = datetime.now()
    
    for session in scheduled_sessions[:]:  # Copy to avoid modification issues
        session_str = session['session']
        start_time = datetime.fromisoformat(session['start_time'])
        end_time = datetime.fromisoformat(session['end_time'])
        
        # Check for initial notification
        if not session['notified'] and start_time > now:
            message = f"📣 Free Electric Session Scheduled: {session_str}"
            send_discord_notification(message, "date_time")
            session['notified'] = True
            logging.info(f"Initial notification sent for {session_str}")
        
        # Check for reminder (only if reminder_time is set)
        if session['reminder_time'] and not session['reminder_sent']:
            reminder_time = datetime.fromisoformat(session['reminder_time'])
            if reminder_time <= now and start_time > now:
                message = f"📣 T-5mins to Delta! {session_str}"
                send_discord_notification(message, "5min_delta")
                session['reminder_sent'] = True
                logging.info(f"Reminder sent for {session_str}")
        
        # Check for end reminder (only if end_reminder_time is set)
        if session['end_reminder_time'] and not session['end_sent']:
            end_reminder_time = datetime.fromisoformat(session['end_reminder_time'])
            if end_reminder_time <= now and end_time > now:
                message = f"🐰 End State: {session_str}"
                send_discord_notification(message, "end_state")
                session['end_sent'] = True
                logging.info(f"End reminder sent for {session_str}")
        
        # Move to past if ended
        if end_time <= now:
            past_sessions.append(session)
            scheduled_sessions.remove(session)
            logging.info(f"Moved {session_str} to past sessions")
    
    # Save updates
    save_scheduled_sessions(scheduled_sessions)
    save_past_scheduled_sessions(past_sessions)