# Slack Monthly Decimal Submission Bot

A corporate intranet Slack bot built with Python Slack Bolt that collects decimal number submissions (0.00-100.00, exactly 2 decimal places) from designated users every month via interactive modal forms. Submissions are stored in SQL Server with interactive correction flow for validation errors.

## Features

- **Monthly Scheduled Triggers**: APScheduler sends a submission request on the 1st of each month at 9:00 AM UTC (configurable)
- **Interactive Modal Forms**: Users click a button to open a modal, enter their decimal value with real-time validation
- **Slack Socket Mode**: No inbound public Slack endpoint required; the bot opens an outbound WebSocket to Slack
- **SQL Server Integration**: All submissions stored in SQL Server with audit trail
- **Validation & Correction Flow**: Invalid inputs trigger inline error messages allowing users to correct and resubmit without closing the modal
- **Status Tracking**: Button to check submission status - see who has/hasn't submitted
- **Health Endpoint**: Flask `/health` endpoint on port 5000 for monitoring
- **Graceful Shutdown**: Proper signal handling for Windows Task Scheduler restarts
- **Comprehensive Logging**: All events logged to both file and console

## Architecture

```
app.py              - Main Slack Bolt application
config.py           - Configuration and environment variables
database.py         - SQL Server connection and CRUD operations
handlers.py         - Slack event handlers (buttons, modals, validation)
scheduler.py        - APScheduler setup for monthly triggers
health.py           - Flask health check endpoint
requirements.txt    - Python dependencies
run_bot.bat         - Windows batch script for Task Scheduler
```

## Installation

### Prerequisites

- Python 3.9+
- Windows Server or Windows 10+
- SQL Server 2016+ (or compatible)
- ODBC Driver 17 for SQL Server installed

### Setup Steps

1. **Clone/Create Project**
   ```bash
   mkdir slack-decimal-bot
   cd slack-decimal-bot
   ```

2. **Create Python Virtual Environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   - Copy `.env.example` to `.env`
   - Update with your values:
     ```env
     SLACK_BOT_TOKEN=xoxb-your-token
      SLACK_APP_TOKEN=xapp-your-app-token
     SQL_CONNECTION_STRING=Driver={ODBC Driver 17 for SQL Server};Server=YOUR_SERVER;Database=YOUR_DB;Trusted_Connection=yes;
     SLACK_CHANNEL_ID=C0XXXXXX
     TARGET_USER_IDS=U123456,U234567,U345678
     ```

5. **Initialize SQL Server Tables**
   - Tables are auto-created on first run, but ensure your connection string is valid

6. **Test Locally**
   ```bash
   python app.py
   ```
   - Bot should start and display logs
   - Health endpoint should be available at `http://localhost:5000/health`

## Windows Task Scheduler Setup

### Create Scheduled Task

1. **Open Task Scheduler** (Windows Key + Run > `taskschd.msc`)

2. **Create Basic Task**
   - Name: `Slack Decimal Bot`
   - Description: `Monthly decimal submission bot for corporate intranet`

3. **Set Trigger**
   - Select "At startup"
   - Also create additional trigger for periodic restarts (if desired)

4. **Set Action**
   - Program/script: `C:\path\to\run_bot.bat`
   - Start in: `C:\PycharmProjects\slack-decimal-bot`

5. **Configure Settings**
   - Check: "Run whether user is logged in or not"
   - Check: "Do not store password"
   - Set restart policy: "Restart the task if it fails"
     - Stop the task if it runs longer than: 24 hours
     - If the task fails, restart every: 5 minutes
     - Attempt to restart up to: 288 times (1 day)

6. **Create Additional Repeating Trigger** (Optional - for health checks)
   - Trigger type: "On a schedule"
   - Repeat every 1 hour
   - Action: Start the task

## Configuration Reference

### Environment Variables (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `SLACK_BOT_TOKEN` | Slack bot token | `xoxb-...` |
| `SLACK_APP_TOKEN` | Slack Socket Mode app-level token | `xapp-...` |
| `SQL_CONNECTION_STRING` | SQL Server connection | `Driver={ODBC Driver 17 for SQL Server};Server=SERVER;Database=DB;Trusted_Connection=yes;` |
| `SLACK_CHANNEL_ID` | Channel for monthly submissions | `C0XXXXXX` |
| `TARGET_USER_IDS` | Slack user IDs to collect from | `U123,U456,U789` |
| `TRIGGER_DAY_OF_MONTH` | Day to trigger submissions | `1` |
| `TRIGGER_HOUR` | Hour (UTC) | `9` |
| `TRIGGER_MINUTE` | Minute (UTC) | `0` |
| `SUBMISSION_DEADLINE_DAYS` | Days from trigger to deadline | `10` |
| `MIN_DECIMAL` | Minimum allowed value | `0.00` |
| `MAX_DECIMAL` | Maximum allowed value | `100.00` |
| `LOG_FILE` | Log file path | `logs/bot.log` |
| `HEALTH_PORT` | Health endpoint port | `5000` |

## Slack App Configuration

### Required OAuth Scopes

- `chat:write` - Post messages to channels
- `chat:write.public` - Post to public channels when needed
- `users:read` - Read user information
- `channels:read` - Read channel information
- `groups:read` - Read private channel information
- `im:write` - Send direct messages to users

### App-Level Token

- Create an app-level token with the `connections:write` scope
- Save it as `SLACK_APP_TOKEN` in `.env`

### Socket Mode

- Enable **Socket Mode** in the Slack app settings
- No public Slack **Request URL** is required for buttons or modal submissions

### Event Subscriptions

(Not required for this bot - uses only interactive actions and direct API calls)

### Interactivity

- Enable Interactivity so button clicks and modal submissions are allowed
- With Socket Mode enabled, Slack delivers those payloads over the outbound WebSocket connection

### Corporate Proxy Support

If your organization requires outbound internet access through a proxy:

```env
# Proxy URL
SLACK_PROXY_URL=http://proxy.company.com:8080

# Optional: Proxy authentication headers (JSON)
SLACK_PROXY_HEADERS={"Proxy-Authorization": "Bearer token"}
```

See `SLACK_CONFIGURATION_GUIDE.md` Appendix A for complete proxy setup instructions.

## Usage

### For Users

1. Navigate to the designated Slack channel
2. On the 1st of each month, a message appears with "Submit [Month] Data" button
3. Click the button to open the submission modal
4. Enter your decimal value (0.00-100.00, exactly 2 decimal places)
5. Click Submit
6. Receive confirmation message
7. Can submit multiple times per month (latest overrides previous)

### For Admins

#### Check Submission Status
- Click "Check Status" button in channel message
- Receive DM with count of submissions received

#### View Database
- Connect to SQL Server directly
- Query `MonthlySubmissions` table for submission history
- Query `SubmissionStatus` for monthly totals

#### Manual Trigger (for testing)
- Edit `app.py` to add a manual trigger command before starting
- Or restart bot and wait for scheduled trigger

## Monitoring

### Health Checks

Monitor the bot's health via HTTP endpoint:

```bash
# From any machine with network access to server
curl http://[SERVER_IP]:5000/health

# Response (if healthy):
{
  "status": "healthy",
  "bot_running": true,
  "timestamp": "2024-07-01T09:15:30.123456",
  "uptime_seconds": 3600,
  "last_error": null
}
```

### Log Files

- Location: `C:\PycharmProjects\slack-decimal-bot\logs\bot.log`
- Contains all submissions, errors, and scheduling events
- Rotated daily (configure in `config.py` if needed)

### Windows Event Viewer

- Task Scheduler logs available in Event Viewer > Windows Logs > System
- Filtered by source "TaskScheduler"

## Troubleshooting

### Bot Won't Start

1. **Check .env file** - Ensure all required variables are set
2. **Test SQL connection** - Verify connection string with `pyodbc` test script
3. **Check logs** - Review `logs/bot.log` for detailed errors
4. **Verify network access** - Ensure the server can make outbound HTTPS/WebSocket connections to Slack and inbound access to port 5000 is allowed only if you need the health endpoint
5. **ODBC Driver** - Verify ODBC Driver 17 is installed: `odbcad32.exe`

### Submissions Not Saving

1. **SQL Server connectivity** - Test connection string
2. **Database tables** - Verify tables exist (auto-created on startup)
3. **Permissions** - Ensure bot has INSERT permissions on tables
4. **Check logs** - Database errors logged in `bot.log`

### Scheduled Trigger Not Firing

1. **Check Task Scheduler** - Verify task is enabled and configured correctly
2. **APScheduler logs** - Review `bot.log` for scheduler messages
3. **Manual test** - Restart bot to trigger on-startup verification
4. **Timezone** - Ensure UTC times are correct for desired local time
5. **Socket Mode connectivity** - Confirm outbound access to Slack is permitted from the server/proxy

### Modal Validation Errors

- **Invalid format**: Ensure exactly 2 decimal places (e.g., "45.67" not "45.6" or "45")
- **Out of range**: Value must be between 0.00 and 100.00
- **Non-numeric**: Only numbers and decimal point allowed

## Development

### Running Locally

```bash
# Activate venv
venv\Scripts\activate

# Set timezone if needed (Windows)
$env:TZ = "UTC"

# Run bot
python app.py
```

### Local Slack Integration

No ngrok tunnel is required with Socket Mode. As long as your machine can make outbound connections to Slack, interactive payloads are delivered over the WebSocket session opened by the bot.

### Manual Database Testing

```python
from database import db

# Test connection
try:
    db._init_tables()
    print("Connected to SQL Server successfully")
except Exception as e:
    print(f"Connection failed: {e}")
```

## Deployment Checklist

- [ ] `.env` file created with all required values
- [ ] SQL Server connection tested and working
- [ ] ODBC Driver 17 installed on server
- [ ] Python virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `run_bot.bat` script paths verified
- [ ] Windows Task Scheduler task created and tested
- [ ] Slack channel and users configured
- [ ] Health endpoint tested (`curl http://localhost:5000/health`)
- [ ] First scheduled run tested (or manual trigger)
- [ ] Log file monitoring set up
- [ ] Backups of `.env` file secured

## Support & Issues

For bugs or feature requests, check logs at `logs/bot.log` for details. Common issues:

1. **Connection timeouts** - Check SQL Server firewall rules
2. **Invalid credentials** - Verify connection string format
3. **Modal not appearing** - Check Slack app OAuth scopes
4. **Submissions lost** - Verify SQL Server transactions are committing

## License

Internal Corporate Use Only

