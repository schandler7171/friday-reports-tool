"""
HTML Report Builder

Assembles complete HTML reports from:
- GPT-generated summaries
- Comparison data tables
- Generated graphs
- Template styling

Reports are styled for email delivery with inline CSS.
"""

import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from premailer import transform

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    DATA_DIR, REPORTS_DIR, GRAPHS_DIR, TEMPLATES_DIR,
    IMAGE_HOST_URL, CLIENT_CONFIG_FILE
)


# Section headers with emojis for visual appeal
SECTION_HEADERS = {
    "30v30": "📊 30 Days vs Previous 30",
    "yoy": "📈 30 Day Year over Year Comparison",
    "ga4": "💹 Google Analytics",
    "top_growth": "🚀 Top 5 Growth by Impressions",
    "top_drop": "📉 Top 5 Drop by Impressions",
    "resources": "🧰 Additional Resources"
}


def get_css_styles():
    """Return CSS styles for the report."""
    return """
    body {
        font-family: Arial, Helvetica, sans-serif;
        color: #333333;
        padding: 20px;
        max-width: 900px;
        margin: auto;
        line-height: 1.6;
    }
    h1 {
        color: #003366;
        border-bottom: 2px solid #003366;
        padding-bottom: 10px;
    }
    h2, h3 {
        color: #003366;
        margin-top: 30px;
    }
    .summary-box {
        background-color: #f8f9fa;
        border-left: 4px solid #003366;
        padding: 15px;
        margin: 20px 0;
    }
    table.seo-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }
    table.seo-table th {
        background-color: #003366;
        color: white;
        padding: 10px;
        text-align: left;
    }
    table.seo-table td {
        border: 1px solid #dddddd;
        padding: 8px;
        text-align: center;
    }
    table.seo-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    img.seo-graph {
        display: block;
        margin: 20px auto;
        max-width: 100%;
        height: auto;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    .trend-up { color: #28a745; font-weight: bold; }
    .trend-down { color: #dc3545; font-weight: bold; }
    .trend-neutral { color: #6c757d; }
    .footer {
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #ddd;
        font-size: 12px;
        color: #666;
    }
    """


def load_summary(client_slug: str, summary_type: str) -> str:
    """Load GPT-generated summary from file."""
    summary_file = DATA_DIR / f'summary-{summary_type}-{client_slug}.txt'
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            return f.read().strip()
    return ""


def load_comparison_data(client_slug: str, data_type: str) -> pd.DataFrame:
    """Load comparison data from CSV."""
    if data_type == '30v30':
        file_path = DATA_DIR / f'GSC-30vs30-overMonth-{client_slug}.csv'
    elif data_type == 'yoy':
        file_path = DATA_DIR / f'GSC-YOY-overMonth-{client_slug}.csv'
    elif data_type == 'ga4':
        file_path = DATA_DIR / f'GA4-organic-{client_slug}.csv'
    else:
        return pd.DataFrame()

    if file_path.exists():
        return pd.read_csv(file_path)
    return pd.DataFrame()


def df_to_html_table(df: pd.DataFrame) -> str:
    """Convert DataFrame to styled HTML table."""
    if df.empty:
        return "<p><em>No data available</em></p>"

    return df.to_html(
        index=False,
        border=0,
        classes='seo-table',
        escape=False,
        justify='center'
    )


def get_graph_url(client_slug: str, graph_type: str) -> str:
    """Generate URL for hosted graph image."""
    current_week = datetime.today().isocalendar()[1]

    if graph_type == '30v30':
        filename = f'GSC-30vs30-week{current_week}-{client_slug}.png'
    else:  # yoy
        filename = f'GSC-YOY-week{current_week}-{client_slug}.png'

    return f"{IMAGE_HOST_URL}{filename}"


def build_report(client_name: str, client_slug: str) -> str:
    """
    Build complete HTML report for a client.

    Args:
        client_name: Display name for the client
        client_slug: URL-safe client identifier

    Returns:
        Complete HTML report string
    """
    current_week = datetime.today().isocalendar()[1]
    current_date = datetime.today().strftime('%B %d, %Y')

    # Start building HTML
    html_parts = [
        "<!DOCTYPE html>",
        "<html><head>",
        "<meta charset='utf-8'>",
        f"<title>Weekly SEO Update - {client_name}</title>",
        f"<style>{get_css_styles()}</style>",
        "</head><body>",
        f"<h1>Weekly Update {client_name} SEO – Week {current_week}</h1>",
        f"<p><em>Report generated: {current_date}</em></p>"
    ]

    # 30-Day vs Previous 30 Section
    html_parts.append(f"<h2>{SECTION_HEADERS['30v30']}</h2>")

    summary_30v30 = load_summary(client_slug, '30v30')
    if summary_30v30:
        html_parts.append(f"<div class='summary-box'>{summary_30v30}</div>")

    data_30v30 = load_comparison_data(client_slug, '30v30')
    if not data_30v30.empty:
        html_parts.append(df_to_html_table(data_30v30))

    # Add 30v30 graph
    graph_url_30v30 = get_graph_url(client_slug, '30v30')
    html_parts.append(f"<img src='{graph_url_30v30}' class='seo-graph' alt='30-Day Comparison Chart' />")

    # Year-over-Year Section
    html_parts.append(f"<h2>{SECTION_HEADERS['yoy']}</h2>")

    summary_yoy = load_summary(client_slug, 'yoy')
    if summary_yoy:
        html_parts.append(f"<div class='summary-box'>{summary_yoy}</div>")

    data_yoy = load_comparison_data(client_slug, 'yoy')
    if not data_yoy.empty:
        html_parts.append(df_to_html_table(data_yoy))

    # Add YoY graph
    graph_url_yoy = get_graph_url(client_slug, 'yoy')
    html_parts.append(f"<img src='{graph_url_yoy}' class='seo-graph' alt='Year-over-Year Chart' />")

    # Google Analytics Section
    html_parts.append(f"<h2>{SECTION_HEADERS['ga4']}</h2>")

    data_ga4 = load_comparison_data(client_slug, 'ga4')
    if not data_ga4.empty:
        html_parts.append(df_to_html_table(data_ga4))
    else:
        html_parts.append("<p><em>Google Analytics data not available for this period.</em></p>")

    # Footer
    html_parts.append("<div class='footer'>")
    html_parts.append(f"<p>This report was automatically generated on {current_date}.</p>")
    html_parts.append("<p>For questions about this report, please contact your SEO team.</p>")
    html_parts.append("</div>")

    html_parts.append("</body></html>")

    # Join and inline CSS for email compatibility
    raw_html = '\n'.join(html_parts)

    try:
        return transform(raw_html)
    except Exception as e:
        print(f"⚠️ CSS inlining failed: {e}")
        return raw_html


def load_client_config() -> pd.DataFrame:
    """Load client configuration."""
    config_path = Path(CLIENT_CONFIG_FILE)
    if config_path.exists():
        return pd.read_excel(config_path)
    return pd.DataFrame()


def run():
    """
    Main execution function.

    Builds HTML reports for all clients.
    """
    print("=" * 60)
    print("📄 HTML Report Builder")
    print("=" * 60)

    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Get client list from available data files
    data_files = list(DATA_DIR.glob('GSC-30vs30-overMonth-*.csv'))
    print(f"📁 Found data for {len(data_files)} clients")

    reports_generated = 0
    current_week = datetime.today().isocalendar()[1]

    for data_file in data_files:
        client_slug = data_file.stem.replace('GSC-30vs30-overMonth-', '')
        client_name = client_slug.replace('-', ' ').title()

        print(f"\n📝 Building report: {client_name}")

        try:
            html_content = build_report(client_name, client_slug)

            # Save report
            output_file = REPORTS_DIR / f'Weekly-Update-{client_name.replace(" ", "-")}-SEO-Week{current_week}.html'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"   ✅ Saved: {output_file.name}")
            reports_generated += 1

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n✅ Report generation complete: {reports_generated} reports created")

    return {
        'success': True,
        'message': f'Generated {reports_generated} reports',
        'report_count': reports_generated
    }


if __name__ == '__main__':
    run()
