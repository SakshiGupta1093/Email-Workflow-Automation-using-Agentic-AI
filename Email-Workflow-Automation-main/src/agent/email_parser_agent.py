from typing import List, Optional
from pydantic import BaseModel, Field
from google import generativeai as genai
import os

class EmailContent(BaseModel):
    sender: str = Field(..., description="Email sender address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")

class EmailAnalysis(BaseModel):
    title: str = Field(..., description="Concise task title")
    category: str = Field(..., description="Category of the email (e.g., inquiry, notification, etc.)")
    summary: str = Field(..., description="Brief summary of the email content")
    sender_info: str = Field(..., description="Information about the sender")
    key_points: List[str] = Field(..., description="Key points extracted from the email")
    priority: str = Field(..., description="Priority level of the email (Urgent/High/Normal/Low)")
    tags: List[str] = Field(default_factory=list, description="Tags extracted from the email content")
    recommended_actions: List[str] = Field(..., description="List of recommended actions")
    deadline: Optional[str] = Field(None, description="Task deadline if mentioned in the email")
    raw_analysis: str = Field(..., description="Raw analysis from the model")

class EmailParserAgent:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_email(self, email: EmailContent) -> EmailAnalysis:
        """
        Analyze the email content using Gemini model
        """
        prompt = f"""
        Please analyze this email and provide a structured response:
        
        From: {email.sender}
        Subject: {email.subject}
        Body: {email.body}
        
        Provide a structured analysis with the following information:
        1. Task Title (Create a concise, action-oriented title in 5-7 words)
        2. Email Category (e.g., inquiry, notification, request, etc.)
        3. Brief Summary (2-3 sentences summarizing the email)
        4. Sender Information (analyze the sender's details)
        5. Key Points (main points from the email)
        6. Priority Level (Must be one of: Urgent/High/Normal/Low)
        7. Tags (Extract 1-3 relevant tags based on email content)
        8. Deadline (If mentioned in email, extract the deadline/due date in YYYY-MM-DD format. If no deadline mentioned, write "None")
        9. Recommended Actions
        
        Format your response exactly like this:
        Title: [concise task title]
        Category: [category]
        Summary: [brief summary]
        Sender Info: [sender analysis]
        Key Points:
        - [point 1]
        - [point 2]
        Priority: [level]
        Tags:
        - [tag1]
        - [tag2]
        Deadline: [YYYY-MM-DD or None]
        Recommended Actions:
        - [action 1]
        - [action 2]
        """

        try:
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            analysis = response.text

            # Parse the response into structured format
            lines = analysis.strip().split('\n')
            title = ""
            category = ""
            summary = ""
            sender_info = ""
            key_points = []
            priority = "Normal"  # default
            tags = []  # new
            deadline = None  # default
            actions = []
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if line.startswith("Title:"):
                    title = line.replace("Title:", "").strip()
                elif line.startswith("Category:"):
                    category = line.replace("Category:", "").strip()
                elif line.startswith("Summary:"):
                    summary = line.replace("Summary:", "").strip()
                elif line.startswith("Sender Info:"):
                    sender_info = line.replace("Sender Info:", "").strip()
                elif line.startswith("Key Points:"):
                    current_section = "key_points"
                elif line.startswith("Priority:"):
                    priority = line.replace("Priority:", "").strip()
                    current_section = None
                elif line.startswith("Tags:"):
                    current_section = "tags"
                elif line.startswith("Deadline:"):
                    deadline = line.replace("Deadline:", "").strip()
                    if deadline.lower() == "none":
                        deadline = None
                    current_section = None
                elif line.startswith("Recommended Actions:"):
                    current_section = "actions"
                elif line.startswith("- ") and current_section:
                    if current_section == "key_points":
                        key_points.append(line.replace("- ", ""))
                    elif current_section == "tags":
                        tags.append(line.replace("- ", ""))
                    elif current_section == "actions":
                        actions.append(line.replace("- ", ""))

            return EmailAnalysis(
                title=title or "Review Email Content",
                category=category or "Unclassified",
                summary=summary or "No summary available",
                sender_info=sender_info or "No sender analysis available",
                key_points=key_points or ["No key points extracted"],
                priority=priority,
                tags=tags,
                deadline=deadline,
                recommended_actions=actions or ["No actions recommended"],
                raw_analysis=analysis
            )

        except Exception as e:
            print(f"Error during analysis: {str(e)}")
            return EmailAnalysis(
                title="Review Email - Analysis Failed",
                category="Error",
                summary=f"Error during analysis: {str(e)}",
                sender_info=f"Error during analysis: {str(e)}",
                key_points=["Analysis failed"],
                priority="Unknown",
                deadline=None,
                recommended_actions=["Review manually"],
                raw_analysis=str(e)
            ) 