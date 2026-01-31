"""
Asset Uploader

Uploads generated graph images to hosting server via SFTP.
Images are then referenced in HTML reports via public URLs.
"""

import os
import paramiko
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import (
    SFTP_HOST, SFTP_PORT, SFTP_USER, SFTP_PASS,
    SFTP_REMOTE_FOLDER, GRAPHS_DIR
)


def upload_files_sftp():
    """
    Upload graph files to SFTP server.

    Returns:
        dict with upload results
    """
    if not all([SFTP_HOST, SFTP_USER, SFTP_PASS]):
        return {
            'success': False,
            'message': 'SFTP credentials not configured'
        }

    try:
        # Initialize SSH transport
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)

        print(f"📡 Connected to {SFTP_HOST}")

        # Change to remote directory
        try:
            sftp.chdir(SFTP_REMOTE_FOLDER)
            print(f"📁 Remote folder: {SFTP_REMOTE_FOLDER}")
        except IOError:
            print(f"⚠️ Remote folder '{SFTP_REMOTE_FOLDER}' not accessible")
            sftp.close()
            transport.close()
            return {
                'success': False,
                'message': f'Remote folder not accessible: {SFTP_REMOTE_FOLDER}'
            }

        # Upload files
        uploaded = 0
        failed = 0

        for file_path in GRAPHS_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == '.png':
                remote_path = f"{SFTP_REMOTE_FOLDER}/{file_path.name}"

                try:
                    print(f"   ⬆️ Uploading: {file_path.name}")
                    sftp.put(str(file_path), remote_path)
                    uploaded += 1
                except Exception as e:
                    print(f"   ❌ Failed: {file_path.name} - {e}")
                    failed += 1

        # Close connections
        sftp.close()
        transport.close()
        print("🔒 Connection closed")

        return {
            'success': failed == 0,
            'message': f'Uploaded {uploaded} files, {failed} failed',
            'uploaded': uploaded,
            'failed': failed
        }

    except Exception as e:
        print(f"❌ SFTP Error: {e}")
        return {
            'success': False,
            'message': str(e)
        }


def run():
    """
    Main execution function.

    Uploads all graph images to the hosting server.
    """
    print("=" * 60)
    print("⬆️ Asset Uploader (SFTP)")
    print("=" * 60)

    if not GRAPHS_DIR.exists():
        return {
            'success': False,
            'message': f'Graphs directory not found: {GRAPHS_DIR}'
        }

    # Count files to upload
    png_files = list(GRAPHS_DIR.glob('*.png'))
    print(f"📁 Found {len(png_files)} graph files to upload")

    if not png_files:
        print("⚠️ No graph files found, skipping upload")
        return {
            'success': True,
            'message': 'No files to upload'
        }

    # Perform upload
    result = upload_files_sftp()

    if result['success']:
        print(f"\n✅ Upload complete: {result.get('uploaded', 0)} files")
    else:
        print(f"\n❌ Upload failed: {result['message']}")

    return result


if __name__ == '__main__':
    run()
