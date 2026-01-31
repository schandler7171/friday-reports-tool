# Friday Reports Automation 📊

An automated SEO reporting pipeline that pulls data from Google Search Console and Google Analytics 4, generates AI-powered performance summaries, creates professional HTML reports, and delivers them via email every Friday.

## 🎯 Project Overview

This pipeline was built to automate weekly SEO reporting for multiple clients, reducing manual reporting time from hours to minutes while providing consistent, insightful analysis.

### Key Features

- **Multi-Source Data Collection**: Pulls metrics from Google Search Console (GSC) and Google Analytics 4 (GA4)
- **Intelligent Comparison**: Calculates 30-day vs previous 30-day and year-over-year metrics
- **AI-Powered Analysis**: Uses GPT-4 to generate professional performance summaries
- **Visual Reports**: Creates charts and graphs for key metrics
- **Automated Delivery**: Sends HTML email reports to configured recipients
- **Status Notifications**: Alerts you when the pipeline completes

## 📁 Project Structure

```
friday-reports-automation/
├── config/
│   └── settings.py          # Configuration and environment variables
├── src/
│   ├── main.py               # Master pipeline orchestrator
│   ├── data_collection/      # GSC and GA4 data fetching
│   ├── data_processing/      # Metrics calculation and analysis
│   ├── analysis/             # GPT-powered summary generation
│   ├── report_generation/    # Charts and HTML reports
│   └── notifications/        # Email delivery system
├── docs/
│   ├── SETUP.md              # Installation guide
│   └── ARCHITECTURE.md       # Technical architecture
├── templates/                # Report templates
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
└── README.md
```

## 🚀 Pipeline Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Data Source   │     │   Processing    │     │    Delivery     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ • GSC API       │────▶│ • Calculate     │────▶│ • HTML Reports  │
│ • GA4 API       │     │   growth rates  │     │ • Email Drafts  │
│                 │     │ • Generate      │     │ • Status Email  │
│                 │     │   GPT summaries │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Pipeline Steps

1. **Cleanup**: Archives previous run artifacts
2. **Data Collection**: Fetches metrics from GSC and GA4 APIs
3. **Data Processing**: Calculates growth metrics and identifies trends
4. **Analysis**: Generates GPT-powered performance summaries
5. **Report Generation**: Creates charts and HTML reports
6. **Notifications**: Sends reports via email

## 📈 Metrics Collected

### Google Search Console
- Clicks
- Impressions
- Click-through Rate (CTR)
- Average Position

### Google Analytics 4
- New Users (organic)
- Engaged Sessions
- Engagement Rate
- Average Session Duration

## 🔧 Quick Start

### Prerequisites

- Python 3.9+
- Google Cloud Project with APIs enabled:
  - Search Console API
  - Google Analytics Data API
  - Gmail API
- OpenAI API key
- SFTP server for hosting graph images (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/friday-reports-automation.git
cd friday-reports-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Running the Pipeline

```bash
# Run full pipeline
python src/main.py

# Preview without executing (dry run)
python src/main.py --dry-run

# Run specific steps only
python src/main.py --step data_collection --step analysis
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GSC_CREDENTIALS_FILE` | Path to GSC OAuth credentials |
| `GA4_CREDENTIALS_FILE` | Path to GA4 OAuth credentials |
| `GMAIL_CREDENTIALS_FILE` | Path to Gmail OAuth credentials |
| `OPENAI_API_KEY` | OpenAI API key for GPT summaries |
| `SFTP_HOST` | SFTP server for hosting images |
| `STATUS_RECIPIENT` | Email for status notifications |

See `.env.example` for complete list.

### Client Configuration

Create `config/clients.xlsx` with columns:
- `client_name`: Display name
- `gsc_property`: GSC property URL
- `ga4_property_id`: GA4 property ID

Create `config/recipients.csv` with columns:
- `client_name`: Must match clients.xlsx
- `email`: Recipient email address

## 🔒 Security

- All credentials stored in environment variables
- OAuth tokens saved locally (not in repo)
- `.gitignore` prevents accidental credential commits
- No hardcoded sensitive data in source code

## 🛠️ Development

```bash
# Run tests
pytest

# Format code
black src/

# Lint
flake8 src/
```

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

Built with:
- [Google APIs Python Client](https://github.com/googleapis/google-api-python-client)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Pandas](https://pandas.pydata.org/)
- [Matplotlib](https://matplotlib.org/) & [Seaborn](https://seaborn.pydata.org/)
