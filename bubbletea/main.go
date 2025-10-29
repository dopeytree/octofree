package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/table"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/glamour"
	"github.com/charmbracelet/lipgloss"
)

type Session struct {
	Session         string `json:"session"`
	StartTime       string `json:"start_time"`
	EndTime         string `json:"end_time"`
	ReminderTime    string `json:"reminder_time,omitempty"`
	EndReminderTime string `json:"end_reminder_time,omitempty"`
	Notified        bool   `json:"notified"`
	ReminderSent    bool   `json:"reminder_sent"`
	EndSent         bool   `json:"end_sent"`
}

type ScraperLog struct {
	Timestamp           string   `json:"timestamp"`
	WebsiteSessions     []string `json:"website_sessions"`
	XSessions           []string `json:"x_sessions"`
	NewSessionsFromX    []string `json:"new_sessions_from_x"`
	XProvidedUniqueData bool     `json:"x_provided_unique_data"`
}

type model struct {
	currentTime      time.Time
	lastScrapeTime   time.Time
	nextScrapeTime   time.Time
	lastExtracted    []string
	upcomingSessions []Session
	pastSessions     []Session
	scraperLogs      []ScraperLog
	logLines         []string
	upcomingTable    table.Model
	pastTable        table.Model
	spinner          spinner.Model
	activeTab        int // 0 = overview, 1 = upcoming, 2 = past, 3 = logs, 4 = readme
	logScroll        int
	readmeScroll     int
	readmeContent    string
	readmeFiles      []string
	selectedReadme   int
	quitting         bool
}

var (
	// Color styles
	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("201"))

	// Use different color (blue) for subtitles - NOT the same as title
	subtitleStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("39")).
			Bold(true)

	boxStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("39")).
			Padding(0, 1).
			Width(24)

	octopusStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("201")).
			Bold(true)

	infoStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("240"))

	tabActiveStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("15")).
			Background(lipgloss.Color("235")).
			Padding(0, 2)

	tabInactiveStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("15")).
				Padding(0, 2)

	statusGoodStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("39"))

	statusBadStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("15"))

	statusWarningStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("15"))
)

func initialModel() model {
	s := spinner.New()
	s.Spinner = spinner.Line
	s.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("39"))

	m := model{
		activeTab:    0,
		spinner:      s,
		logScroll:    0,
		readmeScroll: 0,
		readmeFiles: []string{
			"README.md",
			"DOCKER_TUI_README.md",
		},
		selectedReadme: 0,
	}

	// Load data from octofree output directory
	loadOctofreeData(&m)

	// Load first README
	loadReadme(&m, 0)

	// Initialize tables
	m.upcomingTable = createUpcomingTable(m.upcomingSessions)
	m.pastTable = createPastTable(m.pastSessions)

	// Auto-scroll logs to show latest entries (last 20 lines)
	if len(m.logLines) > 20 {
		m.logScroll = len(m.logLines) - 20
	} else {
		m.logScroll = 0
	}

	// Calculate next scrape time (1 hour from last scrape)
	if !m.lastScrapeTime.IsZero() {
		m.nextScrapeTime = m.lastScrapeTime.Add(time.Hour)
	} else {
		// If no last scrape, assume next scrape is in 1 hour from now
		m.nextScrapeTime = time.Now().Add(time.Hour)
	}

	return m
}

func loadOctofreeData(m *model) {
	// Get the output directory - use /data in Docker, or ../octofree/output locally
	var outputDir string
	if _, err := os.Stat("/data/octofree.log"); err == nil {
		// Running in Docker container
		outputDir = "/data"
	} else {
		// Running locally
		wd, _ := os.Getwd()
		outputDir = filepath.Join(wd, "..", "octofree", "output")
	}

	// Load scheduled sessions
	if data, err := ioutil.ReadFile(filepath.Join(outputDir, "scheduled_sessions.json")); err == nil {
		json.Unmarshal(data, &m.upcomingSessions)
	}

	// Load past sessions
	if data, err := ioutil.ReadFile(filepath.Join(outputDir, "past_scheduled_sessions.json")); err == nil {
		json.Unmarshal(data, &m.pastSessions)
	}

	// Load last extracted sessions
	if data, err := ioutil.ReadFile(filepath.Join(outputDir, "last_extracted_sessions.json")); err == nil {
		json.Unmarshal(data, &m.lastExtracted)
	}

	// Load scraper logs
	if data, err := ioutil.ReadFile(filepath.Join(outputDir, "x_scraper_log.json")); err == nil {
		json.Unmarshal(data, &m.scraperLogs)
		if len(m.scraperLogs) > 0 {
			// Get the most recent scrape time
			if t, err := time.Parse(time.RFC3339, m.scraperLogs[len(m.scraperLogs)-1].Timestamp); err == nil {
				m.lastScrapeTime = t
			}
		}
	}

	// Load log file
	if data, err := ioutil.ReadFile(filepath.Join(outputDir, "octofree.log")); err == nil {
		m.logLines = strings.Split(string(data), "\n")
		// Keep logs in chronological order (oldest first, newest last)
		// No reversal needed

		// Parse the most recent "Sleeping main loop" message to calculate next scrape
		for i := len(m.logLines) - 1; i >= 0; i-- {
			line := m.logLines[i]
			if strings.Contains(line, "Sleeping main loop for 1 hour") {
				// Parse timestamp from log line: "2025-10-25 18:01:28,479 INFO: ..."
				parts := strings.SplitN(line, " ", 3)
				if len(parts) >= 2 {
					// Combine date and time, strip milliseconds
					timestampStr := parts[0] + " " + strings.Split(parts[1], ",")[0]
					if t, err := time.Parse("2006-01-02 15:04:05", timestampStr); err == nil {
						m.lastScrapeTime = t
						m.nextScrapeTime = t.Add(time.Hour)
						break
					}
				}
			}
		}
	}

	// Reverse past sessions order to show most recent first
	for i, j := 0, len(m.pastSessions)-1; i < j; i, j = i+1, j-1 {
		m.pastSessions[i], m.pastSessions[j] = m.pastSessions[j], m.pastSessions[i]
	}

	// Sort upcoming sessions by start time
	sort.Slice(m.upcomingSessions, func(i, j int) bool {
		ti, _ := time.Parse(time.RFC3339, m.upcomingSessions[i].StartTime)
		tj, _ := time.Parse(time.RFC3339, m.upcomingSessions[j].StartTime)
		return ti.Before(tj)
	})
}

func loadReadme(m *model, index int) {
	if index < 0 || index >= len(m.readmeFiles) {
		return
	}

	// Determine base path - use /app in Docker, or ../ locally
	var basePath string
	if _, err := os.Stat("/app/README.md"); err == nil {
		// Running in Docker container
		basePath = "/app"
	} else {
		// Running locally
		wd, _ := os.Getwd()
		basePath = filepath.Join(wd, "..")
	}

	readmePath := filepath.Join(basePath, m.readmeFiles[index])

	data, err := ioutil.ReadFile(readmePath)
	if err != nil {
		m.readmeContent = fmt.Sprintf("Error loading README: %v", err)
		return
	}

	// Render markdown with glamour
	r, err := glamour.NewTermRenderer(
		glamour.WithAutoStyle(),
		glamour.WithWordWrap(100),
	)
	if err != nil {
		m.readmeContent = string(data)
		return
	}

	rendered, err := r.Render(string(data))
	if err != nil {
		m.readmeContent = string(data)
		return
	}

	m.readmeContent = rendered
	m.selectedReadme = index
	m.readmeScroll = 0
}

func createUpcomingTable(sessions []Session) table.Model {
	columns := []table.Column{
		{Title: "Session", Width: 35},
		{Title: "Start", Width: 16},
		{Title: "End", Width: 8},
		{Title: "Status", Width: 15},
	}

	rows := []table.Row{}
	for _, session := range sessions {
		startTime, _ := time.Parse(time.RFC3339, session.StartTime)
		endTime, _ := time.Parse(time.RFC3339, session.EndTime)

		status := ""
		if session.Notified {
			status += "[N] "
		}
		if session.ReminderSent {
			status += "[R] "
		}
		if session.EndSent {
			status += "[E] "
		}
		if status == "" {
			status = "Pending"
		}

		rows = append(rows, table.Row{
			session.Session,
			startTime.Format("Mon 2 Jan 15:04"),
			endTime.Format("15:04"),
			status,
		})
	}

	t := table.New(
		table.WithColumns(columns),
		table.WithRows(rows),
		table.WithFocused(false),
		table.WithHeight(7),
	)

	s := table.DefaultStyles()
	s.Header = s.Header.
		BorderStyle(lipgloss.NormalBorder()).
		BorderForeground(lipgloss.Color("240")).
		BorderBottom(true).
		Bold(true).
		Foreground(lipgloss.Color("15"))
	s.Selected = s.Selected.
		Foreground(lipgloss.Color("15")).
		Background(lipgloss.Color("0")).
		Bold(false)

	t.SetStyles(s)
	return t
}

func createPastTable(sessions []Session) table.Model {
	columns := []table.Column{
		{Title: "Session", Width: 40},
		{Title: "Notified", Width: 10},
		{Title: "Reminders", Width: 15},
	}

	rows := []table.Row{}
	for _, session := range sessions {
		notified := "[X]"
		if session.Notified {
			notified = "[✓]"
		}

		reminders := ""
		reminderParts := []string{}
		if session.ReminderSent {
			reminderParts = append(reminderParts, "Start")
		}
		if session.EndSent {
			reminderParts = append(reminderParts, "End")
		}
		if len(reminderParts) > 0 {
			reminders = strings.Join(reminderParts, ", ")
		} else {
			reminders = "-"
		}

		rows = append(rows, table.Row{
			"- " + session.Session,
			notified,
			reminders,
		})
	}

	// Reverse rows to show most recent first
	for i, j := 0, len(rows)-1; i < j; i, j = i+1, j-1 {
		rows[i], rows[j] = rows[j], rows[i]
	}

	t := table.New(
		table.WithColumns(columns),
		table.WithRows(rows),
		table.WithFocused(false),
		table.WithHeight(7),
	)

	s := table.DefaultStyles()
	s.Header = s.Header.
		BorderStyle(lipgloss.NormalBorder()).
		BorderForeground(lipgloss.Color("240")).
		BorderBottom(true).
		Bold(true).
		Foreground(lipgloss.Color("15")).
		Align(lipgloss.Left).
		Padding(0, 0) // Remove all padding from headers
	// Force all row styles to be white - disable selection completely
	s.Cell = lipgloss.NewStyle().Foreground(lipgloss.Color("15"))
	s.Selected = lipgloss.NewStyle().Foreground(lipgloss.Color("15"))

	t.SetStyles(s)
	t.Focus() // Focus the table
	t.Blur()  // Then immediately blur it to clear selection

	return t
}

func getOctopusArt() string {
	octopus := `          ,'""'.
         / _  _ \
         |(@)(@)|
         )  __  (
        /,')))(('.\
       (( ((  )) ))
        ` + "`" + `\ ` + "`" + `)(' /'`

	return octopusStyle.Render(octopus)
}

func (m model) Init() tea.Cmd {
	return tea.Batch(tickCmd(), m.spinner.Tick)
}

func tickCmd() tea.Cmd {
	return tea.Tick(time.Second, func(t time.Time) tea.Msg {
		return tickMsg(t)
	})
}

type tickMsg time.Time

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			m.quitting = true
			return m, tea.Quit
		case "r":
			// Refresh data
			loadOctofreeData(&m)
			m.upcomingTable = createUpcomingTable(m.upcomingSessions)
			m.pastTable = createPastTable(m.pastSessions)
			// Auto-scroll to latest logs after refresh
			if len(m.logLines) > 20 {
				m.logScroll = len(m.logLines) - 20
			} else {
				m.logScroll = 0
			}
		case "tab":
			m.activeTab = (m.activeTab + 1) % 5
			if m.activeTab == 3 { // Logs tab
				// Auto-scroll to latest logs when switching to logs tab
				if len(m.logLines) > 20 {
					m.logScroll = len(m.logLines) - 20
				} else {
					m.logScroll = 0
				}
			} else if m.activeTab == 4 { // README tab
				m.readmeScroll = 0
			}
		case "1":
			m.activeTab = 0
		case "2":
			m.activeTab = 1
		case "3":
			m.activeTab = 2
		case "4":
			m.activeTab = 3
			// Auto-scroll to latest logs when switching to logs tab
			if len(m.logLines) > 20 {
				m.logScroll = len(m.logLines) - 20
			} else {
				m.logScroll = 0
			}
		case "5":
			m.activeTab = 4
			m.readmeScroll = 0
		case "up", "k":
			if m.activeTab == 3 && m.logScroll > 0 {
				m.logScroll--
			} else if m.activeTab == 4 && m.readmeScroll > 0 {
				m.readmeScroll--
			}
		case "down", "j":
			if m.activeTab == 3 && m.logScroll < len(m.logLines)-20 {
				m.logScroll++
			} else if m.activeTab == 4 {
				readmeLines := strings.Count(m.readmeContent, "\n")
				if m.readmeScroll < readmeLines-20 {
					m.readmeScroll++
				}
			}
		case "g":
			// Go to top of logs or README
			if m.activeTab == 3 {
				m.logScroll = 0
			} else if m.activeTab == 4 {
				m.readmeScroll = 0
			}
		case "G":
			// Go to bottom of logs or README
			if m.activeTab == 3 && len(m.logLines) > 20 {
				m.logScroll = len(m.logLines) - 20
			} else if m.activeTab == 4 {
				readmeLines := strings.Count(m.readmeContent, "\n")
				if readmeLines > 20 {
					m.readmeScroll = readmeLines - 20
				}
			}
		case "left", "h":
			// Previous README file
			if m.activeTab == 4 && m.selectedReadme > 0 {
				loadReadme(&m, m.selectedReadme-1)
			}
		case "right", "l":
			// Next README file
			if m.activeTab == 4 && m.selectedReadme < len(m.readmeFiles)-1 {
				loadReadme(&m, m.selectedReadme+1)
			}
		}
	case tickMsg:
		m.currentTime = time.Time(msg)
		return m, tickCmd()
	default:
		var cmd tea.Cmd
		m.spinner, cmd = m.spinner.Update(msg)
		return m, cmd
	}
	return m, nil
}

func (m model) View() string {
	if m.quitting {
		return statusGoodStyle.Render("👋 Goodbye!\n")
	}

	var b strings.Builder

	// App title and date/time on same line
	titleStr := titleStyle.Render("++ OCTOFREE ENERGY MONITOR ++")
	dateStr := lipgloss.NewStyle().Foreground(lipgloss.Color("39")).Bold(true).
		Render(m.currentTime.Format("Monday 2 January 2006"))
	timeStr := lipgloss.NewStyle().
		Foreground(lipgloss.Color("39")).
		Background(lipgloss.Color("235")).
		Bold(true).
		Padding(0, 1).
		Render(m.currentTime.Format("15:04:05"))
	b.WriteString(titleStr + "  " + dateStr + " - " + timeStr + "\n\n")

	// Tabs below title
	tabs := []string{"Overview", "Upcoming", "Past", "Logs", "README"}
	var tabBar strings.Builder
	for i, tab := range tabs {
		if i == m.activeTab {
			tabBar.WriteString(tabActiveStyle.Render(tab))
		} else {
			tabBar.WriteString(tabInactiveStyle.Render(tab))
		}
		tabBar.WriteString(" ")
	}
	b.WriteString(tabBar.String() + "\n")

	// 2 lines of space above octopus
	b.WriteString("\n\n")

	// Octopus
	b.WriteString(getOctopusArt() + "\n")

	// 2 lines of space below octopus
	b.WriteString("\n\n")

	// Content based on active tab
	switch m.activeTab {
	case 0: // Overview
		b.WriteString(m.renderOverview())
	case 1: // Upcoming
		b.WriteString(m.renderUpcoming())
	case 2: // Past
		b.WriteString(m.renderPast())
	case 3: // Logs
		b.WriteString(m.renderLogs())
	case 4: // README
		b.WriteString(m.renderReadme())
	}

	// Footer
	b.WriteString("\n" + strings.Repeat("─", 120) + "\n")

	if m.activeTab == 3 {
		footer := infoStyle.Render("↑/↓ or j/k to scroll • g/G for top/bottom • [1-5]/TAB to switch • [r] refresh • [q] quit")
		b.WriteString(footer + "\n")
	} else if m.activeTab == 4 {
		footer := infoStyle.Render("↑/↓ or j/k to scroll • ←/→ or h/l to switch READMEs • g/G for top/bottom • [1-5]/TAB to switch • [q] quit")
		b.WriteString(footer + "\n")
	} else {
		footer := infoStyle.Render("Press [1-5] or TAB to switch tabs • [r] to refresh • [q] to quit")
		b.WriteString(footer + "\n")
	}

	return b.String()
}

func (m model) renderOverview() string {
	var b strings.Builder

	// Stats boxes with spinner and countdown
	upcomingCount := len(m.upcomingSessions)
	pastCount := len(m.pastSessions)

	// Calculate time until next scrape
	timeUntilScrape := time.Until(m.nextScrapeTime)
	scrapeCountdown := ""
	if timeUntilScrape > 0 {
		mins := int(timeUntilScrape.Minutes())
		secs := int(timeUntilScrape.Seconds()) % 60
		scrapeCountdown = fmt.Sprintf("%dm %ds", mins, secs)
	} else {
		scrapeCountdown = "due now"
	}

	statsLine := lipgloss.JoinHorizontal(
		lipgloss.Top,
		boxStyle.Render(fmt.Sprintf("Upcoming\n%s", lipgloss.NewStyle().Foreground(lipgloss.Color("15")).Render(fmt.Sprintf("[%d]", upcomingCount)))),
		"  ",
		boxStyle.Render(fmt.Sprintf("Past\n%s", lipgloss.NewStyle().Foreground(lipgloss.Color("240")).Render(fmt.Sprintf("[%d]", pastCount)))),
	)
	b.WriteString(statsLine + "\n\n")

	// Horizontal line separator
	b.WriteString(strings.Repeat("─", 120) + "\n\n")

	// Next scrape countdown with spinner
	scrapeInfo := fmt.Sprintf("%s Next scrape in: %s",
		m.spinner.View(),
		statusWarningStyle.Render(scrapeCountdown))
	b.WriteString(scrapeInfo + "\n\n")

	// Upcoming Sessions section
	b.WriteString(subtitleStyle.Render(fmt.Sprintf("/////// Upcoming Sessions (%d)", upcomingCount)) + "\n")

	// Show upcoming sessions
	if len(m.upcomingSessions) > 0 {
		for i, session := range m.upcomingSessions {
			if i >= 3 { // Show max 3 sessions on overview
				break
			}
			startTime, _ := time.Parse(time.RFC3339, session.StartTime)
			endTime, _ := time.Parse(time.RFC3339, session.EndTime)
			timeUntil := time.Until(startTime)

			b.WriteString(fmt.Sprintf("  %s\n", statusGoodStyle.Render(session.Session)))
			b.WriteString(fmt.Sprintf("  %s -> %s",
				startTime.Format("Mon 2 Jan 15:04"),
				endTime.Format("15:04")))

			if timeUntil > 0 {
				b.WriteString(fmt.Sprintf(" - %s\n", statusWarningStyle.Render(fmt.Sprintf("in %s", formatDuration(timeUntil)))))
			} else {
				b.WriteString(fmt.Sprintf(" - %s\n", statusBadStyle.Render("passed")))
			}
			b.WriteString("\n")
		}
	} else {
		b.WriteString(statusWarningStyle.Render("  [!] No upcoming sessions scheduled") + "\n\n")
	}

	// Last extracted sessions
	if len(m.lastExtracted) > 0 {
		b.WriteString(subtitleStyle.Render("/////// Last Extracted Sessions:") + "\n")
		for _, session := range m.lastExtracted {
			b.WriteString(fmt.Sprintf("  - %s\n", session))
		}
	} else {
		b.WriteString(statusWarningStyle.Render("[!] No sessions extracted yet") + "\n")
	}

	// Show latest 5 log lines
	if len(m.logLines) > 0 {
		b.WriteString("\n" + subtitleStyle.Render("/////// Latest Log Activity:") + "\n")
		start := len(m.logLines) - 5
		if start < 0 {
			start = 0
		}
		for i := start; i < len(m.logLines); i++ {
			line := m.logLines[i]

			// Shorten timestamp: "2025-10-25 18:01:28,479" -> "2025-10-25 18:01"
			if len(line) > 23 && line[10] == ' ' && line[13] == ':' {
				shortenedLine := line[:16] + line[23:]
				line = shortenedLine
			}

			// Apply same styling as in log viewer
			var styledLine string
			if strings.Contains(line, "ERROR") {
				if idx := strings.Index(line, "ERROR: "); idx >= 0 {
					prefix := line[:idx+7]
					message := line[idx+7:]
					styledLine = statusBadStyle.Render(prefix) + message
				} else {
					styledLine = statusBadStyle.Render(line)
				}
			} else if strings.Contains(line, "WARNING") {
				if idx := strings.Index(line, "WARNING: "); idx >= 0 {
					prefix := line[:idx+9]
					message := line[idx+9:]
					styledLine = statusWarningStyle.Render(prefix) + message
				} else {
					styledLine = statusWarningStyle.Render(line)
				}
			} else if strings.Contains(line, "INFO") {
				if idx := strings.Index(line, "INFO: "); idx >= 0 {
					prefix := line[:idx+6]
					message := line[idx+6:]
					styledLine = statusGoodStyle.Render(prefix) + message
				} else {
					styledLine = statusGoodStyle.Render(line)
				}
			} else {
				styledLine = line
			}
			b.WriteString("  " + styledLine + "\n")
		}
	} else {
		b.WriteString("\n" + statusWarningStyle.Render("[!] No log activity yet") + "\n")
	}

	return b.String()
}

func (m model) renderUpcoming() string {
	var b strings.Builder

	b.WriteString(subtitleStyle.Render(fmt.Sprintf("/////// Upcoming Sessions (%d)", len(m.upcomingSessions))) + "\n\n")
	b.WriteString(strings.Repeat("─", 120) + "\n\n")

	if len(m.upcomingSessions) > 0 {
		b.WriteString(m.upcomingTable.View() + "\n")
	} else {
		b.WriteString(statusWarningStyle.Render("[!] No upcoming sessions scheduled") + "\n\n")
	}

	return b.String()
}

func (m model) renderPast() string {
	var b strings.Builder

	b.WriteString(subtitleStyle.Render(fmt.Sprintf("/////// Past Sessions (%d total, showing 10 most recent)", len(m.pastSessions))) + "\n\n")
	b.WriteString(strings.Repeat("─", 120) + "\n\n")

	if len(m.pastSessions) > 0 {
		b.WriteString(m.pastTable.View() + "\n")
	} else {
		b.WriteString(infoStyle.Render("No past sessions recorded") + "\n")
	}

	return b.String()
}

func (m model) renderLogs() string {
	var b strings.Builder

	totalLines := len(m.logLines)
	displayLines := 20

	b.WriteString(subtitleStyle.Render(fmt.Sprintf("/////// Application Logs (Total: %d lines)", totalLines)) + "\n")
	b.WriteString(infoStyle.Render(fmt.Sprintf("Showing lines %d-%d (use ↑/↓ or j/k to scroll, g/G for top/bottom)",
		m.logScroll+1,
		min(m.logScroll+displayLines, totalLines))) + "\n\n")
	b.WriteString(strings.Repeat("─", 120) + "\n\n")

	if totalLines == 0 {
		b.WriteString(statusWarningStyle.Render("[!] No log entries found") + "\n")
		return b.String()
	}

	// Restore the log box with flexible sizing to preserve emojis
	logBox := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("240")).
		Padding(1, 2)
		// No fixed width/height to allow natural emoji rendering

	var logContent strings.Builder
	start := m.logScroll
	end := min(start+displayLines, totalLines)

	for i := start; i < end; i++ {
		line := m.logLines[i]

		// Shorten timestamp: "2025-10-25 18:01:28,479" -> "2025-10-25 18:01"
		if len(line) > 23 && line[10] == ' ' && line[13] == ':' {
			// Extract: "YYYY-MM-DD HH:MM" (first 16 chars) + rest after milliseconds
			shortenedLine := line[:16] + line[23:]
			line = shortenedLine
		}

		// Apply styling only to log level prefixes, preserve emojis in messages
		var styledLine string
		if strings.Contains(line, "ERROR") {
			if idx := strings.Index(line, "ERROR: "); idx >= 0 {
				prefix := line[:idx+7] // Include "ERROR: "
				message := line[idx+7:]
				styledLine = statusBadStyle.Render(prefix) + message
			} else {
				styledLine = statusBadStyle.Render(line)
			}
		} else if strings.Contains(line, "WARNING") {
			if idx := strings.Index(line, "WARNING: "); idx >= 0 {
				prefix := line[:idx+9] // Include "WARNING: "
				message := line[idx+9:]
				styledLine = statusWarningStyle.Render(prefix) + message
			} else {
				styledLine = statusWarningStyle.Render(line)
			}
		} else if strings.Contains(line, "INFO") {
			if idx := strings.Index(line, "INFO: "); idx >= 0 {
				prefix := line[:idx+6] // Include "INFO: "
				message := line[idx+6:]
				styledLine = statusGoodStyle.Render(prefix) + message
			} else {
				styledLine = statusGoodStyle.Render(line)
			}
		} else {
			styledLine = line // No styling for other lines
		}
		logContent.WriteString(styledLine + "\n")
	}

	b.WriteString(logBox.Render(logContent.String()))

	return b.String()
}

func (m model) renderReadme() string {
	var b strings.Builder

	// Header with file selector
	readmeHeader := fmt.Sprintf("/////// README (%d/%d): %s",
		m.selectedReadme+1,
		len(m.readmeFiles),
		m.readmeFiles[m.selectedReadme])
	b.WriteString(subtitleStyle.Render(readmeHeader) + "\n")
	b.WriteString(infoStyle.Render("Use ←/→ or h/l to switch between README files, ↑/↓ or j/k to scroll") + "\n\n")
	b.WriteString(strings.Repeat("─", 120) + "\n\n")

	// Display rendered markdown content
	contentLines := strings.Split(m.readmeContent, "\n")
	totalLines := len(contentLines)
	displayLines := 25

	if totalLines == 0 {
		b.WriteString(statusWarningStyle.Render("[!] README content is empty") + "\n")
		return b.String()
	}

	start := m.readmeScroll
	end := min(start+displayLines, totalLines)

	for i := start; i < end; i++ {
		b.WriteString(contentLines[i] + "\n")
	}

	if totalLines > displayLines {
		b.WriteString("\n" + infoStyle.Render(fmt.Sprintf("Showing lines %d-%d of %d", start+1, end, totalLines)) + "\n")
	}

	return b.String()
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func formatDuration(d time.Duration) string {
	if d < 0 {
		return "expired"
	}
	if d < time.Minute {
		return fmt.Sprintf("%.0fs", d.Seconds())
	} else if d < time.Hour {
		return fmt.Sprintf("%.0fm", d.Minutes())
	} else if d < 24*time.Hour {
		hours := int(d.Hours())
		mins := int(d.Minutes()) % 60
		return fmt.Sprintf("%dh%dm", hours, mins)
	} else {
		days := int(d.Hours() / 24)
		hours := int(d.Hours()) % 24
		return fmt.Sprintf("%dd%dh", days, hours)
	}
}

func main() {
	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Printf("Alas, there's been an error: %v", err)
		os.Exit(1)
	}
}
