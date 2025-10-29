# ✅ Octofree TUI Docker Integration - Complete

## What Was Done

### 1. ✅ Replaced Dockerfile
- **Old**: `Dockerfile` → `Dockerfile.old` (backed up)
- **New**: `Dockerfile.multi` created with multi-stage build
- Build Context: Parent directory (includes both `octofree/` and `bubbletea/`)

### 2. ✅ Updated Build Script
- **File**: `build-with-tui.sh`
- Builds from parent directory to include both Python and Go code
- Shows helpful post-build instructions

### 3. ✅ Auto-Launch TUI Option
- **File**: `docker-console.sh` - Interactive menu when opening console
- **File**: `tui-launcher.sh` - Quick launcher from host

### Build Status: ✅ SUCCESS
```
Build time: ~10.7 seconds
Final image: octofree:latest
Go binary included: /usr/local/bin/octofree-monitor
```

---

## How to Use

### Building the Image
```bash
cd /path/to/octofree
./build-with-tui.sh
```

### Running the Container
```bash
docker run -d \
  --name octofree \
  -v $(pwd)/octofree/output:/data \
  -e DISCORD_WEBHOOK_URL="your_webhook_url" \
  octofree
```

### Launching the TUI

**Option 1 - Quick Launcher (Easiest):**
```bash
./tui-launcher.sh
```

**Option 2 - Direct Docker Command:**
```bash
docker exec -it octofree octofree-monitor
```

**Option 3 - Interactive Menu:**
```bash
docker exec -it octofree docker-console
```
Then press `1` to launch TUI

---

## Unraid XML Template Code

### Copy this to your Unraid template repository

```xml
<!-- TUI Monitor Console Configuration -->
<Config Name="Console Shell" 
        Target="" 
        Default="/usr/local/bin/docker-console" 
        Mode="" 
        Description="Opens interactive menu when clicking Console. Options: 1=TUI Monitor, 2=View Logs, 3=Shell Access" 
        Type="Variable" 
        Display="advanced" 
        Required="false" 
        Mask="false">/usr/local/bin/docker-console</Config>

<!-- TUI Monitor Information -->
<Config Name="TUI Monitor" 
        Target="" 
        Default="" 
        Mode="" 
        Description="Interactive Terminal Dashboard: Click Console button and select option 1, or run: docker exec -it octofree octofree-monitor" 
        Type="Label" 
        Display="always" 
        Required="false" 
        Mask="false">Access via Console</Config>
```

### Update Description (Optional)
```xml
<Overview>Octofree Energy Monitor - Tracks Octopus Energy free electricity sessions with interactive TUI dashboard. Click Console to access real-time monitoring interface!</Overview>

<Description>
Monitors and notifies about Octopus Energy free electricity sessions.

**NEW: Interactive Terminal UI Dashboard!**
- Real-time monitoring with beautiful terminal interface
- Multiple tabs: Overview, Upcoming, Past Sessions, Logs, README
- ASCII art octopus mascot
- Live countdown timers and session tracking

**Access TUI:**
1. Click Console in Unraid
2. Select option 1 to launch TUI Monitor
3. Or run: docker exec -it octofree octofree-monitor

**Features:**
- Automatic session detection and Discord notifications
- Hourly scraping of Octopus Energy website
- Persistent storage with volume mounting
- Runs Python scraper in background while TUI is available on-demand
</Description>
```

### Example Docker Run in Template
```xml
<Overview>octofree</Overview>
<Category>Tools:</Category>
<Name>octofree</Name>
<Support>https://github.com/dopeytree/octofree</Support>
<Repository>octofree:latest</Repository>
<Registry>https://hub.docker.com/r/yourusername/octofree</Registry>
<Shell>/usr/local/bin/docker-console</Shell>

<Config Name="DISCORD_WEBHOOK_URL" 
        Target="DISCORD_WEBHOOK_URL" 
        Default="" 
        Mode="" 
        Description="Discord webhook URL for notifications" 
        Type="Variable" 
        Display="always" 
        Required="true" 
        Mask="false"></Config>

<Config Name="OUTPUT_DIR" 
        Target="OUTPUT_DIR" 
        Default="/data" 
        Mode="" 
        Description="Output directory for logs and sessions" 
        Type="Variable" 
        Display="advanced" 
        Required="false" 
        Mask="false">/data</Config>

<Config Name="AppData" 
        Target="/data" 
        Default="/mnt/user/appdata/octofree" 
        Mode="rw" 
        Description="Container Path: /data" 
        Type="Path" 
        Display="always" 
        Required="true" 
        Mask="false">/mnt/user/appdata/octofree</Config>

<!-- TUI Monitor Console Configuration -->
<Config Name="Console Shell" 
        Target="" 
        Default="/usr/local/bin/docker-console" 
        Mode="" 
        Description="Opens interactive menu when clicking Console" 
        Type="Variable" 
        Display="advanced" 
        Required="false" 
        Mask="false">/usr/local/bin/docker-console</Config>
```

---

## User Instructions for Unraid

### After Installing from Community Applications:

**1. Start the Container**
- Install "Octofree" from Community Applications
- Configure Discord webhook URL
- Start the container

**2. Access the TUI Monitor**

**Method A - Console Button (Easiest):**
1. Click the Octofree icon in Docker tab
2. Click "Console"
3. You'll see an interactive menu
4. Press `1` to launch the TUI Monitor
5. Press `q` to quit back to menu

**Method B - Terminal Command:**
1. Open Unraid terminal
2. Run: `docker exec -it octofree octofree-monitor`
3. Press `q` to exit

**3. Using the TUI**
- **TAB** or **[1-5]**: Switch between tabs
- **↑/↓** or **j/k**: Scroll logs/README
- **←/→** or **h/l**: Navigate README files
- **r**: Refresh data
- **q**: Quit

---

## Files Created

✅ `/octofree/Dockerfile.multi` - Multi-stage Docker build file
✅ `/octofree/Dockerfile.old` - Backup of original Dockerfile  
✅ `/octofree/build-with-tui.sh` - Build script (parent directory context)
✅ `/octofree/tui-launcher.sh` - Quick TUI launcher from host
✅ `/octofree/docker-console.sh` - Interactive console menu
✅ `/octofree/DOCKER_TUI_README.md` - Detailed Docker documentation
✅ `/octofree/UNRAID_TEMPLATE.md` - This file with Unraid XML
✅ `/bubbletea/octofree-monitor` - Go binary (built inside Docker)

---

## Architecture

```
┌─────────────────────────────────────┐
│   Docker Container: octofree        │
├─────────────────────────────────────┤
│                                     │
│  Background Process:                │
│  ├── Python main.py (scraper)      │
│  └── Runs continuously              │
│                                     │
│  On-Demand TUI:                     │
│  ├── /usr/local/bin/octofree-monitor│
│  ├── Reads from /data               │
│  └── Launch with docker exec        │
│                                     │
│  Interactive Console:               │
│  ├── /usr/local/bin/docker-console │
│  └── Menu: TUI / Logs / Shell      │
│                                     │
└─────────────────────────────────────┘
         ↕
   /data (volume)
   ↕
   Host: /mnt/user/appdata/octofree
```

---

## What Users See

### When Clicking Console in Unraid:
```
╔════════════════════════════════════════════════════╗
║         OCTOFREE ENERGY MONITOR                    ║
╚════════════════════════════════════════════════════╝

Python app is running in the background...

Options:
  [1] Launch TUI Monitor (interactive dashboard)
  [2] View logs (tail -f)
  [3] Shell access
  [q] Exit console

Choose an option: _
```

### When Selecting Option 1 (TUI):
```
++ OCTOFREE ENERGY MONITOR ++  Tuesday 29 October 2025 - 01:05:23

  Overview    Upcoming    Past    Logs    README

          ,'""'.
         / _  _ \
         |(@)(@)|
         )  __  (
        /,')))(('.\
       (( ((  )) ))
        `\ `)(' /'

────────────────────────────────────────────────────

⏳ Next scrape in: 45m 12s

/////// Upcoming Sessions (2)
...
```

---

## Testing

Tested successfully:
✅ Multi-stage build completes (~10.7s)
✅ Go binary compiled and included  
✅ Python app runs in background
✅ TUI launches with `docker exec -it octofree octofree-monitor`
✅ Interactive menu works
✅ Volume mounting for /data
✅ All scripts executable

---

## Next Steps for Unraid Template Repo

1. Copy the XML snippets from above
2. Add to your Unraid template XML file
3. Update Overview and Description
4. Test installation from Community Applications
5. Document in template README that users should click Console → option 1

---

## Support

- Main README: `/README.md`
- GUI README: `/bubbletea/GUI-README.md`
- Docker README: `/octofree/DOCKER_TUI_README.md`
- Unraid Template: This file

For issues, check logs:
```bash
docker exec octofree tail -f /data/octofree.log
```

Or access via TUI (Logs tab, option 4)!
