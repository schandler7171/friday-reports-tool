# Setup Guide

This guide walks you through setting up the Friday Reports Automation pipeline.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Access to Google Cloud Console
- OpenAI API account

## Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/friday-reports-automation.git
cd friday-reports-automation

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Google Cloud Setup

### Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Note your Project ID

### Enable Required APIs

Navigate to **APIs & Services > Library** and enable:
- Google Search Console API
- Google Analytics Data API
- Gmail API

### Create OAuth Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Select **Desktop app** as application type
4. Download the JSON file
5. Rename and save to your credentials folder:
   - `credentials/gsc_credentials.json`
   - `credentials/ga4_credentials.json`
   - `credentials/gmail_credentials.json`

> **Note**: You can use the same OAuth credentials for all three services if the project has all APIs enabled.

### Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** or **Internal** (Internal requires Google Workspace)
3. Fill in the required fields
4. Add scopes:
   - `https://www.googleapis.com/auth/webmasters.readonly`
   - `https://www.googleapis.com/auth/analytics.readonly`
   - `https://www.googleapis.com/auth/gmail.compose`

## Step 3: OpenAI Setup

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Navigate to **API Keys**
3. Create a new API key
4. Copy the key (you won't see it again)

## Step 4: Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your values
nano .env  # or use your preferred editor
```

### Required Environment Variables

```env
# Google API credentials
GSC_CREDENTIALS_FILE=credentials/gsc_credentials.json
GA4_CREDENTIALS_FILE=credentials/ga4_credentials.json
GMAIL_CREDENTIALS_FILE=credentials/gmail_credentials.json

# OpenAI
OPENAI_API_KEY=sk-your-api-key-here

# Status notifications
STATUS_RECIPIENT=your-email@example.com
```

## Step 5: Client Configuration

### Create clients.xlsx

Create `config/clients.xlsx` with the following columns:

| client_name | gsc_property | ga4_property_id |
|-------------|--------------|-----------------|
| Acme Corp | https://www.acme.com/ | 123456789 |
| Beta Inc | https://www.betainc.com/ | 987654321 |

### Create recipients.csv

Create `config/recipients.csv`:

```csv
client_name,email
Acme Corp,john@acme.com
Acme Corp,jane@acme.com
Beta Inc,marketing@betainc.com
```

## Step 6: First Run Authentication

On first run, you'll need to authenticate with Google:

```bash
python src/main.py --step data_collection
```

A browser window will open for each Google service. Log in with the Google account that has access to GSC/GA4 properties. The tokens will be saved locally for future runs.

## Step 7: SFTP Setup (Optional)

If you want to host graph images externally (recommended for email delivery):

1. Set up an SFTP server or use existing hosting
2. Create a directory for graph images
3. Configure in `.env`:

```env
SFTP_HOST=your-server.com
SFTP_PORT=22
SFTP_USER=your-username
SFTP_PASS=your-password
SFTP_REMOTE_FOLDER=/public_html/reports/graphs
IMAGE_HOST_URL=https://your-domain.com/reports/graphs/
```

## Step 8: Test the Pipeline

```bash
# Dry run to see what would execute
python src/main.py --dry-run

# Run data collection only
python src/main.py --step data_collection

# Full pipeline run
python src/main.py
```

## Scheduling (Cron/Task Scheduler)

### Linux/Mac (Cron)

```bash
# Edit crontab
crontab -e

# Run every Friday at 8 AM
0 8 * * 5 cd /path/to/friday-reports-automation && /path/to/venv/bin/python src/main.py >> logs/cron.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to Weekly, Friday at 8:00 AM
4. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `src\main.py`
   - Start in: `C:\path\to\friday-reports-automation`

## Troubleshooting

### "Credentials not found"
Ensure the credential files exist in the `credentials/` directory.

### "Token expired"
Delete the `.pickle` token files and re-authenticate.

### "API quota exceeded"
Check Google Cloud Console for quota limits. Default limits are usually sufficient for weekly runs.

### "SFTP connection failed"
Verify SFTP credentials and that the remote folder exists.

## Security Best Practices

1. Never commit `.env` or credential files
2. Use strong, unique SFTP passwords
3. Regularly rotate API keys
4. Keep the OAuth consent screen in "Testing" mode unless needed
5. Add authorized users only
