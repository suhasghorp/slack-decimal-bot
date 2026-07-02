# Architecture & Design Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          WINDOWS SERVER                                  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
        ┌───────────▼──────────┐  ┌──────▼──────────────┐
        │  Python Slack Bot    │  │  Task Scheduler    │
        │  (Continuous)        │  │  (Startup Trigger) │
        │                      │  └────────────────────┘
        │  ┌────────────────┐  │
        │  │  Slack Bolt    │  │
        │  │  Event Handler │  │
        │  └────────┬───────┘  │
        │           │          │
        │  ┌────────▼───────┐  │
        │  │ APScheduler    │  │
        │  │ Monthly Cron   │  │
        │  └────────┬───────┘  │
        │           │          │
        │  ┌────────▼───────┐  │
        │  │  Flask Health  │  │
        │  │  /health (5000)│  │
        │  └────────────────┘  │
        │                      │
        └─────────────┬────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
          │           │           │
    ┌─────▼──┐  ┌─────▼──┐  ┌────▼─────┐
    │ Slack  │  │  SQL   │  │   Logs   │
    │  API   │  │ Server │  │  Files   │
    │(Cloud) │  │(Network)│  │(Local)   │
    └────────┘  └────────┘  └──────────┘
```

## Process Flow

### Monthly Submission Flow

```
┌────────────────────────────────────────────────────────────────┐
│ 1st of Month, 9:00 AM UTC (APScheduler triggers)              │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│ 2. Bot Posts Message to Slack Channel                          │
│    - Title: "Monthly Data Submission - [Month]"               │
│    - Button: "Submit [Month] Data"                            │
│    - Status button for tracking                               │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│ 3. User Clicks "Submit [Month] Data" Button                   │
│    - Slack sends action event to bot                          │
│    - Bot validates user is in TARGET_USER_IDS                 │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│ 4. Bot Opens Interactive Modal                                │
│    - Input field: "Enter value between 0.00 and 100.00"      │
│    - Placeholder: "e.g., 45.67"                              │
│    - Submit button                                           │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│ 5. User Enters Decimal Value and Clicks Submit               │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼  (Slack view submission event)
┌────────────────────────────────────────────────────────────────┐
│ 6. Bot Validates Input                                        │
│    ✓ Format: regex match "^\d+\.\d{2}$"                     │
│    ✓ Range: MIN_DECIMAL <= value <= MAX_DECIMAL             │
│                                                               │
│    If INVALID:                                               │
│    │ └─► Show inline error in modal                         │
│    │     Allow user to correct and retry                    │
│    │     (No modal close, interactive flow)                 │
│    │                                                         │
│    If VALID:                                                │
│    └─► Proceed to step 7                                    │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│ 7. Bot Stores Submission in SQL Server                        │
│    - Table: MonthlySubmissions                               │
│    - Fields: user_id, value, timestamp, month_year           │
│    - Update SubmissionStatus: total_received++               │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│ 8. Bot Acknowledges Modal and Sends Confirmation              │
│    - Close modal automatically                                │
│    - Send DM to user with confirmation:                       │
│      "✅ Submission Confirmed"                               │
│      "Value: 45.67"                                          │
│      "Month: July"                                           │
│      "Time: 2024-07-01 09:15 UTC"                            │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
    [End of Flow]

User can resubmit anytime during the submission period.
Latest submission overrides previous.
```

## Event Handler Architecture

```
┌──────────────────────────────────┐
│     Slack Bolt App               │
│  (Socket Mode)                   │
└────────────────┬─────────────────┘
                 │
                 ├─ Bot Events
                 │  (messages, reactions, etc.)
                 │
                 ├─ Interactive Events
                 │  ├─ Button Clicks
                 │  │  ├─ submit_data_button
                 │  │  │  └─► handle_submit_button()
                 │  │  │      ├─ Validate user_id
                 │  │  │      ├─ Build modal
                 │  │  │      └─ Open modal via trigger_id
                 │  │  │
                 │  │  └─ check_status_button
                 │  │     └─► handle_status_button()
                 │  │         ├─ Query SubmissionStatus
                 │  │         ├─ Get pending users
                 │  │         └─ Send DM to user
                 │  │
                 │  └─ View Submissions (Modals)
                 │     └─ submission_modal
                 │        └─► handle_modal_submission()
                 │            ├─ Extract decimal_value
                 │            ├─ validate_decimal_input()
                 │            │  ├─ Check format
                 │            │  ├─ Check range
                 │            │  └─ Return errors if invalid
                 │            ├─ ack(errors={...}) if invalid
                 │            │  (user sees error, can retry)
                 │            ├─ db.insert_submission() if valid
                 │            ├─ ack() (close modal)
                 │            └─ Send confirmation DM
                 │
                 └─ Errors
                    └─► custom_error_handler()
                        └─ Log error + details
```

## Data Flow: Socket Mode → Database

```
User Clicks Button
        │
        ▼
┌──────────────────────────────┐
│ Slack Cloud                  │
│ Sends action over Socket Mode│
└────────┬─────────────────────┘
         │ (Outbound WebSocket session)
         │
         ▼
┌──────────────────────────────────────┐
│ Bot: handle_submit_button()          │
│ - Acknowledge immediately            │
│ - Build modal JSON                   │
│ - Call client.views_open()           │
└────────┬─────────────────────────────┘
         │
         ▼
   User sees Modal
   Enters decimal value
   Clicks Submit
         │
         ▼ (view_submission event)
┌──────────────────────────────────────┐
│ Bot: handle_modal_submission()       │
│ - Extract input: "45.67"             │
│ - Validate with validate_decimal... │
│   - Regex check: ^\d+\.\d{2}$       │
│   - Range check: 0.00 ≤ x ≤ 100.00 │
└────────┬─────────────────────────────┘
         │
         ├─ INVALID
         │  │
         │  ▼
         │  ack(response_action="errors",
         │      errors={"block": error_msg})
         │  │
         │  └─► User sees error in modal
         │      Can correct and retry
         │
         └─ VALID
            │
            ▼
         ┌──────────────────────────────────┐
         │ db.insert_submission()           │
         │ - Connect to SQL Server          │
         │ - INSERT MonthlySubmissions      │
         │ - UPDATE SubmissionStatus        │
         │ - Close connection               │
         └────────┬─────────────────────────┘
                  │
                  ▼
         ┌──────────────────────────────────┐
         │ ack() (close modal)              │
         │ client.chat_postMessage()        │
         │ Send confirmation DM             │
         └──────────────────────────────────┘
```

## Configuration Hierarchy

```
Environment (.env)
  │
  ├─ config.py (loads .env)
  │  ├─ SLACK_BOT_TOKEN
  │  ├─ SLACK_APP_TOKEN      ──► Used to open the Socket Mode connection
  │  ├─ SQL_CONNECTION_STRING ──► Used to create database connections
  │  ├─ TARGET_USER_IDS       ──► Defines who can submit
  │  ├─ TRIGGER_DAY_OF_MONTH  ──► APScheduler cron trigger
  │  ├─ MIN/MAX_DECIMAL       ──► Validation rules
  │  └─ LOG configuration
  │
  └─ Used by:
     ├─ app.py (initialization)
     ├─ database.py (SQL connections)
     ├─ handlers.py (validation rules)
     ├─ scheduler.py (cron timing)
     └─ health.py (port config)
```

## Error Handling Strategy

```
┌─────────────────────────────────────────────────────┐
│              Error Handling Layers                  │
└─────────────────────────────────────────────────────┘
         │
         ├─ Input Validation Errors
         │  └─ User sees error in modal
         │     Can retry without closing
         │
         ├─ Database Errors
         │  ├─ Connection errors
         │  │  └─ Log error, notify user to retry
         │  └─ Insert/Update errors
         │     └─ Log error, notify user
         │
         ├─ Slack API Errors
         │  ├─ Invalid token
         │  ├─ Rate limit
         │  └─ Malformed requests
         │     └─ Log all to bot.log
         │
         ├─ Scheduler Errors
         │  └─ Trigger failures
         │     └─ App continues, retry on next cycle
         │
         └─ System Errors
            └─ Process restart via Task Scheduler
               (after 5-minute delay, up to 288 times)
```

## Deployment Pipeline

```
┌────────────────────────────────────────┐
│ 1. Development / Testing               │
│    - Run: python app.py                │
│    - Local on Windows dev machine      │
│    - Test all features                 │
└────────┬─────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ 2. Pre-Deployment Validation           │
│    - Run: python test_config.py        │
│    - Verify all systems ready          │
│    - Check SQL Server access           │
│    - Validate Slack credentials        │
└────────┬─────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ 3. Deploy to Windows Server            │
│    - Copy all files to server path     │
│    - Update .env with prod values      │
│    - Verify run_bot.bat path          │
│    - Test manually: .\run_bot.bat     │
└────────┬─────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ 4. Configure Task Scheduler            │
│    - Create task with startup trigger  │
│    - Set restart policy (5 min, 288x)  │
│    - Enable logging                    │
│    - Test: Start-ScheduledTask         │
└────────┬─────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ 5. Production Monitoring               │
│    - Check health: /health endpoint    │
│    - Monitor logs regularly            │
│    - Track submissions in SQL Server   │
│    - Monthly: export_submissions_to_csv│
└─────────────────────────────────────────┘
```

## Key Design Decisions

### 1. **Interactive Modal Correction Flow**
- **Decision**: Show validation errors inline without closing modal
- **Rationale**: Better UX, users can see and fix mistakes immediately
- **Implementation**: Use `ack(response_action="errors", errors={...})`

### 2. **APScheduler for Monthly Trigger**
- **Decision**: Run scheduler within the bot process
- **Rationale**: Corporate intranet = controlled environment, simplest deployment
- **Alternative**: External cron job (more complex setup)

### 3. **SQL Server (not SQLite)**
- **Decision**: Enterprise SQL Server database
- **Rationale**: Corporate requirement, better audit, queryability, backups
- **Implementation**: PyODBC with connection pooling

### 4. **Flask Health Endpoint**
- **Decision**: Separate Flask app thread for monitoring
- **Rationale**: Enable external health checks without disrupting bot
- **Alternative**: Could use Slack slash commands (less standard)

### 5. **Direct User ID Identification**
- **Decision**: Use Slack user ID directly as primary key
- **Rationale**: Platform-agnostic, no additional mapping table needed
- **Tradeoff**: Less flexibility for future migrations

### 6. **Multiple Submissions Per Month**
- **Decision**: Allow updates, latest submission wins
- **Rationale**: Users can correct mistakes; audit trail preserved
- **Implementation**: No unique constraint, just ORDER BY timestamp DESC

### 7. **No Hard Deadline Enforcement**
- **Decision**: Warn users but don't close submissions
- **Rationale**: Flexibility for real-world delays/extensions
- **Enhancement**: Could add `/close-submissions` admin command

## Scalability & Performance

### Current Capacity
- **Users**: 100+ concurrent submissions (no issue)
- **Submissions/month**: 1000+ handled easily
- **Response time**: Modal opens < 500ms, validation < 100ms, submit < 1s

### Bottlenecks (unlikely to hit)
- SQL Server connections: Configured for pooling
- Slack API rate limits: Per-app limits high (hundreds/sec)
- APScheduler overhead: Negligible

### Future Optimization Options
- Add database read replicas for reporting
- Cache SubmissionStatus in memory
- Async database operations (if needed)
- Redis cache for health checks

## Security Considerations

1. **Authentication**
   - Slack app credentials (token, signing secret) ✓
   - Windows integrated auth to SQL Server ✓
   - No external API exposure ✓

2. **Data Protection**
   - SQL Server backups recommended
   - Log files contain only user IDs (no PII) ✓
   - HTTPS to Slack (native) ✓

3. **Access Control**
   - Bot only accessible in dedicated channel
   - Only target users can submit
   - No admin commands exposed

4. **Audit Trail**
   - All submissions timestamped
   - Bot logs all events
   - Database maintains complete history

