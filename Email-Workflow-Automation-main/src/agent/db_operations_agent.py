from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import os
from pydantic import BaseModel, Field
from tools.db_ops_tool import EmailTaskRecord, DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DBOperationResult(BaseModel):
    """Result of a database operation"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Success or error message")
    data: Optional[Dict[str, Any]] = Field(None, description="Any returned data")

class DBOperationsAgent:
    """Agent responsible for database operations"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the database operations agent"""
        # Get database path from environment variable or use default
        if db_path is None:
            db_path = os.getenv('DATABASE_URL', 'tests/database.db')
            # Remove sqlite:/// prefix if present
            if db_path.startswith('sqlite:///'):
                db_path = db_path[10:]
        
        self.db_manager = DatabaseManager(db_path)
        logger.info(f"Database Operations Agent initialized with database: {db_path}")

    def store_email_task(self, email_data: Dict[str, Any]) -> DBOperationResult:
        """
        Store email and task information in the database
        
        Args:
            email_data (dict): Dictionary containing email and task information
            
        Returns:
            DBOperationResult: Result of the database operation
        """
        try:
            # Convert data to EmailTaskRecord for validation
            record = EmailTaskRecord(**email_data)
            
            # Insert record into database
            record_id = self.db_manager.insert_record(record)
            
            return DBOperationResult(
                success=True,
                message=f"Successfully stored email task record with ID: {record_id}",
                data={"record_id": record_id}
            )
        except Exception as e:
            error_msg = f"Failed to store email task record: {str(e)}"
            logger.error(error_msg)
            return DBOperationResult(
                success=False,
                message=error_msg,
                data=None
            )

    def get_task_history(self, limit: Optional[int] = None) -> DBOperationResult:
        """
        Retrieve task history from the database
        
        Args:
            limit (Optional[int]): Maximum number of records to retrieve
            
        Returns:
            DBOperationResult: Result of the database operation with task history
        """
        try:
            records = self.db_manager.get_all_records()
            if limit:
                records = records[:limit]
            
            return DBOperationResult(
                success=True,
                message=f"Successfully retrieved {len(records)} records",
                data={"records": records}
            )
        except Exception as e:
            error_msg = f"Failed to retrieve task history: {str(e)}"
            logger.error(error_msg)
            return DBOperationResult(
                success=False,
                message=error_msg,
                data=None
            )

    def get_task_details(self, task_id: int) -> DBOperationResult:
        """
        Retrieve details of a specific task
        
        Args:
            task_id (int): ID of the task to retrieve
            
        Returns:
            DBOperationResult: Result of the database operation with task details
        """
        try:
            record = self.db_manager.get_record_by_id(task_id)
            if record:
                return DBOperationResult(
                    success=True,
                    message=f"Successfully retrieved task details for ID: {task_id}",
                    data={"record": record}
                )
            else:
                return DBOperationResult(
                    success=False,
                    message=f"No task found with ID: {task_id}",
                    data=None
                )
        except Exception as e:
            error_msg = f"Failed to retrieve task details: {str(e)}"
            logger.error(error_msg)
            return DBOperationResult(
                success=False,
                message=error_msg,
                data=None
            ) 