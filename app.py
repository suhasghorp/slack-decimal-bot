#!/usr/bin/env python3
"""
Main Slack Bolt Bot for Monthly Decimal Submissions
Corporate Intranet Bot - SQL Server Backend
"""

import logging
import signal
import sys
from threading import Event

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config import (
    SLACK_BOT_TOKEN, SLACK_APP_TOKEN,
    SLACK_PROXY_URL, SLACK_PROXY_HEADERS,
    validate_config, logger
)
from handlers import register_handlers
from scheduler import setup_scheduler
from health import start_health_server, set_bot_state

# Global scheduler reference
scheduler = None
socket_mode_handler = None
shutdown_event = Event()


def stop_bot(reason):
    """Stop background services and signal the main thread to exit."""
    global scheduler, socket_mode_handler

    if shutdown_event.is_set():
        return

    logger.info(reason)

    if scheduler:
        try:
            scheduler.shutdown(wait=False)
        except Exception as e:
            logger.warning(f"Error shutting down scheduler: {e}")
        finally:
            scheduler = None

    if socket_mode_handler:
        try:
            socket_mode_handler.close()
        except Exception as e:
            logger.warning(f"Error closing Socket Mode handler: {e}")
        finally:
            socket_mode_handler = None

    set_bot_state(False, reason)
    shutdown_event.set()


def setup_signal_handlers():
    """Setup graceful shutdown handlers"""
    def signal_handler(sig, frame):
        stop_bot(f"Signal {sig} received. Shutting down gracefully...")
    
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main entry point for the bot"""
    try:
        shutdown_event.clear()

        # Validate configuration
        validate_config()
        
        # Initialize Slack app
        app = App(
            token=SLACK_BOT_TOKEN,
            logger=logger
        )
        
        logger.info("Slack Bolt app initialized")
        
        # Start health check server
        start_health_server()
        
        # Register event handlers
        register_handlers(app)
        logger.info("Event handlers registered")
        
        # Setup scheduler
        global scheduler
        scheduler = setup_scheduler(app, app.client)
        logger.info("APScheduler initialized")

        # Initialize Socket Mode handler
        global socket_mode_handler
        socket_mode_handler = SocketModeHandler(
            app,
            SLACK_APP_TOKEN,
            logger=logger,
            proxy=SLACK_PROXY_URL,
            proxy_headers=SLACK_PROXY_HEADERS
        )
        logger.info("Socket Mode handler initialized")
        
        # Mark bot as running
        set_bot_state(True)
        
        # Setup signal handlers for graceful shutdown
        setup_signal_handlers()
        
        logger.info("=" * 60)
        logger.info("Slack Bot Started - Monthly Decimal Collection")
        logger.info("Socket Mode connected - no inbound Slack request URL required")
        logger.info("=" * 60)
        
        # Start the bot via outbound Socket Mode connection
        socket_mode_handler.connect()
        shutdown_event.wait()
        return 0

    except KeyboardInterrupt:
        stop_bot("Keyboard interrupt received. Shutting down gracefully...")
        return 0
    
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        set_bot_state(False, str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())

