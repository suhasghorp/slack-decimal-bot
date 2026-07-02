import logging
from flask import Flask, jsonify
from datetime import datetime
from config import HEALTH_PORT, HEALTH_HOST

logger = logging.getLogger(__name__)

health_app = Flask(__name__)

# Global state
bot_status = {
    "running": False,
    "started_at": None,
    "last_error": None
}


@health_app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        uptime = None
        if bot_status["started_at"]:
            uptime = (datetime.utcnow() - bot_status["started_at"]).total_seconds()
        
        return jsonify({
            "status": "healthy" if bot_status["running"] else "unhealthy",
            "bot_running": bot_status["running"],
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime,
            "last_error": bot_status["last_error"]
        }), 200 if bot_status["running"] else 503
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500


@health_app.route('/health/ready', methods=['GET'])
def readiness_check():
    """Readiness check endpoint"""
    return jsonify({
        "ready": bot_status["running"],
        "timestamp": datetime.utcnow().isoformat()
    }), 200 if bot_status["running"] else 503


def set_bot_state(running, error=None):
    """Update bot state"""
    global bot_status
    bot_status["running"] = running
    bot_status["last_error"] = error
    if running and not bot_status["started_at"]:
        bot_status["started_at"] = datetime.utcnow()
    logger.info(f"Bot state updated: running={running}, error={error}")


def start_health_server():
    """Start the Flask health check server in a separate thread"""
    import threading
    
    def run_server():
        try:
            health_app.run(
                host=HEALTH_HOST,
                port=HEALTH_PORT,
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"Health server error: {e}")
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    logger.info(f"Health check server started on {HEALTH_HOST}:{HEALTH_PORT}")
    return thread

