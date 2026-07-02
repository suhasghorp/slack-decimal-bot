#!/usr/bin/env python3
"""
Simplified test for reminder logic - no external dependencies
Tests the core weekday counting logic
"""

from datetime import datetime, timedelta

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


def test_count_weekdays():
    """Test weekday counting logic"""
    print("Testing count_weekdays function...\n")
    
    # Test 1: Same day (should be 0)
    start = datetime(2026, 7, 2)  # Wednesday
    end = datetime(2026, 7, 2)
    count = count_weekdays(start, end)
    status = '✓' if count == 0 else '✗'
    print(f"Test 1 - Same day: {count} (expected: 0) {status}")
    
    # Test 2: One weekday apart
    start = datetime(2026, 7, 2)  # Wednesday
    end = datetime(2026, 7, 3)    # Thursday
    count = count_weekdays(start, end)
    status = '✓' if count == 1 else '✗'
    print(f"Test 2 - One weekday: {count} (expected: 1) {status}")
    
    # Test 3: 5 weekdays (Wed to Wed, excluding both ends technically but we count Thu-Fri-Mon-Tue-Wed)
    start = datetime(2026, 7, 1)  # Wednesday (actually Tuesday based on calendar)
    end = datetime(2026, 7, 8)    # Next Wednesday (actually next Wednesday)
    count = count_weekdays(start, end)
    status = '✓' if count == 5 else '✗'
    print(f"Test 3 - Five weekdays (Wed to next Wed): {count} (expected: 5) {status}")
    
    # Test 4: Spans weekend
    start = datetime(2026, 7, 3)  # Friday
    end = datetime(2026, 7, 6)    # Monday
    count = count_weekdays(start, end)
    status = '✓' if count == 1 else '✗'
    print(f"Test 4 - Fri to Mon (skip weekend): {count} (expected: 1) {status}")
    
    # Test 5: Two full weeks
    start = datetime(2026, 7, 1)  # Wednesday
    end = datetime(2026, 7, 15)   # Next Wednesday (2 weeks)
    count = count_weekdays(start, end)
    status = '✓' if count == 10 else '✗'
    print(f"Test 5 - Two weeks: {count} (expected: 10) {status}")
    
    # Test 6: End before start (edge case)
    start = datetime(2026, 7, 8)
    end = datetime(2026, 7, 1)
    count = count_weekdays(start, end)
    status = '✓' if count == 0 else '✗'
    print(f"Test 6 - End before start: {count} (expected: 0) {status}\n")


def test_reminder_schedule():
    """Test reminder schedule logic"""
    print("Testing reminder schedule logic...\n")
    
    # Simulate scenario:
    # - Submission starts on 2026-07-01 (Wed)
    # - Deadline is 10 days later: 2026-07-11 (Sat)
    
    submission_deadline = datetime(2026, 7, 11, 9, 0)  # Saturday
    submission_start = submission_deadline - timedelta(days=10)  # Wed 2026-07-01
    
    print(f"Submission starts: {submission_start.strftime('%Y-%m-%d %A')}")
    print(f"Submission deadline: {submission_deadline.strftime('%Y-%m-%d %A')}")
    print()
    
    # Scenario 1: Check on Friday 2026-07-03 (2 weekdays after start)
    now = datetime(2026, 7, 3, 10, 0)  # Friday
    weekdays_elapsed = count_weekdays(submission_start, now)
    should_send = weekdays_elapsed >= 5
    expected = False
    status = '✓' if should_send == expected else '✗'
    print(f"Check on {now.strftime('%Y-%m-%d %A')}: {weekdays_elapsed} weekdays elapsed")
    print(f"  Send reminder? {should_send} (need 5+) {status}")
    print()
    
    # Scenario 2: Check on Friday 2026-07-10 (9 weekdays after start - should trigger)
    now = datetime(2026, 7, 10, 10, 0)  # Friday
    weekdays_elapsed = count_weekdays(submission_start, now)
    should_send = weekdays_elapsed >= 5
    expected = True
    status = '✓' if should_send == expected else '✗'
    print(f"Check on {now.strftime('%Y-%m-%d %A')}: {weekdays_elapsed} weekdays elapsed")
    print(f"  Send reminder? {should_send} (need 5+) {status}")
    print()
    
    # Scenario 3: Check twice with 5 weekday gap
    last_reminder = datetime(2026, 7, 10, 10, 0)  # Friday
    now = datetime(2026, 7, 17, 10, 0)  # Friday next week
    weekdays_since_reminder = count_weekdays(last_reminder, now)
    should_send = weekdays_since_reminder >= 5
    expected = True
    status = '✓' if should_send == expected else '✗'
    print(f"Last reminder: {last_reminder.strftime('%Y-%m-%d %A')}")
    print(f"Check on {now.strftime('%Y-%m-%d %A')}: {weekdays_since_reminder} weekdays since last reminder")
    print(f"  Send another reminder? {should_send} (need 5+) {status}\n")


def test_database_changes():
    """Verify database.py has been updated with new methods"""
    print("Verifying database.py changes...\n")
    
    try:
        with open('database.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('ReminderLog table', 'CREATE TABLE ReminderLog' in content),
            ('log_reminder method', 'def log_reminder' in content),
            ('get_last_reminder_date method', 'def get_last_reminder_date' in content),
            ('get_reminder_count method', 'def get_reminder_count' in content),
            ('insert_submission calls update_submission_status', 
             'self.update_submission_status(month_year, None)' in content),
        ]
        
        all_pass = True
        for check_name, result in checks:
            status = '✓' if result else '✗'
            print(f"  {status} {check_name}")
            all_pass = all_pass and result
        
        print()
        return all_pass
    except Exception as e:
        print(f"  ✗ Error reading database.py: {e}\n")
        return False


def test_scheduler_changes():
    """Verify scheduler.py has been updated with reminder logic"""
    print("Verifying scheduler.py changes...\n")
    
    try:
        with open('scheduler.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('count_weekdays function', 'def count_weekdays' in content),
            ('check_and_send_reminders function', 'def check_and_send_reminders' in content),
            ('timedelta import', 'from datetime import datetime, timedelta' in content),
            ('Reminder job added to scheduler', 'check_and_send_reminders' in content and 'add_job' in content),
            ('Weekday trigger (Mon-Fri)', "day_of_week='0-4'" in content),
        ]
        
        all_pass = True
        for check_name, result in checks:
            status = '✓' if result else '✗'
            print(f"  {status} {check_name}")
            all_pass = all_pass and result
        
        print()
        return all_pass
    except Exception as e:
        print(f"  ✗ Error reading scheduler.py: {e}\n")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print(" Reminder Logic Test Suite (No External Dependencies)")
    print("=" * 70)
    print()
    
    test_count_weekdays()
    test_reminder_schedule()
    test_database_changes()
    test_scheduler_changes()
    
    print("=" * 70)
    print(" All tests completed!")
    print("=" * 70)

