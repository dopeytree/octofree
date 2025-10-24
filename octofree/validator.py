"""
Data Validation and Correction Module for Octofree.

This module validates and corrects previously saved session data to ensure
that any fixes to parsing logic are also applied to historical data.
Runs on container startup to maintain data integrity.

Functions validate:
- Session time parsing accuracy
- Duration reasonableness (detects > 4 hour sessions)
- Start/end time consistency with session strings
- AM/PM inference correctness

When errors are detected, sessions are automatically corrected using current
parsing logic and changes are logged for audit purposes.
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Tuple
from utils import parse_session_date, parse_session_to_reminder, parse_session_to_end_reminder, parse_session_end_date


def validate_session_times(session_data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate that session times are correctly parsed against the session string.
    
    Performs comprehensive validation including:
    - Checks duration is reasonable (0-4 hours typically)
    - Verifies end time is after start time
    - Compares parsed times against session string format
    - Validates AM/PM inference matches expected values
    
    Args:
        session_data (Dict): Session dictionary containing 'session' string,
            'start_time', and 'end_time' ISO format strings.
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
            - is_valid: True if no errors found, False otherwise
            - list_of_errors: Descriptions of any validation failures
    """
    errors = []
    session_str = session_data.get('session', '')
    
    if not session_str:
        errors.append("Missing session string")
        return False, errors
    
    # Parse times using current (fixed) parsing logic
    try:
        start_time = datetime.fromisoformat(session_data['start_time'])
        end_time = datetime.fromisoformat(session_data['end_time'])
        
        # Calculate duration
        duration_hours = (end_time - start_time).total_seconds() / 3600
        
        # Check for common errors
        # 1. Duration should be between 0 and 4 hours typically
        if duration_hours < 0:
            errors.append(f"End time ({end_time.strftime('%H:%M')}) is before start time ({start_time.strftime('%H:%M')})")
        elif duration_hours > 4:
            errors.append(f"Duration is unusually long: {duration_hours:.1f} hours (start: {start_time.strftime('%H:%M')}, end: {end_time.strftime('%H:%M')})")
        
        # 2. Check if time matches the session string
        # Extract time range from session string (e.g., "9-10pm" or "11am-12pm")
        import re
        time_match = re.match(r'(\d+)(am|pm)?-(\d+)(am|pm)', session_str, re.IGNORECASE)
        if time_match:
            start_hour_str = time_match.group(1)
            start_ampm = time_match.group(2)  # May be None
            end_hour_str = time_match.group(3)
            end_ampm = time_match.group(4).lower()
            
            # Expected end hour
            expected_end_hour = int(end_hour_str)
            if end_ampm == 'pm' and expected_end_hour != 12:
                expected_end_hour += 12
            elif end_ampm == 'am' and expected_end_hour == 12:
                expected_end_hour = 0
            
            # Check if stored end time matches expected
            if end_time.hour != expected_end_hour:
                errors.append(f"End time mismatch: stored as {end_time.strftime('%H:%M')} but session string indicates {end_hour_str}{end_ampm} (hour {expected_end_hour})")
            
            # Expected start hour
            expected_start_hour = int(start_hour_str)
            # If start has explicit AM/PM, use it; otherwise inherit from end
            if start_ampm:
                actual_start_ampm = start_ampm.lower()
            else:
                actual_start_ampm = end_ampm
                
            if actual_start_ampm == 'pm' and expected_start_hour != 12:
                expected_start_hour += 12
            elif actual_start_ampm == 'am' and expected_start_hour == 12:
                expected_start_hour = 0
                
            # Check if stored start time matches expected
            if start_time.hour != expected_start_hour:
                if start_ampm:
                    errors.append(f"Start time mismatch: stored as {start_time.strftime('%H:%M')} but session string indicates {start_hour_str}{start_ampm} (hour {expected_start_hour})")
                else:
                    errors.append(f"Start time mismatch: stored as {start_time.strftime('%H:%M')} but session string indicates {start_hour_str} (hour {expected_start_hour} based on {end_ampm})")
        
    except (ValueError, KeyError) as e:
        errors.append(f"Error parsing datetime fields: {e}")
        return False, errors
    
    return len(errors) == 0, errors


def correct_session_data(session_data: Dict) -> Dict:
    """
    Correct session data by re-parsing with current (fixed) logic.
    
    Takes a session dictionary that failed validation and re-parses all
    datetime fields using the current parsing functions from utils.py.
    This ensures historical data benefits from any bug fixes in parsing logic.
    
    Args:
        session_data (Dict): Session dictionary with potentially incorrect times.
    
    Returns:
        Dict: Corrected session dictionary with re-parsed datetime values.
    """
    session_str = session_data['session']
    
    # Re-parse times using current (fixed) logic
    start_time = parse_session_date(session_str)
    reminder_time = parse_session_to_reminder(session_str)
    end_time = parse_session_end_date(session_str)
    end_reminder_time = parse_session_to_end_reminder(session_str)
    
    # Create corrected data
    corrected = session_data.copy()
    
    if start_time:
        corrected['start_time'] = start_time.isoformat()
    if reminder_time:
        corrected['reminder_time'] = reminder_time.isoformat()
    if end_time:
        corrected['end_time'] = end_time.isoformat()
    if end_reminder_time:
        corrected['end_reminder_time'] = end_reminder_time.isoformat()
    
    return corrected


def log_correction_details(session_str: str, old_data: Dict, new_data: Dict, errors: List[str]):
    """
    Log detailed information about session data corrections.
    
    Provides comprehensive audit trail of what was corrected and why,
    including before/after timestamps and duration calculations.
    
    Args:
        session_str (str): Session description string.
        old_data (Dict): Original (incorrect) session data.
        new_data (Dict): Corrected session data.
        errors (List[str]): List of validation errors that triggered correction.
    """
    logging.warning(f"🔧 CORRECTING SESSION DATA: '{session_str}'")
    logging.warning(f"   Errors found: {len(errors)}")
    for error in errors:
        logging.warning(f"   - {error}")
    
    # Log old vs new times
    old_start = datetime.fromisoformat(old_data['start_time'])
    new_start = datetime.fromisoformat(new_data['start_time'])
    old_end = datetime.fromisoformat(old_data['end_time'])
    new_end = datetime.fromisoformat(new_data['end_time'])
    
    logging.warning(f"   OLD: {old_start.strftime('%Y-%m-%d %H:%M:%S')} to {old_end.strftime('%H:%M:%S')} (duration: {(old_end - old_start).total_seconds() / 3600:.1f}h)")
    logging.warning(f"   NEW: {new_start.strftime('%Y-%m-%d %H:%M:%S')} to {new_end.strftime('%H:%M:%S')} (duration: {(new_end - new_start).total_seconds() / 3600:.1f}h)")


def validate_and_correct_sessions_file(file_path: str, file_description: str) -> bool:
    """
    Validate and correct a sessions JSON file (scheduled or past).
    
    Loads the file, validates each session, corrects any errors found,
    and saves back to disk if corrections were made. Provides detailed
    logging of all validation and correction activities.
    
    Args:
        file_path (str): Absolute path to the JSON file to validate.
        file_description (str): Human-readable description for logging
            (e.g., "Scheduled Sessions", "Past Scheduled Sessions").
    
    Returns:
        bool: True if corrections were made, False if all data was valid
            or file doesn't exist.
    """
    try:
        # Load the file
        with open(file_path, 'r') as f:
            sessions = json.load(f)
        
        if not sessions:
            logging.info(f"  ✓ {file_description}: No sessions to validate")
            return False
        
        logging.info(f"🔍 VALIDATING {file_description.upper()}: {len(sessions)} session(s)")
        
        # Sort sessions by start time (recent to old) for chronological display
        try:
            sorted_sessions = sorted(
                sessions,
                key=lambda s: datetime.fromisoformat(s.get('start_time', '1970-01-01T00:00:00')),
                reverse=True  # Most recent first
            )
        except (ValueError, TypeError):
            # Fallback to original order if sorting fails
            logging.warning(f"  ⚠️ Could not sort sessions by date, using file order")
            sorted_sessions = sessions
        
        corrections_made = False
        corrected_sessions = []
        
        for i, session_data in enumerate(sorted_sessions):
            session_str = session_data.get('session', 'Unknown')
            
            # Use box drawing characters for tree structure
            if i == len(sorted_sessions) - 1:
                prefix = "└──"
            else:
                prefix = "├──"
            
            # Validate the session
            is_valid, errors = validate_session_times(session_data)
            
            if is_valid:
                logging.info(f"  {prefix} ✓ '{session_str}' - Valid")
                corrected_sessions.append(session_data)
            else:
                # Correct the session
                corrected_data = correct_session_data(session_data)
                
                # Log the correction
                log_correction_details(session_str, session_data, corrected_data, errors)
                
                corrected_sessions.append(corrected_data)
                corrections_made = True
        
        # Save corrected data if changes were made
        if corrections_made:
            with open(file_path, 'w') as f:
                json.dump(corrected_sessions, f, indent=2)
            logging.warning(f"✓ {file_description}: Corrections saved to {file_path}")
        else:
            logging.info(f"✅ {file_description}: All sessions valid, no corrections needed")
        
        return corrections_made
        
    except FileNotFoundError:
        logging.info(f"✓ {file_description}: File not found (new installation)")
        return False
    except json.JSONDecodeError as e:
        logging.error(f"❌ {file_description}: Invalid JSON format: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ {file_description}: Unexpected error: {e}")
        return False


def validate_and_correct_extracted_sessions(file_path: str) -> bool:
    """
    Validate last_extracted_sessions.json file format.
    
    Simpler validation than full session validation since this file only
    contains a list of session strings (not full session objects with times).
    Ensures file is a proper JSON list of non-empty strings.
    
    Args:
        file_path (str): Path to last_extracted_sessions.json file.
    
    Returns:
        bool: True if valid, False if format is incorrect.
    """
    try:
        with open(file_path, 'r') as f:
            sessions = json.load(f)
        
        if not sessions:
            logging.info(f"  ✓ Last Extracted Sessions: No sessions found")
            return True
        
        logging.info(f"🔍 VALIDATING LAST EXTRACTED SESSIONS: {len(sessions)} session(s)")
        
        # Just verify it's a list of strings and show each one in tree format
        if isinstance(sessions, list) and all(isinstance(s, str) for s in sessions):
            for i, session_str in enumerate(sessions):
                # Use box drawing characters for tree structure
                if i == len(sessions) - 1:
                    prefix = "└──"
                else:
                    prefix = "├──"
                logging.info(f"  {prefix} ✓ '{session_str}' - Valid string")
            return True
        else:
            logging.warning(f"  ⚠️ Extracted sessions format is incorrect")
            return False
            
    except FileNotFoundError:
        logging.info(f"✓ Last Extracted Sessions: File not found (new installation)")
        return True
    except Exception as e:
        logging.error(f"❌ Last Extracted Sessions: Error: {e}")
        return False


def run_startup_validation(output_dir: str) -> Dict[str, bool]:
    """
    Run validation and correction on all session files at startup.
    
    This is the main entry point called from main.py during application startup.
    Validates and corrects:
    - scheduled_sessions.json
    - past_scheduled_sessions.json  
    - last_extracted_sessions.json
    
    Provides comprehensive logging with visual separators and summary.
    Ensures all historical data is consistent with current parsing logic.
    
    Args:
        output_dir (str): Absolute path to directory containing session files.
    
    Returns:
        Dict[str, bool]: Results dictionary with keys:
            - 'scheduled': True if corrections made to scheduled_sessions.json
            - 'past': True if corrections made to past_scheduled_sessions.json
            - 'extracted': True if last_extracted_sessions.json is valid
    """
    import os
    
    logging.info("🚀 STARTING DATA VALIDATION & CORRECTION")
    logging.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    results = {}
    
    # Validate scheduled sessions
    scheduled_path = os.path.join(output_dir, 'scheduled_sessions.json')
    results['scheduled'] = validate_and_correct_sessions_file(
        scheduled_path,
        "Scheduled Sessions"
    )
    
    # Validate past scheduled sessions
    past_path = os.path.join(output_dir, 'past_scheduled_sessions.json')
    results['past'] = validate_and_correct_sessions_file(
        past_path,
        "Past Scheduled Sessions"
    )
    
    # Validate last extracted sessions (simpler format)
    extracted_path = os.path.join(output_dir, 'last_extracted_sessions.json')
    results['extracted'] = validate_and_correct_extracted_sessions(extracted_path)
    
    # Summary
    logging.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if any(results.values()):
        logging.warning("🟡 VALIDATION COMPLETE")
        logging.warning("  ⚠️ Corrections applied to historical data")
        logging.warning("  └─ Updated to match current parsing logic")
    else:
        logging.info("🟢 VALIDATION COMPLETE")
        logging.info("  ✓ All data is correct, no changes needed")
    logging.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return results
