# Improved TEST_MODE Implementation Proposal

## Current Problems with TEST_MODE

1. **Modifies production data files** - Resets notification flags in `scheduled_sessions.json`
2. **No time manipulation** - Can't test reminder notifications without waiting hours
3. **No isolation** - Test runs affect real session tracking
4. **Limited testing scope** - Only tests initial notifications, not the full lifecycle
5. **Risk of data corruption** - If script crashes during test mode, production data is compromised

## Proposed Solution: Isolated Test Environment

### Core Concept

Create a **separate test data directory** that TEST_MODE uses instead of the production `/data` directory. This keeps production data safe while allowing comprehensive testing.

### Implementation Strategy

```python
# In main.py, modify output_dir based on TEST_MODE

test_mode = os.getenv('TEST_MODE', '').strip().lower() == 'true'

if test_mode:
    # Use separate test directory
    output_dir = os.getenv('OUTPUT_DIR', './output') + '_test'
    logging.info(f"🧪 TEST MODE: Using test directory: {output_dir}")
else:
    output_dir = os.getenv('OUTPUT_DIR', './output')
```

### Benefits

✅ **Zero risk to production data** - Test files are completely separate  
✅ **Can be deleted/reset anytime** - `rm -rf /data_test/*`  
✅ **Parallel testing** - Can run test mode while production container runs  
✅ **Easy cleanup** - Test data automatically isolated  

## Enhanced TEST_MODE Features

### Feature 1: Time Offset Manipulation

Allow TEST_MODE to create sessions with custom time offsets for rapid testing.

```python
TEST_MODE=true
TEST_TIME_OFFSET="+2m"  # Sessions start in 2 minutes from now
```

**Use Cases:**
- `"+2m"` - Session starts in 2 minutes (tests initial notification + 5min reminder)
- `"+10m"` - Session starts in 10 minutes (tests reminder notification)
- `"+65m"` - Session starts in 65 minutes (tests full lifecycle within 70 minutes)

**Implementation:**

```python
def apply_test_time_offset(session_str, offset_str):
    """
    Apply time offset to session for testing.
    
    Args:
        session_str: Original session string (e.g., "Sunday 27th October, 3-4pm")
        offset_str: Offset string (e.g., "+2m", "+10m", "+65m")
    
    Returns:
        Modified session string with adjusted times
    """
    if not offset_str:
        return session_str
    
    # Parse offset
    import re
    match = re.match(r'([+-])(\d+)([mh])', offset_str)
    if not match:
        return session_str
    
    sign, amount, unit = match.groups()
    offset_minutes = int(amount) if unit == 'm' else int(amount) * 60
    if sign == '-':
        offset_minutes = -offset_minutes
    
    # Parse original session
    start_time = parse_session_date(session_str)
    if not start_time:
        return session_str
    
    # Apply offset
    new_start = datetime.now() + timedelta(minutes=offset_minutes)
    
    # Calculate duration from original session
    end_time = parse_session_end_date(session_str)
    duration = (end_time - start_time).total_seconds() / 3600 if end_time else 1
    new_end = new_start + timedelta(hours=duration)
    
    # Reconstruct session string with new times
    # Format: "Wednesday 30th October, 2:05PM - 3:05PM"
    day_name = new_start.strftime('%A')
    day_num = new_start.day
    suffix = 'th' if 11 <= day_num <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day_num % 10, 'th')
    month = new_start.strftime('%B')
    
    start_str = new_start.strftime('%-I:%M%p')
    end_str = new_end.strftime('%-I:%M%p')
    
    return f"{day_name} {day_num}{suffix} {month}, {start_str} - {end_str}"
```

### Feature 2: Synthetic Test Sessions

Create fake sessions specifically for testing without scraping the website.

```bash
TEST_MODE=true
TEST_SESSIONS='[
  "Monday 28th October, 2:05PM - 3:05PM",
  "Tuesday 29th October, 5:30PM - 6:30PM"
]'
```

**Implementation:**

```python
def load_test_sessions():
    """Load synthetic sessions from TEST_SESSIONS env var."""
    test_sessions_json = os.getenv('TEST_SESSIONS')
    if test_sessions_json:
        try:
            return json.loads(test_sessions_json)
        except json.JSONDecodeError:
            logging.error("Invalid TEST_SESSIONS JSON format")
    return None

# In main loop:
if test_mode and load_test_sessions():
    current_sessions = load_test_sessions()
    logging.info(f"🧪 Using {len(current_sessions)} synthetic test sessions")
else:
    # Normal website scraping
    html_content = fetch_page_content(url)
```

### Feature 3: Accelerated Time Mode

Speed up the notification lifecycle for rapid testing.

```bash
TEST_MODE=true
TEST_ACCELERATE=60  # 1 real second = 60 test seconds (1 real minute = 1 test hour)
```

**How it works:**
- Main loop sleep becomes: `time.sleep(3600 / 60) = 60 seconds` (1 minute instead of 1 hour)
- Reminder checker sleep becomes: `time.sleep(60 / 60) = 1 second` (checks every second)
- Session times scaled down proportionally

**Implementation:**

```python
# Global test acceleration factor
TEST_ACCELERATE = int(os.getenv('TEST_ACCELERATE', '1'))

def test_sleep(seconds):
    """Sleep with test acceleration applied."""
    actual_sleep = seconds / TEST_ACCELERATE if test_mode else seconds
    time.sleep(actual_sleep)

# Replace all time.sleep() calls with:
test_sleep(3600)  # Sleeps 1 hour normally, 1 minute in TEST_ACCELERATE=60
```

### Feature 4: Test Scenario Presets

Predefined test scenarios for common testing needs.

```bash
TEST_MODE=true
TEST_SCENARIO=quick_lifecycle  # Tests full notification lifecycle in 10 minutes
```

**Scenarios:**

1. **`quick_lifecycle`** - Full lifecycle in 10 minutes
   - Session starts in 7 minutes (initial notification now)
   - Reminder at 2 minutes (in 5 real minutes)
   - Session starts at 7 minutes
   - End reminder at 62 minutes (55 real minutes after start)
   - Session ends at 67 minutes (1 hour 7 minutes from now)

2. **`immediate_reminders`** - Tests reminders immediately
   - Session starts in 6 minutes
   - Reminder triggers in 1 minute
   - End reminder triggers in ~55 minutes

3. **`multiple_sessions`** - Tests concurrent session handling
   - Creates 3 overlapping sessions with different start times
   - Tests queue management and priority

4. **`past_recovery`** - Tests Bayesian update logic
   - Creates sessions that "should have" happened
   - Tests recovery and flag preservation

**Implementation:**

```python
TEST_SCENARIOS = {
    'quick_lifecycle': {
        'sessions': [
            {'offset_minutes': 7, 'duration_minutes': 60}
        ],
        'accelerate': 1,  # Real-time
        'description': 'Full lifecycle in ~67 minutes'
    },
    'immediate_reminders': {
        'sessions': [
            {'offset_minutes': 6, 'duration_minutes': 60}
        ],
        'accelerate': 1,
        'description': 'Reminder in 1 minute'
    },
    'multiple_sessions': {
        'sessions': [
            {'offset_minutes': 10, 'duration_minutes': 60},
            {'offset_minutes': 15, 'duration_minutes': 60},
            {'offset_minutes': 90, 'duration_minutes': 60}
        ],
        'accelerate': 1,
        'description': 'Three concurrent sessions'
    },
    'accelerated': {
        'sessions': [
            {'offset_minutes': 420, 'duration_minutes': 60}  # 7 hours from now
        ],
        'accelerate': 60,  # 1 minute = 1 hour
        'description': 'Full lifecycle in 7 real minutes'
    }
}

def load_test_scenario(scenario_name):
    """Load and setup test scenario."""
    scenario = TEST_SCENARIOS.get(scenario_name)
    if not scenario:
        logging.error(f"Unknown test scenario: {scenario_name}")
        return None
    
    logging.info(f"🧪 TEST SCENARIO: {scenario_name}")
    logging.info(f"   {scenario['description']}")
    
    # Generate session strings
    now = datetime.now()
    sessions = []
    for sess in scenario['sessions']:
        start = now + timedelta(minutes=sess['offset_minutes'])
        end = start + timedelta(minutes=sess['duration_minutes'])
        
        day_name = start.strftime('%A')
        day_num = start.day
        suffix = 'th' if 11 <= day_num <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day_num % 10, 'th')
        month = start.strftime('%B')
        
        start_str = start.strftime('%-I:%M%p')
        end_str = end.strftime('%-I:%M%p')
        
        session_str = f"{day_name} {day_num}{suffix} {month}, {start_str} - {end_str}"
        sessions.append(session_str)
        
        logging.info(f"   📅 {session_str}")
        logging.info(f"      Start: {sess['offset_minutes']}min from now ({start.strftime('%H:%M:%S')})")
        logging.info(f"      Reminder: {sess['offset_minutes']-5}min from now ({(start - timedelta(minutes=5)).strftime('%H:%M:%S')})")
    
    return sessions, scenario.get('accelerate', 1)
```

## File Structure with Test Mode

```
/data/                              # Production data (never touched by TEST_MODE)
  ├── scheduled_sessions.json
  ├── past_scheduled_sessions.json
  ├── last_extracted_sessions.json
  └── last_sent_session.txt

/data_test/                         # Test data (created by TEST_MODE)
  ├── scheduled_sessions.json       # Test session tracking
  ├── past_scheduled_sessions.json  # Test past sessions
  ├── last_extracted_sessions.json  # Test extraction log
  └── last_sent_session.txt         # Test notification log
```

## Usage Examples

### Example 1: Quick Full Lifecycle Test (10 minutes)

```bash
# Test all notifications in 10 minutes
docker run -e TEST_MODE=true \
           -e TEST_TIME_OFFSET="+7m" \
           -e SINGLE_RUN=false \
           -v /test_data:/data_test \
           octofree
```

**Timeline:**
- T+0: Initial notification sent
- T+2min: 5-minute start reminder sent
- T+7min: Session starts
- T+62min: 5-minute end reminder sent
- T+67min: Session ends, moved to past

### Example 2: Immediate Reminder Test

```bash
# Test reminder notification in 1 minute
docker run -e TEST_MODE=true \
           -e TEST_TIME_OFFSET="+6m" \
           -e SINGLE_RUN=false \
           octofree
```

### Example 3: Accelerated Full Test (7 minutes real time = 7 hours test time)

```bash
# Ultra-fast testing with time acceleration
docker run -e TEST_MODE=true \
           -e TEST_ACCELERATE=60 \
           -e TEST_TIME_OFFSET="+420m" \
           -e SINGLE_RUN=false \
           octofree
```

### Example 4: Scenario-Based Testing

```bash
# Use predefined test scenario
docker run -e TEST_MODE=true \
           -e TEST_SCENARIO=quick_lifecycle \
           octofree
```

### Example 5: Multiple Session Testing

```bash
# Test concurrent session handling
docker run -e TEST_MODE=true \
           -e TEST_SCENARIO=multiple_sessions \
           octofree
```

## Implementation Checklist

### Phase 1: Data Isolation (Critical)
- [ ] Modify `output_dir` logic to use `{OUTPUT_DIR}_test` when `TEST_MODE=true`
- [ ] Update all file I/O functions to respect the test directory
- [ ] Add logging to clearly show which directory is being used
- [ ] Test that production data is never touched

### Phase 2: Time Offset
- [ ] Implement `TEST_TIME_OFFSET` environment variable parsing
- [ ] Create `apply_test_time_offset()` function
- [ ] Modify session parsing to apply offsets in test mode
- [ ] Add validation and error handling

### Phase 3: Synthetic Sessions
- [ ] Implement `TEST_SESSIONS` JSON parsing
- [ ] Modify main loop to use synthetic sessions when provided
- [ ] Add session format validation
- [ ] Test with various session formats

### Phase 4: Time Acceleration (Advanced)
- [ ] Implement `TEST_ACCELERATE` factor
- [ ] Create `test_sleep()` wrapper function
- [ ] Replace all `time.sleep()` calls with `test_sleep()`
- [ ] Scale session times proportionally
- [ ] Test main loop and reminder thread with acceleration

### Phase 5: Test Scenarios (Nice to Have)
- [ ] Define test scenario dictionary
- [ ] Implement `TEST_SCENARIO` loading
- [ ] Create session generation from scenario config
- [ ] Document each scenario's purpose and timeline

## Rollout Plan

1. **Week 1**: Implement data isolation (Phase 1)
   - Merge and test thoroughly
   - Deploy to updates branch

2. **Week 2**: Add time offset capability (Phase 2)
   - Test with various offset values
   - Update documentation

3. **Week 3**: Synthetic sessions (Phase 3)
   - Allow manual session creation
   - Test complex scenarios

4. **Week 4**: Time acceleration (Phase 4) - Optional
   - If needed for faster testing
   - Requires careful testing

5. **Future**: Scenario presets (Phase 5)
   - Community feedback on common test needs
   - Iterate on scenario design

## Safety Measures

1. **Automatic cleanup on exit**
   ```python
   def cleanup_test_data():
       if test_mode:
           logging.info("🧹 Cleaning up test data directory")
           shutil.rmtree(f"{output_dir}_test", ignore_errors=True)
   
   atexit.register(cleanup_test_data)
   ```

2. **Visual indicators in logs**
   ```
   🧪 TEST MODE ACTIVE - Using isolated test directory
   🧪 TEST MODE: /data_test
   ```

3. **Prevent accidental production usage**
   ```python
   if test_mode and '/data' in output_dir and '_test' not in output_dir:
       raise ValueError("TEST_MODE cannot use production data directory!")
   ```

4. **Test mode summary on exit**
   ```
   🧪 TEST MODE SUMMARY
     ├─ Test directory: /data_test
     ├─ Sessions processed: 3
     ├─ Notifications sent: 7
     ├─ Reminders tested: 6
     └─ Production data: UNTOUCHED ✓
   ```

## Comparison: Current vs Proposed

| Feature | Current | Proposed |
|---------|---------|----------|
| Data isolation | ❌ Modifies production files | ✅ Separate test directory |
| Time manipulation | ❌ None | ✅ Offset + acceleration |
| Quick testing | ❌ Must wait hours | ✅ Full test in 10 minutes |
| Multiple sessions | ❌ Manual setup | ✅ Scenario presets |
| Safety | ⚠️ Risk of corruption | ✅ Zero risk to production |
| Cleanup | ❌ Manual | ✅ Automatic |
| Flexibility | ⚠️ Limited | ✅ Highly configurable |

## Future Enhancements

- **Test assertion framework** - Verify notifications were sent correctly
- **Mock Discord webhook** - Capture and validate notification content
- **Test report generation** - JSON summary of test run results
- **CI/CD integration** - Automated testing on commits
- **Performance profiling** - Measure notification latency
- **Chaos testing** - Random failures to test error handling
