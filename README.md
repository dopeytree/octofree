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
- docker
- discord [server]
- discord [mobile device] 

## Virtual Environment

Preferred method is docker but you can also run in a Python virtual environment located a `.venv` folder.

- create the virtual environment:

```sh
python3 -m venv .venv
```

- activate the virtual environment (macOS/Linux):

```sh
source .venv/bin/activate
```

## Unraid 

- add container
- repo url: 
- ```sh 
  ghcr.io/dopeytree/octofree:latest 
  ```
- icon : 
- add variable:
- add variable:
- add variable: 
- add path:

## Docker

Prefer the official published image on GitHub Container Registry (recommended):

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

Notes:

- Use `--env-file ./octofree/settings.env` or set individual `-e` variables to provide your `DISCORD_WEBHOOK_URL`, `OUTPUT_DIR`, and other options. If no `settings.env` file exists in your workspace, copy or create one from `octofree/settings.env.template`.
- Bind-mount a host folder to persist logs and state. Set `OUTPUT_DIR=/data` (or another mounted path) so the `output/` files appear on the host.

Quick local build (optional, light documentation):

```sh
# Build locally (if you need to modify code or prefer a local image)
docker build -t octofree ./octofree

# Run the locally built image
docker run --rm --env-file ./octofree/settings.env -v /path/on/host/octofree-data:/data octofree
```

If you want the helper script and vulnerability scan, run the included `./octofree/build.sh` (it builds the image and runs a Trivy scan).

Example `docker-compose.yml` (recommended for long-running deployments):

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

Tips & troubleshooting
- If you change `settings.env` locally, avoid rebuilding by supplying `--env-file` or `-e` variables at `docker run` time.
- Check logs and last-sent session inside the mounted folder (`octofree.log`, `last_sent_session.txt`) when debugging notifications.
- The `build.sh` script runs Trivy; if you don't have Trivy available you can skip it and use `docker build` directly.
