import re
from datetime import datetime, timedelta

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
        return None
    reminder_time = session_start - timedelta(minutes=5)
    if reminder_time <= now:
        return None
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