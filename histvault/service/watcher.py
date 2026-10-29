"""
Copyright 2026 HistVault Open Source Project Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, Optional, Callable
from histvault.service.synchronizer import VaultSynchronizer


class VaultWatcherDaemon:
    """
    Background daemon monitoring browser history databases for modifications
    and automatically archiving them without user intervention.
    """

    def __init__(self, synchronizer: Optional[VaultSynchronizer] = None, interval_seconds: int = 30):
        self.synchronizer = synchronizer or VaultSynchronizer()
        self.interval = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_mtimes: Dict[str, float] = {}
        self.on_sync_callback: Optional[Callable] = None

    def start(self):
        """Starts the background watcher thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="HistVaultWatcher")
        self._thread.start()

    def stop(self):
        """Signals the background thread to terminate."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run_loop(self):
        # Initial synchronization on startup
        try:
            report = self.synchronizer.sync_all()
            if self.on_sync_callback:
                self.on_sync_callback(report)
        except Exception as e:
            print(f"[WATCHER] Initial sync error: {e}")

        while not self._stop_event.is_set():
            time.sleep(self.interval)
            if self._stop_event.is_set():
                break

            try:
                profiles = self.synchronizer.extractor.discover_profiles()
                modified = False

                for profile in profiles:
                    path = Path(profile.history_file_path)
                    if path.exists():
                        current_mtime = os.path.getmtime(path)
                        last_mtime = self._last_mtimes.get(profile.identifier, 0.0)

                        if current_mtime > last_mtime:
                            modified = True
                            self._last_mtimes[profile.identifier] = current_mtime

                if modified:
                    report = self.synchronizer.sync_all(profiles)
                    if self.on_sync_callback:
                        self.on_sync_callback(report)
            except Exception as e:
                print(f"[WATCHER] Polling cycle error: {e}")
