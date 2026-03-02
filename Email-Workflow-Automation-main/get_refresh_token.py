from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
import json
from pathlib import Path

# If modifying these scopes, delete any existing token.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]

def get_refresh_token():
    """Gets a refresh token for Gmail API access."""
    try:
        # Create the flow using the client secrets file
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secrets.json',
            SCOPES
        )
        
        # Run the local server flow. This will open a browser window for authentication
        creds = flow.run_local_server(port=0)
        
        # Print the refresh token and other credentials
        print("\nAuthentication successful!")
        print("\nYour refresh token is:", creds.refresh_token)
        print("\nAdd this to your .env file as GMAIL_REFRESH_TOKEN")
        
        # Read and print the client configuration
        with open('client_secrets.json', 'r') as f:
            client_config = json.load(f)
            client_info = client_config['installed']
            print("\nYour client ID is:", client_info['client_id'])
            print("Your client secret is:", client_info['client_secret'])
        
        # Update the .env file automatically
        env_path = Path('.env')
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Update the refresh token
            if 'GMAIL_REFRESH_TOKEN' in env_content:
                env_lines = env_content.splitlines()
                updated_lines = []
                for line in env_lines:
                    if line.startswith('GMAIL_REFRESH_TOKEN='):
                        line = f'GMAIL_REFRESH_TOKEN="{creds.refresh_token}"'
                    updated_lines.append(line)
                env_content = '\n'.join(updated_lines)
            else:
                env_content += f'\nGMAIL_REFRESH_TOKEN="{creds.refresh_token}"'
            
            # Write the updated content back
            with open(env_path, 'w') as f:
                f.write(env_content)
            print("\nUpdated .env file with new refresh token!")
        
        return creds.refresh_token
        
    except Exception as e:
        print(f"\nError during authentication: {str(e)}")
        raise

if __name__ == '__main__':
    print("Starting Gmail API authentication process...")
    print("This will open a browser window for you to authenticate with your Google account.")
    get_refresh_token() 