"""
Year-over-Year Comparison Calculator

Processes GSC data to calculate:
- YoY performance changes
- Seasonal trend adjustments
- Long-term growth indicators
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import DATA_DIR


def calculate_yoy_change(current: float, previous: float) -> dict:
    """
    Calculate year-over-year percentage change.

    Returns:
        dict with 'change_pct', 'change_abs', 'trend', 'trend_text' keys
    """
    if previous == 0:
        if current == 0:
            return {
                'change_pct': 0,
                'change_abs': 0,
                'trend': 'neutral',
                'trend_text': 'No change'
            }
        return {
            'change_pct': 100,
            'change_abs': current,
            'trend': 'up',
            'trend_text': 'New metric (no previous year data)'
        }

    change_abs = current - previous
    change_pct = (change_abs / previous) * 100

    # Determine trend with descriptive text
    if change_pct > 20:
        trend = 'strong_up'
        trend_text = 'Strong year-over-year growth'
    elif change_pct > 5:
        trend = 'up'
        trend_text = 'Moderate year-over-year growth'
    elif change_pct > -5:
        trend = 'neutral'
        trend_text = 'Stable year-over-year'
    elif change_pct > -20:
        trend = 'down'
        trend_text = 'Moderate year-over-year decline'
    else:
        trend = 'strong_down'
        trend_text = 'Significant year-over-year decline'

    return {
        'change_pct': round(change_pct, 2),
        'change_abs': round(change_abs, 2),
        'trend': trend,
        'trend_text': trend_text
    }


def process_yoy_file(file_path: Path) -> dict:
    """Process YoY comparison file."""
    try:
        df = pd.read_csv(file_path)

        metrics = {}
        for _, row in df.iterrows():
            metric_name = row['Metric'].lower().replace(' ', '_')
            current = row.iloc[1]  # Current Year column
            previous = row.iloc[2]  # Previous Year column

            # Handle percentage strings
            if isinstance(current, str) and '%' in current:
                current = float(current.replace('%', ''))
                previous = float(previous.replace('%', ''))
            else:
                current = float(current)
                previous = float(previous)

            metrics[metric_name] = {
                'current_year': current,
                'previous_year': previous,
                **calculate_yoy_change(current, previous)
            }

        return metrics

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return {}


def generate_yoy_summary(metrics: dict, client_name: str) -> str:
    """Generate human-readable YoY summary."""
    lines = [f"Year-over-Year Summary for {client_name}:"]
    lines.append("-" * 40)

    for metric_name, data in metrics.items():
        icon = '🟢' if 'up' in data['trend'] else '🔴' if 'down' in data['trend'] else '🟡'
        display_name = metric_name.replace('_', ' ').title()
        lines.append(f"{icon} {display_name}: {data['change_pct']:+.1f}%")
        lines.append(f"   {data['trend_text']}")

    return '\n'.join(lines)


def run():
    """
    Main execution function.

    Processes all YoY comparison files.
    """
    print("=" * 60)
    print("📅 Year-over-Year Comparison Calculator")
    print("=" * 60)

    # Find all YoY comparison files
    yoy_files = list(DATA_DIR.glob('GSC-YOY-overMonth-*.csv'))
    print(f"📁 Found {len(yoy_files)} YoY comparison files")

    all_metrics = {}

    for file_path in yoy_files:
        client_slug = file_path.stem.replace('GSC-YOY-overMonth-', '')
        print(f"\n📈 Processing: {client_slug}")

        metrics = process_yoy_file(file_path)

        if metrics:
            all_metrics[client_slug] = metrics

            # Print summary
            summary = generate_yoy_summary(metrics, client_slug.replace('-', ' ').title())
            print(summary)

            # Save detailed YoY metrics
            metrics_df = pd.DataFrame([
                {
                    'metric': name,
                    'current_year': data['current_year'],
                    'previous_year': data['previous_year'],
                    'change_pct': data['change_pct'],
                    'trend': data['trend'],
                    'trend_text': data['trend_text']
                }
                for name, data in metrics.items()
            ])

            metrics_df.to_csv(
                DATA_DIR / f'yoy-metrics-{client_slug}.csv',
                index=False
            )

    # Consolidated YoY summary
    summary_data = []
    for client, metrics in all_metrics.items():
        row = {'client': client}
        for metric_name, data in metrics.items():
            row[f'{metric_name}_yoy_change'] = data['change_pct']
            row[f'{metric_name}_trend'] = data['trend']
        summary_data.append(row)

    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(DATA_DIR / 'yoy-summary-all-clients.csv', index=False)

    print(f"\n✅ YoY comparison complete for {len(all_metrics)} clients")

    return {
        'success': True,
        'message': f'Processed {len(all_metrics)} clients',
        'clients': list(all_metrics.keys())
    }


if __name__ == '__main__':
    run()
