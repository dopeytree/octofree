# Unraid Docker Template XML Additions for Octofree TUI Monitor

## Add these sections to your Unraid XML template

### Option 1: Console Button (Recommended)
Add this to launch TUI when clicking Console button:

```xml
  <Config Name="Shell" Target="" Default="/bin/sh" Mode="" Description="Shell to use when opening console" Type="Variable" Display="advanced" Required="false" Mask="false">/usr/local/bin/docker-console</Config>
```

This will show an interactive menu when you click Console in Unraid.

---

### Option 2: WebUI Link (Alternative)
Add this to create a "Monitor" button in the Unraid UI:

```xml
  <Config Name="Monitor WebUI" Target="" Default="" Mode="" Description="Launch TUI Monitor (use via Console)" Type="Label" Display="always" Required="false" Mask="false">Click Console and type: octofree-monitor</Config>
```

---

### Option 3: Post Arguments (Auto-launch TUI)
If you want the TUI to launch automatically when opening console:

```xml
  <PostArgs>sh -c "python3 /app/main.py &amp; exec /usr/local/bin/docker-console"</PostArgs>
```

This will:
- Start Python app in background
- Show interactive menu when console is opened

---

### Full Example Template Section

Here's a complete section you can add to your template:

```xml
  <!-- TUI Monitor Configuration -->
  <Config Name="Console Shell" Target="" Default="/usr/local/bin/docker-console" Mode="" Description="Opens interactive menu when clicking Console. Options: 1=TUI Monitor, 2=View Logs, 3=Shell" Type="Variable" Display="advanced" Required="false" Mask="false">/usr/local/bin/docker-console</Config>
  
  <Config Name="TUI Monitor Info" Target="" Default="" Mode="" Description="To launch TUI monitor, click Console in Unraid and select option 1, or run: docker exec -it octofree octofree-monitor" Type="Label" Display="always" Required="false" Mask="false"></Config>
```

---

### Complete Docker Run Command for Reference

```bash
docker run -d \
  --name='octofree' \
  -e 'DISCORD_WEBHOOK_URL'='your_webhook_url_here' \
  -e 'SINGLE_RUN'='false' \
  -e 'TEST_MODE'='false' \
  -e 'OUTPUT_DIR'='/data' \
  -v '/mnt/user/appdata/octofree':'/data':'rw' \
  'octofree'
```

---

### How Users Access the TUI

After installing with the updated template, users can:

**Method 1 - Console Button:**
1. Click "Console" on the Docker container in Unraid
2. See interactive menu
3. Press `1` to launch TUI Monitor

**Method 2 - Direct Command:**
```bash
docker exec -it octofree octofree-monitor
```

**Method 3 - Terminal in Unraid:**
1. Open terminal in Unraid
2. Run: `docker exec -it octofree octofree-monitor`

---

### Notes for Template

- The TUI requires a TTY (terminal), so it only works via Console, not WebUI
- The Python app runs continuously in the background
- TUI can be launched/closed multiple times without affecting the scraper
- The TUI reads from the same `/data` directory as the Python app
- Keyboard controls: TAB to switch tabs, arrow keys to navigate, q to quit

---

### Icon and Description Updates (Optional)

You might want to update these in your template:

```xml
  <Overview>Octofree Energy Monitor - Tracks Octopus Energy free electricity sessions. Now includes interactive TUI dashboard for monitoring! Click Console to access the TUI monitor.</Overview>
  
  <Description>
    Monitors and notifies about Octopus Energy free electricity sessions.
    
    Features:
    - Automatic session detection and Discord notifications
    - Interactive Terminal UI (TUI) dashboard with real-time monitoring
    - Multiple tabs: Overview, Upcoming Sessions, Past Sessions, Logs, README
    - Beautiful terminal interface with octopus ASCII art
    
    Access the TUI: Click Console and select "Launch TUI Monitor" or run: docker exec -it octofree octofree-monitor
  </Description>
```

---

### Testing the Template

After updating your template:

1. Install/Update the container in Unraid
2. Click the Docker icon → Console
3. You should see the interactive menu
4. Press `1` to launch the TUI
5. Press `q` to exit back to menu or container

The Python app continues running in the background for scraping and notifications!
