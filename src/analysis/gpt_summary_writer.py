"""
GPT Summary Writer

Uses OpenAI API to generate intelligent analysis summaries:
- Performance insights
- Trend explanations
- Actionable recommendations

Summaries are written in professional tone suitable for client reports.
"""

import os
import json
import pandas as pd
from pathlib import Path
from openai import OpenAI

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    DATA_DIR,
    ANALYSIS_MAX_CHARS,
    ANALYSIS_MIN_CHARS
)


def get_openai_client():
    """Initialize OpenAI client."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAI(api_key=OPENAI_API_KEY)


def generate_30v30_summary(metrics_data: dict, client_name: str) -> str:
    """
    Generate a summary paragraph for 30-day vs previous 30-day comparison.

    Args:
        metrics_data: Dict containing current/previous values and changes
        client_name: Name of the client for context

    Returns:
        Professional summary paragraph (400-480 characters)
    """
    client = get_openai_client()

    # Format metrics for the prompt
    metrics_text = ""
    for metric, data in metrics_data.items():
        metrics_text += f"- {metric.title()}: {data['current']:,.0f} "
        metrics_text += f"(was {data['previous']:,.0f}, change: {data['change_pct']:+.1f}%)\n"

    prompt = f"""You are an SEO analyst writing a brief performance summary for a client report.

Client: {client_name}

30-Day Performance vs Previous 30 Days:
{metrics_text}

Write a professional summary paragraph (between {ANALYSIS_MIN_CHARS} and {ANALYSIS_MAX_CHARS} characters) that:
1. Highlights the most significant changes
2. Provides context for the performance
3. Maintains a professional, informative tone
4. Does NOT include specific numbers (use terms like "increased significantly", "slight decline", etc.)
5. Ends with a brief forward-looking statement

Important: Keep the summary concise and focused on the key takeaways."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional SEO analyst who writes clear, concise performance summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        summary = response.choices[0].message.content.strip()

        # Validate length
        if len(summary) < ANALYSIS_MIN_CHARS:
            print(f"⚠️ Summary too short ({len(summary)} chars), regenerating...")
            return generate_30v30_summary(metrics_data, client_name)
        elif len(summary) > ANALYSIS_MAX_CHARS + 50:
            # Truncate at last sentence
            summary = summary[:ANALYSIS_MAX_CHARS]
            last_period = summary.rfind('.')
            if last_period > ANALYSIS_MIN_CHARS:
                summary = summary[:last_period + 1]

        return summary

    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return f"Performance data for the past 30 days shows varied results across key metrics. Please review the detailed data for specific insights."


def generate_yoy_summary(metrics_data: dict, client_name: str) -> str:
    """
    Generate a summary paragraph for year-over-year comparison.

    Args:
        metrics_data: Dict containing YoY values and changes
        client_name: Name of the client for context

    Returns:
        Professional summary paragraph
    """
    client = get_openai_client()

    metrics_text = ""
    for metric, data in metrics_data.items():
        metrics_text += f"- {metric.title()}: {data['current_year']:,.0f} "
        metrics_text += f"(last year: {data['previous_year']:,.0f}, change: {data['change_pct']:+.1f}%)\n"

    prompt = f"""You are an SEO analyst writing a year-over-year performance summary.

Client: {client_name}

Year-over-Year Comparison (same 30-day period):
{metrics_text}

Write a professional summary paragraph (between {ANALYSIS_MIN_CHARS} and {ANALYSIS_MAX_CHARS} characters) that:
1. Contextualizes the year-over-year changes
2. Acknowledges any seasonal factors that might apply
3. Highlights long-term trends
4. Does NOT include specific numbers
5. Maintains an objective, analytical tone

Important: Focus on the strategic implications of the year-over-year performance."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional SEO analyst specializing in long-term performance trends."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        summary = response.choices[0].message.content.strip()

        # Validate and adjust length
        if len(summary) > ANALYSIS_MAX_CHARS + 50:
            summary = summary[:ANALYSIS_MAX_CHARS]
            last_period = summary.rfind('.')
            if last_period > ANALYSIS_MIN_CHARS:
                summary = summary[:last_period + 1]

        return summary

    except Exception as e:
        print(f"❌ Error generating YoY summary: {e}")
        return "Year-over-year performance shows continued organic search development. Detailed analysis of seasonal patterns and long-term trends is available in the full report."


def load_metrics_file(file_path: Path) -> dict:
    """Load metrics from CSV file into dictionary format."""
    try:
        df = pd.read_csv(file_path)
        metrics = {}

        for _, row in df.iterrows():
            metric_name = row['metric']
            metrics[metric_name] = {
                'current': row.get('current', row.get('current_year', 0)),
                'previous': row.get('previous', row.get('previous_year', 0)),
                'change_pct': row.get('change_pct', 0)
            }
            # Handle YoY specific columns
            if 'current_year' in row:
                metrics[metric_name]['current_year'] = row['current_year']
            if 'previous_year' in row:
                metrics[metric_name]['previous_year'] = row['previous_year']

        return metrics

    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return {}


def run():
    """
    Main execution function.

    Generates GPT-powered summaries for all client data.
    """
    print("=" * 60)
    print("🤖 GPT Summary Writer")
    print("=" * 60)

    if not OPENAI_API_KEY:
        return {
            'success': False,
            'message': 'OPENAI_API_KEY not configured'
        }

    # Find growth metrics files
    growth_files = list(DATA_DIR.glob('growth-metrics-*.csv'))
    yoy_files = list(DATA_DIR.glob('yoy-metrics-*.csv'))

    print(f"📁 Found {len(growth_files)} growth metric files")
    print(f"📁 Found {len(yoy_files)} YoY metric files")

    summaries = {}

    # Generate 30v30 summaries
    for file_path in growth_files:
        client_slug = file_path.stem.replace('growth-metrics-', '')
        client_name = client_slug.replace('-', ' ').title()
        print(f"\n✍️ Generating 30v30 summary: {client_name}")

        metrics = load_metrics_file(file_path)
        if metrics:
            summary = generate_30v30_summary(metrics, client_name)
            summaries[f'{client_slug}_30v30'] = summary
            print(f"   ✅ Summary generated ({len(summary)} chars)")

            # Save individual summary
            summary_file = DATA_DIR / f'summary-30v30-{client_slug}.txt'
            with open(summary_file, 'w') as f:
                f.write(summary)

    # Generate YoY summaries
    for file_path in yoy_files:
        client_slug = file_path.stem.replace('yoy-metrics-', '')
        client_name = client_slug.replace('-', ' ').title()
        print(f"\n✍️ Generating YoY summary: {client_name}")

        metrics = load_metrics_file(file_path)
        if metrics:
            # Transform for YoY format
            yoy_metrics = {}
            for name, data in metrics.items():
                yoy_metrics[name] = {
                    'current_year': data.get('current_year', data.get('current', 0)),
                    'previous_year': data.get('previous_year', data.get('previous', 0)),
                    'change_pct': data.get('change_pct', 0)
                }

            summary = generate_yoy_summary(yoy_metrics, client_name)
            summaries[f'{client_slug}_yoy'] = summary
            print(f"   ✅ Summary generated ({len(summary)} chars)")

            # Save individual summary
            summary_file = DATA_DIR / f'summary-yoy-{client_slug}.txt'
            with open(summary_file, 'w') as f:
                f.write(summary)

    # Save all summaries to JSON
    with open(DATA_DIR / 'all-summaries.json', 'w') as f:
        json.dump(summaries, f, indent=2)

    print(f"\n✅ Generated {len(summaries)} summaries")

    return {
        'success': True,
        'message': f'Generated {len(summaries)} summaries',
        'summary_count': len(summaries)
    }


if __name__ == '__main__':
    run()
