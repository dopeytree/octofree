# Background Reminder Thread - Example Logs

This document shows how the background reminder checker thread appears in the logs throughout its lifecycle.

## Thread Startup (Normal Mode)

```log
2025-10-25 14:23:45 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-10-25 14:23:45 INFO: ⚙️ LOADING SETTINGS
2025-10-25 14:23:45 INFO:   ├── 🔐 DISCORD_WEBHOOK: *****************************7890
2025-10-25 14:23:45 INFO:   ├── 🔵 TEST_MODE: false
2025-10-25 14:23:45 INFO:   ├── 🔵 SINGLE_RUN: false
2025-10-25 14:23:45 INFO:   └── 🔵 OUTPUT_DIR: /data
2025-10-25 14:23:45 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-10-25 14:23:45 INFO: ✅ Background reminder checker started                    <-- THREAD STARTED
2025-10-25 14:23:45 INFO: 🔔 Reminder checker thread started (checks every 60 seconds)   <-- THREAD LOGGING
2025-10-25 14:23:45 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-10-25 14:23:45 INFO: ✅ [STARTUP UPDATE] Bayesian update complete (no changes needed)
```

## Thread Startup (SINGLE_RUN Mode)

```log
2025-10-25 14:23:45 INFO: ⚙️ LOADING SETTINGS
2025-10-25 14:23:45 INFO:   ├── 🔐 DISCORD_WEBHOOK: *****************************7890
2025-10-25 14:23:45 INFO:   ├── 🔵 TEST_MODE: false
2025-10-25 14:23:45 INFO:   ├── 🔵 SINGLE_RUN: true
2025-10-25 14:23:45 INFO:   └── 🔵 OUTPUT_DIR: /data
2025-10-25 14:23:45 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-10-25 14:23:45 INFO: ℹ️  Reminder checker disabled in SINGLE_RUN mode          <-- NO THREAD IN SINGLE_RUN
2025-10-25 14:23:45 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-10-25 14:23:45 INFO: 🔸 SINGLE RUN MODE - Will exit after this cycle
```

## Thread Running - Checking Every 60 Seconds

The thread silently checks every 60 seconds. It only logs when:
1. A reminder needs to be sent
2. An error occurs

### Example: No Reminders Due

```log
2025-10-25 14:23:45 INFO: ⏰ Sleeping for 1 hour before next scan...
2025-10-25 14:23:45 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(60 seconds pass - thread checks silently, no reminders due)
(120 seconds pass - thread checks silently, no reminders due)
(180 seconds pass - thread checks silently, no reminders due)
```

### Example: Reminder Sent by Background Thread

```log
2025-10-25 14:55:03 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-10-25 14:55:03 INFO: 🔔 REMINDER CHECK: Checking for due reminder notifications...
2025-10-25 14:55:03 INFO: ⏰ [REMINDER] Session starting soon:
2025-10-25 14:55:03 INFO:   📅 Sunday 27th October, 3:00PM - 4:00PM
2025-10-25 14:55:03 INFO:   ⏱️  Starts in 5 minutes
2025-10-25 14:55:03 INFO: 📤 Sending Discord notification...
2025-10-25 14:55:03 INFO: ✅ Discord notification sent successfully
2025-10-25 14:55:03 DEBUG: 💾 [STORAGE] Updating scheduled_sessions.json (reminder sent)
```

### Example: End Reminder Sent by Background Thread

```log
2025-10-25 15:55:02 INFO: 🔔 REMINDER CHECK: Checking for due reminder notifications...
2025-10-25 15:55:02 INFO: ⏰ [END REMINDER] Session ending soon:
2025-10-25 15:55:02 INFO:   📅 Sunday 27th October, 3:00PM - 4:00PM
2025-10-25 15:55:02 INFO:   ⏱️  Ends in 5 minutes
2025-10-25 15:55:02 INFO: 📤 Sending Discord notification...
2025-10-25 15:55:02 INFO: ✅ Discord notification sent successfully
2025-10-25 15:55:02 DEBUG: 💾 [STORAGE] Updating scheduled_sessions.json (end reminder sent)
```

### Example: Error in Background Thread

```log
2025-10-25 14:55:03 ERROR: ❌ Error in reminder checker thread: Connection timeout
(Thread continues running, will retry in 60 seconds)
```

## Thread Shutdown - Graceful Stop (Ctrl+C or Docker Stop)

```log
2025-10-25 18:45:23 INFO: ⏰ Sleeping for 1 hour before next scan...
2025-10-25 18:45:23 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
^C
2025-10-25 18:45:25 INFO: 🛑 Received signal 2, shutting down gracefully...        <-- SIGINT (Ctrl+C)
2025-10-25 18:45:25 INFO: 🔕 Reminder checker thread stopped                      <-- THREAD CLEANLY STOPPED
(Process exits)
```

```log
2025-10-25 18:45:23 INFO: ⏰ Sleeping for 1 hour before next scan...
2025-10-25 18:45:23 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(docker stop command issued)
2025-10-25 18:45:27 INFO: 🛑 Received signal 15, shutting down gracefully...       <-- SIGTERM (Docker stop)
2025-10-25 18:45:27 INFO: 🔕 Reminder checker thread stopped                      <-- THREAD CLEANLY STOPPED
(Container exits gracefully)
```

## Complete Startup Sequence with Thread

```log
2025-10-25 14:00:00 INFO: ╔═════════════════════════════════════════════════════════════════════════════════════════════════════╗
2025-10-25 14:00:00 INFO: ║                                                                                                     ║
2025-10-25 14:00:00 INFO: ║                                    🐙 OCTOFREE MONITOR 🐙                                          ║
2025-10-25 14:00:00 INFO: ║                                                                                                     ║
2025-10-25 14:00:00 INFO: ║                         Monitoring Octopus Energy Free Electricity                                  ║
2025-10-25 14:00:00 INFO: ║                                                                                                     ║
2025-10-25 14:00:00 INFO: ╚═════════════════════════════════════════════════════════════════════════════════════════════════════╝
2025-10-25 14:00:00 INFO: 
2025-10-25 14:00:00 INFO: Created by: dopeytree
2025-10-25 14:00:00 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-10-25 14:00:00 INFO: ⚙️ LOADING SETTINGS
2025-10-25 14:00:00 INFO:   ├── 🔐 DISCORD_WEBHOOK: *****************************7890
2025-10-25 14:00:00 INFO:   ├── 🔵 TEST_MODE: false
2025-10-25 14:00:00 INFO:   ├── 🔵 SINGLE_RUN: false
2025-10-25 14:00:00 INFO:   └── 🔵 OUTPUT_DIR: /data
2025-10-25 14:00:00 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-10-25 14:00:00 INFO: ✅ Background reminder checker started                    👈 THREAD STARTS HERE
2025-10-25 14:00:00 INFO: 🔔 Reminder checker thread started (checks every 60 seconds)
2025-10-25 14:00:00 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-10-25 14:00:01 INFO: ✅ [STARTUP UPDATE] Bayesian update complete (no changes needed)
2025-10-25 14:00:01 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-10-25 14:00:01 INFO: 🔍 SCRAPER STATUS
2025-10-25 14:00:01 INFO:   X.com scraper ENABLED (checks at 11am/8pm)
2025-10-25 14:00:01 INFO: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
(Main loop continues, thread runs independently in background checking every 60 seconds)
```

## How It Works

### Thread Lifecycle:

1. **Startup**: Thread created and started right after settings are loaded (unless SINGLE_RUN mode)
2. **Running**: Thread loops forever checking every 60 seconds:
   - Calls `check_and_send_notifications()`
   - Catches any exceptions and logs errors
   - Sleeps for 60 seconds
   - Repeats
3. **Shutdown**: When signal received (Ctrl+C or Docker stop):
   - Signal handler sets `reminder_thread_running = False`
   - Thread exits its while loop
   - Logs "🔕 Reminder checker thread stopped"
   - Process exits cleanly

### Key Features:

- **Daemon thread**: Set as daemon, so it won't prevent program from exiting
- **60-second checks**: Ensures 5-minute reminders caught within 1-minute accuracy
- **Silent operation**: Only logs when reminders sent or errors occur
- **Error resilient**: Catches exceptions and continues running
- **Graceful shutdown**: Responds to SIGINT/SIGTERM signals cleanly
- **Disabled in SINGLE_RUN**: No overhead when running in test/single-run mode

### Why This Solves the Problem:

**Before**: Main loop checked every 3600 seconds (1 hour)
- If reminder time was 2:55PM and main loop checked at 2:00PM → Too early
- Next check at 3:00PM → Too late (session already started)
- Result: **Reminder missed!**

**After**: Background thread checks every 60 seconds
- Thread checks at 2:54PM → Too early
- Thread checks at 2:55PM → **Reminder sent!** ✅
- Result: **Reminder caught within 1-minute accuracy**
