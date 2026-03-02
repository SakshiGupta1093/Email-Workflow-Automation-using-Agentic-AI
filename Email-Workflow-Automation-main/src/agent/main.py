#!/usr/bin/env python
import os
from email_parser_agent import EmailParserAgent, EmailContent
from clickup_agent import ClickUpAgent
from db_operations_agent import DBOperationsAgent
from tools.email_ops import read_emails
from dotenv import load_dotenv

load_dotenv()


# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the email parser agent and create ClickUp tasks.
    """
    print("Reading emails...")
    emails = read_emails()

    if not emails:
        print("No emails found.")
        return

    latest_email = emails[0]

    # Extract email components using the new structure
    sender_email = latest_email.get('from', 'Unknown Sender')
    email_subject = latest_email.get('subject', 'No Subject')
    email_body = latest_email.get('snippet', '')

    # Create structured email content
    email = EmailContent(
        sender=sender_email,
        subject=email_subject,
        body=email_body
    )

    print("\nProcessing Email:")
    print(f"From: {email.sender}")
    print(f"Subject: {email.subject}")
    print(f"Body: {email.body}")

    # Create email parser agent and analyze email
    email_agent = EmailParserAgent()
    analysis = email_agent.analyze_email(email)

    # Print email analysis results
    print("\n=== Email Analysis Results ===")
    print(f"Category: {analysis.category}")
    print(f"Sender Information: {analysis.sender_info}")
    print("\nKey Points:")
    for point in analysis.key_points:
        print(f"- {point}")
    print(f"\nPriority: {analysis.priority}")
    print("\nRecommended Actions:")
    for action in analysis.recommended_actions:
        print(f"- {action}")

    print("\n=== Raw Analysis ===")
    print(analysis.raw_analysis)

    # Create ClickUp task from email analysis
    print("\nCreating ClickUp task...")
    clickup_agent = ClickUpAgent()
    try:
        task = clickup_agent.create_task_from_email(analysis)
        print("\n=== ClickUp Task Created ===")
        print(f"Task Name: {task.name}")
        print(f"Priority: {task.priority}")
        print(f"Status: {task.status}")
        print("\nTask Description:")
        print(task.description)

        # Store the record in the database using DBOperationsAgent
        print("\nStoring record in database...")
        db_agent = DBOperationsAgent()
        db_payload = {
            "sender_name": email.sender,
            "contact_details": email.sender,  # Using sender email as contact details
            "email_content": email.body,
            "category": analysis.category,
            "clickup_task_title": task.name,
            "clickup_task_link": "https://app.clickup.com/t/task",  # Using a placeholder link since we don't have the actual task URL
            "priority": analysis.priority,
            "tags": analysis.tags
        }
        
        result = db_agent.store_email_task(db_payload)
        if result.success:
            print(result.message)
        else:
            print(f"Error storing record: {result.message}")

    except Exception as e:
        print(f"\nError in workflow: {str(e)}")

if __name__ == "__main__":
    run()
