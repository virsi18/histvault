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

import json
import os
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from typing import Any, Optional
from histvault.constants import DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT
from histvault.core.database import VaultDatabase
from histvault.service.synchronizer import VaultSynchronizer
from histvault.service.exporter import HistoryExporter


STATIC_DIR = Path(__file__).parent / "static"


class VaultRequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Concise logging
        pass

    @property
    def database(self) -> VaultDatabase:
        return self.server.database

    @property
    def synchronizer(self) -> VaultSynchronizer:
        return self.server.synchronizer

    @property
    def exporter(self) -> HistoryExporter:
        return self.server.exporter

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/stats":
            self.handle_api_stats()
        elif path == "/api/history":
            self.handle_api_history(query)
        elif path == "/api/top-domains":
            self.handle_api_top_domains(query)
        elif path == "/api/export":
            self.handle_api_export(query)
        elif path == "/" or path == "/index.html":
            self.serve_file(STATIC_DIR / "index.html", "text/html")
        else:
            # Serve static assets
            safe_rel = path.lstrip("/")
            file_path = STATIC_DIR / safe_rel
            if file_path.exists() and file_path.is_file():
                mime, _ = mimetypes.guess_type(str(file_path))
                self.serve_file(file_path, mime or "application/octet-stream")
            else:
                self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/sync":
            self.handle_api_sync()
        else:
            self.send_error(404, "Endpoint Not Found")

    def handle_api_stats(self):
        stats = self.database.get_stats()
        self.send_json(200, stats)

    def handle_api_history(self, query):
        q = query.get("q", [""])[0]
        category = query.get("category", [None])[0]
        browser = query.get("browser", [None])[0]
        deleted_only = query.get("deleted_only", ["false"])[0].lower() in ("true", "1")
        active_only = query.get("active_only", ["false"])[0].lower() in ("true", "1")

        try:
            limit = min(200, max(1, int(query.get("limit", [50])[0])))
            offset = max(0, int(query.get("offset", [0])[0]))
        except ValueError:
            limit = 50
            offset = 0

        entries = self.database.search_urls(
            query=q,
            category=category,
            browser=browser,
            deleted_only=deleted_only,
            active_only=active_only,
            limit=limit,
            offset=offset
        )

        self.send_json(200, {
            "entries": [e.to_dict() for e in entries],
            "limit": limit,
            "offset": offset,
            "count": len(entries)
        })

    def handle_api_top_domains(self, query):
        try:
            limit = int(query.get("limit", [10])[0])
        except ValueError:
            limit = 10
        top = self.database.get_top_domains(limit)
        self.send_json(200, top)

    def handle_api_sync(self):
        report = self.synchronizer.sync_all()
        self.send_json(200, report.to_dict())

    def handle_api_export(self, query):
        fmt = query.get("format", ["json"])[0].lower()
        deleted_only = query.get("deleted_only", ["false"])[0].lower() in ("true", "1")

        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        out_file = temp_dir / f"histvault_export.{fmt}"

        if fmt == "csv":
            self.exporter.export_csv(out_file, deleted_only=deleted_only)
            mime = "text/csv"
        elif fmt == "html":
            self.exporter.export_html(out_file, deleted_only=deleted_only)
            mime = "text/html"
        elif fmt == "md" or fmt == "markdown":
            self.exporter.export_markdown(out_file, deleted_only=deleted_only)
            mime = "text/markdown"
        else:
            self.exporter.export_json(out_file, deleted_only=deleted_only)
            mime = "application/json"

        content = out_file.read_bytes()
        try:
            out_file.unlink()
        except OSError:
            pass

        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Disposition", f'attachment; filename="histvault_export.{fmt}"')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, status: int, data: Any):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, file_path: Path, mime_type: str):
        try:
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Internal Error: {e}")


class VaultServer(ThreadingHTTPServer):
    def __init__(self, host: str = DEFAULT_SERVER_HOST, port: int = DEFAULT_SERVER_PORT, database: Optional[VaultDatabase] = None):
        super().__init__((host, port), VaultRequestHandler)
        self.database = database or VaultDatabase()
        self.synchronizer = VaultSynchronizer(self.database)
        self.exporter = HistoryExporter(self.database)
