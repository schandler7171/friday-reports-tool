"""
Email Draft Creator

Creates Gmail drafts with HTML reports attached.
Drafts allow for review before sending.

Uses Gmail API with OAuth2 authentication.
"""

import os
import base64
import pickle
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from premailer import transform

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE, GMAIL_SCOPES,
    REPORTS_DIR, EMAIL_RECIPIENTS_FILE
)


def get_gmail_service():
    """
    Authenticate and return Gmail API service.

    Uses OAuth2 flow with token caching.
    """
    creds = None
    token_path = Path(GMAIL_TOKEN_FILE)

    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_FILE, GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def create_message(to: str, subject: str, html_content: str) -> dict:
    """
    Create an email message for Gmail API.

    Args:
        to: Recipient email address
        subject: Email subject line
        html_content: HTML body content

    Returns:
        dict with 'raw' key containing base64-encoded message
    """
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['subject'] = subject

    # Inline CSS for email client compatibility
    try:
        inlined_html = transform(html_content)
    except Exception as e:
        print(f"⚠️ CSS inlining failed: {e}")
        inlined_html = html_content

    html_part = MIMEText(inlined_html, 'html', _charset='utf-8')
    message.attach(html_part)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}


def save_draft(service, message: dict) -> dict:
    """Save message as a draft in Gmail."""
    return service.users().drafts().create(
        userId='me',
        body={'message': message}
    ).execute()


def load_recipients() -> pd.DataFrame:
    """Load recipient configuration from CSV."""
    recipients_path = Path(EMAIL_RECIPIENTS_FILE)
    if recipients_path.exists():
        return pd.read_csv(recipients_path)
    return pd.DataFrame()


def run():
    """
    Main execution function.

    Creates email drafts for all generated reports.
    """
    print("=" * 60)
    print("📧 Email Draft Creator")
    print("=" * 60)

    # Check for reports
    html_files = list(REPORTS_DIR.glob('*.html'))
    print(f"📁 Found {len(html_files)} HTML reports")

    if not html_files:
        return {
            'success': True,
            'message': 'No reports to send'
        }

    # Load recipients configuration
    recipients_df = load_recipients()
    if recipients_df.empty:
        print("⚠️ No recipients configured")
        return {
            'success': False,
            'message': 'No recipients configured'
        }

    # Get Gmail service
    try:
        service = get_gmail_service()
        print("✅ Gmail API connected")
    except Exception as e:
        return {
            'success': False,
            'message': f'Gmail authentication failed: {e}'
        }

    current_week = datetime.today().isocalendar()[1]
    drafts_created = 0

    for report_file in html_files:
        # Extract client name from filename
        # Format: Weekly-Update-Client-Name-SEO-Week##.html
        filename = report_file.stem
        client_name = filename.replace('Weekly-Update-', '').replace(f'-SEO-Week{current_week}', '')
        client_name = client_name.replace('-', ' ')

        print(f"\n📝 Processing: {client_name}")

        # Find recipients for this client
        client_recipients = recipients_df[
            recipients_df['client_name'].str.lower() == client_name.lower()
        ]

        if client_recipients.empty:
            print(f"   ⚠️ No recipients found for {client_name}")
            continue

        # Read report content
        with open(report_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Create drafts for each recipient
        for _, recipient in client_recipients.iterrows():
            email = recipient['email']
            subject = f"Weekly SEO Update - {client_name} - Week {current_week}"

            try:
                msg = create_message(email, subject, html_content)
                draft = save_draft(service, msg)
                print(f"   ✅ Draft created for: {email}")
                drafts_created += 1
            except Exception as e:
                print(f"   ❌ Failed for {email}: {e}")

    print(f"\n✅ Created {drafts_created} email drafts")

    return {
        'success': True,
        'message': f'Created {drafts_created} drafts',
        'drafts_created': drafts_created
    }


if __name__ == '__main__':
    run()
