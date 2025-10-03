# 🐙 octofree - Is here to serve
- 🐙 Octopus - Free Electric!!! ⚡APP — 16:53
  - 🕰️ 12-2pm, Saturday 4th October
  - 📣 T- 5mins to Delta!
  - 🐰 End State 

## Never miss Octopus free electricity again! 
- 💰 *saving sessions* are free electric periods (usually 1-2hrs) frequent during *strong winds* 
  - 👩‍💻 48 hours prior Octopus Energy send an email to the account holder
  - ❌ we then forget to act, missing out on free energy
  - ✅ hence octofree will ping your mobile!

- 🧠 the script scans https://octopus.energy/free-electricity/ 
  - 📆 extracts the next *saving session* date & time 
  - 📱 sends you a [discord webhook](#discord-webhook-notification) notification on your mobile
  - 📣 reminds you again 5mins before *saving session* starts
  - 🐰 warns 3mins before the end state

![logo](https://github.com/dopeytree/octofree/blob/61e16adea141812f674ca91d86ab697ac02e0c91/logo_octofree.png?raw=true)

## Screenshot

![screenshot](https://github.com/dopeytree/octofree/blob/30b013c68437122c40854ba1d52ec4a67115318f/screenshot.png?raw=true)

## Requirements 

- octopus energy customer + signed up to saving sessions
- 24/7 powered - server | pc | mac | raspberry pi | etc
- internet access
- python3
- [discord webhook](#discord-webhook-notification) [server]
- discord [mobile device] 

## Installation 

<details>
<summary>- Virtual Environment</summary>

## Virtual Environment

Preferred method is [docker](#docker) but you can also run in a Python virtual environment located a `.venv` folder

- create the virtual environment:
```sh
python3 -m venv .venv
```
- activate the virtual environment (macOS/Linux):
```sh
source .venv/bin/activate
```
- set [settings](#settings-configuration) in settings.env 
- run the script
```sh  
 python3 octofree/octofree.py 
 ```
</details>

<details>
<summary>- Unraid Server</summary>

## Unraid Server

- add CONTAINER
- repo url: 
```sh 
ghcr.io/dopeytree/octofree:latest 
```
- advanced --> icon url: 
```sh 
https://github.com/dopeytree/octofree/blob/61e16adea141812f674ca91d86ab697ac02e0c91/logo_octofree.png?raw=true
```
#### add VARIABLE -> discord:
- `key` = 
```sh
DISCORD_WEBHOOK_URL
```
- `value` = 
- `enter_your_discord_server_webhook`

#### add VARIABLE -> test mode:
- `key`=
```sh
TEST_MODE
```
- `value` = 
```sh
false
```
#### add VARIABLE -> loop:
- `key` = 
```sh
SINGLE_RUN
```
- `value` = 
```sh
false
  ```
#### add PATH:
- `container path` = 
```sh
  /data
```
- `host path` = 
```sh
/mnt/user/appdata/octofree
```
#### APPLY settings
</details>

<details>
<summary>- Docker</summary>

## Docker

- Official published image on GitHub Container Registry :

```sh
docker pull ghcr.io/dopeytree/octofree:latest
```

Run the published image (recommended):

```sh
docker run --rm \
  --env-file ./octofree/settings.env \
  -v /path/on/host/octofree-data:/data \
  ghcr.io/dopeytree/octofree:latest
```

#### Notes:

- Use `--env-file ./octofree/settings.env` or set individual `-e` variables to provide your 
  - `DISCORD_WEBHOOK_URL`, `OUTPUT_DIR`, and other options
  - If no `settings.env` file exists in your workspace, copy or create one from `octofree/settings.env.template`
- Bind-mount a host folder to persist logs and state
  - Set `OUTPUT_DIR=/data` (or another mounted path) so the `output/` files appear on the host

#### Optional quick local build:

```sh
# Build locally (if you need to modify code or prefer a local image)
docker build -t octofree ./octofree
```
```sh
# Run the locally built image
docker run --rm --env-file ./octofree/settings.env -v /path/on/host/octofree-data:/data octofree
```

If you want the helper script and vulnerability scan, run the included `./octofree/build.sh` (it builds the image and runs a Trivy scan).

## Example `docker-compose.yml` (recommended for long-running deployments):

```yaml
version: '3.8'
services:
  octofree:
    image: ghcr.io/dopeytree/octofree:latest
    environment:
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
      - OUTPUT_DIR=/data
      - SINGLE_RUN=false
      - TEST_MODE=false
    volumes:
      - /path/on/host/octofree-data:/data
    restart: unless-stopped
```

### Docker Tips & troubleshooting
- If you change `settings.env` locally, avoid rebuilding by supplying `--env-file` or `-e` variables at `docker run` time
- Check logs and last-sent session inside the mounted folder (`octofree.log`, `last_sent_session.txt`) when debugging notifications
- The `build.sh` script runs Trivy; if you don't have Trivy available you can skip it and use `docker build` directly

</details>

## Settings

see `settings.env`

<details>
<summary>- Discord Webhook Notification</summary>

### Discord Webhook Notification

- [required for notifications]
- load or create a server in *discord*
- create a new channel called 'octofree'
- click the cogs to get the settings then find the webhooks button
- create a new webhook & copy the url
- set your *discord* webhook URL in `settings.env`

```sh
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```
</details>

<details>
<summary>- Test Mode</summary>

### Test Mode

- allows multiple notifcation testing when 1x is live
- DEFAULT=`false` to send only 1x notification per *saving sessions*
- set to `true` to send > than 1x notification per current session
- `true` currently only works during an *active* saving session

```sh
TEST_MODE=false
TEST_MODE=true
```
</details>

<details>
<summary>- Single Run</summary>

### Single Run

- to loop or not
- true = runs the script once & exits (instead of looping every hour)
- DEFAULT=false
- set to `false` for continuous hourly monitoring

```sh
SINGLE_RUN=false
SINGLE_RUN=true
```
</details>

<details>
<summary>- Storage</summary>

### Storage

Only required for [unraid](#unraid) & [docker](#docker)
```sh
volumes:
      - /path/on/host/octofree-data:/data
```
</details>

## Logs

Check your setup for the exact path to the [storage](#storage) ouput folder
- `output/octofree.log`
  - main log file for all activity and errors
- `output/last_sent_session.txt`
  - tracks the last session for which a notification was sent
