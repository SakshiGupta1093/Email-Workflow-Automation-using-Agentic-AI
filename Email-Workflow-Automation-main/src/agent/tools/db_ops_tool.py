from typing import List, Optional, Dict, Any
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, validator
from langchain.tools import Tool
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailTaskRecord(BaseModel):
    """Pydantic model for email task records"""
    sender_name: str = Field(..., description="Name of the sender")
    contact_details: str = Field(..., description="Contact details of the sender")
    email_content: str = Field(..., description="Content of the email")
    category: str = Field(..., description="Category of the email")
    clickup_task_title: str = Field(..., description="Title of the Task Created")
    clickup_task_link: str = Field(..., description="Link of the Task Created")
    priority: str = Field(..., description="Priority level of the task")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the task")
    created_at: datetime = Field(default_factory=datetime.now)

    @validator('email_content')
    def validate_email_content(cls, v):
        if not v.strip():
            raise ValueError("Email content cannot be empty")
        return v

    @validator('clickup_task_link')
    def validate_task_link(cls, v):
        if not v.startswith(('https://app.clickup.com/', 'https://app.asana.com/')):
            raise ValueError("Invalid task link format")
        return v

class DatabaseManager:
    """Manages database operations for email task records"""
    def __init__(self, db_path: str = 'database.db'):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Ensures the database and required tables exist with all necessary columns"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # First, check if the table exists
            cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='email_task_log'
            ''')
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create new table with all columns
                cursor.execute('''
                    CREATE TABLE email_task_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender_name TEXT NOT NULL,
                        contact_details TEXT NOT NULL,
                        email_content TEXT NOT NULL,
                        category TEXT NOT NULL,
                        clickup_task_title TEXT NOT NULL,
                        clickup_task_link TEXT NOT NULL,
                        priority TEXT NOT NULL,
                        tags TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                # Check for missing columns and add them if necessary
                cursor.execute('PRAGMA table_info(email_task_log)')
                existing_columns = {col[1] for col in cursor.fetchall()}
                
                # Add priority column if missing
                if 'priority' not in existing_columns:
                    cursor.execute('ALTER TABLE email_task_log ADD COLUMN priority TEXT NOT NULL DEFAULT "Normal"')
                
                # Add tags column if missing
                if 'tags' not in existing_columns:
                    cursor.execute('ALTER TABLE email_task_log ADD COLUMN tags TEXT NOT NULL DEFAULT "[]"')
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            raise
        finally:
            conn.close()

    def insert_record(self, record: EmailTaskRecord) -> int:
        """Inserts a new record into the database"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO email_task_log (
                    sender_name, contact_details, email_content, category,
                    clickup_task_title, clickup_task_link, priority, tags, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.sender_name,
                record.contact_details,
                record.email_content,
                record.category,
                record.clickup_task_title,
                record.clickup_task_link,
                record.priority,
                json.dumps(record.tags),  # Store tags as JSON string
                record.created_at.isoformat()
            ))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error inserting record: {e}")
            raise
        finally:
            conn.close()

    def get_all_records(self) -> List[Dict[str, Any]]:
        """Retrieves all records from the database"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, sender_name, contact_details, email_content, category,
                       clickup_task_title, clickup_task_link, priority, tags, created_at
                FROM email_task_log
                ORDER BY created_at DESC
            ''')
            columns = [description[0] for description in cursor.description]
            records = []
            for row in cursor.fetchall():
                record = dict(zip(columns, row))
                # Parse tags from JSON string
                record['tags'] = json.loads(record['tags'])
                records.append(record)
            return records
        except Exception as e:
            logger.error(f"Error retrieving records: {e}")
            raise
        finally:
            conn.close()

    def get_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a specific record by ID"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, sender_name, contact_details, email_content, category,
                       clickup_task_title, clickup_task_link, priority, tags, created_at
                FROM email_task_log
                WHERE id = ?
            ''', (record_id,))
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                record = dict(zip(columns, row))
                # Parse tags from JSON string
                record['tags'] = json.loads(record['tags'])
                return record
            return None
        except Exception as e:
            logger.error(f"Error retrieving record {record_id}: {e}")
            raise
        finally:
            conn.close()

def db_ops_function(payload: dict) -> str:
    """
    Function to handle database operations for email tasks.
    
    Args:
        payload (dict): Dictionary containing email and task information
        
    Returns:
        str: Success message or error description
    """
    try:
        # Convert payload to Pydantic model for validation
        record = EmailTaskRecord(**payload)
        
        # Initialize database manager and insert record
        db_manager = DatabaseManager('tests/database.db')  # Using the correct path from DATABASE_URL
        record_id = db_manager.insert_record(record)
        
        return f"Successfully inserted record with ID: {record_id}"
    except Exception as e:
        error_msg = f"Failed to insert record: {str(e)}"
        logger.error(error_msg)
        return error_msg

# Create the Tool instance for use with LangChain
db_ops_tool = Tool(
    name="DB Operations Tool",
    func=db_ops_function,
    description="""Inserts email and task data into a SQLite database. 
    Required fields: sender_name, contact_details, email_content, category, clickup_task_title, clickup_task_link"""
)


def read_all_records():
    """Read all records from the database"""
    try:
        db_manager = DatabaseManager('tests/database.db')
        records = db_manager.get_all_records()
        return records
    except Exception as e:
        logger.error(f"Error reading records: {e}")
        return []
