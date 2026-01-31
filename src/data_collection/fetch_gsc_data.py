"""
Google Search Console Data Fetcher

Fetches search performance data from GSC API:
- 30-day period vs previous 30 days
- Year-over-year comparisons
- Per-URL and per-query metrics

Metrics retrieved:
- Clicks
- Impressions
- CTR (Click-through rate)
- Average Position
"""

import os
import pickle
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    GSC_CREDENTIALS_FILE,
    GSC_TOKEN_FILE,
    GSC_SCOPES,
    DATA_DIR,
    REPORT_LOOKBACK_DAYS,
    CLIENT_CONFIG_FILE
)


def get_gsc_service():
    """
    Authenticate and return GSC API service.

    Uses OAuth2 flow with token caching for subsequent runs.
    """
    creds = None
    token_path = Path(GSC_TOKEN_FILE)

    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GSC_CREDENTIALS_FILE, GSC_SCOPES
            )
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('searchconsole', 'v1', credentials=creds)


def fetch_search_analytics(service, site_url: str, start_date: str, end_date: str,
                           dimensions: list = None, row_limit: int = 25000) -> pd.DataFrame:
    """
    Fetch search analytics data for a specific site and date range.

    Args:
        service: GSC API service object
        site_url: The site URL (e.g., 'https://example.com/')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        dimensions: List of dimensions ['date', 'query', 'page', 'country', 'device']
        row_limit: Maximum rows to retrieve

    Returns:
        DataFrame with search analytics data
    """
    if dimensions is None:
        dimensions = ['query', 'page']

    request_body = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': dimensions,
        'rowLimit': row_limit,
        'dataState': 'final'
    }

    try:
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_body
        ).execute()

        if 'rows' not in response:
            print(f"⚠️ No data returned for {site_url}")
            return pd.DataFrame()

        rows = response['rows']
        data = []

        for row in rows:
            row_data = {}
            for i, dim in enumerate(dimensions):
                row_data[dim] = row['keys'][i]
            row_data['clicks'] = row.get('clicks', 0)
            row_data['impressions'] = row.get('impressions', 0)
            row_data['ctr'] = row.get('ctr', 0)
            row_data['position'] = row.get('position', 0)
            data.append(row_data)

        return pd.DataFrame(data)

    except Exception as e:
        print(f"❌ Error fetching GSC data for {site_url}: {e}")
        return pd.DataFrame()


def fetch_aggregate_metrics(service, site_url: str, start_date: str, end_date: str) -> dict:
    """
    Fetch aggregate metrics (totals) for a site and date range.

    Returns:
        dict with total clicks, impressions, avg CTR, avg position
    """
    request_body = {
        'startDate': start_date,
        'endDate': end_date,
        'dataState': 'final'
    }

    try:
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_body
        ).execute()

        if 'rows' in response and len(response['rows']) > 0:
            row = response['rows'][0]
            return {
                'clicks': row.get('clicks', 0),
                'impressions': row.get('impressions', 0),
                'ctr': row.get('ctr', 0),
                'position': row.get('position', 0)
            }

        return {'clicks': 0, 'impressions': 0, 'ctr': 0, 'position': 0}

    except Exception as e:
        print(f"❌ Error fetching aggregate metrics: {e}")
        return {'clicks': 0, 'impressions': 0, 'ctr': 0, 'position': 0}


def calculate_date_ranges():
    """Calculate date ranges for 30-day and YoY comparisons."""
    today = datetime.today()

    # Current 30 days (ending yesterday for complete data)
    current_end = today - timedelta(days=1)
    current_start = current_end - timedelta(days=REPORT_LOOKBACK_DAYS - 1)

    # Previous 30 days
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=REPORT_LOOKBACK_DAYS - 1)

    # Year-over-year (same period last year)
    yoy_end = current_end.replace(year=current_end.year - 1)
    yoy_start = current_start.replace(year=current_start.year - 1)

    return {
        'current': (current_start.strftime('%Y-%m-%d'), current_end.strftime('%Y-%m-%d')),
        'previous': (previous_start.strftime('%Y-%m-%d'), previous_end.strftime('%Y-%m-%d')),
        'yoy': (yoy_start.strftime('%Y-%m-%d'), yoy_end.strftime('%Y-%m-%d'))
    }


def load_client_config() -> pd.DataFrame:
    """Load client configuration with site URLs."""
    config_path = Path(CLIENT_CONFIG_FILE)
    if not config_path.exists():
        raise FileNotFoundError(f"Client config not found: {config_path}")

    return pd.read_excel(config_path)


def run():
    """
    Main execution function for GSC data collection.

    Fetches data for all configured clients and saves to CSV files.
    """
    print("=" * 60)
    print("🔍 Google Search Console Data Fetcher")
    print("=" * 60)

    # Load client configuration
    try:
        clients_df = load_client_config()
        print(f"📋 Loaded {len(clients_df)} clients from config")
    except Exception as e:
        return {'success': False, 'message': f"Failed to load client config: {e}"}

    # Get API service
    service = get_gsc_service()

    # Calculate date ranges
    date_ranges = calculate_date_ranges()
    print(f"\n📅 Date Ranges:")
    print(f"   Current: {date_ranges['current'][0]} to {date_ranges['current'][1]}")
    print(f"   Previous: {date_ranges['previous'][0]} to {date_ranges['previous'][1]}")
    print(f"   YoY: {date_ranges['yoy'][0]} to {date_ranges['yoy'][1]}")

    results = []

    for _, client in clients_df.iterrows():
        client_name = client.get('client_name', 'Unknown')
        site_url = client.get('gsc_property', '')

        if not site_url:
            print(f"⚠️ Skipping {client_name}: No GSC property configured")
            continue

        print(f"\n🌐 Processing: {client_name}")
        print(f"   Site: {site_url}")

        # Fetch aggregate metrics for each period
        current_metrics = fetch_aggregate_metrics(
            service, site_url,
            date_ranges['current'][0], date_ranges['current'][1]
        )
        previous_metrics = fetch_aggregate_metrics(
            service, site_url,
            date_ranges['previous'][0], date_ranges['previous'][1]
        )
        yoy_metrics = fetch_aggregate_metrics(
            service, site_url,
            date_ranges['yoy'][0], date_ranges['yoy'][1]
        )

        # Create comparison DataFrames
        comparison_30v30 = pd.DataFrame([
            {'Metric': 'Clicks', 'Current 30 Days': current_metrics['clicks'],
             'Previous 30 Days': previous_metrics['clicks']},
            {'Metric': 'Impressions', 'Current 30 Days': current_metrics['impressions'],
             'Previous 30 Days': previous_metrics['impressions']},
            {'Metric': 'CTR', 'Current 30 Days': f"{current_metrics['ctr']*100:.2f}%",
             'Previous 30 Days': f"{previous_metrics['ctr']*100:.2f}%"},
            {'Metric': 'Position', 'Current 30 Days': f"{current_metrics['position']:.1f}",
             'Previous 30 Days': f"{previous_metrics['position']:.1f}"}
        ])

        comparison_yoy = pd.DataFrame([
            {'Metric': 'Clicks', 'Current Year (30d)': current_metrics['clicks'],
             'Previous Year (30d)': yoy_metrics['clicks']},
            {'Metric': 'Impressions', 'Current Year (30d)': current_metrics['impressions'],
             'Previous Year (30d)': yoy_metrics['impressions']},
            {'Metric': 'CTR', 'Current Year (30d)': f"{current_metrics['ctr']*100:.2f}%",
             'Previous Year (30d)': f"{yoy_metrics['ctr']*100:.2f}%"},
            {'Metric': 'Position', 'Current Year (30d)': f"{current_metrics['position']:.1f}",
             'Previous Year (30d)': f"{yoy_metrics['position']:.1f}"}
        ])

        # Save comparison files
        client_slug = client_name.lower().replace(' ', '-')
        comparison_30v30.to_csv(
            DATA_DIR / f'GSC-30vs30-overMonth-{client_slug}.csv',
            index=False
        )
        comparison_yoy.to_csv(
            DATA_DIR / f'GSC-YOY-overMonth-{client_slug}.csv',
            index=False
        )

        # Fetch detailed query data for top performers analysis
        query_data = fetch_search_analytics(
            service, site_url,
            date_ranges['current'][0], date_ranges['current'][1],
            dimensions=['query']
        )
        if not query_data.empty:
            query_data.to_csv(DATA_DIR / f'GSC-queries-{client_slug}.csv', index=False)

        print(f"   ✅ Data saved for {client_name}")
        results.append({'client': client_name, 'success': True})

    print(f"\n✅ GSC data collection complete: {len(results)} clients processed")

    return {
        'success': True,
        'message': f'Processed {len(results)} clients',
        'clients': results
    }


if __name__ == '__main__':
    run()
