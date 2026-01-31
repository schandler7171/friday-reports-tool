"""
Graph Generator

Creates visual charts for SEO reports:
- 30-day vs previous 30-day comparison bar charts
- Year-over-year comparison charts
- Trend line visualizations

Uses Seaborn and Matplotlib for professional-quality graphics.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import DATA_DIR, GRAPHS_DIR

# Configure Seaborn styling
sns.set_theme(style="whitegrid")

# Brand colors
COLORS = {
    'primary': '#103CC1',    # Current period (blue)
    'secondary': '#FBBD09',  # Previous period (yellow)
    'accent': '#28A745',     # Positive change (green)
    'warning': '#DC3545',    # Negative change (red)
}


def generate_comparison_chart(csv_path: Path, output_path: Path,
                              title: str, format_type: str = "30vs30"):
    """
    Generate a comparison bar chart from CSV data.

    Args:
        csv_path: Path to CSV with comparison data
        output_path: Path to save the PNG output
        title: Chart title
        format_type: '30vs30' or 'YOY' for column name mapping
    """
    try:
        df = pd.read_csv(csv_path)
        df.columns = [col.strip() for col in df.columns]

        # Map columns based on format type
        if format_type == "30vs30":
            metric_col = "Metric"
            current_col = "Current 30 Days"
            previous_col = "Previous 30 Days"
            label_current = "Current 30 Days"
            label_previous = "Previous 30 Days"
        else:  # YOY
            metric_col = "Metric"
            current_col = "Current Year (30d)"
            previous_col = "Previous Year (30d)"
            label_current = "This Year"
            label_previous = "Last Year"

        # Validate columns exist
        required_cols = [metric_col, current_col, previous_col]
        for col in required_cols:
            if col not in df.columns:
                print(f"⚠️ Missing column: '{col}' in {csv_path}")
                return False

        # Focus on Clicks and Impressions for clarity
        metrics = ["Clicks", "Impressions"]

        fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(12, 5))
        axs = axs.flatten()

        for i, metric in enumerate(metrics):
            sub_df = df[df[metric_col].str.strip().str.lower() == metric.lower()]

            if sub_df.empty:
                axs[i].text(0.5, 0.5, f"No {metric} data",
                           ha='center', va='center', transform=axs[i].transAxes)
                continue

            row = sub_df.iloc[0]

            # Handle numeric conversion
            current_val = row[current_col]
            previous_val = row[previous_col]

            # Remove % signs if present
            if isinstance(current_val, str):
                current_val = float(current_val.replace('%', '').replace(',', ''))
            if isinstance(previous_val, str):
                previous_val = float(previous_val.replace('%', '').replace(',', ''))

            current_val = float(current_val)
            previous_val = float(previous_val)

            # Create plot data
            plot_df = pd.DataFrame({
                "Period": [label_current, label_previous],
                "Value": [current_val, previous_val]
            })

            # Generate bar chart
            sns.barplot(
                x="Period", y="Value", hue="Period",
                data=plot_df, ax=axs[i],
                palette=[COLORS['primary'], COLORS['secondary']],
                legend=False
            )

            # Calculate change percentage
            if previous_val > 0:
                change_pct = ((current_val - previous_val) / previous_val) * 100
                change_text = f"{change_pct:+.1f}%"
                change_color = COLORS['accent'] if change_pct >= 0 else COLORS['warning']
            else:
                change_text = "N/A"
                change_color = 'gray'

            axs[i].set_title(f"{metric.upper()}\n({change_text})",
                            fontsize=12, fontweight='bold')
            axs[i].tick_params(axis='x', rotation=0)

            # Format y-axis for large numbers
            axs[i].yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: f'{int(x):,}')
            )

        # Add overall title
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()

        # Save figure
        plt.savefig(output_path, dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        plt.close()

        print(f"   ✅ Saved: {output_path.name}")
        return True

    except Exception as e:
        print(f"   ❌ Error generating chart: {e}")
        return False


def run():
    """
    Main execution function.

    Generates graphs for all comparison data files.
    """
    print("=" * 60)
    print("📊 Graph Generator")
    print("=" * 60)

    # Ensure output directory exists
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

    current_week = datetime.today().isocalendar()[1]
    graphs_generated = 0

    # Generate 30vs30 graphs
    print("\n📈 Generating 30-Day Comparison Graphs...")
    for csv_file in DATA_DIR.glob('GSC-30vs30-overMonth-*.csv'):
        client_slug = csv_file.stem.replace('GSC-30vs30-overMonth-', '')
        output_file = GRAPHS_DIR / f'GSC-30vs30-week{current_week}-{client_slug}.png'

        print(f"\n   Processing: {client_slug}")
        if generate_comparison_chart(
            csv_file, output_file,
            title="30 Days vs Previous 30 Days",
            format_type="30vs30"
        ):
            graphs_generated += 1

    # Generate YoY graphs
    print("\n📅 Generating Year-over-Year Graphs...")
    for csv_file in DATA_DIR.glob('GSC-YOY-overMonth-*.csv'):
        client_slug = csv_file.stem.replace('GSC-YOY-overMonth-', '')
        output_file = GRAPHS_DIR / f'GSC-YOY-week{current_week}-{client_slug}.png'

        print(f"\n   Processing: {client_slug}")
        if generate_comparison_chart(
            csv_file, output_file,
            title="Year-over-Year Comparison (30 Days)",
            format_type="YOY"
        ):
            graphs_generated += 1

    print(f"\n✅ Graph generation complete: {graphs_generated} graphs created")

    return {
        'success': True,
        'message': f'Generated {graphs_generated} graphs',
        'graph_count': graphs_generated
    }


if __name__ == '__main__':
    run()
