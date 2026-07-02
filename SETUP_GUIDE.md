# Slack Monthly Decimal Submission Bot - Setup Guide

## Quick Start

### 1. Prerequisites
- Windows Server 2016+ or Windows 10+
- Python 3.9+
- SQL Server 2016+ with ODBC Driver 17
- Slack Workspace with admin access
- Network access to both SQL Server and Slack API

### 2. Initial Setup

#### Step 1: Create Project Structure
```powershell
# Create project folder
mkdir C:\PycharmProjects\slack-decimal-bot
cd C:\PycharmProjects\slack-decimal-bot

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

#### Step 3: Configure Environment
```powershell
# Copy example to actual .env file
Copy-Item .env.example .env

# Edit .env with your values (use Notepad or your editor)
notepad .env
```

**Required values to set in .env:**
```
SLACK_BOT_TOKEN=xoxb-...        # From Slack App settings
SLACK_APP_TOKEN=xapp-...         # App-level token with connections:write
SQL_CONNECTION_STRING=...        # Your SQL Server connection
SLACK_CHANNEL_ID=C0...           # Target Slack channel ID
TARGET_USER_IDS=U123,U456,...   # Comma-separated user IDs
```

#### Step 4: Test Configuration
```powershell
python test_config.py
```

This will verify:
- ✓ All Python packages installed
- ✓ Environment variables set
- ✓ SQL Server connectivity
- ✓ Slack credentials valid
- ✓ Database tables created
- ✓ APScheduler configured

**Fix any issues before proceeding to deployment.**

### 3. Slack App Setup

#### Create New Slack App
1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Add name: "Decimal Submission Bot" and select your workspace
4. Go to "Oauth & Permissions"

#### Add OAuth Scopes
In "Scopes" section, add these Bot Token Scopes:
- `chat:write` - Post messages
- `chat:write.public` - Post to public channels when needed
- `users:read` - Read user info
- `channels:read` - Read channels
- `groups:read` - Read private channels
- `im:write` - Send confirmation/status DMs

#### Enable Socket Mode
1. Go to "Socket Mode"
2. Toggle "Enable Socket Mode" ON
3. Create an app-level token with the `connections:write` scope
4. Copy the token (starts with `xapp-`) into `.env` as `SLACK_APP_TOKEN`

#### Enable Interactivity
1. Go to "Interactivity & Shortcuts"
2. Toggle "Interactivity" ON
3. No public Request URL is needed when Socket Mode is enabled
4. Slack will route button clicks and modal submissions over the Socket Mode connection instead

#### Install App to Workspace
1. Go to "Install App"
2. Click "Install to Workspace"
3. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
4. Paste into `.env` as `SLACK_BOT_TOKEN`

#### DMZ / Corporate Network Note
1. The bot server does **not** need inbound internet access from Slack
2. The server **does** need outbound HTTPS/WebSocket access to Slack on port 443
3. If outbound internet is completely blocked, Socket Mode cannot connect and the bot will not work
4. Allow outbound access directly or through an approved corporate proxy/firewall rule
5. If you use a corporate proxy, set `SLACK_PROXY_URL` and optionally `SLACK_PROXY_HEADERS` in `.env` — see `SLACK_CONFIGURATION_GUIDE.md` Appendix A

#### Get Channel ID
1. Go to your Slack workspace
2. In the target channel, click on channel name at top
3. Look for "Channel ID" near the bottom
4. Copy and paste into `.env` as `SLACK_CHANNEL_ID`

#### Get User IDs
1. In Slack, right-click on a user profile
2. Select "View profile" and look for the "@" handle
3. Click on "..." menu at top → "Copy member ID"
4. Repeat for all target users
5. Paste comma-separated into `.env` as `TARGET_USER_IDS`

### 4. SQL Server Setup

#### Verify ODBC Driver
```powershell
# Check if ODBC Driver 17 is installed
Get-OdbcDriver | Select Name

# If not found, install from: 
# https://go.microsoft.com/fwlink/?linkid=2245617
```

#### Test Connection String
```powershell
python -c "
import pyodbc
conn_str = 'Driver={ODBC Driver 17 for SQL Server};Server=YOUR_SERVER;Database=YOUR_DB;Trusted_Connection=yes;'
try:
    conn = pyodbc.connect(conn_str)
    print('✓ Connection successful')
    conn.close()
except Exception as e:
    print(f'✗ Connection failed: {e}')
"
```

#### Add Connection String to .env
```
SQL_CONNECTION_STRING=Driver={ODBC Driver 17 for SQL Server};Server=YOUR_SERVER;Database=YOUR_DB;Trusted_Connection=yes;
```

### 5. Local Testing

#### Start the Bot
```powershell
.\venv\Scripts\Activate.ps1
python app.py
```

You should see:
```
2024-07-01 09:15:30 - root - INFO - Slack Bolt app initialized
2024-07-01 09:15:31 - apscheduler.scheduler - INFO - Scheduler started
2024-07-01 09:15:31 - root - INFO - ============================================================
2024-07-01 09:15:31 - root - INFO - Slack Bot Started - Monthly Decimal Collection
2024-07-01 09:15:31 - root - INFO - ============================================================
```

#### Test Health Endpoint
In another terminal:
```powershell
Invoke-WebRequest http://localhost:5000/health
```

Should return:
```json
{
  "status": "healthy",
  "bot_running": true,
  "timestamp": "2024-07-01T09:15:30.123456",
  "uptime_seconds": 60,
  "last_error": null
}
```

#### Manual Submission Test (Optional)
To test without waiting for scheduled trigger, edit `app.py` temporarily:

Add at end of `main()` after scheduler initialization:
```python
# Temporary test trigger
print("Executing manual trigger for testing...")
from scheduler import trigger_now
trigger_now(app.client)
```

Then run `python app.py` - you should see submission message in Slack channel.

### 6. Windows Task Scheduler Deployment

#### Create Batch Script
The `run_bot.bat` file is already created. Verify it matches your installation path.

#### Create Task Scheduler Task

**Option A: Using GUI**

1. Press `Windows Key` + `R` → type `taskschd.msc` → Enter
2. Right-click "Task Scheduler Library" → "Create Basic Task..."
3. Name: `Slack Decimal Bot`
4. Description: `Monthly decimal submission bot for corporate intranet`
5. Click "Next >"
6. Trigger: Select "At startup"
7. Click "Next >"
8. Action: Select "Start a program"
9. Program/script: `C:\PycharmProjects\slack-decimal-bot\run_bot.bat`
10. Start in: `C:\PycharmProjects\slack-decimal-bot`
11. Click "Next >"
12. Check all boxes:
    - ☑ "Run with highest privileges"
    - ☑ "Run whether user is logged in or not" (requires no password)
    - ☑ "Hidden"
13. Click "Finish"

**Configure restart policy:**
1. Right-click the new task → "Properties"
2. Go to "Conditions" tab
   - Uncheck "Stop the task if it runs longer than"
3. Go to "Settings" tab
   - Check "If the task fails, restart every:" → Set to `5 minutes`
   - Set "Attempt to restart up to:" → `288` (24 hours)
   - Check "If the task fails to run
 again, retry: immediately"

**Option B: Using PowerShell Script**

Save as `create_task.ps1`:
```powershell
$taskName = "Slack Decimal Bot"
$taskPath = "\Slack Decimal Bot\"
$scriptPath = "C:\PycharmProjects\slack-decimal-bot\run_bot.bat"
$scriptDir = "C:\PycharmProjects\slack-decimal-bot"

# Remove existing task if it exists
try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
} catch {}

# Create trigger
$trigger = New-ScheduledTaskTrigger -AtStartup

# Create action
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory $scriptDir

# Create principal
$principal = New-ScheduledTaskPrincipal -UserID "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register task
Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Principal $principal -Force

# Configure restart policy
$task = Get-ScheduledTask -TaskName $taskName
$task.Settings.RestartCount = 288
$task.Settings.RestartInterval = "PT5M"
Set-ScheduledTask -InputObject $task

Write-Host "✓ Task created successfully"
```

Run as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
.\create_task.ps1
```

#### Verify Task Creation
```powershell
Get-ScheduledTask -TaskName "Slack Decimal Bot" | Select * | Format-List
```

#### Test Task
```powershell
Start-ScheduledTask -TaskName "Slack Decimal Bot"

# Wait 10 seconds then check if running
Start-Sleep -Seconds 10
Get-Process python -ErrorAction SilentlyContinue | Select ProcessName, Id

# Check logs
Get-Content C:\PycharmProjects\slack-decimal-bot\logs\bot.log -Tail 20
```

### 7. Monitoring

#### Check Bot Status
```powershell
# Health check
$health = Invoke-WebRequest -Uri "http://localhost:5000/health" | ConvertFrom-Json
$health | Format-Table

# View recent logs
Get-Content C:\PycharmProjects\slack-decimal-bot\logs\bot.log -Tail 50

# Check if process is running
Get-Process python | Where-Object {$_.CommandLine -like "*app.py*"}
```

#### View Submissions in SQL Server
```sql
-- SQL Server query to view submissions
SELECT TOP 100 
    u.user_name,
    m.submitted_value,
    m.submission_date,
    m.month_year
FROM MonthlySubmissions m
JOIN TargetUsers u ON m.slack_user_id = u.slack_user_id
ORDER BY m.submission_date DESC
```

### 8. Troubleshooting

#### Bot Won't Start
1. Check `.env` file exists and is complete
2. Run `test_config.py` to identify specific issue
3. Check `logs/bot.log` for error messages
4. Ensure Python venv activated: `.\venv\Scripts\Activate.ps1`

#### Submissions Not Saving
1. Test SQL connection: `python test_config.py`
2. Verify tables exist in SQL Server
3. Check user has INSERT permission on tables
4. Review database errors in `bot.log`

#### Scheduled Task Fails
1. Check Windows Event Viewer for Task Scheduler errors
2. Verify `run_bot.bat` path is correct
3. Test running batch file manually:
   ```powershell
   cd C:\PycharmProjects\slack-decimal-bot
   .\run_bot.bat
   ```
4. Check outbound Slack connectivity and proxy/firewall rules for Socket Mode

#### Modal Doesn't Appear
1. Verify Socket Mode is enabled in the Slack app
2. Check `SLACK_APP_TOKEN` in `.env` is correct
3. Ensure the server can make outbound connections to Slack on port 443
4. Check `logs/bot.log` for interaction errors

### 9. Post-Deployment

#### First Month Run
1. When bot starts, it runs initial APScheduler check
2. On configured day/time (e.g., 1st, 9 AM UTC), submission message appears in channel
3. Users click button, fill modal, submit
4. Verify in SQL Server that submissions are recorded

#### Monthly Verification
- Check health endpoint: `http://[SERVER]:5000/health`
- Query `MonthlySubmissions` table for submission count
- Review `bot.log` for any errors
- Verify Task Scheduler task status remains "Ready"

#### Backup Procedures
- Backup `.env` file (securely store bot token)
- Regular SQL Server backups of `MonthlySubmissions` table
- Backup `logs/` folder periodically for audit trail

---

**You're now ready to deploy!** Questions? Check `README.md` for more details.

