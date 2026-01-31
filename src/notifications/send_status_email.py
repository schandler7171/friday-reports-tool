"""
Status Email Sender

Sends a status notification email after pipeline completion.
Includes summary of processed clients and any errors encountered.
"""

import os
import json
import base64
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE, GMAIL_SCOPES,
    STATUS_RECIPIENT, BASE_DIR
)


def get_gmail_service():
    """Authenticate and return Gmail API service."""
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


def load_latest_report() -> dict:
    """Load the most recent pipeline execution report."""
    logs_dir = BASE_DIR / 'logs'
    if not logs_dir.exists():
        return {}

    # Find most recent pipeline report
    report_files = sorted(logs_dir.glob('pipeline_report_*.json'), reverse=True)
    if not report_files:
        return {}

    with open(report_files[0], 'r') as f:
        return json.load(f)


def build_status_email(report: dict) -> tuple:
    """
    Build status email content.

    Returns:
        tuple of (subject, html_body)
    """
    current_week = datetime.today().isocalendar()[1]
    current_date = datetime.today().strftime('%B %d, %Y')

    # Determine overall status
    overall_success = report.get('success', False)
    status_emoji = "✅" if overall_success else "❌"
    status_text = "Completed Successfully" if overall_success else "Completed with Errors"

    subject = f"{status_emoji} Friday Reports Pipeline - Week {current_week}"

    # Build HTML body
    html_parts = [
        "<html><body style='font-family: Arial, sans-serif; max-width: 600px; margin: auto;'>",
        f"<h2>{status_emoji} Friday Reports Pipeline Status</h2>",
        f"<p><strong>Date:</strong> {current_date}</p>",
        f"<p><strong>Week:</strong> {current_week}</p>",
        f"<p><strong>Status:</strong> {status_text}</p>",
    ]

    # Add timing info
    if 'total_duration' in report:
        duration = report['total_duration']
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        html_parts.append(f"<p><strong>Duration:</strong> {minutes}m {seconds}s</p>")

    # Add step summary
    html_parts.append("<h3>Step Summary</h3>")
    html_parts.append("<table style='border-collapse: collapse; width: 100%;'>")
    html_parts.append("<tr style='background-color: #003366; color: white;'>")
    html_parts.append("<th style='padding: 8px; text-align: left;'>Step</th>")
    html_parts.append("<th style='padding: 8px; text-align: center;'>Status</th>")
    html_parts.append("</tr>")

    for step_name, step_data in report.get('steps', {}).items():
        step_success = step_data.get('success', False)
        icon = "✅" if step_success else "❌"
        bg_color = "#f8f9fa" if step_success else "#fff3f3"

        html_parts.append(f"<tr style='background-color: {bg_color};'>")
        html_parts.append(f"<td style='padding: 8px; border: 1px solid #ddd;'>{step_name}</td>")
        html_parts.append(f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{icon}</td>")
        html_parts.append("</tr>")

    html_parts.append("</table>")

    # Add error details if any
    errors = []
    for step_name, step_data in report.get('steps', {}).items():
        for module in step_data.get('modules', []):
            if not module.get('success', True):
                errors.append({
                    'step': step_name,
                    'module': module.get('module', 'Unknown'),
                    'error': module.get('message', 'Unknown error')
                })

    if errors:
        html_parts.append("<h3>⚠️ Errors Encountered</h3>")
        html_parts.append("<ul>")
        for error in errors:
            html_parts.append(f"<li><strong>{error['step']}/{error['module']}:</strong> {error['error']}</li>")
        html_parts.append("</ul>")

    # Footer
    html_parts.append("<hr style='margin-top: 30px;'>")
    html_parts.append("<p style='font-size: 12px; color: #666;'>")
    html_parts.append("This is an automated status email from the Friday Reports Pipeline.")
    html_parts.append("</p>")
    html_parts.append("</body></html>")

    return subject, '\n'.join(html_parts)


def send_email(service, to: str, subject: str, html_body: str) -> dict:
    """Send an email via Gmail API."""
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['subject'] = subject

    html_part = MIMEText(html_body, 'html', _charset='utf-8')
    message.attach(html_part)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    return service.users().messages().send(
        userId='me',
        body={'raw': raw_message}
    ).execute()


def run():
    """
    Main execution function.

    Sends status email notification.
    """
    print("=" * 60)
    print("📬 Status Email Sender")
    print("=" * 60)

    if not STATUS_RECIPIENT:
        print("⚠️ STATUS_RECIPIENT not configured")
        return {
            'success': False,
            'message': 'STATUS_RECIPIENT not configured'
        }

    # Load pipeline report
    report = load_latest_report()
    if not report:
        print("⚠️ No pipeline report found")
        # Create minimal report
        report = {
            'success': True,
            'steps': {},
            'message': 'No detailed report available'
        }

    # Build email
    subject, html_body = build_status_email(report)

    # Get Gmail service
    try:
        service = get_gmail_service()
        print("✅ Gmail API connected")
    except Exception as e:
        return {
            'success': False,
            'message': f'Gmail authentication failed: {e}'
        }

    # Send email
    try:
        result = send_email(service, STATUS_RECIPIENT, subject, html_body)
        print(f"✅ Status email sent to: {STATUS_RECIPIENT}")
        print(f"   Message ID: {result.get('id', 'Unknown')}")

        return {
            'success': True,
            'message': f'Status email sent to {STATUS_RECIPIENT}',
            'message_id': result.get('id')
        }

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return {
            'success': False,
            'message': str(e)
        }


if __name__ == '__main__':
    run()
