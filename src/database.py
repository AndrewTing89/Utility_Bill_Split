import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

from config.settings import settings


class BillDatabase:
    """Handles SQLite database operations for bill tracking"""
    
    def __init__(self):
        self.db_path = settings.DB_PATH
        self.logger = logging.getLogger(__name__)
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist"""
        settings.ensure_directories()
        
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS bills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_amount DECIMAL(10,2) NOT NULL,
                    due_date DATE NOT NULL,
                    bill_period_start DATE,
                    bill_period_end DATE,
                    roommate_portion DECIMAL(10,2) NOT NULL,
                    my_portion DECIMAL(10,2) NOT NULL,
                    email_id TEXT NOT NULL,
                    email_subject TEXT,
                    email_date TIMESTAMP,
                    pdf_path TEXT,
                    pdf_generated BOOLEAN DEFAULT FALSE,
                    pdf_sent BOOLEAN DEFAULT FALSE,
                    venmo_link TEXT,
                    venmo_sent BOOLEAN DEFAULT FALSE,
                    processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    notes TEXT,
                    UNIQUE(bill_amount, due_date)  -- Prevent duplicates by amount + due date
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processing_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bill_id) REFERENCES bills (id)
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def add_bill(self, bill_info: Dict) -> Tuple[bool, str, Optional[int]]:
        """Add a new bill or detect duplicate
        
        Args:
            bill_info: Parsed bill information from Gmail
            
        Returns:
            Tuple of (success, message, bill_id)
            - success: True if added, False if duplicate detected
            - message: Description of what happened
            - bill_id: Database ID if added, None if duplicate
        """
        try:
            # Calculate split amounts
            roommate_portion = bill_info['amount'] * settings.ROOMMATE_SPLIT_RATIO
            my_portion = bill_info['amount'] * settings.MY_SPLIT_RATIO
            
            with self._get_connection() as conn:
                # Check for duplicate first
                existing = conn.execute('''
                    SELECT id, email_id, processed_date, status 
                    FROM bills 
                    WHERE bill_amount = ? AND due_date = ?
                ''', (bill_info['amount'], bill_info['due_date'])).fetchone()
                
                if existing:
                    # Log that we found a duplicate
                    self._log_action(
                        conn, 
                        existing['id'], 
                        'duplicate_detected',
                        f"Duplicate bill detected. Original email: {existing['email_id']}, "
                        f"New email: {bill_info['email_id']}, Status: {existing['status']}"
                    )
                    
                    return False, f"Duplicate bill detected (${bill_info['amount']} due {bill_info['due_date']}). " \
                                 f"Original processed on {existing['processed_date']}", None
                
                # Add new bill
                cursor = conn.execute('''
                    INSERT INTO bills (
                        bill_amount, due_date, bill_period_start, bill_period_end,
                        roommate_portion, my_portion, email_id, email_subject, 
                        email_date, status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bill_info['amount'],
                    bill_info['due_date'],
                    bill_info.get('bill_period', [None, None])[0] if bill_info.get('bill_period') else None,
                    bill_info.get('bill_period', [None, None])[1] if bill_info.get('bill_period') else None,
                    roommate_portion,
                    my_portion,
                    bill_info['email_id'],
                    bill_info['email_subject'],
                    bill_info['email_date'],
                    'pending',
                    f"Added from email: {bill_info['email_subject']}"
                ))
                
                bill_id = cursor.lastrowid
                
                # Log the addition
                self._log_action(
                    conn,
                    bill_id,
                    'bill_added',
                    f"New bill added: ${bill_info['amount']} due {bill_info['due_date']}"
                )
                
                conn.commit()
                
                return True, f"New bill added: ${bill_info['amount']} due {bill_info['due_date']} " \
                            f"(Roommate: ${roommate_portion:.2f}, You: ${my_portion:.2f})", bill_id
                
        except sqlite3.IntegrityError as e:
            return False, f"Database integrity error: {e}", None
        except Exception as e:
            self.logger.error(f"Error adding bill: {e}")
            return False, f"Error adding bill: {e}", None
    
    def _log_action(self, conn, bill_id: int, action: str, details: str = None):
        """Log an action to the processing log"""
        conn.execute('''
            INSERT INTO processing_log (bill_id, action, details)
            VALUES (?, ?, ?)
        ''', (bill_id, action, details))
    
    def log_action(self, bill_id: int, action: str, details: str = None):
        """Public method to log an action"""
        try:
            with self._get_connection() as conn:
                self._log_action(conn, bill_id, action, details)
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error logging action: {e}")
    
    def get_bill_by_id(self, bill_id: int) -> Optional[Dict]:
        """Get a bill by its database ID"""
        with self._get_connection() as conn:
            row = conn.execute('SELECT * FROM bills WHERE id = ?', (bill_id,)).fetchone()
            return dict(row) if row else None
    
    def get_recent_bills(self, limit: int = 10) -> List[Dict]:
        """Get recent bills ordered by processed date"""
        with self._get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM bills 
                ORDER BY processed_date DESC 
                LIMIT ?
            ''', (limit,)).fetchall()
            return [dict(row) for row in rows]
    
    def get_bills_by_status(self, status: str) -> List[Dict]:
        """Get bills by status (pending, completed, etc.)"""
        with self._get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM bills 
                WHERE status = ? 
                ORDER BY due_date ASC
            ''', (status,)).fetchall()
            return [dict(row) for row in rows]
    
    def update_bill_status(self, bill_id: int, status: str, notes: str = None) -> bool:
        """Update bill status"""
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    UPDATE bills 
                    SET status = ?, notes = COALESCE(?, notes)
                    WHERE id = ?
                ''', (status, notes, bill_id))
                
                self._log_action(conn, bill_id, 'status_updated', f"Status changed to: {status}")
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error updating bill status: {e}")
            return False
    
    def mark_pdf_generated(self, bill_id: int, pdf_path: str) -> bool:
        """Mark that PDF has been generated for a bill"""
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    UPDATE bills 
                    SET pdf_generated = TRUE, pdf_path = ?
                    WHERE id = ?
                ''', (pdf_path, bill_id))
                
                self._log_action(conn, bill_id, 'pdf_generated', f"PDF saved to: {pdf_path}")
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error marking PDF generated: {e}")
            return False
    
    def mark_pdf_sent(self, bill_id: int) -> bool:
        """Mark that PDF has been sent to roommate"""
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    UPDATE bills 
                    SET pdf_sent = TRUE
                    WHERE id = ?
                ''', (bill_id,))
                
                self._log_action(conn, bill_id, 'pdf_sent', "PDF sent to roommate")
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error marking PDF sent: {e}")
            return False
    
    def mark_venmo_sent(self, bill_id: int, venmo_link: str) -> bool:
        """Mark that Venmo request has been sent"""
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    UPDATE bills 
                    SET venmo_sent = TRUE, venmo_link = ?
                    WHERE id = ?
                ''', (venmo_link, bill_id))
                
                self._log_action(conn, bill_id, 'venmo_sent', f"Venmo link generated: {venmo_link}")
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error marking Venmo sent: {e}")
            return False
    
    def get_processing_log(self, bill_id: int = None, limit: int = 50) -> List[Dict]:
        """Get processing log entries"""
        with self._get_connection() as conn:
            if bill_id:
                rows = conn.execute('''
                    SELECT * FROM processing_log 
                    WHERE bill_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (bill_id, limit)).fetchall()
            else:
                rows = conn.execute('''
                    SELECT pl.*, b.bill_amount, b.due_date 
                    FROM processing_log pl
                    LEFT JOIN bills b ON pl.bill_id = b.id
                    ORDER BY pl.timestamp DESC 
                    LIMIT ?
                ''', (limit,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self._get_connection() as conn:
            stats = {
                'total_bills': conn.execute('SELECT COUNT(*) FROM bills').fetchone()[0],
                'pending_bills': conn.execute('SELECT COUNT(*) FROM bills WHERE status = "pending"').fetchone()[0],
                'completed_bills': conn.execute('SELECT COUNT(*) FROM bills WHERE status = "completed"').fetchone()[0],
                'pdfs_generated': conn.execute('SELECT COUNT(*) FROM bills WHERE pdf_generated = TRUE').fetchone()[0],
                'pdfs_sent': conn.execute('SELECT COUNT(*) FROM bills WHERE pdf_sent = TRUE').fetchone()[0],
                'venmo_sent': conn.execute('SELECT COUNT(*) FROM bills WHERE venmo_sent = TRUE').fetchone()[0],
            }
            
            # Get total amounts
            totals = conn.execute('''
                SELECT 
                    SUM(bill_amount) as total_amount,
                    SUM(roommate_portion) as total_roommate,
                    SUM(my_portion) as total_my
                FROM bills
            ''').fetchone()
            
            if totals and totals[0]:
                stats.update({
                    'total_amount': float(totals[0]),
                    'total_roommate_portion': float(totals[1]),
                    'total_my_portion': float(totals[2])
                })
            else:
                stats.update({
                    'total_amount': 0.0,
                    'total_roommate_portion': 0.0,
                    'total_my_portion': 0.0
                })
            
            return stats