import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import json
from pathlib import Path

# Scopes required for Gmail API
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]

def authenticate_gmail():
    """Authenticate with Gmail API using OAuth 2.0."""
    creds = None
    token_path = Path('token.json')

    # Load existing token if available
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception:
            if token_path.exists():
                token_path.unlink()  # Delete invalid token file

    # If no valid credentials available, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # If refresh fails, force re-authentication
                creds = None
                if token_path.exists():
                    token_path.unlink()

        if not creds:
            # Load client configuration from environment variables
            client_config = {
                "installed": {
                    "client_id": os.getenv("GMAIL_CLIENT_ID"),
                    "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": os.getenv("GMAIL_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                    "redirect_uris": ["http://localhost"]
                }
            }

            # Create flow instance
            flow = InstalledAppFlow.from_client_config(
                client_config,
                SCOPES,
                redirect_uri="http://localhost"
            )

            # Run the OAuth flow
            creds = flow.run_local_server(port=0)

            # Save the credentials for future use
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

    return creds

def read_emails():
    """Read unread emails from Gmail."""
    try:
        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)

        # Get the list of unread messages
        results = service.users().messages().list(userId='me', maxResults=5, q="is:unread").execute()
        messages = results.get('messages', [])

        if not messages:
            print("No unread messages found.")
            return []

        emails = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
            # Extract email details
            headers = msg['payload']['headers']
            email_data = {
                'id': msg['id'],
                'threadId': msg['threadId'],
                'snippet': msg['snippet']
            }
            
            # Extract specific headers
            for header in headers:
                if header['name'].lower() in ['from', 'to', 'subject', 'date']:
                    email_data[header['name'].lower()] = header['value']
            
            emails.append(email_data)
            
        return emails

    except HttpError as error:
        print(f'An error occurred: {error}')
        return []
    except Exception as e:
        print(f'An unexpected error occurred: {str(e)}')
        return []


# def send_email(to, subject, message_text):
#     try:
#         creds = authenticate_gmail()
#         service = build('gmail', 'v1', credentials=creds)

#         # Create a MIMEText email
#         message = MIMEMultipart()
#         message['to'] = to
#         message['subject'] = subject
#         message.attach(MIMEText(message_text, 'plain'))

#         # Encode the message
#         raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
#         body = {'raw': raw_message}

#         # Send the email
#         message = service.users().messages().send(userId='me', body=body).execute()
#         print(f"Message sent with ID: {message['id']}")

#     except HttpError as error:
#         print(f'An error occurred: {error}')

