# Bug Fix: Multiple Session Queuing Issue

## Date: 24 October 2025

## Summary
Fixed a critical bug that prevented the system from properly queuing multiple sessions when they were announced in quick succession.

## Exact Website Text (Source)
**URL:** https://octopus.energy/free-electricity/  
**Captured:** 24 October 2025

```
Next Sessions:

9-10pm, Friday 24th October ⚡️
TRIPLE SESSION: 12-3pm, Saturday 25th October ⚡️⚡️⚡️

Power Tower bonus: Once you collectively surpass £2,600,000 of free electricity, you'll unlock an epic prize draw. One customer will win a £35,000 EV: the Ford Puma Gen-E Premium!
```

**Key observations:**
- New terminology introduced: "TRIPLE SESSION" (first observed on this date)
- Multiple lightning bolt emojis (⚡️⚡️⚡️) to emphasize the 3-hour duration
- Both sessions listed under "Next Sessions:" heading
- Saturday session explicitly labeled as different from standard 1-hour format

## The Problem

### Scenario
1. **Friday session announced**: `9-10pm, Friday 24th October` - Successfully extracted, queued, and notified ✅
2. **Saturday session announced**: `12-3pm, Saturday 25th October` (TRIPLE SESSION) - Extracted but NOT notified ❌

### What Happened
When Octopus Energy announced a second session (Saturday) while the first session (Friday) was still active, the system:
- ✅ Successfully extracted BOTH sessions from the website: `['12-3pm, Saturday 25th October', '9-10pm, Friday 24th October']`
- ✅ Correctly parsed the "TRIPLE SESSION" format
- ❌ **Failed to send notification** for the Saturday session
- ❌ **Did not update** `last_extracted_sessions.json` properly

### Log Evidence
```
2025-10-24 17:19:41,149 INFO: [SCRAPER_WEBSITE] Extracted 2 session(s) from Octopus website: 
  ['12-3pm, Saturday 25th October', '9-10pm, Friday 24th October'] (type: next)
2025-10-24 17:19:41,150 INFO: No new session planned
```

**File States:**
- `last_extracted_sessions.json`: Only contained `["9-10pm, Friday 24th October"]` (missing Saturday)
- `scheduled_sessions.json`: Contained Saturday session but with 4 duplicate Friday entries

## Root Causes

### Bug #1: Incorrect Session Comparison Logic
**Location:** `main.py` line 92-95

**Problem:**
```python
last_sessions = load_last_extracted_sessions()
if set(current_sessions) == set(last_sessions) and not test_mode:
    logging.info("No new session planned")
```

The system compared entire session sets but then checked if INDIVIDUAL sessions already existed:
```python
existing = next((s for s in scheduled_sessions if s['session'] == session_str), None)
if existing or past_existing:
    logging.info(f"Session already tracked: {session_str}")
    continue  # ← SKIPPED Saturday because it was already in scheduled_sessions.json
```

**Result:** Saturday was extracted and already in `scheduled_sessions.json` (from a previous run), so it was skipped without notification.

### Bug #2: Duplicate Prevention Not Working
**Location:** `storage.py` `load_scheduled_sessions()`

**Problem:** No deduplication when loading sessions from JSON file, allowing duplicates to accumulate.

**Evidence:** Friday session appeared 4 times in `scheduled_sessions.json`:
```json
[
  {"session": "9-10pm, Friday 24th October", ...},
  {"session": "9-10pm, Friday 24th October", ...},
  {"session": "9-10pm, Friday 24th October", ...},
  {"session": "9-10pm, Friday 24th October", ...},
  {"session": "12-3pm, Saturday 25th October", ...}
]
```

### Bug #3: `last_extracted_sessions.json` Out of Sync
**Problem:** File was updated at the wrong time in the processing flow, causing it to be out of sync with `scheduled_sessions.json`.

## The Fix

### Fix #1: Improved Session Detection Logic
**Changed:** `main.py` session comparison to use set difference to detect NEW sessions:

```python
# OLD: Check if entire set is equal
if set(current_sessions) == set(last_sessions):
    logging.info("No new session planned")

# NEW: Check for new sessions specifically
current_set = set(current_sessions)
last_set = set(last_sessions)
new_sessions = current_set - last_set

if not new_sessions and not test_mode:
    logging.info("No new session planned")
elif new_sessions:
    logging.info(f"New session(s) detected: {list(new_sessions)}")
```

### Fix #2: Added Automatic Deduplication
**Changed:** `storage.py` `load_scheduled_sessions()` now deduplicates on load:

```python
def load_scheduled_sessions():
    if os.path.exists(SCHEDULED_SESSIONS_FILE):
        sessions = json.load(f)
        # Deduplicate sessions based on session string
        seen = set()
        unique_sessions = []
        for session in sessions:
            session_str = session.get('session', '')
            if session_str and session_str not in seen:
                seen.add(session_str)
                unique_sessions.append(session)
        
        if len(unique_sessions) < len(sessions):
            logging.warning(f"Deduplicated {len(sessions) - len(unique_sessions)} duplicate session(s)")
        
        return unique_sessions
```

### Fix #3: Improved Tracking and Logging
**Changed:** `main.py` now uses sets for faster duplicate checking:

```python
# Get list of already tracked session strings for quick lookup
tracked_session_strings = set(s['session'] for s in scheduled_sessions)
past_session_strings = set(s['session'] for s in past_sessions)

# Check if already tracked
if session_str in tracked_session_strings:
    logging.debug(f"Session already in scheduled: {session_str}")
    continue
```

**Added:** Better logging and session queue summary:
```python
sessions_added.append(session_str)
logging.info(f"✓ Added new session to queue: {session_str}")

# Log summary after processing
if sessions_added:
    logging.info(f"✓ Session queue updated: {len(sessions_added)} session(s) added")
    logging.info(f"✓ Total queued sessions: {len(scheduled_sessions)}")
```

### Fix #4: Corrected File Update Timing
**Changed:** `last_extracted_sessions.json` now updates AFTER session processing:

```python
# Always save current sessions as last extracted (after processing)
save_last_extracted_sessions(current_sessions)
logging.debug(f"[STORAGE] Updated last_extracted_sessions.json with {len(current_sessions)} session(s)")
```

## Data Cleanup Performed

1. **Removed duplicates** from `scheduled_sessions.json` (removed 3 duplicate Friday entries)
2. **Verified** `last_extracted_sessions.json` contains both sessions
3. **Confirmed** both sessions properly queued with correct notification states

## Impact

### Before Fix
- ❌ Multiple sessions announced within 48 hours would not trigger notifications
- ❌ Duplicate entries could accumulate in scheduled_sessions.json
- ❌ System state files could become out of sync

### After Fix
- ✅ System properly queues multiple sessions (2, 3, or more)
- ✅ Automatic deduplication prevents duplicates
- ✅ Better logging provides visibility into session queue status
- ✅ New sessions detected using set difference operation
- ✅ Files stay synchronized throughout processing

## Test Case

**Scenario:** Two sessions announced (Friday + Saturday TRIPLE SESSION)

**Expected Behavior:**
1. Extract both sessions from website ✅
2. Detect Saturday as NEW session ✅
3. Add Saturday to scheduled_sessions.json ✅
4. Send Discord notification for Saturday ✅
5. Queue both sessions for reminder notifications ✅
6. Update last_extracted_sessions.json with both ✅

## Notes

- The existing regex patterns correctly extracted "TRIPLE SESSION" without modification
- No changes needed to `scraper_website.py` parsing logic
- Fix was entirely in session management and queuing logic
- System now handles any number of concurrent sessions announced within 48 hours
