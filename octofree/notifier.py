"""
Discord notification module for Octofree.

This module handles sending Discord webhook notifications for various session
events including:
- Initial session announcements (when first detected)
- 5-minute reminder before session starts
- 5-minute reminder before session ends
- Moving completed sessions to past history

Manages notification state tracking to prevent duplicate messages.
"""

import requests
import os
import logging
import threading
from datetime import datetime, timedelta
from storage import load_scheduled_sessions, save_scheduled_sessions, load_past_scheduled_sessions, save_past_scheduled_sessions, update_last_sent_session
from utils import parse_session_date, parse_session_to_reminder, parse_session_to_end_reminder, parse_session_end_date  # Import from utils

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def send_discord_notification(message, notification_type="general"):
    """
    Send a notification message to Discord via webhook.
    
    Uses the DISCORD_WEBHOOK_URL environment variable to post messages.
    All messages are sent with the username "🐙 Octopus - Free Electric!!! ⚡️".
    
    Args:
        message (str): The notification message content to send.
        notification_type (str, optional): Type of notification for logging.
            Common types: "general", "date_time", "5min_delta", "end_state".
            Defaults to "general".
    
    Returns:
        None. Logs success or error.
    """
    if not DISCORD_WEBHOOK_URL:
        logging.error("ERROR: DISCORD_WEBHOOK_URL environment variable must be set.")
        return
    data = {
        "content": message,
        "username": "🐙 Octopus - Free Electric!!! ⚡️"
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
        logging.info(f"{notification_type} notification sent successfully: {message}")
    except Exception as e:
        logging.error(f"Error sending notification: {e}")

active_timers = []  # Global list to keep references to active timers

def check_and_send_notifications():
    """
    Check scheduled sessions and send time-based notifications.
    
    This function is called regularly (every hour) to check if any notifications
    need to be sent. For each scheduled session, it:
    1. Sends initial notification if not yet sent
    2. Sends 5-minute warning before start (if reminder_time reached)
    3. Sends 5-minute warning before end (if end_reminder_time reached)
    4. Moves session to past_sessions when end_time is reached
    
    Updates notification flags (notified, reminder_sent, end_sent) to prevent
    duplicate notifications. All state changes are persisted to JSON files.
    
    Returns:
        None. Modifies scheduled_sessions and past_sessions files.
    """
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
            # Original message (commented for easy reverting):
            # message = f"📣 Free Electric Session Scheduled: {session_str}"
            
            # New message with verification links
            message = (
                f"📣 Free Electric Session Scheduled: {session_str}\n"
                f"- Check with: https://octopus.energy/free-electricity/\n"
                f"  or https://x.com/savingsessions"
            )
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