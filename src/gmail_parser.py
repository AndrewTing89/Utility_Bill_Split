import os
import json
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import settings
from config.pge_patterns import PGEPatterns


class GmailParser:
    """Handles Gmail API authentication and email parsing"""
    
    def __init__(self):
        self.service = None
        self.creds = None
        
    def authenticate(self):
        """Authenticate with Gmail API"""
        # Token file stores the user's access and refresh tokens
        if settings.TOKEN_PATH.exists():
            self.creds = Credentials.from_authorized_user_file(
                str(settings.TOKEN_PATH), 
                settings.GMAIL_SCOPES
            )
        
        # If there are no (valid) credentials available, let user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not settings.CREDENTIALS_PATH.exists():
                    raise FileNotFoundError(
                        f"Gmail credentials not found at: {settings.CREDENTIALS_PATH}"
                    )
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(settings.CREDENTIALS_PATH),
                    settings.GMAIL_SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(settings.TOKEN_PATH, 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=self.creds)
        print("✓ Gmail API authenticated successfully")
    
    def search_pge_bills(self, days_back: int = 30) -> List[Dict]:
        """Search for PG&E bills in Gmail
        
        Args:
            days_back: Number of days to search back from today
            
        Returns:
            List of email messages
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated. Call authenticate() first.")
        
        # Build search query
        after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        query = f'from:{settings.PGE_SENDER} after:{after_date}'
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            print(f"Found {len(messages)} PG&E emails from last {days_back} days")
            
            return messages
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def get_email_content(self, message_id: str) -> Dict:
        """Get full email content by message ID
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dict with email metadata and body
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()
            
            # Extract headers
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            return {
                'id': message_id,
                'subject': subject,
                'date': date,
                'body': body,
                'raw_message': message
            }
            
        except HttpError as error:
            print(f'Error fetching email {message_id}: {error}')
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract body from email payload
        
        Args:
            payload: Gmail message payload
            
        Returns:
            Email body text
        """
        body = ''
        
        # Single part message
        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        # Multipart message
        elif 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'text/html' and not body:
                    # Use HTML if no plain text found
                    data = part['body'].get('data', '')
                    if data:
                        html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                        # Convert HTML to text (basic conversion)
                        import html2text
                        h = html2text.HTML2Text()
                        h.ignore_links = True
                        body = h.handle(html_body)
        
        return body
    
    def parse_pge_bill(self, message_id: str) -> Optional[Dict]:
        """Parse a PG&E bill from email
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Parsed bill information or None if parsing fails
        """
        email = self.get_email_content(message_id)
        if not email:
            return None
        
        try:
            # Parse bill using our patterns
            bill_info = PGEPatterns.parse_bill_email(email['body'])
            
            # Add email metadata
            bill_info['email_id'] = message_id
            bill_info['email_subject'] = email['subject']
            bill_info['email_date'] = email['date']
            bill_info['email_body'] = email['body']
            
            return bill_info
            
        except ValueError as e:
            print(f"Failed to parse bill from email {message_id}: {e}")
            return None
    
    def get_latest_bill(self) -> Optional[Dict]:
        """Get and parse the latest PG&E bill
        
        Returns:
            Parsed bill information or None if no bills found
        """
        messages = self.search_pge_bills(days_back=45)  # Look back 45 days
        
        if not messages:
            print("No PG&E bills found in recent emails")
            return None
        
        # Try to parse bills starting with most recent
        for message in messages:
            bill = self.parse_pge_bill(message['id'])
            if bill:
                print(f"✓ Successfully parsed bill: ${bill['amount']} due {bill['due_date']}")
                return bill
        
        print("Failed to parse any PG&E bills")
        return None
    
    def test_connection(self) -> bool:
        """Test Gmail API connection
        
        Returns:
            True if connection successful
        """
        try:
            # Try to get user profile
            profile = self.service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress', 'Unknown')
            print(f"✓ Connected to Gmail as: {email}")
            return True
        except Exception as e:
            print(f"✗ Gmail connection failed: {e}")
            return False