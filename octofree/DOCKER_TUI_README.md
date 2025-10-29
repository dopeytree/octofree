# Docker Integration for Octofree TUI Monitor

## Quick Start

### 1. Build the Docker Image
```bash
cd /path/to/octofree
docker build -f Dockerfile.new -t octofree .
```

### 2. Run the Container
```bash
docker run -d \
  --name octofree \
  -v /path/to/data:/data \
  -e DISCORD_WEBHOOK_URL="your_webhook_url" \
  octofree
```

## Using the TUI Monitor

### Option A: Direct Launch (Recommended)
When you want to view the TUI, attach to the console with a TTY:

```bash
docker exec -it octofree octofree-monitor
```

This will launch the interactive dashboard directly!

### Option B: Interactive Menu
Attach to console and get a menu:

```bash
docker exec -it octofree docker-console
```

This shows a menu with options:
1. Launch TUI Monitor
2. View logs
3. Shell access

### Option C: Docker Desktop/Unraid Console
When you click "Console" in Docker Desktop or Unraid, you can:

1. **Modify the Dockerfile** to use the console script as default:
   ```dockerfile
   CMD ["sh", "-c", "python3 /app/main.py & /usr/local/bin/docker-console"]
   ```

2. Or **use the exec command** from the Unraid template.

## Background vs Foreground

### Current Setup (Recommended)
- **Python app runs in background** (doing the actual scraping/notifications)
- **TUI monitor is launched on-demand** (for viewing status)

### Alternative: TUI as Main Process
If you want the TUI to be the main interface:

```dockerfile
# In Dockerfile, change CMD to:
CMD ["sh", "-c", "python3 /app/main.py & /usr/local/bin/octofree-monitor"]
```

This will:
- Start Python app in background
- Launch TUI as the foreground process
- When TUI exits, container keeps running

## Unraid Template Configuration

Add this to your Unraid template XML:

```xml
<Config Name="Console Command" Target="" Default="" Mode="" Description="Opens the monitoring TUI" Type="Variable" Display="advanced" Required="false" Mask="false">docker exec -it octofree octofree-monitor</Config>
```

Or add a custom script button:
```xml
<Config Name="Launch Monitor" Target="" Default="" Mode="" Description="Launch TUI Monitor" Type="Path" Display="always" Required="false" Mask="false">/usr/local/bin/octofree-monitor</Config>
```

## Manual Access

### From Host Machine
```bash
# Launch TUI
docker exec -it octofree octofree-monitor

# View logs
docker exec -it octofree tail -f /data/octofree.log

# Shell access
docker exec -it octofree /bin/sh
```

### Inside Container
If you're already in the container shell:
```bash
# Launch TUI
octofree-monitor

# It's in the PATH, so just run it!
```

## Building from Scratch

The multi-stage Dockerfile:
1. **Stage 1**: Compiles the Go TUI app
2. **Stage 2**: Creates final Python image with the binary

This keeps the final image small (no Go compiler needed).

## Troubleshooting

### TUI doesn't display properly
Make sure you're using `-it` flags:
```bash
docker exec -it octofree octofree-monitor
```

### Python app not running
Check if it's running:
```bash
docker exec octofree ps aux | grep python
```

### Can't see output directory
Make sure volume is mounted:
```bash
docker inspect octofree | grep Mounts -A 10
```

## File Locations in Container

- **TUI Binary**: `/usr/local/bin/octofree-monitor`
- **Python App**: `/app/main.py`
- **Output Data**: `/data/` (mounted volume)
- **Console Script**: `/usr/local/bin/docker-console`

## Performance Notes

- TUI reads from the same `/data` directory as the Python app
- No performance impact on Python app when TUI is not running
- TUI can be launched/closed multiple times without affecting the scraper
