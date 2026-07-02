import pyodbc
import logging
from datetime import datetime
from config import SQL_CONNECTION_STRING, MIN_DECIMAL, MAX_DECIMAL

logger = logging.getLogger(__name__)


class SQLServerConnection:
    """Handles all SQL Server database operations for monthly submissions"""
    
    def __init__(self):
        self.connection_string = SQL_CONNECTION_STRING
        self._init_tables()
    
    def get_connection(self):
        """Get a new database connection"""
        try:
            conn = pyodbc.connect(self.connection_string, autocommit=True)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to SQL Server: {e}")
            raise
    
    def _init_tables(self):
        """Initialize database tables if they don't exist"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create TargetUsers table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='TargetUsers')
                CREATE TABLE TargetUsers (
                    slack_user_id NVARCHAR(50) PRIMARY KEY,
                    user_name NVARCHAR(255) NOT NULL,
                    added_at DATETIME DEFAULT GETUTCDATE()
                )
            """)
            
            # Create MonthlySubmissions table
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
            
            # Create SubmissionStatus table
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
            
            # Create ReminderLog table to track reminders sent to users
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='ReminderLog')
                CREATE TABLE ReminderLog (
                    id INT PRIMARY KEY IDENTITY(1,1),
                    slack_user_id NVARCHAR(50) NOT NULL,
                    month_year NVARCHAR(20) NOT NULL,
                    reminder_sent_at DATETIME DEFAULT GETUTCDATE(),
                    FOREIGN KEY (slack_user_id) REFERENCES TargetUsers(slack_user_id)
                )
            """)
            
            conn.close()
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {e}")
            raise
    
    def insert_submission(self, slack_user_id, submitted_value, month_year):
        """Insert a new submission into the database and refresh status"""
        try:
            if not (MIN_DECIMAL <= submitted_value <= MAX_DECIMAL):
                raise ValueError(f"Value {submitted_value} is outside valid range [{MIN_DECIMAL}, {MAX_DECIMAL}]")
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO MonthlySubmissions (slack_user_id, submitted_value, month_year)
                VALUES (?, ?, ?)
            """, (slack_user_id, submitted_value, month_year))
            
            conn.close()
            logger.info(f"Submission recorded: user={slack_user_id}, value={submitted_value}, month={month_year}")
            
            # Refresh submission status after inserting
            self.update_submission_status(month_year, None)
            
            return True
        except Exception as e:
            logger.error(f"Failed to insert submission: {e}")
            raise
    
    def get_latest_submission_for_user_month(self, slack_user_id, month_year):
        """Get the latest submission for a user in a specific month"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT TOP 1 id, submitted_value, submission_date
                FROM MonthlySubmissions
                WHERE slack_user_id = ? AND month_year = ?
                ORDER BY submission_date DESC
            """, (slack_user_id, month_year))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'value': row[1],
                    'submission_date': row[2]
                }
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve submission: {e}")
            raise
    
    def get_all_submissions_for_month(self, month_year):
        """Get all submissions for a specific month"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT slack_user_id
                FROM MonthlySubmissions
                WHERE month_year = ?
            """, (month_year,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Failed to get submissions for month: {e}")
            raise
    
    def update_submission_status(self, month_year, total_required):
        """Update submission status for a month (refresh received count)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Count received submissions
            cursor.execute("""
                SELECT COUNT(DISTINCT slack_user_id)
                FROM MonthlySubmissions
                WHERE month_year = ?
            """, (month_year,))
            
            total_received = cursor.fetchone()[0]
            
            # If total_required is None, fetch from existing record; else use provided value
            if total_required is None:
                cursor.execute("""
                    SELECT total_required FROM SubmissionStatus WHERE month_year = ?
                """, (month_year,))
                row = cursor.fetchone()
                if row:
                    total_required = row[0]
                else:
                    logger.warning(f"No SubmissionStatus found for {month_year}, cannot update total_received")
                    conn.close()
                    return False
            
            # Update or insert status
            cursor.execute("""
                IF EXISTS (SELECT 1 FROM SubmissionStatus WHERE month_year = ?)
                    UPDATE SubmissionStatus
                    SET total_received = ?, last_updated = GETUTCDATE()
                    WHERE month_year = ?
                ELSE
                    INSERT INTO SubmissionStatus (month_year, total_required, total_received, submission_deadline)
                    VALUES (?, ?, ?, DATEADD(day, 10, GETUTCDATE()))
            """, (month_year, total_received, month_year, month_year, total_required, total_received))
            
            conn.close()
            logger.info(f"Submission status updated: month={month_year}, received={total_received}/{total_required}")
            return True
        except Exception as e:
            logger.error(f"Failed to update submission status: {e}")
            raise
    
    def get_users_who_submitted(self, month_year):
        """Get list of users who have submitted for a specific month"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT slack_user_id
                FROM MonthlySubmissions
                WHERE month_year = ?
            """, (month_year,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Failed to get users who submitted: {e}")
            raise
    
    def get_pending_users(self, month_year):
        """Get list of target users who have NOT submitted for a specific month"""
        try:
            from config import TARGET_USER_IDS
            submitted = self.get_users_who_submitted(month_year)
            pending = [uid for uid in TARGET_USER_IDS if uid not in submitted]
            return pending
        except Exception as e:
            logger.error(f"Failed to get pending users: {e}")
            raise
    
    def get_submission_status(self, month_year):
        """Get submission status for a month"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT month_year, total_required, total_received, submission_deadline
                FROM SubmissionStatus
                WHERE month_year = ?
            """, (month_year,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'month_year': row[0],
                    'total_required': row[1],
                    'total_received': row[2],
                    'submission_deadline': row[3]
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get submission status: {e}")
            raise
    
    def log_reminder(self, slack_user_id, month_year):
        """Log that a reminder was sent to a user for a month"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ReminderLog (slack_user_id, month_year)
                VALUES (?, ?)
            """, (slack_user_id, month_year))
            
            conn.close()
            logger.info(f"Reminder logged for user {slack_user_id}, month {month_year}")
            return True
        except Exception as e:
            logger.error(f"Failed to log reminder: {e}")
            raise
    
    def get_last_reminder_date(self, slack_user_id, month_year):
        """Get the most recent reminder sent to a user for a month"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT TOP 1 reminder_sent_at
                FROM ReminderLog
                WHERE slack_user_id = ? AND month_year = ?
                ORDER BY reminder_sent_at DESC
            """, (slack_user_id, month_year))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return row[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get last reminder date: {e}")
            raise
    
    def get_reminder_count(self, slack_user_id, month_year):
        """Get how many reminders have been sent to a user for a month"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*)
                FROM ReminderLog
                WHERE slack_user_id = ? AND month_year = ?
            """, (slack_user_id, month_year))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
        except Exception as e:
            logger.error(f"Failed to get reminder count: {e}")
            raise


# Global database instance
db = SQLServerConnection()

