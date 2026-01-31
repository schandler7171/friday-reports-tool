# Architecture Overview

This document describes the technical architecture of the Friday Reports Automation pipeline.

## System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        Friday Reports Pipeline                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   External   │    │   Pipeline   │    │   Output     │          │
│  │   Services   │    │   Modules    │    │   Channels   │          │
│  ├──────────────┤    ├──────────────┤    ├──────────────┤          │
│  │              │    │              │    │              │          │
│  │ GSC API ─────┼────▶ Data        │    │ HTML Reports │          │
│  │              │    │ Collection   │    │              │          │
│  │ GA4 API ─────┼────▶              │    │ Email Drafts │          │
│  │              │    │ Processing   │    │              │          │
│  │ OpenAI API ──┼────▶              │    │ Graph Images │          │
│  │              │    │ Analysis     │    │              │          │
│  │ Gmail API ───┼────▶              │    │ Status Email │          │
│  │              │    │ Reporting    │    │              │          │
│  │ SFTP Server ─┼────▶              │    │              │          │
│  │              │    │ Notifications│    │              │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘
```

## Module Structure

### Main Orchestrator (`src/main.py`)

The central pipeline controller that:
- Loads configuration from YAML
- Executes modules in sequence
- Handles errors and logging
- Generates execution reports

```python
PIPELINE_STEPS = {
    'cleanup': ['data_processing.cleanup'],
    'data_collection': [
        'data_collection.fetch_gsc_data',
        'data_collection.fetch_ga4_data',
    ],
    'data_processing': [
        'data_processing.calculate_growth_metrics',
        'data_processing.identify_top_performers',
        'data_processing.calculate_yoy_comparison',
    ],
    'analysis': ['analysis.gpt_summary_writer'],
    'report_generation': [
        'report_generation.generate_graphs',
        'report_generation.build_html_reports',
        'report_generation.upload_assets',
    ],
    'notifications': [
        'notifications.create_email_drafts',
        'notifications.send_status_email',
    ]
}
```

### Data Collection

#### `fetch_gsc_data.py`
- Authenticates with Google Search Console API
- Fetches search analytics for configured properties
- Calculates date ranges for comparisons
- Exports data to CSV files

#### `fetch_ga4_data.py`
- Authenticates with Google Analytics Data API
- Filters for organic search traffic
- Retrieves engagement metrics
- Exports comparison data

### Data Processing

#### `cleanup.py`
- Archives previous run data
- Ensures clean execution environment
- Maintains backup history

#### `calculate_growth_metrics.py`
- Processes 30-day comparison data
- Calculates percentage changes
- Determines trend direction

#### `identify_top_performers.py`
- Analyzes query-level data
- Identifies growth leaders
- Finds optimization opportunities

#### `calculate_yoy_comparison.py`
- Processes year-over-year data
- Contextualizes seasonal patterns

### Analysis

#### `gpt_summary_writer.py`
- Connects to OpenAI API
- Generates professional summaries
- Maintains character limits
- Produces both 30v30 and YoY summaries

### Report Generation

#### `generate_graphs.py`
- Creates bar charts with Matplotlib/Seaborn
- Applies consistent styling
- Exports PNG files

#### `build_html_reports.py`
- Assembles HTML from components
- Inlines CSS for email compatibility
- References hosted images

#### `upload_assets.py`
- Uploads graphs via SFTP
- Makes images publicly accessible

### Notifications

#### `create_email_drafts.py`
- Creates Gmail drafts per client
- Maps clients to recipients
- Allows review before sending

#### `send_status_email.py`
- Summarizes pipeline execution
- Reports any errors
- Confirms successful completion

## Data Flow

```
GSC API ──▶ CSV ──▶ Growth Calc ──▶ GPT Summary ──▶ HTML ──▶ Email Draft
   │                                    │                        │
   └── Query Data ──▶ Top Performers ───┘                        │
                                                                  │
GA4 API ──▶ CSV ──────────────────────────────────────▶ HTML ────┘
   │
   └── Comparison Data
```

## Authentication Flow

All Google APIs use OAuth 2.0 with the following flow:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   First     │     │   Token     │     │   API       │
│   Run       │     │   Refresh   │     │   Request   │
├─────────────┤     ├─────────────┤     ├─────────────┤
│             │     │             │     │             │
│ Check for   │     │ Check if    │     │ Use valid   │
│ saved token │────▶│ token valid │────▶│ token for   │
│             │     │             │     │ API call    │
│     ↓       │     │     ↓       │     │             │
│ If none:    │     │ If expired: │     │             │
│ Browser     │     │ Refresh     │     │             │
│ auth flow   │     │ token       │     │             │
│             │     │             │     │             │
│ Save token  │     │ Save new    │     │             │
│ to pickle   │     │ token       │     │             │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Configuration Management

### Environment Variables
Sensitive configuration stored in `.env`:
- API keys
- OAuth credentials paths
- SFTP credentials
- Email addresses

### Client Configuration
Business configuration stored in Excel/CSV:
- Client names and properties
- Email recipients

### Pipeline Configuration
Execution order stored in YAML (optional):
- Custom step ordering
- Module selection

## Error Handling

The pipeline implements defensive error handling:

1. **Module-level try/catch**: Each module handles its own errors
2. **Step continuation**: Pipeline attempts all modules in a step
3. **Logging**: All errors logged with timestamps
4. **Status reporting**: Errors included in status email
5. **Graceful degradation**: Pipeline continues despite individual failures

## Scalability Considerations

- **Multi-client**: Designed for multiple client processing
- **Modular**: Easy to add new data sources or outputs
- **Configurable**: No code changes for new clients
- **Schedulable**: Designed for cron/task scheduler execution

## Security Measures

1. **No hardcoded credentials**: All sensitive data in environment
2. **Token storage**: OAuth tokens stored locally, not in repo
3. **Gitignore**: Comprehensive exclusion of sensitive files
4. **SFTP authentication**: Secure file transfer for assets
