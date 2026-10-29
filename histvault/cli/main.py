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
import argparse
import time
from pathlib import Path
from histvault.constants import APP_NAME, APP_VERSION, DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT, DEFAULT_DB_PATH
from histvault.core.database import VaultDatabase
from histvault.service.synchronizer import VaultSynchronizer
from histvault.service.watcher import VaultWatcherDaemon
from histvault.service.exporter import HistoryExporter
from histvault.server.app import VaultServer


def print_banner():
    banner = f"""
  _    _ _     _  __      __          _ _   
 | |  | (_)   | | \\ \\    / /         | | |  
 | |__| |_ ___| |_ \\ \\  / /_ _ _   _| | |_ 
 |  __  | / __| __| \\ \\/ / _` | | | | | __|
 | |  | | \\__ \\ |_   \\  / (_| | |_| | | |_ 
 |_|  |_|_|___/\\__|   \\/ \\__,_|\\__,_|_|\\__|
 >> AUTOMATED BROWSER HISTORY PRESERVATION VAULT v{APP_VERSION} <<
 >> PRESERVES BROWSER HISTORY EVEN WHEN DELETED <<
    """
    print(banner)


def cmd_sync(args, db: VaultDatabase):
    print(">>> Scanning installed browsers and synchronizing history into Vault...")
    sync = VaultSynchronizer(db)
    report = sync.sync_all()

    print(f"\n[SYNC COMPLETE]")
    print(f" * Profiles Scanned:          {report.profiles_scanned}")
    print(f" * New URLs Archived:         {report.new_urls}")
    print(f" * Updated URLs:              {report.updated_urls}")
    print(f" * Newly Detected Deleted:    {report.newly_detected_deleted} (Preserved in Vault!)")
    print(f" * Total Records in Vault:    {report.total_preserved_urls}")

    if report.errors:
        print("\nWarnings:")
        for err in report.errors:
            print(f" ! {err}")


def cmd_stats(args, db: VaultDatabase):
    stats = db.get_stats()
    top_domains = db.get_top_domains(limit=5)

    print("\n================ HISTVAULT STATISTICS ================")
    print(f" Total Preserved History:     {stats['total_urls']:,} entries")
    print(f" Deleted in Browser:          {stats['deleted_preserved_urls']:,} entries (100% Preserved)")
    print(f" Active in Browser:           {stats['active_urls']:,} entries")
    print(f" Total Recorded Visits:       {stats['total_visits']:,} visits")
    print(f" Unique Domains:              {stats['unique_domains']:,}")

    print("\n--- Browser Breakdown ---")
    for b_name, count in stats.get("browser_breakdown", {}).items():
        print(f"  * {b_name:<15}: {count:,} records")

    print("\n--- Category Breakdown ---")
    for cat_name, count in stats.get("category_breakdown", {}).items():
        print(f"  * {cat_name:<25}: {count:,} records")

    print("\n--- Top Visited Domains ---")
    for d in top_domains:
        print(f"  * {d['domain']:<25}: {d['total_visits']:,} visits ({d['entry_count']} URLs)")
    print("======================================================\n")


def cmd_list(args, db: VaultDatabase):
    entries = db.search_urls(
        query=args.query or "",
        category=args.category,
        deleted_only=args.deleted_only,
        limit=args.limit
    )

    if not entries:
        print("No matching records found in Vault.")
        return

    print(f"\nDisplaying {len(entries)} entries:\n")
    print(f"{'STATUS':<20} | {'BROWSER':<8} | {'DOMAIN':<22} | {'VISITS':<6} | TITLE & URL")
    print("-" * 105)

    for e in entries:
        status = "🔴 DELETED (SAVED)" if e.is_deleted_from_browser else "🟢 ACTIVE"
        title = (e.title or e.url)[:35]
        print(f"{status:<20} | {e.browser_name:<8} | {e.domain[:22]:<22} | {e.visit_count:<6} | {title} -> {e.url}")


def cmd_serve(args, db: VaultDatabase):
    host = args.host
    port = args.port

    print_banner()
    # Trigger initial sync on startup
    sync = VaultSynchronizer(db)
    print("Performing initial background sync...")
    report = sync.sync_all()
    print(f"Loaded {report.total_preserved_urls} preserved records into Vault.")

    server = VaultServer(host=host, port=port, database=db)
    print(f"\n🚀 HistVault Web GUI running at: http://{host}:{port}")
    print("Press Ctrl+C to terminate server.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down HistVault server.")
        server.server_close()


def cmd_watch(args, db: VaultDatabase):
    print(f">>> Launching HistVault background daemon (polling interval: {args.interval}s)...")
    sync = VaultSynchronizer(db)
    watcher = VaultWatcherDaemon(sync, interval_seconds=args.interval)

    def on_sync(rep):
        if rep.new_urls > 0 or rep.newly_detected_deleted > 0:
            print(f"[{time.strftime('%X')}] Auto-sync: +{rep.new_urls} new, {rep.newly_detected_deleted} deleted preserved.")

    watcher.on_sync_callback = on_sync
    watcher.start()
    print("Daemon active. Monitoring browser database changes. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping daemon...")
        watcher.stop()
        print("Daemon stopped.")


def cmd_export(args, db: VaultDatabase):
    exporter = HistoryExporter(db)
    out_path = Path(args.output)
    fmt = args.format.lower()

    if fmt == "csv":
        count = exporter.export_csv(out_path, deleted_only=args.deleted_only)
    elif fmt == "html":
        count = exporter.export_html(out_path, deleted_only=args.deleted_only)
    elif fmt in ("md", "markdown"):
        count = exporter.export_markdown(out_path, deleted_only=args.deleted_only)
    else:
        count = exporter.export_json(out_path, deleted_only=args.deleted_only)

    print(f"[SUCCESS] Exported {count} records to {out_path.resolve()} (format: {fmt})")


def main():
    parser = argparse.ArgumentParser(
        prog="histvault",
        description="HistVault: Automated Browser History Preservation Vault & Anti-Deletion Archive"
    )
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Custom vault SQLite database path")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # sync
    subparsers.add_parser("sync", help="Synchronize history from all installed browsers")

    # stats
    subparsers.add_parser("stats", help="Display Vault statistics and top domains")

    # list
    p_list = subparsers.add_parser("list", help="List preserved history entries")
    p_list.add_argument("-q", "--query", type=str, help="Search query")
    p_list.add_argument("-c", "--category", type=str, help="Filter by category")
    p_list.add_argument("--deleted-only", action="store_true", help="Show only history that was deleted from browser")
    p_list.add_argument("-n", "--limit", type=int, default=20, help="Number of records to show")

    # serve
    p_serve = subparsers.add_parser("serve", help="Launch interactive Web GUI dashboard")
    p_serve.add_argument("--host", type=str, default=DEFAULT_SERVER_HOST, help="Server host")
    p_serve.add_argument("--port", type=int, default=DEFAULT_SERVER_PORT, help="Server port")

    # watch
    p_watch = subparsers.add_parser("watch", help="Run background daemon monitoring browser files")
    p_watch.add_argument("-i", "--interval", type=int, default=30, help="Polling interval in seconds")

    # export
    p_export = subparsers.add_parser("export", help="Export history archive to file")
    p_export.add_argument("-f", "--format", choices=["json", "csv", "html", "md"], default="html", help="Export format")
    p_export.add_argument("-o", "--output", type=str, required=True, help="Destination output file path")
    p_export.add_argument("--deleted-only", action="store_true", help="Export only deleted entries")

    args = parser.parse_args()
    db = VaultDatabase(Path(args.db))

    if args.command == "sync":
        cmd_sync(args, db)
    elif args.command == "stats":
        cmd_stats(args, db)
    elif args.command == "list":
        cmd_list(args, db)
    elif args.command == "serve":
        cmd_serve(args, db)
    elif args.command == "watch":
        cmd_watch(args, db)
    elif args.command == "export":
        cmd_export(args, db)
    else:
        print_banner()
        cmd_stats(args, db)
        print("Use --help to view available commands: sync, serve, list, stats, watch, export.")


if __name__ == "__main__":
    main()
