# 🐙 octofree

Never miss Octopus free electricity again! 
- 💰 *Saving Sessions* are frequent during *high winds* 
- 👩‍💻 Octopus Energy send an email to the registered account holder about 48hours before
- ❌ We then forget to act
- ✅ Hence octofree!

The script scans the website https://octopus.energy/free-electricity/ for the next session date & time then sends a Discord webhook notification to your mobile.

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

### Persisting output when running in Docker

By default the script writes runtime files to the `output/` folder inside the project. When running inside Docker you should bind-mount a host folder so logs and state persist across container restarts. There are two simple options:

- Set the `OUTPUT_DIR` environment variable to a path inside the container that you've mounted from the host (recommended). For example, mount a host folder to `/data` and set `OUTPUT_DIR=/data` in `settings.env` or your container environment.
- Alternatively, mount your host folder directly over the container's project `output/` folder.

Example `docker-compose.yml` snippet (recommended - mount to `/data` and set `OUTPUT_DIR`):

```yaml
services:
	octofree:
		image: your-image-name:latest
		environment:
			- DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
			- OUTPUT_DIR=/data
			- SINGLE_RUN=false
			- TEST_MODE=false
		volumes:
			- /path/on/host/octofree-data:/data
		restart: unless-stopped
```

When the container runs, the script will use the `OUTPUT_DIR` value to write `octofree.log` and `last_sent_session.txt` to the mounted host folder so you can inspect them on the host (Unraid) even after the container stops or is recreated.
