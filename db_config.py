"""
MySQL Database Configuration and Operations Module
Handles all database connections and queries for member data
Falls back to SQLite if MySQL is unavailable
"""

import pymysql
from pymysql import Error
from pymysql.cursors import DictCursor
import json
import os
import sqlite3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# DATABASE CONFIGURATION (from .env file)
# ============================================================================

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'face_recognition'),
    'port': int(os.getenv('DB_PORT', 3306))
}

USE_SQLITE_FALLBACK = os.getenv('SQLITE_FALLBACK', 'True').lower() == 'true'

# ============================================================================
# DATABASE SETUP
# ============================================================================

class DatabaseManager:
    """Manages all database operations (supports both MySQL and SQLite)"""
    
    def __init__(self, config=None, use_sqlite=False):
        """Initialize database manager"""
        self.config = config or DB_CONFIG
        self.connection = None
        self.use_sqlite = use_sqlite
        self.db_file = 'face_recognition.db'
    
    def connect(self):
        """Establish connection to database (MySQL or SQLite)"""
        try:
            if self.use_sqlite:
                self.connection = sqlite3.connect(self.db_file)
                self.connection.row_factory = sqlite3.Row
                print("[OK] Connected to SQLite database")
            else:
                # Use PyMySQL for better compatibility with caching_sha2_password
                mysql_config = {
                    'host': self.config['host'],
                    'user': self.config['user'],
                    'password': self.config['password'],
                    'database': self.config.get('database', ''),
                    'port': self.config.get('port', 3306),
                    'connect_timeout': 10,
                    'autocommit': False
                }
                
                self.connection = pymysql.connect(**mysql_config)
                print("[OK] Connected to MySQL database")
            return True
        except (Error, Exception) as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            db_type = "SQLite" if self.use_sqlite else "MySQL"
            print(f"[OK] Disconnected from {db_type} database")
    
    def create_database(self):
        """Create the database if it doesn't exist (MySQL only)"""
        if self.use_sqlite:
            return True  # SQLite creates DB automatically
        
        try:
            # Connect without specifying database first
            mysql_config = {
                'host': self.config['host'],
                'user': self.config['user'],
                'password': self.config['password'],
                'port': self.config.get('port', 3306),
                'connect_timeout': 10
            }
            
            connection = pymysql.connect(**mysql_config)
            cursor = connection.cursor()
            
            db_name = self.config['database']
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            print(f"[OK] Database '{db_name}' ensured to exist")
            
            cursor.close()
            connection.close()
            return True
        except Error as e:
            print(f"[ERROR] Failed to create database: {e}")
            return False
    
    def create_members_table(self):
        """Create the members table"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = None
            try:
                if self.use_sqlite:
                    cursor = self.connection.cursor()
                    # Create table with all columns including profile_link
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        age INTEGER,
                        gender TEXT,
                        location TEXT,
                        photo TEXT,
                        profile_link TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """)
                    self.connection.commit()
                    
                    # Check if profile_link column exists, add if not
                    cursor.execute("PRAGMA table_info(members)")
                    columns = [c[1] for c in cursor.fetchall()]
                    if 'profile_link' not in columns:
                        cursor.execute("ALTER TABLE members ADD COLUMN profile_link TEXT")
                        self.connection.commit()
                else:
                    cursor = self.connection.cursor()
                    # Create table with all columns including profile_link
                    create_table_query = """
                    CREATE TABLE IF NOT EXISTS members (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL UNIQUE,
                        age INT,
                        gender VARCHAR(50),
                        location VARCHAR(255),
                        photo VARCHAR(500),
                        profile_link VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                    """
                    cursor.execute(create_table_query)
                    self.connection.commit()
                    
                    # Add profile_link column if it doesn't exist (for existing tables)
                    try:
                        cursor.execute("ALTER TABLE members ADD COLUMN profile_link VARCHAR(500)")
                        self.connection.commit()
                    except Exception:
                        pass  # Column already exists
            finally:
                if cursor:
                    cursor.close()
            
            print("[OK] Members table created/verified")
            return True
        except (Error, Exception) as e:
            print(f"[ERROR] Failed to create members table: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def insert_member(self, name, age, gender, location, photo, profile_link=None):
        """Insert a new member into the database"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            
            if self.use_sqlite:
                cursor.execute("""
                INSERT OR REPLACE INTO members (name, age, gender, location, photo, profile_link)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (name, age, gender, location, photo, profile_link))
            else:
                insert_query = """
                INSERT INTO members (name, age, gender, location, photo, profile_link)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    age = VALUES(age),
                    gender = VALUES(gender),
                    location = VALUES(location),
                    photo = VALUES(photo),
                    profile_link = VALUES(profile_link),
                    updated_at = CURRENT_TIMESTAMP
                """
                cursor.execute(insert_query, (name, age, gender, location, photo, profile_link))
            
            self.connection.commit()
            cursor.close()
            return True
        except (Error, Exception) as e:
            print(f"[ERROR] Failed to insert member {name}: {e}")
            return False
    
    def get_all_members(self):
        """Retrieve all members from the database"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            
            if self.use_sqlite:
                cursor.execute("SELECT * FROM members ORDER BY id ASC")
                rows = cursor.fetchall()
                members = [dict(row) for row in rows]
            else:
                cursor = self.connection.cursor(DictCursor)
                cursor.execute("SELECT * FROM members ORDER BY id ASC")
                members = cursor.fetchall()
            
            cursor.close()
            return members
        except (Error, Exception) as e:
            print(f"[ERROR] Failed to retrieve members: {e}")
            return []
    
    def get_member_by_name(self, name):
        """Retrieve a specific member by name"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            
            if self.use_sqlite:
                cursor.execute("SELECT * FROM members WHERE name = ?", (name,))
                row = cursor.fetchone()
                member = dict(row) if row else None
            else:
                cursor = self.connection.cursor(DictCursor)
                cursor.execute("SELECT * FROM members WHERE name = %s", (name,))
                member = cursor.fetchone()
            
            cursor.close()
            return member
        except (Error, Exception) as e:
            print(f"[ERROR] Failed to retrieve member {name}: {e}")
            return None
    
    def get_members_dict(self):
        """Get all members as a dictionary (name as key)"""
        members = self.get_all_members()
        return {member['name']: member for member in members}
    
    def delete_member(self, member_id):
        """Delete a member by ID"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            
            if self.use_sqlite:
                cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
            else:
                cursor.execute("DELETE FROM members WHERE id = %s", (member_id,))
            
            self.connection.commit()
            cursor.close()
            return True
        except (Error, Exception) as e:
            print(f"[ERROR] Failed to delete member: {e}")
            return False
    
    def update_member(self, member_id, **kwargs):
        """Update a member's information"""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            
            if self.use_sqlite:
                # Build dynamic update query for SQLite
                columns = []
                values = []
                for key, value in kwargs.items():
                    columns.append(f"{key} = ?")
                    values.append(value)
                values.append(member_id)
                
                update_query = f"UPDATE members SET {', '.join(columns)} WHERE id = ?"
                cursor.execute(update_query, values)
            else:
                # MySQL version
                columns = []
                values = []
                for key, value in kwargs.items():
                    columns.append(f"{key} = %s")
                    values.append(value)
                values.append(member_id)
                
                update_query = f"UPDATE members SET {', '.join(columns)} WHERE id = %s"
                cursor.execute(update_query, values)
            
            self.connection.commit()
            cursor.close()
            return True
        except (Error, Exception) as e:
            print(f"[ERROR] Failed to update member: {e}")
            return False

    def migrate_from_json(self, json_file='members.json'):
        """Migrate data from JSON file to database"""
        try:
            if not os.path.exists(json_file):
                print(f"[ERROR] JSON file '{json_file}' not found")
                return False
            
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            members = data.get('members', [])
            successful = 0
            
            print(f"\n[*] Migrating {len(members)} members from JSON to database...")
            
            for member in members:
                if self.insert_member(
                    name=member.get('name'),
                    age=member.get('age'),
                    gender=member.get('gender'),
                    location=member.get('location'),
                    photo=member.get('photo'),
                    profile_link=member.get('view full profile')
                ):
                    successful += 1
                    print(f"[OK] {member.get('name')}")
            
            print(f"\n[OK] Migration completed: {successful}/{len(members)} members imported\n")
            return successful == len(members)
        except (json.JSONDecodeError, Exception) as e:
            print(f"[ERROR] Migration failed: {e}")
            return False


# ============================================================================
# INITIALIZATION FUNCTION
# ============================================================================

def initialize_database():
    """Initialize database: create it, create tables, and migrate data if needed"""
    
    # Try MySQL first, fallback to SQLite
    db_manager = None
    use_sqlite = False
    
    try:
        # Try MySQL
        db_manager = DatabaseManager(use_sqlite=False)
        db_manager.create_database()
        if db_manager.connect():
            db_manager.create_members_table()
            members = db_manager.get_all_members()
            if len(members) == 0:
                print("\n[*] No members in MySQL. Migrating from JSON...\n")
                if db_manager.migrate_from_json():
                    return db_manager
            else:
                print(f"[OK] MySQL database ready with {len(members)} members")
                return db_manager
    except Exception as e:
        print(f"\n[WARN] MySQL connection failed: {e}")
    
    # Fallback to SQLite
    if USE_SQLITE_FALLBACK:
        print("\n[*] Falling back to SQLite database...")
        db_manager = DatabaseManager(use_sqlite=True)
        if db_manager.connect():
            db_manager.create_members_table()
            members = db_manager.get_all_members()
            if len(members) == 0:
                print("\n[*] Migrating from JSON to SQLite...\n")
                db_manager.migrate_from_json()
            else:
                print(f"[OK] SQLite database ready with {len(members)} members")
            return db_manager
    
    return None
