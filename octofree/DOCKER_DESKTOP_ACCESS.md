# How to Access the TUI from Docker Desktop Console

## Method 1: Direct Command (Easiest)

1. In Docker Desktop, find your `octofree-tui-test` container
2. Click the **Terminal** icon (or three dots → Open in Terminal)
3. Type this command:
   ```bash
   octofree-monitor
   ```
4. Press Enter
5. The TUI dashboard will launch! 🎉

## Method 2: Interactive Menu

1. In Docker Desktop, click the **Terminal** icon
2. Type this command:
   ```bash
   docker-console
   ```
3. Press `1` to launch TUI Monitor

## Keyboard Controls in TUI

- **TAB** or **1-5**: Switch tabs
- **↑/↓** or **j/k**: Scroll
- **q**: Quit back to shell

## Troubleshooting

If you see "command not found":
- Make sure you're in the container terminal (you should see `/ #` or `/app #`)
- The binary is located at: `/usr/local/bin/octofree-monitor`
- Try the full path: `/usr/local/bin/octofree-monitor`

## Note

✅ No need to copy files - the Go binary is already built into the Docker image!
✅ The multi-stage Dockerfile compiled it during `docker build`
✅ It's in `/usr/local/bin/` which is in the container's PATH
