#!/usr/bin/env python3
"""
Test script to verify Slack bot configuration and database connectivity
Run this before deploying to production
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all required packages can be imported"""
    print("Testing imports...")
    try:
        import slack_bolt
        from slack_bolt.adapter.socket_mode import SocketModeHandler
        import pyodbc
        import apscheduler
        import flask
        from dotenv import load_dotenv
        print("✓ All required packages imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_environment_variables():
    """Test that all required environment variables are set"""
    print("\nTesting environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "SLACK_BOT_TOKEN",
        "SLACK_APP_TOKEN",
        "SQL_CONNECTION_STRING",
        "SLACK_CHANNEL_ID",
        "TARGET_USER_IDS"
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"✗ Missing: {var}")
        else:
            # Mask sensitive values in output
            if "TOKEN" in var or "SECRET" in var or "CONNECTION" in var:
                display_value = value[:10] + "..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"✓ {var}: {display_value}")
    
    return len(missing) == 0


def test_database_connection():
    """Test SQL Server connectivity"""
    print("\nTesting SQL Server connection...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from database import db
        
        # Try to connect
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        conn.close()
        
        print(f"✓ Connected to SQL Server")
        print(f"  Version: {version.split()[0:3]}")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def test_slack_credentials():
    """Test Slack Socket Mode credentials"""
    print("\nTesting Slack credentials...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from slack_sdk import WebClient
        
        bot_token = os.getenv("SLACK_BOT_TOKEN")
        app_token = os.getenv("SLACK_APP_TOKEN")
        client = WebClient(token=bot_token)
        
        # Test bot token
        auth_test = client.auth_test()
        print(f"✓ Slack bot token authentication successful")
        print(f"  Bot User ID: {auth_test['user_id']}")
        print(f"  Bot Name: {auth_test['user']}")
        print(f"  Team: {auth_test['team']}")

        # Test app-level token used by Socket Mode
        socket_mode_test = WebClient().apps_connections_open(app_token=app_token)
        if not socket_mode_test.get("url"):
            raise ValueError("Slack did not return a Socket Mode connection URL")

        print("✓ Slack app token accepted for Socket Mode")
        return True
    except Exception as e:
        print(f"✗ Slack authentication failed: {e}")
        return False


def test_database_tables():
    """Test that database tables were created"""
    print("\nTesting database tables...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from database import db
        
        # Test table existence
        conn = db.get_connection()
        cursor = conn.cursor()
        
        tables = ["TargetUsers", "MonthlySubmissions", "SubmissionStatus"]
        for table in tables:
            cursor.execute(f"""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = '{table}'
            """)
            exists = cursor.fetchone()[0] > 0
            status = "✓" if exists else "✗"
            print(f"{status} Table: {table}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database table test failed: {e}")
        return False


def test_scheduler_setup():
    """Test APScheduler configuration"""
    print("\nTesting APScheduler setup...")
    try:
        from config import TRIGGER_DAY_OF_MONTH, TRIGGER_HOUR, TRIGGER_MINUTE
        from apscheduler.triggers.cron import CronTrigger
        
        # Verify trigger configuration
        trigger = CronTrigger(
            day=TRIGGER_DAY_OF_MONTH,
            hour=TRIGGER_HOUR,
            minute=TRIGGER_MINUTE
        )
        
        print(f"✓ APScheduler configured")
        print(f"  Trigger: Day {TRIGGER_DAY_OF_MONTH}, {TRIGGER_HOUR:02d}:{TRIGGER_MINUTE:02d} UTC")
        return True
    except Exception as e:
        print(f"✗ APScheduler setup failed: {e}")
        return False


def test_config_validation():
    """Test configuration validation"""
    print("\nTesting configuration validation...")
    try:
        from config import validate_config
        validate_config()
        print("✓ Configuration validation passed")
        return True
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Slack Decimal Bot - Pre-Deployment Configuration Test")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Environment Variables", test_environment_variables),
        ("Configuration Validation", test_config_validation),
        ("Database Connection", test_database_connection),
        ("Database Tables", test_database_tables),
        ("Slack Credentials", test_slack_credentials),
        ("Scheduler Setup", test_scheduler_setup),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' encountered an error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Bot is ready for deployment.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

