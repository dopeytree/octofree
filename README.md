# 🐙 octofree

Never miss Octopus free electricity again! 
*Saving Sessions* are frequent during high winds. Usually octopus send an email about 48hours before hand. 
We then forget.
Hence octofree. 

This script scans the website https://octopus.energy/free-electricity/ for the next seshion date & time then sends a Discord webhook notification to you.

## Virtual Environment

This project uses a Python virtual environment located in the `.venv` folder.

To activate the virtual environment (macOS/Linux, zsh):

```sh
source .venv/bin/activate
```

To deactivate:

```sh
deactivate
```

If you need to create the virtual environment:

```sh
python3 -m venv .venv
```

## Features & Configuration

### Discord Webhook Notification

Set your Discord webhook URL in `settings.env`:

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

This is required for notifications.

### Test Mode

Enable test mode: allows more than 1x notification per current session:

```
TEST_MODE=true
```

Set to `false` to only notify for new sessions.

### Single Run

Run the script once and exit (instead of looping every hour):

```
SINGLE_RUN=true
```

Set to `false` for continuous monitoring.

### Output Files

- `output/last_sent_session.txt`: Tracks the last session for which a notification was sent.
- `output/octofree.log`: Main log file for all activity and errors.
