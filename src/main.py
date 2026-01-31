#!/usr/bin/env python3
"""
Friday Reports Automation - Master Runner

Orchestrates the complete Friday reporting pipeline:
1. Clean up previous run artifacts
2. Pull data from Google Search Console (GSC)
3. Pull data from Google Analytics 4 (GA4)
4. Analyze keyword performance and growth trends
5. Generate GPT-powered analysis summaries
6. Create HTML reports with embedded graphs
7. Upload graphs to hosting server
8. Send reports via email
9. Send status notification

Usage:
    python src/main.py
    python src/main.py --dry-run
    python src/main.py --step data_collection
"""

import os
import sys
import json
import yaml
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import BASE_DIR, REPORTS_DIR, DATA_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(BASE_DIR / 'logs' / f'friday_reports_{datetime.now():%Y%m%d_%H%M%S}.log')
    ]
)
logger = logging.getLogger(__name__)

# Pipeline configuration
PIPELINE_STEPS = {
    'cleanup': [
        'data_processing.cleanup',
    ],
    'data_collection': [
        'data_collection.fetch_gsc_data',
        'data_collection.fetch_ga4_data',
    ],
    'data_processing': [
        'data_processing.calculate_growth_metrics',
        'data_processing.identify_top_performers',
        'data_processing.calculate_yoy_comparison',
    ],
    'analysis': [
        'analysis.gpt_summary_writer',
    ],
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


def load_pipeline_config(config_file: str = None) -> dict:
    """Load pipeline configuration from YAML file."""
    if config_file is None:
        config_file = BASE_DIR / 'config' / 'pipeline.yaml'

    if Path(config_file).exists():
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    # Return default configuration
    return {'steps': PIPELINE_STEPS}


def run_module(module_name: str, dry_run: bool = False) -> dict:
    """
    Execute a pipeline module and return results.

    Args:
        module_name: Dot-notation module path (e.g., 'data_collection.fetch_gsc_data')
        dry_run: If True, only log what would be executed

    Returns:
        dict with 'success', 'duration', and 'message' keys
    """
    start_time = datetime.now()

    if dry_run:
        logger.info(f"[DRY RUN] Would execute: {module_name}")
        return {
            'success': True,
            'duration': 0,
            'message': 'Dry run - skipped'
        }

    try:
        logger.info(f"▶️ Starting: {module_name}")

        # Import and run the module
        module_path = f"src.{module_name}"
        module = __import__(module_path, fromlist=['run'])

        if hasattr(module, 'run'):
            result = module.run()
        else:
            result = {'success': True, 'message': 'Module executed (no run function)'}

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Completed: {module_name} ({duration:.2f}s)")

        return {
            'success': True,
            'duration': duration,
            'message': result.get('message', 'Success')
        }

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Failed: {module_name} - {str(e)}")

        return {
            'success': False,
            'duration': duration,
            'message': str(e)
        }


def run_pipeline(steps: list = None, dry_run: bool = False) -> dict:
    """
    Execute the complete pipeline or specific steps.

    Args:
        steps: List of step names to run (None = all steps)
        dry_run: If True, only log what would be executed

    Returns:
        dict with pipeline execution results
    """
    start_time = datetime.now()
    results = {
        'start_time': start_time.isoformat(),
        'steps': {},
        'success': True
    }

    config = load_pipeline_config()
    pipeline_steps = config.get('steps', PIPELINE_STEPS)

    # Filter to specific steps if requested
    if steps:
        pipeline_steps = {k: v for k, v in pipeline_steps.items() if k in steps}

    logger.info("=" * 60)
    logger.info("🚀 Friday Reports Pipeline Starting")
    logger.info(f"   Steps: {list(pipeline_steps.keys())}")
    logger.info(f"   Dry Run: {dry_run}")
    logger.info("=" * 60)

    for step_name, modules in pipeline_steps.items():
        logger.info(f"\n📋 Step: {step_name}")
        logger.info("-" * 40)

        step_results = []
        step_success = True

        for module_name in modules:
            result = run_module(module_name, dry_run)
            step_results.append({
                'module': module_name,
                **result
            })

            if not result['success']:
                step_success = False
                results['success'] = False
                logger.warning(f"⚠️ Step '{step_name}' encountered an error")
                break  # Stop this step on failure

        results['steps'][step_name] = {
            'success': step_success,
            'modules': step_results
        }

    # Calculate total duration
    end_time = datetime.now()
    results['end_time'] = end_time.isoformat()
    results['total_duration'] = (end_time - start_time).total_seconds()

    # Log summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Pipeline Summary")
    logger.info("=" * 60)

    for step_name, step_result in results['steps'].items():
        status = "✅" if step_result['success'] else "❌"
        logger.info(f"   {status} {step_name}")

    logger.info(f"\n   Total Duration: {results['total_duration']:.2f}s")
    logger.info(f"   Overall Status: {'✅ SUCCESS' if results['success'] else '❌ FAILED'}")

    # Save execution report
    report_file = BASE_DIR / 'logs' / f'pipeline_report_{datetime.now():%Y%m%d_%H%M%S}.json'
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"   Report saved: {report_file}")

    return results


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Friday Reports Automation Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python src/main.py                    # Run full pipeline
    python src/main.py --dry-run          # Preview what would run
    python src/main.py --step data_collection --step analysis
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview pipeline without executing'
    )

    parser.add_argument(
        '--step',
        action='append',
        choices=list(PIPELINE_STEPS.keys()),
        help='Run specific step(s) only'
    )

    args = parser.parse_args()

    # Run the pipeline
    results = run_pipeline(steps=args.step, dry_run=args.dry_run)

    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
