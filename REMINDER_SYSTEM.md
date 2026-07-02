# Non-Submission Handling Implementation

## Overview

This document describes how the Slack Decimal Bot handles non-submission of user data and implements a gentle reminder system.

## Problem Statement

**The Gap (now fixed):**
- Previously, `total_received` count in the status database was only updated when the monthly job ran
- This meant status messages could show stale received counts even after new submissions
- **Solution:** `insert_submission()` now calls `update_submission_status()` to refresh the count immediately after each submission

## Current Implementation

### 1. Non-Submission Detection

**How it works:**
- Compare configured `TARGET_USER_IDS` against actual submitters for the current month
- Users in target list but not in submissions list = **pending users**

**Key functions:**
- `database.get_pending_users(month_year)` - Returns list of users who haven't submitted
- `database.get_users_who_submitted(month_year)` - Returns list of users who have submitted
- `database.get_submission_status(month_year)` - Returns summary (received/total counts)

### 2. Gentle Reminder System (NEW)

**What it does:**
- Sends automated reminders to pending users every 5 weekdays
- Runs on weekdays (Mon-Fri) at 10:00 UTC
- Tracks reminders in database to avoid spam
- Continues until user submits

**How it works:**

#### First Reminder
- After 5 weekdays since submission period started
- Sent to all pending users

#### Subsequent Reminders  
- Another reminder every 5 weekdays if user still hasn't submitted
- Includes counter (e.g., "This is reminder #2")

#### Weekday Counting
- Counts business days (Mon-Fri only)
- Example: Friday to next Friday = 5 weekdays (Mon, Tue, Wed, Thu, Fri)
- Weekends are skipped

### 3. Database Schema

#### New Table: `ReminderLog`
```sql
CREATE TABLE ReminderLog (
    id INT PRIMARY KEY IDENTITY(1,1),
    slack_user_id NVARCHAR(50) NOT NULL,
    month_year NVARCHAR(20) NOT NULL,
    reminder_sent_at DATETIME DEFAULT GETUTCDATE(),
    FOREIGN KEY (slack_user_id) REFERENCES TargetUsers(slack_user_id)
)
```

Tracks every reminder sent to each user per month.

### 4. Scheduler Jobs

#### Job 1: Monthly Submission Trigger
- **Schedule:** First day of each month at configured time
- **Action:** Posts submission request to channel, initializes status tracking
- **Existing behavior:** Unchanged

#### Job 2: Check and Send Reminders (NEW)
- **Schedule:** Every weekday (Mon-Fri) at 10:00 UTC
- **Action:** 
  1. Get pending users for current month
  2. For each pending user:
     - Check if 5+ weekdays have passed since submission started (first reminder) or since last reminder (subsequent reminders)
     - If yes, send DM reminder and log it

## Implementation Details

### Key Changes

#### 1. `database.py`

**New methods:**
```python
def log_reminder(slack_user_id, month_year)
    # Insert reminder record into ReminderLog

def get_last_reminder_date(slack_user_id, month_year)
    # Get most recent reminder sent to user for month

def get_reminder_count(slack_user_id, month_year)
    # Count how many reminders sent to user for month
```

**Updated method:**
```python
def insert_submission(slack_user_id, submitted_value, month_year)
    # NOW: Refreshes total_received count immediately after insertion
    # Previously: Left count stale until next monthly job
```

#### 2. `scheduler.py`

**New function:**
```python
def count_weekdays(start_date, end_date)
    # Counts business days between two dates
    # Returns 0 if dates are in wrong order

def check_and_send_reminders(client)
    # Main reminder job
    # Runs daily on weekdays (Mon-Fri)
    # Sends DM reminders to pending users every 5 weekdays
```

**Updated:**
- `setup_scheduler()` now adds both monthly job AND reminder job
- Reminder job uses cron trigger: `day_of_week='0-4'` (Mon-Fri), `hour=10`, `minute=0`

## Workflow Example

### Day 1 (Wednesday) - July 1, 2026
- Monthly trigger fires at configured time
- Slack channel message posted: "July Data Collection"
- 5 users targeted, 0 submissions yet
- Reminder log is empty for all users

### Day 8 (Wednesday) - July 8, 2026
- Reminder job checks (runs daily Mon-Fri)
- Counts: 5 weekdays elapsed since July 1
- Sends "📧 Reminder: July Submission Pending" DM to all 5 pending users
- Logs reminder for each user

### Day 3 (Monday) - July 13, 2026
- User1 submits
- `insert_submission()` refreshes status → now shows 1/5 received
- User1 removed from pending list for next reminder check

### Day 15 (Wednesday) - July 15, 2026
- Reminder job checks
- Counts weekdays: 5+ since last reminder (July 8)
- Only pending users now: User2, User3, User4, User5
- Sends reminder #2 to each with counter
- Logs second reminder

## Configuration

### Reminder Schedule
- **Time:** 10:00 UTC on weekdays (configurable by code edit)
- **Frequency:** Every 5 weekdays
- **Start:** 5 weekdays after submission starts
- **Stop:** When user submits

### To Customize Reminder Time
Edit `scheduler.py`, line ~191:
```python
reminder_trigger = CronTrigger(
    day_of_week='0-4',      # Mon-Fri (0-4)
    hour=10,                # 10:00 UTC (edit this)
    minute=0                # (edit this)
)
```

### To Customize Weekday Threshold
Edit `scheduler.py`, lines 67 and 72:
```python
if weekdays_elapsed >= 5:  # Change 5 to another number
```

## Monitoring & Debugging

### Check Reminder Logs
```python
# In db_utility.py or app console:
from database import db
count = db.get_reminder_count('U12345', '2026-07')
last_date = db.get_last_reminder_date('U12345', '2026-07')
```

### Check Pending Users
```python
pending = db.get_pending_users('2026-07')
```

### View Submission Status
```python
status = db.get_submission_status('2026-07')
# Returns: {
#   'month_year': '2026-07',
#   'total_required': 5,
#   'total_received': 3,
#   'submission_deadline': datetime(...)
# }
```

### Manual Reminder Trigger
```python
from scheduler import check_and_send_reminders
from slack_bolt import App

app = App(token=SLACK_BOT_TOKEN)
check_and_send_reminders(app.client)
```

## Testing

Run the test suite to verify logic:
```bash
python test_reminders_simple.py
```

**Output includes:**
- ✓ Weekday counting tests
- ✓ Reminder schedule logic
- ✓ Database changes verification
- ✓ Scheduler changes verification

## Edge Cases Handled

1. **User submits same day as reminder check:** 
   - `get_pending_users()` is called at check time, so user won't get reminder if they just submitted
   - Second submission for same month is allowed

2. **Reminder during weekend:**
   - Job only runs Mon-Fri, skips weekends automatically

3. **Leap years and month boundaries:**
   - `count_weekdays()` handles month transitions correctly
   - Example: Friday to next Monday = 1 weekday (skips Sat/Sun)

4. **Stale reminder status:**
   - If bot restarts, `ReminderLog` is persistent in database
   - Reminders won't be re-sent for same date/user/month

5. **All users submitted:**
   - Job checks `pending_users` list
   - If empty, job exits early with info log
   - No errors, no wasted cycles

## Data Integrity

- **Immutable logs:** `ReminderLog` only inserts, never updates
- **Unique constraint:** Not added (allows duplicate reminders if manually triggered)
- **Foreign keys:** All `slack_user_id` references must exist in `TargetUsers`
- **Submission updates status:** Always fresh via `insert_submission()`

## Future Enhancements

### Possible Improvements
1. **Escalation:** After X reminders, notify admin/manager
2. **Exemptions:** Allow marking users as exempt temporarily
3. **Thresholds:** Configure weekday threshold per environment
4. **Reporting:** Dashboard showing reminder stats by month
5. **Multiple channels:** Send reminders in channel + DM
6. **Override:** Admins can force send/skip reminders


