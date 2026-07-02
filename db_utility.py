#!/usr/bin/env python3
"""
Database utility script for managing submissions and status
Useful for admin tasks and troubleshooting
"""

import sys
import os
from datetime import datetime
from pathlib import Path
from tabulate import tabulate

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70 + "\n")


def show_current_month_status():
    """Show submission status for current month"""
    try:
        from database import db
        from handlers import get_current_month_year
        from config import TARGET_USER_IDS
        
        month_year = get_current_month_year()
        
        # Get status
        status = db.get_submission_status(month_year)
        
        print_header(f"Submission Status - {month_year}")
        
        if status:
            print(f"Month: {status['month_year']}")
            print(f"Total Required: {status['total_required']}")
            print(f"Total Received: {status['total_received']}")
            print(f"Completion: {status['total_received']}/{status['total_required']} ({100*status['total_received']/status['total_required']:.1f}%)")
            print(f"Deadline: {status['submission_deadline']}")
            print(f"Last Updated: {status['last_updated']}")
        else:
            print(f"No submissions yet for {month_year}")
        
        # Show pending users
        pending = db.get_pending_users(month_year)
        if pending:
            print(f"\n⏳ Pending Users ({len(pending)}):")
            for user_id in pending:
                print(f"  - {user_id}")
        else:
            print("\n✓ All users have submitted!")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def show_user_submission_history(user_id):
    """Show submission history for a specific user"""
    try:
        from database import db
        import pyodbc
        
        print_header(f"Submission History - User {user_id}")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, submitted_value, submission_date, month_year
            FROM MonthlySubmissions
            WHERE slack_user_id = ?
            ORDER BY submission_date DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            headers = ["ID", "Value", "Submitted", "Month"]
            data = [
                [row[0], f"{row[1]:.2f}", row[2].strftime("%Y-%m-%d %H:%M"), row[3]]
                for row in rows
            ]
            print(tabulate(data, headers=headers, tablefmt="grid"))
            print(f"\nTotal submissions: {len(rows)}")
        else:
            print(f"No submissions found for user {user_id}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def show_all_current_submissions():
    """Show all submissions for current month"""
    try:
        from database import db
        from handlers import get_current_month_year
        
        month_year = get_current_month_year()
        
        print_header(f"All Submissions - {month_year}")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.slack_user_id, m.submitted_value, m.submission_date, 
                   ROW_NUMBER() OVER (PARTITION BY m.slack_user_id ORDER BY m.submission_date DESC) as submission_num
            FROM MonthlySubmissions m
            WHERE m.month_year = ?
            ORDER BY m.slack_user_id, m.submission_date DESC
        """, (month_year,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            # Show only latest submission per user
            latest_entries = {}
            for row in rows:
                user_id = row[0]
                if user_id not in latest_entries or row[3] == 1:
                    latest_entries[user_id] = row
            
            headers = ["User ID", "Value", "Submitted", "Submission #"]
            data = [
                [entry[0], f"{entry[1]:.2f}", entry[2].strftime("%Y-%m-%d %H:%M"), entry[3]]
                for entry in latest_entries.values()
            ]
            print(tabulate(data, headers=headers, tablefmt="grid"))
            print(f"\nTotal users submitted: {len(latest_entries)}")
        else:
            print(f"No submissions found for {month_year}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def clear_current_month_submissions(confirm=True):
    """Clear all submissions for current month (use with caution)"""
    try:
        from database import db
        from handlers import get_current_month_year
        
        month_year = get_current_month_year()
        
        if confirm:
            print_header(f"⚠️  WARNING: Clear Submissions - {month_year}")
            print(f"This will DELETE all submissions for {month_year}")
            response = input("Type 'DELETE' to confirm: ").strip()
            if response != "DELETE":
                print("✗ Cancelled")
                return False
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM MonthlySubmissions
            WHERE month_year = ?
        """, (month_year,))
        
        rows_deleted = cursor.rowcount
        
        cursor.execute("""
            DELETE FROM SubmissionStatus
            WHERE month_year = ?
        """, (month_year,))
        
        conn.close()
        
        print(f"✓ Deleted {rows_deleted} submissions for {month_year}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def export_submissions_to_csv(month_year=None):
    """Export submissions to CSV file"""
    try:
        import csv
        from database import db
        from handlers import get_current_month_year
        
        if not month_year:
            month_year = get_current_month_year()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.user_name, m.slack_user_id, m.submitted_value, 
                   m.submission_date, m.month_year
            FROM MonthlySubmissions m
            JOIN TargetUsers u ON m.slack_user_id = u.slack_user_id
            WHERE m.month_year = ?
            ORDER BY m.submission_date DESC
        """, (month_year,))
        
        rows = cursor.fetchall()
        conn.close()
        
        filename = f"submissions_{month_year}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['User Name', 'Slack ID', 'Value', 'Submitted', 'Month'])
            for row in rows:
                writer.writerow([
                    row[0],
                    row[1],
                    f"{row[2]:.2f}",
                    row[3].strftime("%Y-%m-%d %H:%M:%S"),
                    row[4]
                ])
        
        print(f"✓ Exported {len(rows)} submissions to {filename}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def show_help():
    """Display help menu"""
    print_header("Database Utility - Help Menu")
    print("""
Usage: python db_utility.py [COMMAND] [OPTIONS]

Commands:
  status                 Show current month submission status
  history <USER_ID>      Show submission history for a user
  all                    Show all submissions for current month
  export [MONTH_YEAR]    Export submissions to CSV (format: YYYY-MM)
  clear                  Clear all submissions for current month (WARNED)
  help                   Show this help menu

Examples:
  python db_utility.py status
  python db_utility.py history U123456789
  python db_utility.py all
  python db_utility.py export 2024-07
  python db_utility.py clear
    """)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_help()
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "status":
        return 0 if show_current_month_status() else 1
    
    elif command == "history":
        if len(sys.argv) < 3:
            print("✗ Usage: python db_utility.py history <USER_ID>")
            return 1
        user_id = sys.argv[2]
        return 0 if show_user_submission_history(user_id) else 1
    
    elif command == "all":
        return 0 if show_all_current_submissions() else 1
    
    elif command == "export":
        month_year = sys.argv[3] if len(sys.argv) > 3 else None
        return 0 if export_submissions_to_csv(month_year) else 1
    
    elif command == "clear":
        return 0 if clear_current_month_submissions(confirm=True) else 1
    
    elif command == "help" or command == "-h" or command == "--help":
        show_help()
        return 0
    
    else:
        print(f"✗ Unknown command: {command}")
        show_help()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)

