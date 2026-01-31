"""
Top Performers Identifier

Analyzes keyword/query data to identify:
- Top 5 keywords by impression growth
- Top 5 keywords by impression decline
- Emerging opportunities
- At-risk keywords
"""

import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import DATA_DIR


def identify_growth_leaders(df: pd.DataFrame, metric: str = 'impressions',
                            top_n: int = 5, direction: str = 'growth') -> pd.DataFrame:
    """
    Identify top performing or declining keywords.

    Args:
        df: DataFrame with keyword data (must have 'current' and 'previous' columns)
        metric: Metric to analyze ('impressions', 'clicks')
        top_n: Number of results to return
        direction: 'growth' for top gainers, 'drop' for top losers

    Returns:
        DataFrame with top performers
    """
    # Calculate change
    df = df.copy()
    df['change'] = df[f'{metric}_current'] - df[f'{metric}_previous']
    df['change_pct'] = (df['change'] / df[f'{metric}_previous'].replace(0, 1)) * 100

    # Sort based on direction
    if direction == 'growth':
        df_sorted = df.nlargest(top_n, 'change')
    else:
        df_sorted = df.nsmallest(top_n, 'change')

    return df_sorted[['query', f'{metric}_current', f'{metric}_previous', 'change', 'change_pct']]


def analyze_position_opportunities(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Identify keywords close to page 1 (positions 11-20) with high impressions.

    These represent opportunities for quick wins with optimization.
    """
    df = df.copy()

    # Filter for positions 11-20 (just off page 1)
    opportunity_df = df[
        (df['position'] >= 11) &
        (df['position'] <= 20) &
        (df['impressions'] > df['impressions'].median())
    ]

    # Sort by impressions (highest first)
    return opportunity_df.nlargest(top_n, 'impressions')[
        ['query', 'position', 'impressions', 'clicks', 'ctr']
    ]


def process_query_data(file_path: Path) -> dict:
    """Process query data file and extract insights."""
    try:
        df = pd.read_csv(file_path)

        # Standardize column names
        df.columns = [col.lower().strip() for col in df.columns]

        results = {
            'total_queries': len(df),
            'total_clicks': int(df['clicks'].sum()) if 'clicks' in df.columns else 0,
            'total_impressions': int(df['impressions'].sum()) if 'impressions' in df.columns else 0,
        }

        # Top queries by clicks
        if 'clicks' in df.columns:
            top_clicks = df.nlargest(5, 'clicks')[['query', 'clicks', 'impressions', 'position']]
            results['top_by_clicks'] = top_clicks.to_dict('records')

        # Top queries by impressions
        if 'impressions' in df.columns:
            top_impressions = df.nlargest(5, 'impressions')[['query', 'impressions', 'clicks', 'position']]
            results['top_by_impressions'] = top_impressions.to_dict('records')

        # Position opportunities
        if 'position' in df.columns:
            opportunities = analyze_position_opportunities(df)
            if not opportunities.empty:
                results['opportunities'] = opportunities.to_dict('records')

        return results

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return {}


def run():
    """
    Main execution function.

    Processes query data for all clients and identifies top performers.
    """
    print("=" * 60)
    print("🎯 Top Performers Identifier")
    print("=" * 60)

    # Find all query data files
    query_files = list(DATA_DIR.glob('GSC-queries-*.csv'))
    print(f"📁 Found {len(query_files)} query data files")

    all_results = {}

    for file_path in query_files:
        client_slug = file_path.stem.replace('GSC-queries-', '')
        print(f"\n🔍 Analyzing: {client_slug}")

        results = process_query_data(file_path)

        if results:
            all_results[client_slug] = results

            print(f"   📊 Total queries: {results.get('total_queries', 0):,}")
            print(f"   🖱️ Total clicks: {results.get('total_clicks', 0):,}")
            print(f"   👁️ Total impressions: {results.get('total_impressions', 0):,}")

            # Save top performers
            if 'top_by_clicks' in results:
                top_clicks_df = pd.DataFrame(results['top_by_clicks'])
                top_clicks_df.to_csv(
                    DATA_DIR / f'top-queries-clicks-{client_slug}.csv',
                    index=False
                )

            if 'top_by_impressions' in results:
                top_impr_df = pd.DataFrame(results['top_by_impressions'])
                top_impr_df.to_csv(
                    DATA_DIR / f'top-queries-impressions-{client_slug}.csv',
                    index=False
                )

            if 'opportunities' in results:
                opp_df = pd.DataFrame(results['opportunities'])
                opp_df.to_csv(
                    DATA_DIR / f'keyword-opportunities-{client_slug}.csv',
                    index=False
                )
                print(f"   🎯 Found {len(results['opportunities'])} keyword opportunities")

    print(f"\n✅ Top performers identified for {len(all_results)} clients")

    return {
        'success': True,
        'message': f'Analyzed {len(all_results)} clients',
        'clients': list(all_results.keys())
    }


if __name__ == '__main__':
    run()
