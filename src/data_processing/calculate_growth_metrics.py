"""
Growth Metrics Calculator

Processes GSC and GA4 data to calculate:
- Period-over-period growth rates
- Trend indicators
- Performance summaries
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import DATA_DIR, CLIENT_CONFIG_FILE


def calculate_change(current: float, previous: float) -> dict:
    """
    Calculate percentage change and trend direction.

    Returns:
        dict with 'change_pct', 'change_abs', 'trend' keys
    """
    if previous == 0:
        if current == 0:
            return {'change_pct': 0, 'change_abs': 0, 'trend': 'neutral'}
        return {'change_pct': 100, 'change_abs': current, 'trend': 'up'}

    change_abs = current - previous
    change_pct = (change_abs / previous) * 100

    if change_pct > 5:
        trend = 'up'
    elif change_pct < -5:
        trend = 'down'
    else:
        trend = 'neutral'

    return {
        'change_pct': round(change_pct, 2),
        'change_abs': round(change_abs, 2),
        'trend': trend
    }


def process_gsc_comparison(file_path: Path) -> dict:
    """Process GSC 30vs30 comparison file."""
    try:
        df = pd.read_csv(file_path)

        metrics = {}
        for _, row in df.iterrows():
            metric_name = row['Metric'].lower().replace(' ', '_')
            current = row.iloc[1]  # Current 30 Days column
            previous = row.iloc[2]  # Previous 30 Days column

            # Handle percentage strings
            if isinstance(current, str) and '%' in current:
                current = float(current.replace('%', ''))
                previous = float(previous.replace('%', ''))
            else:
                current = float(current)
                previous = float(previous)

            metrics[metric_name] = {
                'current': current,
                'previous': previous,
                **calculate_change(current, previous)
            }

        return metrics

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return {}


def generate_summary_text(metrics: dict, client_name: str) -> str:
    """Generate a human-readable summary of the metrics."""
    lines = [f"Performance Summary for {client_name}:"]

    if 'clicks' in metrics:
        m = metrics['clicks']
        trend_emoji = '📈' if m['trend'] == 'up' else '📉' if m['trend'] == 'down' else '➡️'
        lines.append(f"{trend_emoji} Clicks: {int(m['current']):,} ({m['change_pct']:+.1f}%)")

    if 'impressions' in metrics:
        m = metrics['impressions']
        trend_emoji = '📈' if m['trend'] == 'up' else '📉' if m['trend'] == 'down' else '➡️'
        lines.append(f"{trend_emoji} Impressions: {int(m['current']):,} ({m['change_pct']:+.1f}%)")

    if 'ctr' in metrics:
        m = metrics['ctr']
        trend_emoji = '📈' if m['trend'] == 'up' else '📉' if m['trend'] == 'down' else '➡️'
        lines.append(f"{trend_emoji} CTR: {m['current']:.2f}% ({m['change_pct']:+.1f}%)")

    if 'position' in metrics:
        m = metrics['position']
        # For position, lower is better
        trend_emoji = '📈' if m['trend'] == 'down' else '📉' if m['trend'] == 'up' else '➡️'
        lines.append(f"{trend_emoji} Avg Position: {m['current']:.1f} ({-m['change_pct']:+.1f}%)")

    return '\n'.join(lines)


def run():
    """
    Main execution function.

    Processes all GSC comparison files and calculates growth metrics.
    """
    print("=" * 60)
    print("📊 Growth Metrics Calculator")
    print("=" * 60)

    # Find all GSC comparison files
    gsc_files = list(DATA_DIR.glob('GSC-30vs30-overMonth-*.csv'))
    print(f"📁 Found {len(gsc_files)} GSC comparison files")

    all_metrics = {}

    for file_path in gsc_files:
        # Extract client name from filename
        client_slug = file_path.stem.replace('GSC-30vs30-overMonth-', '')
        print(f"\n📈 Processing: {client_slug}")

        metrics = process_gsc_comparison(file_path)

        if metrics:
            all_metrics[client_slug] = metrics

            # Generate summary
            summary = generate_summary_text(metrics, client_slug.replace('-', ' ').title())
            print(summary)

            # Save detailed metrics
            metrics_df = pd.DataFrame([
                {
                    'metric': name,
                    'current': data['current'],
                    'previous': data['previous'],
                    'change_pct': data['change_pct'],
                    'change_abs': data['change_abs'],
                    'trend': data['trend']
                }
                for name, data in metrics.items()
            ])

            metrics_df.to_csv(
                DATA_DIR / f'growth-metrics-{client_slug}.csv',
                index=False
            )

    # Save consolidated summary
    summary_data = []
    for client, metrics in all_metrics.items():
        row = {'client': client}
        for metric_name, data in metrics.items():
            row[f'{metric_name}_current'] = data['current']
            row[f'{metric_name}_change'] = data['change_pct']
            row[f'{metric_name}_trend'] = data['trend']
        summary_data.append(row)

    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(DATA_DIR / 'growth-summary-all-clients.csv', index=False)

    print(f"\n✅ Growth metrics calculated for {len(all_metrics)} clients")

    return {
        'success': True,
        'message': f'Processed {len(all_metrics)} clients',
        'clients': list(all_metrics.keys())
    }


if __name__ == '__main__':
    run()
