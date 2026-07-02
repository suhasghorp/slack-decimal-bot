import logging
from datetime import datetime
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
    Setup APScheduler with monthly trigger
    
    Args:
        app: Slack Bolt app (for reference)
        client: Slack web client for posting messages
    """
    scheduler = BackgroundScheduler()
    
    # Create cron trigger for monthly execution
    # Note: day_of_month parameter is 0-indexed for some schedulers
    trigger = CronTrigger(
        day=TRIGGER_DAY_OF_MONTH,
        hour=TRIGGER_HOUR,
        minute=TRIGGER_MINUTE
    )
    
    # Add job
    scheduler.add_job(
        func=monthly_submission_trigger,
        args=[client],
        trigger=trigger,
        id='monthly_submission_trigger',
        name='Monthly Submission Trigger',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(
        f"Scheduler started. Monthly trigger: "
        f"Day {TRIGGER_DAY_OF_MONTH}, {TRIGGER_HOUR:02d}:{TRIGGER_MINUTE:02d} UTC"
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

