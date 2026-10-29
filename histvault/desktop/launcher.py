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

import sys
import time
import socket
import threading
import subprocess
from pathlib import Path
from typing import Optional
from histvault.constants import DEFAULT_DB_PATH
from histvault.core.database import VaultDatabase
from histvault.service.synchronizer import VaultSynchronizer
from histvault.server.app import VaultServer


def find_free_port(preferred_port: int = 8765) -> int:
    """Checks if preferred port is open, otherwise finds an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", preferred_port)) != 0:
            return preferred_port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def launch_desktop_app(db_path: Optional[Path] = None, port: Optional[int] = None):
    """
    Launches HistVault as a native standalone desktop application window.
    """
    database = VaultDatabase(db_path or DEFAULT_DB_PATH)
    server_port = port or find_free_port(8765)
    server_host = "127.0.0.1"
    server_url = f"http://{server_host}:{server_port}"

    print(f"[DESKTOP] Initializing HistVault Desktop App...")
    # 1. Initial silent background sync
    try:
        sync = VaultSynchronizer(database)
        report = sync.sync_all()
        print(f"[DESKTOP] Synced {report.total_preserved_urls} history records.")
    except Exception as e:
        print(f"[DESKTOP] Background sync notice: {e}")

    # 2. Start embedded HTTP server in background thread
    server = VaultServer(host=server_host, port=server_port, database=database)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True, name="HistVaultDesktopServer")
    server_thread.start()

    # Small delay to ensure server socket is listening
    time.sleep(0.3)
    print(f"[DESKTOP] Local server listening on {server_url}")

    # 3. Launch native desktop window
    has_webview = False
    try:
        import webview
        has_webview = True
    except ImportError:
        has_webview = False

    if has_webview:
        print("[DESKTOP] Launching via native Edge WebView2 desktop container...")
        window = webview.create_window(
            title="HistVault — Browser History Preservation Archive",
            url=server_url,
            width=1180,
            height=820,
            min_size=(820, 620),
            background_color="#000000"
        )
        try:
            webview.start(debug=False)
        finally:
            print("[DESKTOP] Desktop window closed. Stopping background server.")
            server.shutdown()
            server.server_close()
    else:
        # Fallback: Launch standalone Windows App Mode
        print("[DESKTOP] Launching in standalone desktop App Mode...")
        app_launched = False

        if sys.platform == "win32":
            edge_candidates = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ]
            for edge_exe in edge_candidates:
                if Path(edge_exe).exists():
                    subprocess.run([edge_exe, f"--app={server_url}"])
                    app_launched = True
                    break

        if not app_launched:
            import webbrowser
            webbrowser.open(server_url)
            print("[DESKTOP] App running in browser. Press Ctrl+C in terminal to exit.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                server.shutdown()
                server.server_close()
