"""
Cleanup Module

Removes artifacts from previous pipeline runs to ensure clean execution.
Moves old files to backup directory for safety.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import DATA_DIR, REPORTS_DIR, GRAPHS_DIR, BASE_DIR

# File extensions to clean up
CLEANUP_EXTENSIONS = ['.csv', '.json', '.html', '.png', '.xlsx']

# Directories to clean (their contents will be moved to backup)
CLEANUP_DIRS = [DATA_DIR, REPORTS_DIR, GRAPHS_DIR]

# Files to preserve (never move these)
PRESERVED_FILES = [
    'clients.xlsx',
    'recipients.csv',
    'template.html',
]


def run():
    """
    Main cleanup function.

    Moves old data files to backup directory before new pipeline run.
    """
    print("=" * 60)
    print("🧹 Cleanup Module")
    print("=" * 60)

    # Create backup directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = BASE_DIR / 'backups' / f'backup_{timestamp}'
    backup_dir.mkdir(parents=True, exist_ok=True)

    files_moved = 0
    files_skipped = 0

    for cleanup_dir in CLEANUP_DIRS:
        cleanup_path = Path(cleanup_dir)

        if not cleanup_path.exists():
            print(f"📁 Creating directory: {cleanup_path}")
            cleanup_path.mkdir(parents=True, exist_ok=True)
            continue

        print(f"\n📂 Cleaning: {cleanup_path}")

        for item in cleanup_path.iterdir():
            # Skip directories (process files only at this level)
            if item.is_dir():
                continue

            # Check if file should be preserved
            if item.name in PRESERVED_FILES:
                print(f"   ⏭️ Preserved: {item.name}")
                files_skipped += 1
                continue

            # Check if file extension matches cleanup list
            if item.suffix.lower() in CLEANUP_EXTENSIONS:
                dest_path = backup_dir / item.name

                # Handle duplicate filenames
                if dest_path.exists():
                    base = dest_path.stem
                    suffix = dest_path.suffix
                    counter = 1
                    while dest_path.exists():
                        dest_path = backup_dir / f"{base}_{counter}{suffix}"
                        counter += 1

                shutil.move(str(item), str(dest_path))
                print(f"   📦 Moved: {item.name}")
                files_moved += 1

    # Clean up graphs subdirectory
    if GRAPHS_DIR.exists():
        for item in GRAPHS_DIR.iterdir():
            if item.is_file() and item.suffix.lower() == '.png':
                dest_path = backup_dir / 'graphs' / item.name
                dest_path.parent.mkdir(exist_ok=True)
                shutil.move(str(item), str(dest_path))
                files_moved += 1

    print(f"\n✅ Cleanup complete:")
    print(f"   Files moved to backup: {files_moved}")
    print(f"   Files preserved: {files_skipped}")
    print(f"   Backup location: {backup_dir}")

    return {
        'success': True,
        'message': f'Moved {files_moved} files to backup',
        'backup_dir': str(backup_dir)
    }


if __name__ == '__main__':
    run()
