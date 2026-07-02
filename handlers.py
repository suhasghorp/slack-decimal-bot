import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from config import MIN_DECIMAL, MAX_DECIMAL, MONTH_NAMES
from database import db

logger = logging.getLogger(__name__)


def get_current_month_year():
    """Get current month in YYYY-MM format"""
    now = datetime.utcnow()
    return now.strftime("%Y-%m")


def validate_decimal_input(value_str):
    """
    Validate decimal input:
    - Must have exactly 2 decimal places
    - Must be within MIN_DECIMAL and MAX_DECIMAL
    
    Returns: (is_valid, error_message, decimal_value)
    """
    try:
        # Check format: must match pattern like "12.34"
        if not re.match(r'^\d+\.\d{2}$', value_str.strip()):
            return False, "❌ Invalid format. Please enter a number with exactly 2 decimal places (e.g., 45.67)", None
        
        # Convert to Decimal for precise validation
        value = Decimal(value_str.strip())
        
        # Check range
        if value < Decimal(str(MIN_DECIMAL)):
            return False, f"❌ Value too low. Minimum allowed: {MIN_DECIMAL:.2f}", None
        
        if value > Decimal(str(MAX_DECIMAL)):
            return False, f"❌ Value too high. Maximum allowed: {MAX_DECIMAL:.2f}", None
        
        return True, "", float(value)
    
    except (InvalidOperation, ValueError) as e:
        logger.warning(f"Invalid decimal input: {value_str} - {e}")
        return False, "❌ Invalid number format. Please try again.", None


def get_month_button_label(month_offset=0):
    """Get button label for current or future month"""
    now = datetime.utcnow()
    month_num = (now.month - 1 + month_offset) % 12
    return MONTH_NAMES[month_num]


def register_handlers(app):
    """Register all Slack event handlers"""
    
    @app.action("submit_data_button")
    def handle_submit_button(ack, body, client, logger):
        """Handle monthly submission button click - open modal"""
        ack()
        
        try:
            user_id = body["user"]["id"]
            month_year = get_current_month_year()
            month_label = get_month_button_label()
            
            # Build the modal
            modal_view = {
                "type": "modal",
                "callback_id": "submission_modal",
                "title": {
                    "type": "plain_text",
                    "text": f"{month_label} Submission"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Submit"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Cancel"
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Submit your decimal value for {month_label}*\n_Please enter a value between {MIN_DECIMAL:.2f} and {MAX_DECIMAL:.2f} with exactly 2 decimal places._"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "decimal_input_block",
                        "label": {
                            "type": "plain_text",
                            "text": f"Value ({MIN_DECIMAL:.2f} - {MAX_DECIMAL:.2f})"
                        },
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "decimal_value_input",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "e.g., 45.67"
                            }
                        },
                        "optional": False
                    }
                ],
                "private_metadata": month_year
            }
            
            # Open modal
            client.views_open(
                trigger_id=body["trigger_id"],
                view=modal_view
            )
            logger.info(f"Modal opened for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error opening modal: {e}")
    
    @app.view("submission_modal")
    def handle_modal_submission(ack, body, client, view, logger):
        """Handle modal submission and validation"""
        
        # Get input value
        decimal_input = view["state"]["values"]["decimal_input_block"]["decimal_value_input"]["value"]
        user_id = body["user"]["id"]
        month_year = view["private_metadata"]
        
        # Validate input
        is_valid, error_msg, decimal_value = validate_decimal_input(decimal_input)
        
        if not is_valid:
            # Return validation error to modal
            ack(response_action="errors", errors={
                "decimal_input_block": error_msg
            })
            logger.warning(f"Invalid submission from {user_id}: {decimal_input}")
            return
        
        # Valid - save to database and acknowledge
        try:
            db.insert_submission(user_id, decimal_value, month_year)
            ack()
            
            # Send confirmation message to user
            month_label = get_month_button_label()
            client.chat_postMessage(
                channel=user_id,
                text=f"✅ *Submission Confirmed*\n"
                     f"Value: `{decimal_value:.2f}`\n"
                     f"Month: {month_label}\n"
                     f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
            )
            
            logger.info(f"Submission confirmed from {user_id}: {decimal_value}")
        
        except Exception as e:
            logger.error(f"Error saving submission: {e}")
            ack(response_action="errors", errors={
                "decimal_input_block": "❌ Failed to save submission. Please try again."
            })
    
    @app.action("check_status_button")
    def handle_status_button(ack, body, client, logger):
        """Handle status check button - show submission status"""
        ack()
        
        try:
            month_year = get_current_month_year()
            status = db.get_submission_status(month_year)
            
            if status:
                pending = db.get_pending_users(month_year)
                pending_count = len(pending)
                received = status['total_received']
                total = status['total_required']
                
                message_text = (
                    f"📊 *Submission Status - {get_month_button_label()}*\n"
                    f"Received: {received}/{total}\n"
                    f"Pending: {pending_count}\n"
                    f"Deadline: {status['submission_deadline'].strftime('%Y-%m-%d %H:%M UTC') if status['submission_deadline'] else 'N/A'}"
                )
            else:
                message_text = f"ℹ️ No submissions yet for {get_month_button_label()}"
            
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=message_text
            )
        
        except Exception as e:
            logger.error(f"Error checking status: {e}")
    
    @app.error
    def custom_error_handler(error, body, logger):
        """Handle errors"""
        logger.error(f"Error: {error}")
        logger.debug(f"Request body: {body}")


def create_submit_button_block(month_offset=0):
    """Create the monthly submission button block"""
    month_label = get_month_button_label(month_offset)
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"📋 *Monthly Data Submission - {month_label}*\n_Click the button below to submit your decimal value._"
        },
        "accessory": {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": f"Submit {month_label} Data"
            },
            "action_id": "submit_data_button",
            "value": "submit_data",
            "style": "primary"
        }
    }


def create_status_block():
    """Create the status check button block"""
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "🔍 _Check submission status to see who has submitted._"
        },
        "accessory": {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Check Status"
            },
            "action_id": "check_status_button",
            "value": "check_status"
        }
    }

