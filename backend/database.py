import sqlite3
import os
from datetime import datetime, timedelta


class Database:
    """Database connection management class"""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Create database tables if they don't exist"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tUsers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userName TEXT UNIQUE NOT NULL,
                    userPass TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create session table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tSession (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userName TEXT NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    expireTime TIMESTAMP NOT NULL,
                    loginTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    logoutFlag INTEGER DEFAULT 0,
                    lastPage TEXT,
                    FOREIGN KEY (userName) REFERENCES tUsers(userName)
                )
            ''')

            # Create companies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tCompanies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    userName TEXT NOT NULL,
                    companyName TEXT NOT NULL,
                    nationalCode TEXT UNIQUE NOT NULL,
                    registrationNumber TEXT NOT NULL,
                    registrationYear INTEGER NOT NULL,
                    registrationMonth INTEGER NOT NULL,
                    registrationDay INTEGER NOT NULL,
                    stateCode TEXT NOT NULL,
                    countyCode TEXT NOT NULL,
                    sectionCode TEXT NOT NULL,
                    cityCode TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (userName) REFERENCES tUsers(userName)
                )
            ''')

            conn.commit()
            conn.close()
            print("[OK] Database initialized successfully")
        except sqlite3.Error as e:
            print(f"[ERROR] Error initializing database: {e}")

    # اضافه کردن متدهای جدید برای مدیریت شرکت‌ها

    def company_exists(self, national_code):
        """Check if company exists by national code"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM tCompanies WHERE nationalCode = ?', (national_code,))
            result = cursor.fetchone()
            return result is not None
        except sqlite3.Error as e:
            print(f"[ERROR] Error checking company: {e}")
            return False
        finally:
            self.close_connection(conn)

    def create_company(self, username, company_data):
        """Create a new company"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tCompanies (
                    userName, companyName, nationalCode, registrationNumber,
                    registrationYear, registrationMonth, registrationDay,
                    stateCode, countyCode, sectionCode, cityCode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                username,
                company_data['companyName'],
                company_data['nationalCode'],
                company_data['registrationNumber'],
                company_data['registrationDate']['year'],
                company_data['registrationDate']['month'],
                company_data['registrationDate']['day'],
                company_data['location']['state'],
                company_data['location']['county'],
                company_data['location']['section'],
                company_data['location']['city']
            ))
            conn.commit()
            print(f"[OK] Company {company_data['companyName']} created successfully")
            return True
        except sqlite3.IntegrityError:
            print(f"[ERROR] Company with national code {company_data['nationalCode']} already exists")
            return False
        except sqlite3.Error as e:
            print(f"[ERROR] Error creating company: {e}")
            return False
        finally:
            self.close_connection(conn)

    def get_companies_by_user(self, username):
        """Get all companies for a user"""
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, companyName, nationalCode, registrationNumber,
                       registrationYear, registrationMonth, registrationDay,
                       stateCode, countyCode, sectionCode, cityCode, created_at
                FROM tCompanies WHERE userName = ?
                ORDER BY created_at DESC
            ''', (username,))
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except sqlite3.Error as e:
            print(f"[ERROR] Error getting companies: {e}")
            return []
        finally:
            self.close_connection(conn)

    def get_connection(self):
        """Establish database connection"""
        try:
            conn = sqlite3.connect('database.db')
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            print(f"[ERROR] Error connecting to database: {e}")
            return None

    def close_connection(self, conn):
        """Close database connection"""
        if conn:
            conn.close()

    def user_exists(self, username):
        """Check if user exists"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM tUsers WHERE userName = ?', (username,))
            result = cursor.fetchone()
            return result is not None
        except sqlite3.Error as e:
            print(f"[ERROR] Error checking user: {e}")
            return False
        finally:
            self.close_connection(conn)

    def get_user_by_username(self, username):
        """Get user by username"""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, userName, userPass FROM tUsers WHERE userName = ?', (username,))
            result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            print(f"[ERROR] Error getting user: {e}")
            return None
        finally:
            self.close_connection(conn)

    def create_user(self, username, hashed_password):
        """Create new user"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO tUsers (userName, userPass) VALUES (?, ?)',
                (username, hashed_password)
            )
            conn.commit()
            print(f"[OK] User {username} created successfully")
            return True
        except sqlite3.IntegrityError:
            print(f"[ERROR] User {username} already exists")
            return False
        except sqlite3.Error as e:
            print(f"[ERROR] Error creating user: {e}")
            return False
        finally:
            self.close_connection(conn)

    def update_user_password(self, username, hashed_password):
        """Update user password"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE tUsers SET userPass = ?, updated_at = CURRENT_TIMESTAMP WHERE userName = ?',
                (hashed_password, username)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[ERROR] Error updating password: {e}")
            return False
        finally:
            self.close_connection(conn)

    # ==================== Session Methods ====================

    def create_session(self, username, token, expire_minutes=15):
        """Create a new session for user"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            expire_time = datetime.now() + timedelta(minutes=expire_minutes)
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO tSession (userName, token, expireTime, loginTime, logoutFlag)
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP, 0)''',
                (username, token, expire_time.strftime('%Y-%m-%d %H:%M:%S'))
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ERROR] Error creating session: {e}")
            return False
        finally:
            self.close_connection(conn)

    def get_session_by_token(self, token):
        """Get session by token"""
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT id, userName, token, expireTime, logoutFlag, lastPage
                   FROM tSession WHERE token = ?''',
                (token,)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            print(f"[ERROR] Error getting session: {e}")
            return None
        finally:
            self.close_connection(conn)

    def update_session_expire(self, token, expire_minutes=15):
        """Update session expiration time"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            expire_time = datetime.now() + timedelta(minutes=expire_minutes)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE tSession SET expireTime = ? WHERE token = ?',
                (expire_time.strftime('%Y-%m-%d %H:%M:%S'), token)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[ERROR] Error updating session expire: {e}")
            return False
        finally:
            self.close_connection(conn)

    def update_session_last_page(self, token, last_page):
        """Update session last page"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE tSession SET lastPage = ? WHERE token = ?',
                (last_page, token)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[ERROR] Error updating session last page: {e}")
            return False
        finally:
            self.close_connection(conn)

    def logout_session(self, token):
        """Mark session as logged out"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE tSession SET logoutFlag = 1 WHERE token = ?',
                (token,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[ERROR] Error logging out session: {e}")
            return False
        finally:
            self.close_connection(conn)

    def delete_session_by_username(self, username):
        """Delete all sessions for a user"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tSession WHERE userName = ?', (username,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ERROR] Error deleting sessions: {e}")
            return False
        finally:
            self.close_connection(conn)

    def delete_session_by_token(self, token):
        """Delete session by token"""
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tSession WHERE token = ?', (token,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[ERROR] Error deleting session: {e}")
            return False
        finally:
            self.close_connection(conn)