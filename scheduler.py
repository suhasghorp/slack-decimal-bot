import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import (
    TRIGGER_DAY_OF_MONTH, TRIGGER_HOUR, TRIGGER_MINUTE,
    TARGET_USER_IDS, SLACK_CHANNEL_ID, MONTH_NAMES
)
from database import db
from handlers import create_submit_button_block, create_status_block

logger = logging.getLogger(__name__)


def get_current_month_year():
    """Get current month in YYYY-MM format"""
    now = datetime.utcnow()
    return now.strftime("%Y-%m")


def count_weekdays(start_date, end_date):
    """Count the number of weekdays (Mon-Fri) between two dates (exclusive of start, inclusive of end)"""
    if start_date >= end_date:
        return 0
    
    count = 0
    current = start_date + timedelta(days=1)
    while current <= end_date:
        # weekday() returns 0-6 (Mon-Sun), so 0-4 are weekdays
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    
    return count


def check_and_send_reminders(client):
    """
    Check for pending users and send reminders every 5 weekdays
    Runs on weekdays (Mon-Fri)
    """
    try:
        month_year = get_current_month_year()
        pending_users = db.get_pending_users(month_year)
        
        if not pending_users:
            logger.info(f"No pending users for {month_year}")
            return
        
        logger.info(f"Checking reminders for {len(pending_users)} pending users in {month_year}")
        
        for user_id in pending_users:
            try:
                # Get last reminder date
                last_reminder = db.get_last_reminder_date(user_id, month_year)
                now = datetime.utcnow()
                
                should_send_reminder = False
                
                if last_reminder is None:
                    # First reminder: send if at least 5 weekdays have passed since submission started
                    status = db.get_submission_status(month_year)
                    if status and status['submission_deadline']:
                        # submission started at deadline - 10 days (approx)
                        submission_start = status['submission_deadline'] - timedelta(days=10)
                        weekdays_elapsed = count_weekdays(submission_start, now)
                        if weekdays_elapsed >= 5:
                            should_send_reminder = True
                else:
                    # Subsequent reminders: send every 5 weekdays
                    weekdays_since_reminder = count_weekdays(last_reminder, now)
                    if weekdays_since_reminder >= 5:
                        should_send_reminder = True
                
                if should_send_reminder:
                    # Send reminder DM
                    reminder_count = db.get_reminder_count(user_id, month_year)
                    month_label = MONTH_NAMES[datetime.utcnow().month - 1]
                    
                    message_text = (
                        f"📧 *Reminder: {month_label} Submission Pending*\n"
                        f"Hello! You haven't submitted your {month_label} data yet.\n"
                        f"Please submit your decimal value (between 0.00 and 100.00) as soon as possible.\n"
                        f"_This is reminder #{reminder_count + 1}_"
                    )
                    
                    client.chat_postMessage(
                        channel=user_id,
                        text=message_text
                    )
                    
                    # Log the reminder
                    db.log_reminder(user_id, month_year)
                    logger.info(f"Reminder #{reminder_count + 1} sent to {user_id} for {month_year}")
            
            except Exception as e:
                logger.error(f"Error sending reminder to {user_id}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error in check_and_send_reminders: {e}")
        raise


def monthly_submission_trigger(client):
    """
    Triggered monthly - posts submission button to channel
    and initializes submission status tracking
    """
    try:
        month_year = get_current_month_year()
        month_label = MONTH_NAMES[datetime.utcnow().month - 1]
        
        logger.info(f"Monthly trigger activated for {month_year}")
        
        # Initialize submission status in database
        db.update_submission_status(month_year, len(TARGET_USER_IDS))
        
        # Build message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📅 {month_label} {datetime.utcnow().year} Data Collection"
                }
            },
            {
                "type": "divider"
            },
            create_submit_button_block(),
            {
                "type": "divider"
            },
            create_status_block(),
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Expected submissions: {len(TARGET_USER_IDS)} | Decimal format: X.XX (0.00 - 100.00)"
                    }
                ]
            }
        ]
        
        # Post to channel
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            blocks=blocks,
            text=f"{month_label} {datetime.utcnow().year} Data Collection Started"
        )
        
        logger.info(f"Monthly message posted to channel {SLACK_CHANNEL_ID}")
        return response
    
    except Exception as e:
        logger.error(f"Error in monthly_submission_trigger: {e}")
        raise


def setup_scheduler(app, client):
    """
    Setup APScheduler with monthly trigger and daily reminder check
    
    Args:
        app: Slack Bolt app (for reference)
        client: Slack web client for posting messages
    """
    scheduler = BackgroundScheduler()
    
    # Create cron trigger for monthly execution
    monthly_trigger = CronTrigger(
        day=TRIGGER_DAY_OF_MONTH,
        hour=TRIGGER_HOUR,
        minute=TRIGGER_MINUTE
    )
    
    # Add monthly submission trigger job
    scheduler.add_job(
        func=monthly_submission_trigger,
        args=[client],
        trigger=monthly_trigger,
        id='monthly_submission_trigger',
        name='Monthly Submission Trigger',
        replace_existing=True
    )
    
    # Create cron trigger for weekday reminder checks (Mon-Fri at 10:00 UTC)
    # day_of_week: 0-6 (Mon-Sun), so 0-4 is Mon-Fri
    reminder_trigger = CronTrigger(
        day_of_week='0-4',
        hour=10,
        minute=0
    )
    
    # Add reminder check job
    scheduler.add_job(
        func=check_and_send_reminders,
        args=[client],
        trigger=reminder_trigger,
        id='check_and_send_reminders',
        name='Check and Send Reminders',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(
        f"Scheduler started.\n"
        f"  Monthly trigger: Day {TRIGGER_DAY_OF_MONTH}, {TRIGGER_HOUR:02d}:{TRIGGER_MINUTE:02d} UTC\n"
        f"  Reminder check: Weekdays (Mon-Fri) at 10:00 UTC"
    )
    
    return scheduler


def trigger_now(client):
    """Manually trigger the monthly submission (for testing)"""
    try:
        monthly_submission_trigger(client)
        logger.info("Manual trigger executed")
        return True
    except Exception as e:
        logger.error(f"Manual trigger failed: {e}")
        return False

