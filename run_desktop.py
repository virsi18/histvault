"""
Convenience launcher for HistVault Desktop Application.
Run directly with: py run_desktop.py
"""
import sys
from pathlib import Path

# Ensure root package directory is on path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from histvault.desktop.launcher import launch_desktop_app

if __name__ == "__main__":
    launch_desktop_app()
