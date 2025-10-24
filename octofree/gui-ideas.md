# Terminal GUI Ideas for Octofree

## Overview

This document explores options for building a full terminal GUI for the Octofree application, moving beyond the current loading screen to create an interactive dashboard that displays session status, countdown timers, and system information.

## 🎨 Terminal GUI Libraries

### 1. Rich (Recommended Starting Point)

**Description**: Modern Python library for rich text and beautiful formatting in the terminal. Perfect for live-updating dashboards.

**Key Features**:

- Live updating displays with `rich.live.Live`
- Beautiful tables for session lists
- Progress bars, spinners, syntax highlighting
- Panels and layouts
- Works great in Docker containers
- Lightweight and easy to integrate

**Example Dashboard**:

```text
┌─────────────────── OCTOFREE DASHBOARD ────────────────────┐
│ Time: 19:45:32 | Status: 🟢 Running | Next Check: 20:00  │
├───────────────────────────────────────────────────────────┤
│ UPCOMING SESSIONS                                         │
│ ┌───────────────┬──────────────┬──────────────┬─────────┐ │
│ │ Date          │ Time         │ Status       │ Notified│ │
│ ├───────────────┼──────────────┼──────────────┼─────────┤ │
│ │ 25 Oct 2025   │ 13:00-14:00  │ ⏳ Scheduled │ ✓       │ │
│ │ 25 Oct 2025   │ 16:30-17:30  │ ⏳ Scheduled │ ✓       │ │
│ └───────────────┴──────────────┴──────────────┴─────────┘ │
│                                                           │
│ ACTIVE SESSION                                            │
│ 🔋 Free Power: 13:00-14:00 (45 mins remaining)           │
│ [████████████████░░░░] 75%                                │
└───────────────────────────────────────────────────────────┘
```

**Installation**: `pip install rich`

**Links**:

- [Rich Documentation](https://rich.readthedocs.io/)
- [Rich Live Display Examples](https://rich.readthedocs.io/en/stable/live.html)
- [Rich Table Examples](https://rich.readthedocs.io/en/stable/tables.html)

### 2. Textual (Full TUI Framework)

**Description**: Complete terminal user interface framework from the Rich creator. Like building a web app for the terminal.

**Key Features**:

- Mouse support (click buttons, scroll)
- Keyboard navigation
- Widgets: buttons, inputs, lists, headers, footers
- CSS-like styling for layouts
- Reactive data binding
- Multiple screens/views

**Use Cases**:

- Interactive app where users can:
  - Click to view session details
  - Navigate between screens (Dashboard → History → Settings)
  - Manually trigger scrapes
  - Toggle test mode on/off
  - Configure webhooks

**Installation**: `pip install textual`

**Links**:

- [Textual Documentation](https://textual.textualize.io/)
- [Textual Examples](https://github.com/Textualize/textual/tree/main/examples)
- [Textual Widgets](https://textual.textualize.io/widgets/)

### 3. Blessed/Curses (Traditional)

**Description**: Lower-level terminal control libraries.

**Pros**:

- Full control over terminal
- Lightweight

**Cons**:

- More manual work
- Older, less modern aesthetic
- Steeper learning curve

**Not recommended unless you need very specific control.**

## 🌐 Web Dashboard + Terminal Aesthetic

### Terminal.css Style Web Dashboard

**Description**: Build a Flask/FastAPI web server with CSS that mimics terminal aesthetics.

**Frameworks**:

- **Terminal.css**: Retro terminal look
- **XTerm.js**: Actual terminal emulator in browser
- **Hack/Monaco fonts**: Monospace terminal fonts

**Benefits**:

- Access from phone/tablet
- Multiple users can view
- Easy to share with household
- Can embed in Home Assistant, etc.

**Links**:

- [Terminal.css](https://terminalcss.xyz/)
- [XTerm.js](https://xtermjs.org/)
- [Hack Font](https://sourcefoundry.org/hack/)

### Web Terminal Streaming (Best of Both Worlds)

**Description**: Stream your terminal GUI to a web browser while keeping terminal aesthetics.

**Tools**:

- **ttyd**: Share terminal over web
- **gotty**: GoTTY - Terminal sharing over HTTP

**How it works**:

- Your Rich/Textual app runs in terminal
- Streams to web browser
- Users see actual terminal in browser
- Keep all terminal aesthetics, gain web access

**Links**:

- [ttyd GitHub](https://github.com/tsl0922/ttyd)
- [ttyd Demo](https://tsl0922.github.io/ttyd/)
- [GoTTY](https://github.com/yudai/gotty)

## 🐳 Docker Considerations

### Terminal GUI in Docker

```dockerfile
# Add to your existing Dockerfile
ENV TERM=xterm-256color  # Enable colors
ENV PYTHONUNBUFFERED=1   # Real-time output

# For interactive TUI (Textual):
# docker run -it octofree

# For live dashboard (Rich):
# Works with docker logs -f automatically
```

### Web Dashboard in Docker

```dockerfile
EXPOSE 8080
# Add web server (Flask/FastAPI)
# docker run -p 8080:8080 octofree
# Access at http://localhost:8080
```

## 🎯 Implementation Recommendations

### Phase 1: Rich Dashboard (Easiest Win)

- Replace current logging with Rich dashboard
- Show live session queue, countdown timers, status
- Keep your loading animation
- Works perfectly in Docker logs
- ~2-3 hours of work

### Phase 2: Optional Upgrades

**For Interactivity**: Add Textual

- Turn into full TUI app
- Keyboard shortcuts (R to refresh, T for test mode, Q to quit)
- Multiple screens

**For Remote Access**: Add FastAPI + Terminal.css

- Small web server alongside scraper
- REST API for session data
- Terminal-styled web dashboard
- Could add webhook config via web UI

## 📋 Example Implementation Plan (Rich Dashboard)

```python
# dashboard.py
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from datetime import datetime

def create_dashboard(scheduled_sessions, current_time):
    layout = Layout()

    # Header
    layout.split(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )

    # Your octopus loading screen on startup
    # Then switch to live dashboard

    # Update every second
    # Show countdown to next session
    # Highlight active sessions
    # Show scraper status

    return layout

# In main.py, replace logging loop with:
with Live(create_dashboard(...), refresh_per_second=1):
    # Your existing main loop
```

## 🤔 Decision Questions

1. **Interactivity**: Do you need to control it, or just watch it?
   - Watch only → Rich dashboard
   - Control needed → Textual TUI or Web UI

2. **Access**: Terminal only, or remote viewing?
   - Terminal only → Rich/Textual
   - Remote → Web dashboard or terminal streaming

3. **Complexity**: How much time to invest?
   - 2-3 hours → Rich dashboard
   - 1-2 days → Textual TUI
   - 2-3 days → Web dashboard

4. **Docker logs**: Do you view via `docker logs -f`?
   - If yes → Rich works great, just prints to stdout
   - Textual needs `docker run -it` (interactive mode)

## 🔗 Additional Resources

- [Awesome TUI](https://github.com/rothgar/awesome-tui) - Curated list of terminal UI tools
- [Terminal Trove](https://terminaltrove.com/) - Terminal UI inspiration
- [Rich Gallery](https://rich.readthedocs.io/en/stable/gallery.html) - Rich examples
- [Textual Gallery](https://textual.textualize.io/gallery/) - Textual examples

## 📝 Notes

- All options maintain your current loading screen animation
- Rich is the easiest to implement and works with your existing Docker setup
- Textual provides the most interactive experience
- Web options provide remote access but require additional infrastructure
