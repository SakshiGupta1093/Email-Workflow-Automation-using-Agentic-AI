from typing import List, Optional
from pydantic import BaseModel, Field
import os
import requests
from email_parser_agent import EmailAnalysis

class ClickUpTask(BaseModel):
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Task description")
    priority: int = Field(..., description="Task priority (1-4)")
    status: str = Field(..., description="Task status")
    due_date: Optional[str] = Field(None, description="Task due date")
    tags: List[str] = Field(default_factory=list, description="Task tags")

class ClickUpAgent:
    def __init__(self):
        self.api_key = os.getenv("CLICKUP_API_KEY")
        self.list_id = os.getenv("CLICKUP_LIST_ID")
        self.headers = {
            "Authorization": self.api_key,  # Personal API tokens don't use Bearer prefix
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.clickup.com/api/v2"

    def _convert_priority(self, email_priority: str) -> int:
        """Convert email priority to ClickUp priority level"""
        priority_map = {
            "Urgent": 1,  # ClickUp: 1 is urgent
            "High": 2,    # 2 is high
            "Normal": 3,  # 3 is normal
            "Low": 4      # 4 is low
        }
        return priority_map.get(email_priority, 3)  # Default to Normal priority

    def create_task_from_email(self, email_analysis: EmailAnalysis) -> ClickUpTask:
        """Create a ClickUp task based on email analysis"""
        # Use the generated title directly
        task_name = email_analysis.title
        
        # Create a well-structured description
        description = f"""
📧 Email Summary
{email_analysis.summary}

📋 Details
• Category: {email_analysis.category}
• Priority: {email_analysis.priority}
• From: {email_analysis.sender_info}
• Due Date: {email_analysis.deadline or "Not specified"}

🏷️ Tags
{chr(10).join(f'• {tag}' for tag in email_analysis.tags)}

🔑 Key Points
{chr(10).join(f'• {point}' for point in email_analysis.key_points)}

📝 Action Items
{chr(10).join(f'• {action}' for action in email_analysis.recommended_actions)}"""
        
        # Convert priority
        priority = self._convert_priority(email_analysis.priority)
        
        # Create task in ClickUp
        try:
            url = f"{self.base_url}/list/{self.list_id}/task"
            payload = {
                "name": task_name,
                "description": description,
                "priority": priority,
                "status": "to do",
                "tags": email_analysis.tags
            }

            # Add due date if present
            if email_analysis.deadline:
                # ClickUp expects Unix timestamp in milliseconds
                from datetime import datetime
                try:
                    due_date = int(datetime.strptime(email_analysis.deadline, "%Y-%m-%d").timestamp() * 1000)
                    payload["due_date"] = due_date
                except ValueError as e:
                    print(f"Warning: Could not parse deadline date: {email_analysis.deadline}")
            
            print(f"Making request to ClickUp API:")
            print(f"URL: {url}")
            print(f"Headers: Authorization: {self.api_key[:10]}... (truncated)")
            print(f"Payload: {payload}")
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                print(f"Error Response: {response.text}")
                if response.status_code == 401:
                    print("\nAuthorization Error:")
                    print("1. Verify your API token is correct")
                    print("2. Make sure you have access to the list ID")
                    print("3. Check if you need to create a Custom App in ClickUp")
                elif response.status_code == 400:
                    print("\nBad Request Error:")
                    print("1. Verify your list ID is correct")
                    print("2. Check if all required fields are present")
                    print(f"Response details: {response.text}")
            
            response.raise_for_status()
            
            return ClickUpTask(
                name=task_name,
                description=description,
                priority=priority,
                status="to do",
                due_date=email_analysis.deadline,
                tags=email_analysis.tags
            )
            
        except Exception as e:
            print(f"Error creating ClickUp task: {str(e)}")
            raise 