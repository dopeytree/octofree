# Updated Unraid Template with Console Wrapper (Option 2)

Add this line to your XML template to make Console button auto-launch the TUI:

```xml
<Shell>/usr/local/bin/console-wrapper</Shell>
```

## Complete Updated Template Section

Here's your existing template with the Shell tag added:

```xml
<?xml version="1.0"?>
<Container version="2">
    <Name>Octofree</Name>
    <Repository>ghcr.io/dopeytree/octofree:latest</Repository>
    <Registry>ghcr.io/dopeytree/octofree</Registry>
    <Network>bridge</Network>
    <WebUI/>
    <Shell>/usr/local/bin/console-wrapper</Shell>
    <Privileged>false</Privileged>
    <Support>https://forums.unraid.net/topic/194221-support-dopeytree-docker-templates/</Support>
    <Project>https://github.com/dopeytree/octofree</Project>
    <Overview>
        🐙 Octopus - Free Electric!!! ⚡️&#xD;
&#xD;
Never miss Octopus free electricity again!&#xD;
&#xD;
✨ NEW: Interactive Terminal UI Dashboard! Click Console to launch automatically.&#xD;
&#xD;
Octofree monitors the Octopus Energy website for upcoming free electricity saving sessions and sends timely Discord notifications to remind you to take advantage of them.&#xD;
&#xD;
💰 Saving sessions are free electric periods (usually 1-2hrs) frequent during strong winds.&#xD;
&#xD;
📱 Sends you a Discord notification on your mobile when a session is scheduled.&#xD;
📣 Reminds you again 5 minutes before the session starts.&#xD;
🐰 Warns 3 minutes before the end.&#xD;
&#xD;
🖥️ Interactive TUI Features:&#xD;
- Real-time monitoring dashboard with live data&#xD;
- Multiple tabs: Overview, Upcoming, Past, Logs, README&#xD;
- Live countdown timers for next scrape and sessions&#xD;
- Beautiful ASCII art octopus interface&#xD;
- Press q to quit TUI, Enter for shell access&#xD;
- Click Console button to launch automatically!&#xD;
    </Overview>
    <Beta>True</Beta>
    <Category>Productivity: Tools: Other: Status:Stable</Category>
    <ExtraSearchTerms>octopus energy free electricity discord notifications monitoring savings unraid terminal ui dashboard tui</ExtraSearchTerms>
    <Icon>https://raw.githubusercontent.com/dopeytree/Unraid-templates/master/logos/octofree-logo.png</Icon>
    <TemplateURL>https://raw.githubusercontent.com/dopeytree/Unraid-templates/master/templates/octofree.xml</TemplateURL>
    <Screenshot>https://raw.githubusercontent.com/dopeytree/Unraid-templates/master/screenshots/octofree-screenshot-1.png</Screenshot>
    <Maintainer>
        <WebPage>https://github.com/dopeytree</WebPage>
    </Maintainer>
    <Changes>
### 2025-10-29

NEW: Interactive Terminal UI Dashboard
- Beautiful terminal interface with real-time monitoring
- Auto-launches when Console button is clicked
- Multiple tabs with live data and countdown timers
- Press 'q' to quit TUI, then Enter for shell access

### 2025-10-14

Initial release
- Full monitoring of Octopus Energy free electricity sessions
- Discord webhook notifications
- Configurable test mode and single run options
    </Changes>
    <Requires>
*** Requires Discord webhook. *** &#xD;
Monitors Octopus Energy free electricity sessions and sends notifications via Discord. &#xD;
&#xD;
💡 TIP: Click the Console button to launch the interactive TUI dashboard automatically!&#xD;
Press 'q' to exit TUI, then Enter for shell access if needed.&#xD;
&#xD;
For support, visit the forum: https://forums.unraid.net/topic/194221-support-dopeytree-docker-templates/ &#xD;or GitHub issues: https://github.com/dopeytree/octofree/issues
    </Requires>
    <Config Name="Discord Webhook URL" Target="DISCORD_WEBHOOK_URL" Default="" Description="Discord webhook URL for sending notifications. Create a webhook in your Discord server settings." Type="Variable" Display="always" Required="true" Mask="true"/>
    <Config Name="Output Directory" Target="/data" Default="/mnt/user/appdata/octofree" Mode="rw" Description="Directory for logs and session data." Type="Path" Display="advanced" Required="false" Mask="false">/mnt/user/appdata/octofree</Config>
    <Config Name="Test Mode" Target="TEST_MODE" Default="false" Description="Enable test mode to send multiple notifications per session for testing. Default: false" Type="Variable" Display="advanced" Required="false" Mask="false">false</Config>
    <Config Name="Single Run" Target="SINGLE_RUN" Default="false" Description="Run once and exit instead of looping continuously. Default: false" Type="Variable" Display="advanced" Required="false" Mask="false">false</Config>
</Container>
```

## What Happens When User Clicks Console:

1. **TUI Launches Immediately** - Beautiful dashboard appears
2. **User interacts with TUI** - Browse tabs, view data, etc.
3. **User presses 'q'** - Exits TUI
4. **Prompt appears:**
   ```
   TUI closed. Press Enter for shell, or Ctrl+C to exit...
   ```
5. **User presses Enter** - Gets shell access (`/bin/sh`)
6. **User types 'exit'** - Loop restarts, TUI launches again!
7. **User presses Ctrl+C** - Exits console completely

## Benefits of This Approach:

✅ TUI launches automatically when Console is clicked  
✅ No menu selection needed - immediate access  
✅ Shell access still available if needed  
✅ Python main.py continues running in background  
✅ TUI can be relaunched by typing 'exit' in shell  
✅ Clean exit with Ctrl+C  

## Testing in Docker Desktop:

You can test this right now with your test container:

```bash
docker exec -it octofree-tui-test console-wrapper
```

This will:
1. Launch the TUI immediately
2. When you press 'q', show the prompt
3. Press Enter to get a shell
4. Type 'exit' to relaunch TUI
5. Press Ctrl+C to exit completely

Perfect for Unraid users! 🎉
