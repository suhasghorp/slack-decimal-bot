import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Slack Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

# SQL Server Configuration
SQL_CONNECTION_STRING = os.getenv("SQL_CONNECTION_STRING")

# Target Users
TARGET_USER_IDS = [uid.strip() for uid in os.getenv("TARGET_USER_IDS", "").split(",") if uid.strip()]

# Monthly Schedule
TRIGGER_DAY_OF_MONTH = int(os.getenv("TRIGGER_DAY_OF_MONTH", "1"))
TRIGGER_HOUR = int(os.getenv("TRIGGER_HOUR", "9"))
TRIGGER_MINUTE = int(os.getenv("TRIGGER_MINUTE", "0"))

# Submission Deadline
SUBMISSION_DEADLINE_DAYS = int(os.getenv("SUBMISSION_DEADLINE_DAYS", "10"))

# Decimal Validation
MIN_DECIMAL = float(os.getenv("MIN_DECIMAL", "0.00"))
MAX_DECIMAL = float(os.getenv("MAX_DECIMAL", "100.00"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/bot.log")

# Health Endpoint Configuration
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "5000"))
HEALTH_HOST = os.getenv("HEALTH_HOST", "0.0.0.0")

# Slack Proxy Configuration (optional, for corporate environments)
SLACK_PROXY_URL = os.getenv("SLACK_PROXY_URL")  # e.g., "http://proxy.company.com:8080"
SLACK_PROXY_HEADERS_RAW = os.getenv("SLACK_PROXY_HEADERS")  # JSON string: '{"Proxy-Authorization": "Bearer token"}'

# Parse proxy headers if provided
SLACK_PROXY_HEADERS = None
if SLACK_PROXY_HEADERS_RAW:
    try:
        import json
        SLACK_PROXY_HEADERS = json.loads(SLACK_PROXY_HEADERS_RAW)
    except Exception as e:
        logger.warning(f"Failed to parse SLACK_PROXY_HEADERS: {e}")

# Month names for button labels
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Setup logging
os.makedirs(os.path.dirname(LOG_FILE) if os.path.dirname(LOG_FILE) else ".", exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Validate required configuration
def validate_config():
    """Validate that all required configuration is present"""
    required = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SQL_CONNECTION_STRING", "SLACK_CHANNEL_ID"]
    missing = [key for key in required if not globals()[key]]
    
    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")

    if not SLACK_BOT_TOKEN.startswith("xoxb-"):
        raise ValueError("SLACK_BOT_TOKEN must start with 'xoxb-'")

    if not SLACK_APP_TOKEN.startswith("xapp-"):
        raise ValueError("SLACK_APP_TOKEN must start with 'xapp-'")
    
    if not TARGET_USER_IDS:
        raise ValueError("TARGET_USER_IDS must not be empty")
    
    logger.info(f"Configuration validated. Target users: {len(TARGET_USER_IDS)}")

