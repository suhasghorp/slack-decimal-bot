# Slack Decimal Bot - Quick Reference

## File Structure

```
slack-decimal-bot/
├── app.py                 # Main Bolt application (entry point)
├── config.py             # Configuration loading and validation
├── database.py           # SQL Server CRUD operations
├── handlers.py           # Slack event handlers (modals, buttons)
├── scheduler.py          # APScheduler monthly trigger setup
├── health.py             # Flask health check endpoint
├── db_utility.py         # Admin utility for database management
├── test_config.py        # Pre-deployment validation script
├── run_bot.bat           # Windows batch script for Task Scheduler
├── requirements.txt      # Python package dependencies
├── .env                  # Environment variables (SECURE - don't commit)
├── .env.example          # Template for .env configuration
├── .gitignore            # Git ignore rules
├── README.md             # Full documentation
├── SETUP_GUIDE.md        # Step-by-step setup instructions
├── QUICK_REFERENCE.md    # This file
├── logs/                 # Log files directory
│   └── bot.log           # Main bot log file
└── venv/                 # Python virtual environment
```

## Key Concepts

### Slack Flow
1. **Trigger**: 1st of each month at 9:00 AM UTC (configurable via `config.py`)
2. **Message Posted**: Bot posts message to dedicated channel with button
3. **User Clicks Button**: LauncherModal form appears
4. **User Enters Value**: 2 decimal place number (0.00-100.00)
5. **Validation**: Backend validates format and range
6. **Error/Success**: Either shows error in modal or confirms submission
7. **Database Save**: Stores submission with timestamp

### Database Schema

#### TargetUsers
```sql
slack_user_id (PK)   - Slack user ID (U123456...)
user_name            - Display name
added_at             - When recording was created
```

#### MonthlySubmissions
```sql
id (PK)              - Auto-increment ID
slack_user_id (FK)   - Reference to TargetUsers
submitted_value      - Decimal value (0.00-100.00)
submission_date      - When submitted
month_year           - YYYY-MM format
```

#### SubmissionStatus
```sql
month_year (PK)      - YYYY-MM format
total_required       - Number of target users
total_received       - Count of submissions received
submission_deadline  - When submissions close
created_at           - Record created timestamp
last_updated         - Last status update
```

## Common Commands

### Starting the Bot

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run bot locally (development)
python app.py

# Run via batch script (production)
.\run_bot.bat
```

### Testing & Validation

```powershell
# Run all configuration tests
python test_config.py

# Test specific functionality
python -c "from database import db; db._init_tables(); print('Tables initialized')"

# Check health endpoint
Invoke-WebRequest http://localhost:5000/health | ConvertFrom-Json | Format-Table
```

### Database Management

```powershell
# View current month status
python db_utility.py status

# Show all current submissions
python db_utility.py all

# View user history
python db_utility.py history U123456789

# Export to CSV
python db_utility.py export

# Export specific month
python db_utility.py export 2024-06
```

### Windows Task Scheduler

```powershell
# View task details
Get-ScheduledTask -TaskName "Slack Decimal Bot" | Select-Object *

# Run task manually
Start-ScheduledTask -TaskName "Slack Decimal Bot"

# Stop task
Stop-ScheduledTask -TaskName "Slack Decimal Bot"

# Delete task
Unregister-ScheduledTask -TaskName "Slack Decimal Bot" -Confirm:$false
```

### Viewing Logs

```powershell
# Last 50 lines of log
Get-Content logs\bot.log -Tail 50

# Live tail (follow)
Get-Content logs\bot.log -Wait -Tail 20

# Search for errors
Select-String "ERROR" logs\bot.log

# Export log to file
Get-Content logs\bot.log | Out-File logs\bot_export_$(Get-Date -Format yyyyMMdd).txt
```

## Configuration Quick Reference

### .env Variables

| Variable | Default | Example |
|----------|---------|---------|
| SLACK_BOT_TOKEN | (required) | `xoxb-12345...` |
| SLACK_APP_TOKEN | (required) | `xapp-12345...` |
| SQL_CONNECTION_STRING | (required) | `Driver={ODBC Driver 17 for SQL Server};...` |
| SLACK_CHANNEL_ID | (required) | `C123ABC...` |
| TARGET_USER_IDS | (required) | `U123,U456,U789` |
| SLACK_PROXY_URL | (optional) | `http://proxy.company.com:8080` |
| SLACK_PROXY_HEADERS | (optional) | `{"Proxy-Authorization": "Bearer token"}` |
| TRIGGER_DAY_OF_MONTH | 1 | Any 1-31 |
| TRIGGER_HOUR | 9 | 0-23 (UTC) |
| TRIGGER_MINUTE | 0 | 0-59 |
| SUBMISSION_DEADLINE_DAYS | 10 | 1-31 |
| MIN_DECIMAL | 0.00 | 0.00-999.99 |
| MAX_DECIMAL | 100.00 | 0.00-999.99 |
| LOG_FILE | `logs/bot.log` | Any path |
| HEALTH_PORT | 5000 | 1024-65535 |

## Troubleshooting Checklist

### ❌ Bot Won't Start
- [ ] Run `python test_config.py` to diagnose
- [ ] Verify `.env` file exists and is complete
- [ ] Check .env file has no syntax errors
- [ ] Test SQL connection manually
- [ ] Verify Python venv is activated

### ❌ Submissions Not Saving
- [ ] Check SQL Server connectivity
- [ ] Verify database tables exist via SQL Server Management Studio
- [ ] Review `logs/bot.log` for SQL errors
- [ ] Check database user permissions

### ❌ Modal Not Appearing
- [ ] Verify Slack channel ID is correct
- [ ] Check bot token in `.env`
- [ ] Check `SLACK_APP_TOKEN` in `.env`
- [ ] Verify "Interactivity" and "Socket Mode" are enabled in Slack app settings
- [ ] Verify outbound access to Slack on port 443 is allowed

### ❌ Scheduled Job Doesn't Fire
- [ ] Check Windows Event Viewer for Task Scheduler errors
- [ ] Verify cron trigger in logs: `Scheduler started`
- [ ] Test manual trigger: Edit `app.py` to call scheduler locally
- [ ] Check system time/timezone

### ❌ Health Endpoint Returns 503
- [ ] Check if bot process is actually running
- [ ] Verify port 5000 is accessible
- [ ] Check logs for startup errors
- [ ] Restart Windows Task Scheduler task

## SQL Server Queries

### View All Submissions
```sql
SELECT * FROM MonthlySubmissions ORDER BY submission_date DESC
```

### View Current Month Status
```sql
SELECT * FROM SubmissionStatus WHERE month_year = '2024-07'
```

### Count Submissions by Month
```sql
SELECT month_year, COUNT(*) as count FROM MonthlySubmissions GROUP BY month_year
```

### Find Users Who Haven't Submitted (current month)
```sql
SELECT u.slack_user_id, u.user_name
FROM TargetUsers u
LEFT JOIN MonthlySubmissions m ON u.slack_user_id = m.slack_user_id 
  AND m.month_year = '2024-07'
WHERE m.id IS NULL
```

### Get Latest Submission Per User (current month)
```sql
SELECT u.user_name, u.slack_user_id, m.submitted_value, m.submission_date
FROM (
    SELECT slack_user_id, submitted_value, submission_date,
           ROW_NUMBER() OVER (PARTITION BY slack_user_id ORDER BY submission_date DESC) as rn
    FROM MonthlySubmissions
    WHERE month_year = '2024-07'
) m
JOIN TargetUsers u ON m.slack_user_id = u.slack_user_id
WHERE m.rn = 1
ORDER BY m.submission_date DESC
```

## Performance Notes

- Bot runs continuously (no CPU/memory issues for typical workload)
- APScheduler uses negligible resources
- Flask health endpoint adds ~1-2% overhead
- SQL Server connections pooled for efficiency
- Log rotation recommended for files > 100MB

## Security Notes

- ⚠️ **Never** commit `.env` file to source control
- Use `Trusted_Connection=yes` for Windows Auth (preferred over SQL passwords)
- Slack bot token is sensitive → store securely
- Logs may contain user IDs → consider access controls
- Run bot with minimal necessary privileges on server
- Regular backups of SQL Server data

## Contact & Support

- For Python/Slack Bolt issues: https://slack.dev/bolt-python/
- For SQL Server: https://docs.microsoft.com/sql/
- For APScheduler: https://apscheduler.readthedocs.io/

---

**Last Updated**: 2024-07-01
**Bot Version**: 1.0.0

