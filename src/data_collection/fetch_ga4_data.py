"""
Google Analytics 4 Data Fetcher

Fetches analytics data from GA4 API:
- Organic search traffic metrics
- User engagement data
- Session statistics

Metrics retrieved:
- New Users (organic)
- Engaged Sessions
- Engagement Rate
- Average Session Duration
"""

import os
import pickle
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest, FilterExpression,
    Filter, FilterExpressionList
)
from google.oauth2.credentials import Credentials

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    GA4_CREDENTIALS_FILE,
    GA4_TOKEN_FILE,
    GA4_SCOPES,
    DATA_DIR,
    REPORT_LOOKBACK_DAYS,
    CLIENT_CONFIG_FILE
)


def get_ga4_credentials():
    """
    Authenticate and return GA4 credentials.

    Uses OAuth2 flow with token caching for subsequent runs.
    """
    creds = None
    token_path = Path(GA4_TOKEN_FILE)

    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GA4_CREDENTIALS_FILE, GA4_SCOPES
            )
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return creds


def fetch_organic_metrics(property_id: str, start_date: str, end_date: str,
                          credentials) -> dict:
    """
    Fetch organic search metrics for a GA4 property.

    Args:
        property_id: GA4 property ID (e.g., '123456789')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        credentials: OAuth2 credentials

    Returns:
        dict with organic traffic metrics
    """
    client = BetaAnalyticsDataClient(credentials=credentials)

    # Filter for organic search traffic
    organic_filter = FilterExpression(
        filter=Filter(
            field_name="sessionDefaultChannelGroup",
            string_filter=Filter.StringFilter(
                value="Organic Search",
                match_type=Filter.StringFilter.MatchType.EXACT
            )
        )
    )

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        metrics=[
            Metric(name="newUsers"),
            Metric(name="engagedSessions"),
            Metric(name="engagementRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="sessions"),
            Metric(name="bounceRate"),
        ],
        dimension_filter=organic_filter
    )

    try:
        response = client.run_report(request)

        if response.rows:
            row = response.rows[0]
            return {
                'new_users': int(row.metric_values[0].value),
                'engaged_sessions': int(row.metric_values[1].value),
                'engagement_rate': float(row.metric_values[2].value),
                'avg_session_duration': float(row.metric_values[3].value),
                'sessions': int(row.metric_values[4].value),
                'bounce_rate': float(row.metric_values[5].value),
            }

        return {
            'new_users': 0, 'engaged_sessions': 0, 'engagement_rate': 0,
            'avg_session_duration': 0, 'sessions': 0, 'bounce_rate': 0
        }

    except Exception as e:
        print(f"❌ Error fetching GA4 data: {e}")
        return {
            'new_users': 0, 'engaged_sessions': 0, 'engagement_rate': 0,
            'avg_session_duration': 0, 'sessions': 0, 'bounce_rate': 0
        }


def format_duration(seconds: float) -> str:
    """Format duration in seconds to MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def format_percentage(value: float) -> str:
    """Format decimal value as percentage."""
    return f"{value * 100:.1f}%"


def calculate_date_ranges():
    """Calculate date ranges for comparisons."""
    today = datetime.today()

    # Current 30 days (ending yesterday for complete data)
    current_end = today - timedelta(days=1)
    current_start = current_end - timedelta(days=REPORT_LOOKBACK_DAYS - 1)

    # Previous 30 days
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=REPORT_LOOKBACK_DAYS - 1)

    return {
        'current': (current_start.strftime('%Y-%m-%d'), current_end.strftime('%Y-%m-%d')),
        'previous': (previous_start.strftime('%Y-%m-%d'), previous_end.strftime('%Y-%m-%d')),
    }


def load_client_config() -> pd.DataFrame:
    """Load client configuration with GA4 property IDs."""
    config_path = Path(CLIENT_CONFIG_FILE)
    if not config_path.exists():
        raise FileNotFoundError(f"Client config not found: {config_path}")

    return pd.read_excel(config_path)


def run():
    """
    Main execution function for GA4 data collection.

    Fetches organic traffic data for all configured clients.
    """
    print("=" * 60)
    print("📊 Google Analytics 4 Data Fetcher")
    print("=" * 60)

    # Load client configuration
    try:
        clients_df = load_client_config()
        print(f"📋 Loaded {len(clients_df)} clients from config")
    except Exception as e:
        return {'success': False, 'message': f"Failed to load client config: {e}"}

    # Get credentials
    credentials = get_ga4_credentials()

    # Calculate date ranges
    date_ranges = calculate_date_ranges()
    print(f"\n📅 Date Ranges:")
    print(f"   Current: {date_ranges['current'][0]} to {date_ranges['current'][1]}")
    print(f"   Previous: {date_ranges['previous'][0]} to {date_ranges['previous'][1]}")

    results = []

    for _, client in clients_df.iterrows():
        client_name = client.get('client_name', 'Unknown')
        property_id = client.get('ga4_property_id', '')

        if not property_id:
            print(f"⚠️ Skipping {client_name}: No GA4 property configured")
            continue

        print(f"\n📈 Processing: {client_name}")
        print(f"   Property ID: {property_id}")

        # Fetch metrics for current period
        current_metrics = fetch_organic_metrics(
            str(property_id),
            date_ranges['current'][0],
            date_ranges['current'][1],
            credentials
        )

        # Fetch metrics for previous period
        previous_metrics = fetch_organic_metrics(
            str(property_id),
            date_ranges['previous'][0],
            date_ranges['previous'][1],
            credentials
        )

        # Calculate changes
        def calc_change(current, previous):
            if previous == 0:
                return "N/A" if current == 0 else "+∞"
            change = ((current - previous) / previous) * 100
            return f"{change:+.1f}%"

        # Create comparison DataFrame
        comparison_df = pd.DataFrame([
            {
                'Metric': 'New Users',
                'Current Period': current_metrics['new_users'],
                'Previous Period': previous_metrics['new_users'],
                'Change': calc_change(current_metrics['new_users'], previous_metrics['new_users'])
            },
            {
                'Metric': 'Engaged Sessions',
                'Current Period': current_metrics['engaged_sessions'],
                'Previous Period': previous_metrics['engaged_sessions'],
                'Change': calc_change(current_metrics['engaged_sessions'], previous_metrics['engaged_sessions'])
            },
            {
                'Metric': 'Engagement Rate',
                'Current Period': format_percentage(current_metrics['engagement_rate']),
                'Previous Period': format_percentage(previous_metrics['engagement_rate']),
                'Change': calc_change(current_metrics['engagement_rate'], previous_metrics['engagement_rate'])
            },
            {
                'Metric': 'Avg Session Duration',
                'Current Period': format_duration(current_metrics['avg_session_duration']),
                'Previous Period': format_duration(previous_metrics['avg_session_duration']),
                'Change': calc_change(current_metrics['avg_session_duration'], previous_metrics['avg_session_duration'])
            },
            {
                'Metric': 'Bounce Rate',
                'Current Period': format_percentage(current_metrics['bounce_rate']),
                'Previous Period': format_percentage(previous_metrics['bounce_rate']),
                'Change': calc_change(current_metrics['bounce_rate'], previous_metrics['bounce_rate'])
            }
        ])

        # Save to CSV
        client_slug = client_name.lower().replace(' ', '-')
        comparison_df.to_csv(
            DATA_DIR / f'GA4-organic-{client_slug}.csv',
            index=False
        )

        print(f"   ✅ Data saved for {client_name}")
        results.append({'client': client_name, 'success': True})

    print(f"\n✅ GA4 data collection complete: {len(results)} clients processed")

    return {
        'success': True,
        'message': f'Processed {len(results)} clients',
        'clients': results
    }


if __name__ == '__main__':
    run()
