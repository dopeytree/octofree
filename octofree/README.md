# 🐙 octofree

Never miss Octopus free electricity again! 
- 💰 *Saving Sessions* are frequent during *high winds* 
- 👩‍💻 Octopus Energy send an email to the registered account holder about 48hours before
- ❌ We then forget to act
- ✅ Hence **octofree!**

The script scans the website https://octopus.energy/free-electricity/ for the next seshion date & time then sends a Discord webhook notification to your server.

## Requirements 

- octopus energy customer
- 24/7 powered: server / pc / mac / raspberry pi / etc
- internet access
- python3
- discord [server]
- discord [mobile device] 

## Virtual Environment

Prefered method is running in a Python virtual environment located a `.venv` folder.

- create the virtual environment:

```sh
python3 -m venv .venv
```

- activate the virtual environment (macOS/Linux):

```sh
source .venv/bin/activate
```

## Configuration

see `settings.env`

### Discord Webhook Notification

- [required for notifications]
- load or create a server in *discord*
- create a new channel called 'octofree'
- click the cogs to get the settings then find the webhooks button
- create a new webhook & copy the url
- set your *discord* webhook URL in `settings.env`
  

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```


### Test Mode

- Allows notifcation testing
- DEFAULT - Set to `false` to send only 1x notification per *saving sessions*
- Set to `true` to send > than 1x notification per current session
- `True` currently only works during an *active* session session

```
TEST_MODE=true

TEST_MODE=false
```



### Single Run

- Run the script once and exit (instead of looping every hour)
- Set to `false` for continuous hourly monitoring.

```
SINGLE_RUN=true
```

### Logs

- `output/last_sent_session.txt`: Tracks the last session for which a notification was sent.
- `output/octofree.log`: Main log file for all activity and errors.
