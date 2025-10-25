#!/usr/bin/env python3
"""
Test script to verify reminder notification logic.

⚠️  WARNING: This script modifies your actual scheduled_sessions.json file!
    It adds test sessions that will be picked up by the main application.
    Use --cleanup to remove test sessions when done.

This script creates test sessions with reminder times set to trigger within
the next few minutes, allowing you to verify that the 5-minute start and end
reminders are working correctly.

Usage:
    python3 test_reminder_notifications.py [OPTIONS]

Options:
    --start-in MINS    Test start reminder (default: 6 minutes from now)
    --end-in MINS      Test end reminder (default: 16 minutes from now)
    --both             Test both reminders (default)
    --start-only       Only test start reminder
    --end-only         Only test end reminder
    --cleanup          Remove all test sessions (sessions containing [TEST])

Examples:
    # Test both reminders with default times
    python3 test_reminder_notifications.py

    # Test start reminder in 3 minutes
    python3 test_reminder_notifications.py --start-only --start-in 3

    # Clean up test sessions when done
    python3 test_reminder_notifications.py --cleanup
"""

import json
import os
import sys
from datetime import datetime, timedelta
import argparse

# Add current directory to path so we can import storage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import save_scheduled_sessions, load_scheduled_sessions

def create_test_session(start_offset_mins=6, end_offset_mins=16, session_name="TEST"):
    """
    Create a test session with reminder times set to trigger soon.
    
    Args:
        start_offset_mins: Minutes from now when session starts (default 6)
        end_offset_mins: Minutes from now when session ends (default 16)
        session_name: Prefix for the session name
    
    Returns:
        dict: Session data structure
    """
    now = datetime.now()
    start_time = now + timedelta(minutes=start_offset_mins)
    end_time = now + timedelta(minutes=end_offset_mins)
    reminder_time = start_time - timedelta(minutes=5)
    end_reminder_time = end_time - timedelta(minutes=5)
    
    # Format session string in the expected format
    session_str = f"{start_time.strftime('%-I')}-{end_time.strftime('%-I%p').lower()}, {start_time.strftime('%A %-d')}th {start_time.strftime('%B')} [{session_name}]"
    
    session_data = {
        'session': session_str,
        'start_time': start_time.isoformat(),
        'reminder_time': reminder_time.isoformat(),
        'end_time': end_time.isoformat(),
        'end_reminder_time': end_reminder_time.isoformat(),
        'notified': True,  # Already "notified" so we don't get initial notification
        'reminder_sent': False,  # NOT sent yet - this is what we're testing
        'end_sent': False  # NOT sent yet - this is what we're testing
    }
    
    return session_data, start_time, end_time, reminder_time, end_reminder_time


def cleanup_test_sessions():
    """Remove all test sessions from scheduled_sessions.json"""
    scheduled_sessions = load_scheduled_sessions()
    original_count = len(scheduled_sessions)
    
    # Filter out any sessions containing [TEST] in the name
    cleaned_sessions = [s for s in scheduled_sessions if '[TEST]' not in s.get('session', '') and 'TEST' not in s.get('session', '')]
    removed_count = original_count - len(cleaned_sessions)
    
    if removed_count > 0:
        save_scheduled_sessions(cleaned_sessions)
        print("━" * 100)
        print(f"🧹 CLEANUP COMPLETE")
        print("━" * 100)
        print(f"✅ Removed {removed_count} test session(s)")
        print(f"📋 Remaining sessions: {len(cleaned_sessions)}")
        print()
        for session in cleaned_sessions:
            print(f"  - {session['session']}")
        print("━" * 100)
    else:
        print("━" * 100)
        print("✅ No test sessions found to clean up")
        print("━" * 100)


def main():
    parser = argparse.ArgumentParser(
        description='Test reminder notification logic',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--start-in', type=int, default=6,
                       help='Minutes until session starts (default: 6)')
    parser.add_argument('--end-in', type=int, default=16,
                       help='Minutes until session ends (default: 16)')
    parser.add_argument('--start-only', action='store_true',
                       help='Only test start reminder')
    parser.add_argument('--end-only', action='store_true',
                       help='Only test end reminder')
    parser.add_argument('--both', action='store_true',
                       help='Test both reminders (default)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Remove all test sessions and exit')
    
    args = parser.parse_args()
    
    # Handle cleanup mode
    if args.cleanup:
        cleanup_test_sessions()
        return
    
    # Default to both if nothing specified
    if not args.start_only and not args.end_only:
        args.both = True
    
    # Load existing scheduled sessions
    scheduled_sessions = load_scheduled_sessions()
    
    print("━" * 100)
    print("🧪 REMINDER NOTIFICATION TEST")
    print("━" * 100)
    print()
    print("⚠️  WARNING: This will add test sessions to your REAL scheduled_sessions.json")
    print("   These will be picked up by the main application.")
    print("   Use 'python3 test_reminder_notifications.py --cleanup' when done testing.")
    print()
    print("━" * 100)
    print()
    
    if args.start_only or args.both:
        # Create session that will trigger start reminder in ~1 minute
        session, start_time, end_time, reminder_time, end_reminder_time = create_test_session(
            start_offset_mins=args.start_in,
            end_offset_mins=args.start_in + 10,  # 10 min duration
            session_name="START-TEST"
        )
        scheduled_sessions.append(session)
        
        print("✅ START REMINDER TEST SESSION CREATED")
        print(f"  Session: {session['session']}")
        print(f"  Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  🔔 Reminder time: {reminder_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     (in {args.start_in - 5} minutes)")
        print(f"  End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print(f"⏰ Expected notification: \"📣 T-5mins to Delta! ...\" in ~{args.start_in - 5} minutes")
        print()
    
    if args.end_only or args.both:
        # Create session that will trigger end reminder in ~1 minute
        # Session "started" in the past, will end soon
        session, start_time, end_time, reminder_time, end_reminder_time = create_test_session(
            start_offset_mins=-5,  # Started 5 minutes ago
            end_offset_mins=args.end_in,
            session_name="END-TEST"
        )
        session['reminder_sent'] = True  # Already sent start reminder
        scheduled_sessions.append(session)
        
        print("✅ END REMINDER TEST SESSION CREATED")
        print(f"  Session: {session['session']}")
        print(f"  Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (already passed)")
        print(f"  End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  🔔 End reminder time: {end_reminder_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     (in {args.end_in - 5} minutes)")
        print()
        print(f"⏰ Expected notification: \"🐰 End State: ...\" in ~{args.end_in - 5} minutes")
        print()
    
    # Save the updated scheduled sessions
    save_scheduled_sessions(scheduled_sessions)
    
    print("━" * 100)
    print("📝 INSTRUCTIONS:")
    print("━" * 100)
    print()
    print("1. Keep your main application running (or start it now)")
    print("   cd /Users/ed/python\\ electric/octofree && python3 main.py")
    print()
    print("2. The check_and_send_notifications() function runs every hour")
    print("   BUT you can manually trigger it by:")
    print()
    print("   Option A: Wait for the next hourly check")
    print("   Option B: Restart the application (triggers immediate check)")
    print("   Option C: Set SINGLE_RUN=true and run multiple times:")
    print("      SINGLE_RUN=true python3 main.py")
    print()
    print("3. Watch your Discord channel for the reminder notifications!")
    print()
    print("4. Check the logs for:")
    print("   - \"⏰ REMINDER SENT: ... (5 mins before start)\"")
    print("   - \"🏁 END REMINDER SENT: ... (5 mins before end)\"")
    print()
    print("5. ⚠️  IMPORTANT: Clean up when done testing:")
    print("   python3 test_reminder_notifications.py --cleanup")
    print()
    print("━" * 100)
    print()
    print("💡 TIP: To test immediately, set shorter times:")
    print("   python3 test_reminder_notifications.py --start-only --start-in 7")
    print("   (Reminder will trigger in ~2 minutes: 7 - 5 = 2)")
    print()
    print("━" * 100)


if __name__ == "__main__":
    main()
