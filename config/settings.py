"""
Configuration settings for Friday Reports Automation.

All sensitive credentials are loaded from environment variables.
Copy .env.example to .env and fill in your values.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
GRAPHS_DIR = REPORTS_DIR / "graphs"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
GRAPHS_DIR.mkdir(exist_ok=True)

# Google Search Console API
GSC_CREDENTIALS_FILE = os.getenv("GSC_CREDENTIALS_FILE", "credentials/gsc_credentials.json")
GSC_TOKEN_FILE = os.getenv("GSC_TOKEN_FILE", "credentials/gsc_token.pickle")
GSC_SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

# Google Analytics 4 API
GA4_CREDENTIALS_FILE = os.getenv("GA4_CREDENTIALS_FILE", "credentials/ga4_credentials.json")
GA4_TOKEN_FILE = os.getenv("GA4_TOKEN_FILE", "credentials/ga4_token.pickle")
GA4_SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']

# Gmail API (for sending reports)
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials/gmail_credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "credentials/gmail_token.pickle")
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

# OpenAI API (for GPT-powered analysis)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# SFTP Configuration (for hosting report graphs)
SFTP_HOST = os.getenv("SFTP_HOST")
SFTP_PORT = int(os.getenv("SFTP_PORT", "22"))
SFTP_USER = os.getenv("SFTP_USER")
SFTP_PASS = os.getenv("SFTP_PASS")
SFTP_REMOTE_FOLDER = os.getenv("SFTP_REMOTE_FOLDER", "/public_html/reports/graphs")

# Image Hosting URL (where uploaded graphs can be accessed)
IMAGE_HOST_URL = os.getenv("IMAGE_HOST_URL", "https://your-domain.com/reports/graphs/")

# Email Configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
STATUS_RECIPIENT = os.getenv("STATUS_RECIPIENT")  # Email to receive status notifications

# Client Configuration
CLIENT_CONFIG_FILE = os.getenv("CLIENT_CONFIG_FILE", "config/clients.xlsx")
EMAIL_RECIPIENTS_FILE = os.getenv("EMAIL_RECIPIENTS_FILE", "config/recipients.csv")

# Report Settings
REPORT_LOOKBACK_DAYS = 30
COMPARISON_LOOKBACK_DAYS = 30
YOY_COMPARISON = True

# GPT Analysis Settings
ANALYSIS_MAX_CHARS = 480
ANALYSIS_MIN_CHARS = 400
