from .database import create_connection
from Enum.usre_role import user_role
import sqlite3
from datetime import datetime
import bcrypt
import logging
import re
from typing import Optional, List, Dict, Any
from sqlite3 import Connection, Cursor, IntegrityError
from contextlib import closing

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Email regex pattern
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
# Password regex pattern (at least 8 characters, one uppercase, one lowercase, one digit, one special character)
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
# Bcrypt salt rounds
SALT_ROUNDS = 12

class UserManagement:
    def __init__(self):
        self.conn = create_connection()
        self.create_tables()
    
    
    def create_tables(self):
        # This function ensures that the necessary tables exist
        from .database import create_tables
        create_tables()

    # Validate email format
    def validate_email(self, email: str) -> bool:
        return re.match(EMAIL_REGEX, email) is not None

    # Validate password complexity
    def validate_password(self, password: str) -> bool:
        return re.match(PASSWORD_REGEX, password) is not None

    # Hash password using bcrypt
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt(SALT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    # Check password against hashed value
    def check_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    # Register a new user
    def register_user(self, name: str, role: str, email: str, password: str) -> Optional[int]:
        if role not in [user_role.ADMIN, user_role.CUSTOMER]:
            logger.error("Invalid role provided.")
            return None
        if not self.validate_email(email):
            logger.error("Invalid email format.")
            return None
        if not self.validate_password(password):
            logger.error("Password does not meet complexity requirements.")
            return None
        
        hashed_password = self.hash_password(password)
        created_at = datetime.now().isoformat()

        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('''
                    INSERT INTO users (name, role, email, password, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, role, email, hashed_password, created_at))
                self.conn.commit()
                logger.info(f"User {email} registered successfully.")
                return cursor.lastrowid
        except IntegrityError as e:
            logger.error(f"Integrity error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None

    # Authenticate user
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('SELECT user_id, name, role, email, password FROM users WHERE email = ?', (email,))
                user = cursor.fetchone()
                if user and self.check_password(password, user[4]):
                    last_login = datetime.now().isoformat()
                    cursor.execute('UPDATE users SET last_login = ? WHERE user_id = ?', (last_login, user[0]))
                    self.conn.commit()
                    logger.info(f"User {email} authenticated successfully.")
                    return {
                        'user_id': user[0],
                        'name': user[1],
                        'role': user[2],
                        'email': user[3],
                        'last_login': last_login
                    }
                else:
                    logger.warning("Authentication failed for user: {}".format(email))
                    return None
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return None

    # Get user details by user_id   
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('SELECT user_id, name, role, email, created_at, last_login FROM users WHERE user_id = ?', (user_id,))
                user = cursor.fetchone()
                if user:
                    return {
                        'user_id': user[0],
                        'name': user[1],
                        'role': user[2],
                        'email': user[3],
                        'created_at': user[4],
                        'last_login': user[5]
                    }
                else:
                    logger.warning(f"User with ID {user_id} not found.")
                    return None
        except Exception as e:
            logger.error(f"Error retrieving user by ID: {e}")
            return None
    
    # Get all users
    def get_all_users(self) -> List[Dict[str, Any]]:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('SELECT user_id, name, role, email, created_at, last_login FROM users')
                users = cursor.fetchall()
                return [
                    {
                        'user_id': user[0],
                        'name': user[1],
                        'role': user[2],
                        'email': user[3],
                        'created_at': user[4],
                        'last_login': user[5]
                    } for user in users
                ]
        except Exception as e:
            logger.error(f"Error retrieving all users: {e}")
            return []
    
    # Update user details
    def update_user(self, user_id: int, name: Optional[str] = None, role: Optional[str] = None, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        updates = []
        params = []
        
        if name:
            updates.append("name = ?")
            params.append(name)
        if role:
            if role not in [user_role.ADMIN, user_role.CUSTOMER]:
                logger.error("Invalid role provided.")
                return False
            updates.append("role = ?")
            params.append(role)
        if email:
            if not self.validate_email(email):
                logger.error("Invalid email format.")
                return False
            updates.append("email = ?")
            params.append(email)
        if password:
            if not self.validate_password(password):
                logger.error("Password does not meet complexity requirements.")
                return False
            hashed_password = self.hash_password(password)
            updates.append("password = ?")
            params.append(hashed_password)
        
        if not updates:
            logger.warning("No updates provided.")
            return False
        
        params.append(user_id)
        sql = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
        
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute(sql, params)
                self.conn.commit()
                if cursor.rowcount == 0:
                    logger.warning(f"No user found with ID {user_id} to update.")
                    return False
                logger.info(f"User with ID {user_id} updated successfully.")
                return True
        except IntegrityError as e:
            logger.error(f"Integrity error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False
    
    # Delete user by user_id
    def delete_user(self, user_id: int) -> bool:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
                self.conn.commit()
                if cursor.rowcount == 0:
                    logger.warning(f"No user found with ID {user_id} to delete.")
                    return False
                logger.info(f"User with ID {user_id} deleted successfully.")
                return True
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
        
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")
    
    def __del__(self):
        self.close()
# End of UserManagement class