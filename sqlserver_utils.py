#!/usr/bin/env python3
"""
SQL Server utilities for database management
Useful for creating tables manually, testing connections, and troubleshooting
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_sql_connection():
    """Test SQL Server connection"""
    try:
        import pyodbc
        from config import SQL_CONNECTION_STRING
        
        print("Testing SQL Server connection...")
        print(f"Connection string: {SQL_CONNECTION_STRING[:50]}...")
        
        conn = pyodbc.connect(SQL_CONNECTION_STRING, autocommit=True)
        cursor = conn.cursor()
        
        # Get SQL Server version
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        
        # Get database name
        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✓ Connection successful")
        print(f"  Database: {db_name}")
        print(f"  Version: {version.split(',')[0]}")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def create_tables_manual():
    """Create tables manually - useful if auto-creation fails"""
    try:
        from config import SQL_CONNECTION_STRING
        import pyodbc
        
        print("Creating database tables...")
        
        conn = pyodbc.connect(SQL_CONNECTION_STRING, autocommit=True)
        cursor = conn.cursor()
        
        # TargetUsers
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='TargetUsers')
            CREATE TABLE TargetUsers (
                slack_user_id NVARCHAR(50) PRIMARY KEY,
                user_name NVARCHAR(255) NOT NULL,
                added_at DATETIME DEFAULT GETUTCDATE()
            )
        """)
        print("  ✓ TargetUsers table created")
        
        # MonthlySubmissions
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='MonthlySubmissions')
            CREATE TABLE MonthlySubmissions (
                id INT PRIMARY KEY IDENTITY(1,1),
                slack_user_id NVARCHAR(50) NOT NULL,
                submitted_value DECIMAL(5,2) NOT NULL,
                submission_date DATETIME DEFAULT GETUTCDATE(),
                month_year NVARCHAR(20) NOT NULL,
                FOREIGN KEY (slack_user_id) REFERENCES TargetUsers(slack_user_id)
            )
        """)
        print("  ✓ MonthlySubmissions table created")
        
        # SubmissionStatus
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='SubmissionStatus')
            CREATE TABLE SubmissionStatus (
                month_year NVARCHAR(20) PRIMARY KEY,
                total_required INT NOT NULL,
                total_received INT DEFAULT 0,
                submission_deadline DATETIME NOT NULL,
                created_at DATETIME DEFAULT GETUTCDATE(),
                last_updated DATETIME DEFAULT GETUTCDATE()
            )
        """)
        print("  ✓ SubmissionStatus table created")
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX idx_month_year ON MonthlySubmissions(month_year)")
        cursor.execute("CREATE INDEX idx_user_month ON MonthlySubmissions(slack_user_id, month_year)")
        print("  ✓ Indexes created")
        
        conn.close()
        print("✓ All tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False


def drop_tables():
    """Drop all application tables (CAUTION - data loss!)"""
    try:
        from config import SQL_CONNECTION_STRING
        import pyodbc
        
        print("\n⚠️  WARNING: This will DELETE all application tables and data!")
        response = input("Type 'DELETE ALL' to confirm: ").strip()
        if response != "DELETE ALL":
            print("Cancelled")
            return False
        
        conn = pyodbc.connect(SQL_CONNECTION_STRING, autocommit=True)
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS MonthlySubmissions")
        print("  ✓ Dropped MonthlySubmissions table")
        
        cursor.execute("DROP TABLE IF EXISTS SubmissionStatus")
        print("  ✓ Dropped SubmissionStatus table")
        
        cursor.execute("DROP TABLE IF EXISTS TargetUsers")
        print("  ✓ Dropped TargetUsers table")
        
        conn.close()
        print("✓ All tables dropped")
        return True
    except Exception as e:
        print(f"✗ Error dropping tables: {e}")
        return False


def list_tables():
    """List all tables in database"""
    try:
        from config import SQL_CONNECTION_STRING
        import pyodbc
        
        conn = pyodbc.connect(SQL_CONNECTION_STRING, autocommit=True)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        conn.close()
        
        if tables:
            print("Tables in database:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("No tables found")
        
        return True
    except Exception as e:
        print(f"✗ Error listing tables: {e}")
        return False


def populate_target_users():
    """Add target users to TargetUsers table"""
    try:
        from config import TARGET_USER_IDS, SQL_CONNECTION_STRING
        import pyodbc
        
        print(f"Adding {len(TARGET_USER_IDS)} target users to database...")
        
        conn = pyodbc.connect(SQL_CONNECTION_STRING, autocommit=True)
        cursor = conn.cursor()
        
        added = 0
        skipped = 0
        for user_id in TARGET_USER_IDS:
            try:
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM TargetUsers WHERE slack_user_id = ?)
                    INSERT INTO TargetUsers (slack_user_id, user_name)
                    VALUES (?, ?)
                """, (user_id, user_id))
                added += 1
            except Exception as e:
                print(f"  ✗ Error adding {user_id}: {e}")
                skipped += 1
        
        conn.close()
        
        print(f"✓ Added {added} users, skipped {skipped}")
        return True
    except Exception as e:
        print(f"✗ Error populating users: {e}")
        return False


def run_sample_query(query):
    """Run a custom SQL query"""
    try:
        from config import SQL_CONNECTION_STRING
        import pyodbc
        
        print(f"Running query: {query}\n")
        
        conn = pyodbc.connect(SQL_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if rows:
            cols = [description[0] for description in cursor.description]
            print(f"Columns: {', '.join(cols)}")
            print(f"Results ({len(rows)} rows):")
            for row in rows:
                print(f"  {row}")
        else:
            print("No results")
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Query error: {e}")
        return False


def show_help():
    """Show help menu"""
    print("""
SQL Server Database Utility

Usage: python sqlserver_utils.py [COMMAND]

Commands:
  test              Test database connection
  tables            List all tables in database
  create            Create application tables
  drop              Drop all application tables (WARNING!)
  populate          Add target users to database
  query <SQL>       Run custom SQL query
  help              Show this help

Examples:
  python sqlserver_utils.py test
  python sqlserver_utils.py tables
  python sqlserver_utils.py create
  python sqlserver_utils.py populate
  python sqlserver_utils.py query "SELECT * FROM TargetUsers"
    """)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_help()
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "test":
        return 0 if test_sql_connection() else 1
    
    elif command == "create":
        return 0 if create_tables_manual() else 1
    
    elif command == "drop":
        return 0 if drop_tables() else 1
    
    elif command == "tables":
        return 0 if list_tables() else 1
    
    elif command == "populate":
        return 0 if populate_target_users() else 1
    
    elif command == "query":
        if len(sys.argv) < 3:
            print("Usage: python sqlserver_utils.py query \"SELECT * FROM TableName\"")
            return 1
        query = " ".join(sys.argv[2:])
        return 0 if run_sample_query(query) else 1
    
    elif command == "help" or command == "-h" or command == "--help":
        show_help()
        return 0
    
    else:
        print(f"Unknown command: {command}")
        show_help()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

