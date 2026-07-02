#!/usr/bin/env python3
"""
Test script for reminder logic
Tests weekday counting and reminder scheduling
"""

from datetime import datetime, timedelta
from scheduler import count_weekdays

def test_count_weekdays():
    """Test weekday counting logic"""
    print("Testing count_weekdays function...\n")
    
    # Test 1: Same day (should be 0)
    start = datetime(2026, 7, 2)  # Wednesday
    end = datetime(2026, 7, 2)
    count = count_weekdays(start, end)
    print(f"Test 1 - Same day: {count} (expected: 0) {'✓' if count == 0 else '✗'}")
    
    # Test 2: One weekday apart
    start = datetime(2026, 7, 2)  # Wednesday
    end = datetime(2026, 7, 3)    # Thursday
    count = count_weekdays(start, end)
    print(f"Test 2 - One weekday: {count} (expected: 1) {'✓' if count == 1 else '✗'}")
    
    # Test 3: 5 weekdays (Wed to Wed, excluding both ends technically but we count Thu-Fri-Mon-Tue-Wed)
    start = datetime(2026, 7, 1)  # Tuesday
    end = datetime(2026, 7, 8)    # Tuesday (next week)
    count = count_weekdays(start, end)
    print(f"Test 3 - Five weekdays (Tue to next Tue): {count} (expected: 5) {'✓' if count == 5 else '✗'}")
    
    # Test 4: Spans weekend
    start = datetime(2026, 7, 3)  # Friday
    end = datetime(2026, 7, 6)    # Monday
    count = count_weekdays(start, end)
    print(f"Test 4 - Fri to Mon (skip weekend): {count} (expected: 1) {'✓' if count == 1 else '✗'}")
    
    # Test 5: Two full weeks
    start = datetime(2026, 7, 1)  # Wednesday
    end = datetime(2026, 7, 15)   # Wednesday (2 weeks)
    count = count_weekdays(start, end)
    print(f"Test 5 - Two weeks: {count} (expected: 10) {'✓' if count == 10 else '✗'}")
    
    # Test 6: End before start (edge case)
    start = datetime(2026, 7, 8)
    end = datetime(2026, 7, 1)
    count = count_weekdays(start, end)
    print(f"Test 6 - End before start: {count} (expected: 0) {'✓' if count == 0 else '✗'}\n")

def test_reminder_schedule():
    """Test reminder schedule logic"""
    print("Testing reminder schedule logic...\n")
    
    # Simulate scenario:
    # - Submission starts on 2026-07-01 (Wed)
    # - Deadline is 10 days later: 2026-07-11 (Sat, but let's say submission_deadline is 2026-07-11)
    
    submission_deadline = datetime(2026, 7, 11, 9, 0)  # Saturday
    submission_start = submission_deadline - timedelta(days=10)  # Wed 2026-07-01
    
    print(f"Submission starts: {submission_start.strftime('%Y-%m-%d %A')}")
    print(f"Submission deadline: {submission_deadline.strftime('%Y-%m-%d %A')}")
    print()
    
    # Scenario 1: Check on Friday 2026-07-03 (2 weekdays after start)
    now = datetime(2026, 7, 3, 10, 0)  # Friday
    weekdays_elapsed = count_weekdays(submission_start, now)
    should_send = weekdays_elapsed >= 5
    print(f"Check on {now.strftime('%Y-%m-%d %A')}: {weekdays_elapsed} weekdays elapsed")
    print(f"  Send reminder? {should_send} (need 5+) {'✓' if not should_send else '✗'}")
    print()
    
    # Scenario 2: Check on Friday 2026-07-10 (9 weekdays after start - should trigger)
    now = datetime(2026, 7, 10, 10, 0)  # Friday
    weekdays_elapsed = count_weekdays(submission_start, now)
    should_send = weekdays_elapsed >= 5
    print(f"Check on {now.strftime('%Y-%m-%d %A')}: {weekdays_elapsed} weekdays elapsed")
    print(f"  Send reminder? {should_send} (need 5+) {'✓' if should_send else '✗'}")
    print()
    
    # Scenario 3: Check twice with 5 weekday gap
    last_reminder = datetime(2026, 7, 10, 10, 0)  # Friday
    now = datetime(2026, 7, 17, 10, 0)  # Friday next week
    weekdays_since_reminder = count_weekdays(last_reminder, now)
    should_send = weekdays_since_reminder >= 5
    print(f"Last reminder: {last_reminder.strftime('%Y-%m-%d %A')}")
    print(f"Check on {now.strftime('%Y-%m-%d %A')}: {weekdays_since_reminder} weekdays since last reminder")
    print(f"  Send another reminder? {should_send} (need 5+) {'✓' if should_send else '✗'}\n")

def test_database_import():
    """Test that database module can be imported"""
    print("Testing database module import...\n")
    try:
        from database import db
        print(f"✓ Successfully imported database module")
        print(f"  Database class: {db.__class__.__name__}")
        print(f"  Has log_reminder: {hasattr(db, 'log_reminder')}")
        print(f"  Has get_last_reminder_date: {hasattr(db, 'get_last_reminder_date')}")
        print(f"  Has get_reminder_count: {hasattr(db, 'get_reminder_count')}\n")
        return True
    except Exception as e:
        print(f"✗ Failed to import database: {e}\n")
        return False

def test_scheduler_import():
    """Test that scheduler module can be imported"""
    print("Testing scheduler module import...\n")
    try:
        from scheduler import check_and_send_reminders, count_weekdays as count_wd
        print(f"✓ Successfully imported scheduler module")
        print(f"  Has check_and_send_reminders: {check_and_send_reminders is not None}")
        print(f"  Has count_weekdays: {count_wd is not None}\n")
        return True
    except Exception as e:
        print(f"✗ Failed to import scheduler: {e}\n")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print(" Reminder Logic Test Suite")
    print("=" * 70)
    print()
    
    test_count_weekdays()
    test_reminder_schedule()
    test_database_import()
    test_scheduler_import()
    
    print("=" * 70)
    print(" All tests completed!")
    print("=" * 70)

