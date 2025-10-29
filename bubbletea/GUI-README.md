# Bubbletea Terminal GUI for Octofree

A beautiful terminal-based monitoring interface for the Octofree application built with [Bubbletea](https://github.com/charmbracelet/bubbletea).

## Features

- 🕐 **Real-time Clock** - Live updating current date and time
- 📊 **Data Overview** - Quick stats on upcoming, past, and extracted sessions
- 📅 **Upcoming Sessions Table** - Detailed view of scheduled free electricity sessions
- 📚 **Past Sessions History** - Track completed sessions and notifications
- 🔍 **Scraper Status** - See when data was last fetched from Octopus Energy
- 🐙 **ASCII Art Octopus** - Fun visual element from the original loading screen
- ⌨️ **Keyboard Navigation** - Switch between tabs with number keys or TAB

## Interface

The interface has three main tabs:

1. **Overview** (Press `1`)
   - Quick statistics dashboard
   - Last extracted sessions
   - Next upcoming session with countdown
   - Stats boxes showing counts

2. **Upcoming** (Press `2`)
   - Table view of all scheduled sessions
   - Start/end times
   - Notification status (📢 notified, ⏰ reminder, 🏁 end reminder)

3. **Past** (Press `3`)
   - Historical sessions
   - Notification tracking
   - Reminder delivery status

## Running the Application

1. Ensure Go is installed (version 1.21 or later)
2. Navigate to the project directory
3. Run `go mod tidy` to download dependencies
4. Run `go run main.go` or build with `go build -o octofree-monitor main.go`

## Keyboard Controls

- `1`, `2`, `3` - Switch to specific tab
- `TAB` - Cycle through tabs
- `r` - Refresh data from octofree output files
- `q` or `Ctrl+C` - Quit application

## Data Source

The monitor reads data from the `../octofree/output/` directory:
- `scheduled_sessions.json` - Upcoming sessions
- `past_scheduled_sessions.json` - Completed sessions
- `last_extracted_sessions.json` - Most recent scrape results
- `x_scraper_log.json` - Scraper activity logs

## Dependencies

- [Bubbletea](https://github.com/charmbracelet/bubbletea) v0.25.0 - TUI framework
- [Bubbles](https://github.com/charmbracelet/bubbles) v0.18.0 - TUI components (tables)
- [Lipgloss](https://github.com/charmbracelet/lipgloss) v0.9.1 - Terminal styling