# 🚀 Quick Reference - Octofree TUI

## Build & Run
```bash
./build-with-tui.sh
docker run -d --name octofree -v $(pwd)/octofree/output:/data octofree
```

## Launch TUI
```bash
./tui-launcher.sh          # Quick launcher
docker exec -it octofree octofree-monitor   # Direct
docker exec -it octofree docker-console     # Menu
```

## Unraid XML (Copy to Template)
```xml
<Config Name="Console Shell" Target="" Default="/usr/local/bin/docker-console" Mode="" 
        Description="Opens menu: 1=TUI Monitor, 2=Logs, 3=Shell" Type="Variable" 
        Display="advanced" Required="false" Mask="false">/usr/local/bin/docker-console</Config>
```

## TUI Controls
- **TAB** / **1-5**: Switch tabs
- **↑↓** / **jk**: Scroll
- **←→** / **hl**: Navigate READMEs  
- **r**: Refresh
- **q**: Quit

## File Locations
- Binary: `/usr/local/bin/octofree-monitor`
- Console: `/usr/local/bin/docker-console`
- Data: `/data` (volume mount)
- Logs: `/data/octofree.log`

## Features
✅ Multi-stage Docker build
✅ Go TUI compiled inside container
✅ Python scraper runs in background
✅ Interactive console menu
✅ Real-time monitoring dashboard
✅ 5 tabs: Overview, Upcoming, Past, Logs, README
