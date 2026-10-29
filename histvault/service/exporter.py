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

import csv
import json
from pathlib import Path
from typing import Optional, List
from histvault.core.database import VaultDatabase
from histvault.core.models import HistoryEntry


class HistoryExporter:
    """
    Exports preserved browser history into multiple portable formats.
    """

    def __init__(self, database: Optional[VaultDatabase] = None):
        self.database = database or VaultDatabase()

    def export_json(self, output_path: Path, deleted_only: bool = False) -> int:
        entries = self.database.search_urls(limit=1000000, deleted_only=deleted_only)
        stats = self.database.get_stats()

        payload = {
            "metadata": {
                "generator": "HistVault",
                "total_records": len(entries),
                "filter_deleted_only": deleted_only,
                "stats": stats
            },
            "history": [e.to_dict() for e in entries]
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        return len(entries)

    def export_csv(self, output_path: Path, deleted_only: bool = False) -> int:
        entries = self.database.search_urls(limit=1000000, deleted_only=deleted_only)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Browser", "Profile", "Domain", "Category",
                "Visit Count", "Last Visit (UTC)", "Deleted In Browser",
                "Deleted Detected At", "Title", "URL"
            ])
            for e in entries:
                writer.writerow([
                    e.id, e.browser_name, e.profile_name, e.domain, e.category,
                    e.visit_count, e.last_visit_utc or "",
                    "YES" if e.is_deleted_from_browser else "NO",
                    e.deleted_detected_at or "",
                    e.title, e.url
                ])

        return len(entries)

    def export_markdown(self, output_path: Path, deleted_only: bool = False) -> int:
        entries = self.database.search_urls(limit=1000000, deleted_only=deleted_only)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# HistVault: Browser History Archive",
            f"Total Preserved Entries: {len(entries)}\n",
            "| Status | Browser | Domain | Title | Visits | Last Visited |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        for e in entries:
            status = "🔴 DELETED (PRESERVED)" if e.is_deleted_from_browser else "🟢 Active"
            safe_title = (e.title or "Untitled").replace("|", "-")
            lines.append(
                f"| {status} | {e.browser_name} | `{e.domain}` | [{safe_title}]({e.url}) | {e.visit_count} | {e.last_visit_utc or '-'} |"
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return len(entries)

    def export_html(self, output_path: Path, deleted_only: bool = False) -> int:
        entries = self.database.search_urls(limit=1000000, deleted_only=deleted_only)
        stats = self.database.get_stats()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        rows_html = []
        for e in entries:
            badge_class = "badge-deleted" if e.is_deleted_from_browser else "badge-active"
            badge_text = "PRESERVED FROM DELETION" if e.is_deleted_from_browser else "ACTIVE IN BROWSER"
            safe_title = (e.title or e.url).replace("<", "&lt;").replace(">", "&gt;")
            rows_html.append(f"""
                <tr>
                    <td><span class="badge {badge_class}">{badge_text}</span></td>
                    <td><strong>{e.browser_name}</strong></td>
                    <td><code>{e.domain}</code></td>
                    <td><a href="{e.url}" target="_blank" rel="noopener">{safe_title}</a></td>
                    <td>{e.category}</td>
                    <td>{e.visit_count}</td>
                    <td>{e.last_visit_utc or '-'}</td>
                </tr>
            """)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HistVault - Preserved Browser History Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; }}
        h1 {{ margin-bottom: 4px; }}
        .subtitle {{ color: #94a3b8; margin-bottom: 24px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .card {{ background: #1e293b; padding: 16px; border-radius: 8px; border: 1px solid #334155; }}
        .card-num {{ font-size: 24px; font-weight: bold; color: #38bdf8; }}
        .card-label {{ color: #94a3b8; font-size: 13px; }}
        table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #334155; font-size: 14px; }}
        th {{ background: #0f172a; color: #cbd5e1; font-weight: 600; }}
        a {{ color: #38bdf8; text-decoration: none; word-break: break-all; }}
        a:hover {{ text-decoration: underline; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        .badge-active {{ background: #065f46; color: #6ee7b7; }}
        .badge-deleted {{ background: #991b1b; color: #fca5a5; }}
    </style>
</head>
<body>
    <h1>HistVault Preservation Archive</h1>
    <p class="subtitle">Immutable browser history vault report | Generated automatically</p>
    <div class="stats-grid">
        <div class="card"><div class="card-num">{stats.get('total_urls', 0):,}</div><div class="card-label">Total Preserved Records</div></div>
        <div class="card"><div class="card-num" style="color: #f87171;">{stats.get('deleted_preserved_urls', 0):,}</div><div class="card-label">Deleted in Browser (Preserved)</div></div>
        <div class="card"><div class="card-num" style="color: #4ade80;">{stats.get('active_urls', 0):,}</div><div class="card-label">Active in Browser</div></div>
        <div class="card"><div class="card-num">{stats.get('unique_domains', 0):,}</div><div class="card-label">Unique Domains</div></div>
    </div>
    <table>
        <thead>
            <tr>
                <th>Status</th>
                <th>Browser</th>
                <th>Domain</th>
                <th>Title / URL</th>
                <th>Category</th>
                <th>Visits</th>
                <th>Last Visited (UTC)</th>
            </tr>
        </thead>
        <tbody>
            {"".join(rows_html)}
        </tbody>
    </table>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return len(entries)
