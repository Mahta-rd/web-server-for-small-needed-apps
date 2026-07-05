import bcrypt
import re
import secrets
from datetime import datetime
from backend.database import Database


class Auth:
    """Authentication and security management class"""

    PASSWORD_MIN_LENGTH = 8
    PASSWORD_PATTERN = {
        'uppercase': r'[A-Z]',
        'lowercase': r'[a-z]',
        'number': r'[0-9]',
        'special': r'[@$!%*?&]'
    }
    SESSION_EXPIRE_MINUTES = 15
    TOKEN_LENGTH = 32

    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        try:
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            print(f"[ERROR] Error hashing password: {e}")
            return None

    @staticmethod
    def verify_password(password, hashed_password):
        """Verify password"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            print(f"[ERROR] Error verifying password: {e}")
            return False

    @staticmethod
    def generate_token(length=TOKEN_LENGTH):
        """Generate a random token"""
        return secrets.token_urlsafe(length)[:length]

    @staticmethod
    def validate_username(username):
        """Validate username"""
        if not username or not username.strip():
            return False, "Username cannot be empty"

        if len(username) < 3:
            return False, "Username must be at least 3 characters"

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers and underscore"

        return True, ""

    @staticmethod
    def validate_password(password):
        """Validate password"""
        errors = []

        if not password or not password.strip():
            return False, ["Password cannot be empty"]

        if len(password) < Auth.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {Auth.PASSWORD_MIN_LENGTH} characters")

        if not re.search(Auth.PASSWORD_PATTERN['uppercase'], password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(Auth.PASSWORD_PATTERN['lowercase'], password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(Auth.PASSWORD_PATTERN['number'], password):
            errors.append("Password must contain at least one number")

        if not re.search(Auth.PASSWORD_PATTERN['special'], password):
            errors.append("Password must contain at least one special character (@$!%*?&)")

        if errors:
            return False, errors

        return True, []


    @staticmethod
    def login(username, password):
        """Login user and create session"""
        db = Database()

        # Validate username
        is_valid_username, username_error = Auth.validate_username(username)
        if not is_valid_username:
            return False, username_error, None

        # Validate password
        is_valid_password, password_errors = Auth.validate_password(password)
        if not is_valid_password:
            return False, password_errors[0] if password_errors else "Invalid password", None

        # Search user in database
        user = db.get_user_by_username(username)

        if user is None:
            # User does not exist
            return False, "نام کاربری یا رمز عبور اشتباه است", None

        # Verify password
        if not Auth.verify_password(password, user['userPass']):
            return False, "نام کاربری یا رمز عبور اشتباه است", None

        # Delete any existing sessions for this user
        db.delete_session_by_username(username)

        # Generate token and create session
        token = Auth.generate_token()
        success = db.create_session(username, token, Auth.SESSION_EXPIRE_MINUTES)

        if not success:
            return False, "Error creating session", None

        return True, "ورود موفق", token

    @staticmethod
    def change_password(username, current_password, new_password):
        """Change user password"""
        db = Database()

        # Validate new password
        is_valid_password, password_errors = Auth.validate_password(new_password)
        if not is_valid_password:
            return False, password_errors[0] if password_errors else "Invalid password"

        # Search user
        user = db.get_user_by_username(username)
        if user is None:
            return False, "User not found"

        # Verify current password
        if not Auth.verify_password(current_password, user['userPass']):
            return False, "Current password is incorrect"

        # Check that new password is not the same as current password
        if Auth.verify_password(new_password, user['userPass']):
            return False, "New password cannot be the same as current password"

        # Hash new password
        hashed_new_password = Auth.hash_password(new_password)
        if hashed_new_password is None:
            return False, "Error hashing new password"

        # Update password
        success = db.update_user_password(username, hashed_new_password)
        if success:
            # Delete all sessions for this user (force re-login)
            db.delete_session_by_username(username)
            return True, "Password changed successfully"
        else:
            return False, "Error changing password"

    @staticmethod
    def validate_session(token):
        """Validate session token and extend if valid"""
        db = Database()

        if not token:
            return False, "No token provided", None

        session = db.get_session_by_token(token)
        if not session:
            return False, "Invalid session", None

        # Check if user logged out
        if session.get('logoutFlag', 0) == 1:
            # Clean up the session
            db.delete_session_by_token(token)
            return False, "Session logged out", None

        # Check if session expired
        expire_time_str = session.get('expireTime')
        if not expire_time_str:
            return False, "Invalid session", None

        # Parse expire time
        try:
            # Handle different datetime formats
            if isinstance(expire_time_str, str):
                expire_time = datetime.strptime(expire_time_str, '%Y-%m-%d %H:%M:%S')
            else:
                expire_time = expire_time_str
        except ValueError:
            return False, "Invalid session expiration", None

        if datetime.now() > expire_time:
            # Session expired, delete it
            db.delete_session_by_token(token)
            return False, "Session expired", None

        # Session is valid, extend expiration
        db.update_session_expire(token, Auth.SESSION_EXPIRE_MINUTES)

        # Get updated session
        updated_session = db.get_session_by_token(token)
        return True, "Session valid", dict(updated_session) if updated_session else None

    @staticmethod
    def logout(token):
        """Logout user by marking session as logged out"""
        db = Database()

        if not token:
            return False, "No token provided"

        session = db.get_session_by_token(token)
        if not session:
            return False, "Invalid session"

        # Mark session as logged out
        success = db.logout_session(token)
        if success:
            return True, "Logged out successfully"
        return False, "Error logging out"

    @staticmethod
    def update_last_page(token, last_page):
        """Update last page in session"""
        db = Database()

        if not token:
            return False

        return db.update_session_last_page(token, last_page)

    # اضافه کردن این متد به کلاس Auth در auth.py

    @staticmethod
    def signup(username, password):
        """Register a new user

        Process:
        1. Validate username and password
        2. Check if username already exists
        3. Hash password and create user
        """
        db = Database()

        # Validate username
        is_valid_username, username_error = Auth.validate_username(username)
        if not is_valid_username:
            return False, username_error

        # Validate password
        is_valid_password, password_errors = Auth.validate_password(password)
        if not is_valid_password:
            return False, password_errors[0] if password_errors else "Invalid password"

        # Check if user already exists
        if db.user_exists(username):
            return False, "این نام کاربری قبلاً ثبت شده است"

        # Hash password
        hashed_password = Auth.hash_password(password)
        if hashed_password is None:
            return False, "Error hashing password"

        # Create user
        success = db.create_user(username, hashed_password)
        if success:
            return True, "ثبت نام با موفقیت انجام شد"
        else:
            return False, "خطا در ثبت نام کاربر"

        # اضافه کردن این متد به کلاس Auth در auth.py

    @staticmethod
    def validate_company_national_code(national_code):
        """Validate company national code

        Args:
            national_code: 11-digit national code string

        Returns:
            True if valid, False otherwise
        """
        # Remove non-digit characters
        cleaned = re.sub(r'\D', '', str(national_code))

        if len(cleaned) != 11:
            return False

        # Check if all digits are the same (invalid)
        if re.match(r'^(\d)\1{10}$', cleaned):
            return False

        # Company national code validation algorithm
        coefficient = [29, 27, 23, 19, 17, 29, 27, 23, 19, 247]
        total = 0
        for i in range(10):
            total += int(cleaned[i]) * coefficient[i]
        total += 460
        remain = total % 11
        control_digit = 0 if remain == 10 else remain

        return control_digit == int(cleaned[10])