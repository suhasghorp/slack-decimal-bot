# Edge Case: Non-Submitter Across Multiple Months

## The Scenario

User never submits in July despite receiving multiple reminders:
- July 1: Monthly job posts submission request
- July 10: Gets reminder #1
- July 17: Gets reminder #2
- July 24: Gets reminder #3
- July 31: DEADLINE PASSES, user still hasn't submitted
- August 1: NEW MONTH BEGINS

**Question:** What happens on August 1st?

---

## Current Behavior: Fresh Start Per Month

### How It Works
The system is **month-aware** and treats each month independently:

```python
# scheduler.py line 43
month_year = get_current_month_year()  # '2026-08' on August 1

# scheduler.py line 44
pending_users = db.get_pending_users(month_year)  # Checks '2026-08' submissions
```

### What Happens on August 1st

1. **Monthly trigger fires** (assuming it's configured for 1st of month)
   - Posts new submission button: "Submit August Data"
   - Initializes new `SubmissionStatus` for '2026-08'
   - `total_received` = 0 (fresh start)

2. **July's data is complete**
   - All July reminders stop (different month_year)
   - July submission period "closes"
   - User's July non-submission is archived in database

3. **August begins with clean slate**
   - User is in `pending_users` for '2026-08' (didn't submit in August yet)
   - User will get new reminders for August after 5 weekdays
   - Reminder counter resets to #1

### Timeline Example

```
July 1         monthly_trigger('2026-07')  → posts submission
July 10        check_reminders('2026-07')  → sends reminder #1
July 17        check_reminders('2026-07')  → sends reminder #2
July 24        check_reminders('2026-07')  → sends reminder #3
July 31        check_reminders('2026-07')  → sends reminder #4
                                            → user still hasn't submitted

August 1       monthly_trigger('2026-08')  → posts NEW submission request
               (July reminders stop)

August 8       check_reminders('2026-08')  → sends reminder #1 for August
August 15      check_reminders('2026-08')  → sends reminder #2 for August
...
```

---

## What's Preserved vs. Reset

### Preserved in Database
- ✅ All July submissions (or lack thereof) in `MonthlySubmissions` table
- ✅ July's complete reminder history in `ReminderLog`
- ✅ July status snapshot in `SubmissionStatus`
- ✅ Audit trail showing user never submitted in July

**Query to check:**
```sql
SELECT month_year, slack_user_id, COUNT(*) as reminder_count
FROM ReminderLog
WHERE slack_user_id = 'U12345'
GROUP BY month_year, slack_user_id
ORDER BY month_year DESC;

-- Output example:
-- month_year  slack_user_id  reminder_count
-- 2026-08     U12345         1              (new month, 1 reminder sent so far)
-- 2026-07     U12345         4              (old month, 4 reminders sent total)
```

### Reset Each Month
- ❌ Reminder counter (starts at #1 again in August)
- ❌ Submission status (starts with 0 received in August)
- ❌ "Days since first reminder" counter (resets to 0)

---

## Implications & Edge Cases

### Case 1: Chronic Non-Submitter
**Scenario:** User never submits any month

```
July         → 4 reminders sent, no submission
August       → 4 reminders sent, no submission
September    → 4 reminders sent, no submission
...
October 1    → User gets ANOTHER fresh month
```

**Current behavior:** System has NO escalation - just keeps reminding every month.

**Possible concerns:**
- No awareness of chronic non-submission
- No manager/admin notification for persistent non-compliance
- Could be repeated forever

**When this might be intentional:**
- Organization doesn't want to escalate
- User might have legitimate reasons per month (leave, exempt, etc.)
- Prefer gentle reminders over hard enforcement

### Case 2: User Submits in Month 2 After Missing Month 1
**Scenario:** Didn't submit July, but submits in August

```
July         → 4 reminders, no submission
August 1     → New month, new submission button
August 10    → User finally submits (first ever submission)
```

**Database state, after August submission:**
- `MonthlySubmissions`: Has June?, July 0 entries, August 1 entry
- `ReminderLog`: July has 4 entries, August has 0 entries (got reminder #1 scheduled but submitted before it)
- Status is accurate: User "submitted eventually"

### Case 3: User Deletes Slack or Leaves Company
**Scenario:** User in TARGET_USER_IDS but no longer exists

```
July         → Reminder DM fails (user not found)
             → Error caught, logged, continues
August 1     → User still in TARGET_USER_IDS
             → Same reminders attempted again
```

**Current handling:**
- `check_and_send_reminders()` has try/catch per user
- Error from one user doesn't affect others
- User stays in pending list forever (unless removed from config)

**Improvement needed:** Detect deleted users and skip them

---

## Database State After Month Transition

### Before: End of July
```sql
-- MonthlySubmissions (July)
id | slack_user_id | submitted_value | month_year
1  | U111111       | 45.67           | 2026-07
2  | U222222       | 89.12           | 2026-07
3  | U333333       | 23.45           | 2026-07
-- U444444 and U555555 are NOT here (didn't submit)

-- ReminderLog (July)
id | slack_user_id | month_year | reminder_sent_at
1  | U444444       | 2026-07    | 2026-07-10 10:00
2  | U444444       | 2026-07    | 2026-07-17 10:00
3  | U444444       | 2026-07    | 2026-07-24 10:00
4  | U444444       | 2026-07    | 2026-07-31 10:00
5  | U555555       | 2026-07    | 2026-07-10 10:00
6  | U555555       | 2026-07    | 2026-07-17 10:00
... (more reminders for U555555)

-- SubmissionStatus (July)
month_year | total_required | total_received | submission_deadline
2026-07    | 5              | 3              | 2026-07-11 09:00
```

### After: August Begins
```sql
-- MonthlySubmissions (unchanged)
-- All July records remain

-- ReminderLog (unchanged so far)
-- All July records remain

-- SubmissionStatus (new month)
month_year | total_required | total_received | submission_deadline
2026-07    | 5              | 3              | 2026-07-11 09:00   (archived)
2026-08    | 5              | 0              | 2026-08-11 09:00   (new)
```

### After: First Reminder in August (August 8th)
```sql
-- ReminderLog (new entry for August)
id | slack_user_id | month_year | reminder_sent_at
... (previous July entries)
X  | U444444       | 2026-08    | 2026-08-08 10:00  (NEW - month changed)
Y  | U555555       | 2026-08    | 2026-08-08 10:00  (NEW - month changed)
```

Notice: Different month_year means separate reminder tracking!

---

## Code Flow: Month Transition

### Line-by-line for August 1st

```python
# app.py - scheduled job fires at 9 AM (1st of month)
monthly_submission_trigger(client)  # Line 105 in scheduler.py

# scheduler.py line 111
month_year = get_current_month_year()  # Returns '2026-08'

# scheduler.py line 117
db.update_submission_status('2026-08', 5)  # Creates new row for August

# Database after:
# SubmissionStatus now has TWO rows:
# - month_year='2026-07' (from July, complete)
# - month_year='2026-08' (from August, fresh start)
```

### Line-by-line for August 8th Reminder Check

```python
# app.py - scheduled job fires at 10 AM (weekday)
check_and_send_reminders(client)  # Line 37 in scheduler.py

# scheduler.py line 43
month_year = get_current_month_year()  # Returns '2026-08' (still August)

# scheduler.py line 44
pending_users = db.get_pending_users('2026-08')
# Returns users from TARGET_USER_IDS who are NOT in MonthlySubmissions FOR 2026-08
# Includes U444444 and U555555 who didn't submit in July
# (they're still "pending for August" even though they were pending for July)

# scheduler.py line 55
last_reminder = db.get_last_reminder_date('U444444', '2026-08')
# Returns NULL because U444444's last reminder was in '2026-07'
# (different month_year)

# scheduler.py line 60-68
if last_reminder is None:
    # First reminder for August!
    status = db.get_submission_status('2026-08')  # Gets August's status
    submission_start = status['submission_deadline'] - timedelta(days=10)
    # submission_start = 2026-08-01 (August 1st)
    weekdays_elapsed = count_weekdays(submission_start, now)
    # count = 5 weekdays (Aug 1-8: Thu, Fri, Mon, Tue, Wed = 5)
    if weekdays_elapsed >= 5:  # TRUE
        should_send_reminder = True  # SENDS FIRST AUGUST REMINDER
```

---

## Current Design Philosophy

The system intentionally:
1. ✅ **Treats each month independently** - Fresh opportunity each month
2. ✅ **Preserves history** - All old data kept for audit/reporting
3. ✅ **Resets reminders per month** - No "memory" of past non-submissions
4. ✅ **Separates concerns** - July submissions ≠ August submissions

This assumes:
- Monthly data is independent
- Each month is a separate collection cycle
- Users deserve a fresh chance each month

---

## Potential Issues & Improvements

### Issue 1: No Escalation for Chronic Non-Submitters
**Current:** User could go years without submitting and just get gentle reminders

**Possible fix:** 
```python
def check_is_chronic_non_submitter(user_id, lookback_months=3):
    """Check if user didn't submit in the last N months"""
    # Query MonthlySubmissions for this user
    # If count = 0 for all recent months → escalate
```

### Issue 2: Deleted Users Still Get Reminder Attempts
**Current:** If user leaves company, monthly reminder still tries to DM them

**Possible fix:**
```python
def get_valid_pending_users(month_year):
    """Get pending users, excluding deleted/inactive users"""
    # Try to call Slack user profile API first
    # Remove users who no longer exist
```

### Issue 3: No Month-End Summary
**Current:** No report of who didn't submit when July ended

**Possible fix:**
```python
def send_month_end_summary(client):
    """Send admin report: who submitted, who didn't"""
    # Runs on last day of month
    # Sends summary to admin channel
```

### Issue 4: No Way to Carry Over "Overdue" Status
**Current:** If July reminder chain is broken, August starts fresh

**Possible fix:**
```python
def check_if_overdue_from_previous_month(user_id):
    """Return True if user failed to submit last month"""
    # Used to prioritize reminders or escalate
```

---

## Behavior Summary Table

| What | July | August | Preserved? |
|-----|------|--------|-----------|
| **Submission Button** | New | New | ❌ (appears fresh) |
| **Submissions Data** | Stored | Stored | ✅ (in DB forever) |
| **Reminder History** | Stored | Stored | ✅ (in ReminderLog) |
| **Reminders Sent** | #1-#4 | #1-# | ❌ (counter resets) |
| **Status Tracking** | July row | Aug row | ✅ (separate rows) |
| **Pending Users List** | Based on July | Based on Aug | ✅ (recalculated) |

---

## Recommendation

### Current design is **good for:**
- ✅ Giving users a fresh chance each month
- ✅ Preventing reminder fatigue (no accumulation)
- ✅ Treating months as independent cycles
- ✅ Simplicity and reliability

### Should add if you want:**
- 🔧 Chronic non-submitter detection (flag in admin dashboard)
- 🔧 Month-end summary reports
- 🔧 Escalation after 3 consecutive months of non-submission
- 🔧 Manager notification for persistent non-compliance
- 🔧 Deleted user detection

These can be added later without changing the core reminder system.

---

## How to Monitor This

### Check who's been non-submitters
```sql
-- Users who missed July AND August
SELECT DISTINCT rl1.slack_user_id
FROM ReminderLog rl1
WHERE rl1.month_year = '2026-07'
AND NOT EXISTS (
    SELECT 1 FROM MonthlySubmissions ms 
    WHERE ms.slack_user_id = rl1.slack_user_id 
    AND ms.month_year = '2026-07'
)
AND NOT EXISTS (
    SELECT 1 FROM MonthlySubmissions ms 
    WHERE ms.slack_user_id = rl1.slack_user_id 
    AND ms.month_year = '2026-08'
);
```

### Check reminders sent per user per month
```sql
SELECT 
    slack_user_id, 
    month_year, 
    COUNT(*) as reminder_count,
    MIN(reminder_sent_at) as first_reminder,
    MAX(reminder_sent_at) as last_reminder
FROM ReminderLog
GROUP BY slack_user_id, month_year
ORDER BY month_year DESC, slack_user_id;
```

---

**Summary:** The system treats each month as a fresh cycle. Non-submitters from July will get new reminders in August. All history is preserved in the database for auditing, but the reminder tracking resets. This is intentional and gives users a fresh chance each month.

If you want chronic non-submitter detection or escalation, those can be added as separate features later.

