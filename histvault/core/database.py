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

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from histvault.constants import DEFAULT_DB_PATH
from histvault.core.models import HistoryEntry


class VaultDatabase:
    """
    Persistent, thread-safe SQLite database preserving browser history.
    Guarantees that history deleted from the browser remains permanently archived.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for concurrent reads & fast writes
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            self._local.conn = conn
        return self._local.conn

    def _init_schema(self):
        conn = self.get_connection()
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    browser_name TEXT NOT NULL,
                    profile_name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    domain TEXT NOT NULL,
                    category TEXT DEFAULT 'Uncategorized',
                    visit_count INTEGER DEFAULT 1,
                    first_visit_utc TEXT,
                    last_visit_utc TEXT,
                    is_deleted_from_browser INTEGER DEFAULT 0,
                    deleted_detected_at TEXT,
                    tags TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(browser_name, profile_name, url)
                );
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_urls_domain ON urls(domain);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_urls_category ON urls(category);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_urls_deleted ON urls(is_deleted_from_browser);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_urls_last_visit ON urls(last_visit_utc DESC);
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    scanned_profiles INTEGER DEFAULT 0,
                    new_urls INTEGER DEFAULT 0,
                    updated_urls INTEGER DEFAULT 0,
                    newly_detected_deleted INTEGER DEFAULT 0,
                    total_preserved_urls INTEGER DEFAULT 0
                );
            """)

            # Full-Text Search Virtual Table
            try:
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS urls_fts USING fts5(
                        title, url, domain, notes, content='urls', content_rowid='id'
                    );
                """)
                # Triggers to keep FTS index synchronized
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS urls_ai AFTER INSERT ON urls BEGIN
                        INSERT INTO urls_fts(rowid, title, url, domain, notes)
                        VALUES (new.id, new.title, new.url, new.domain, new.notes);
                    END;
                """)
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS urls_ad AFTER DELETE ON urls BEGIN
                        INSERT INTO urls_fts(urls_fts, rowid, title, url, domain, notes)
                        VALUES('delete', old.id, old.title, old.url, old.domain, old.notes);
                    END;
                """)
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS urls_au AFTER UPDATE ON urls BEGIN
                        INSERT INTO urls_fts(urls_fts, rowid, title, url, domain, notes)
                        VALUES('delete', old.id, old.title, old.url, old.domain, old.notes);
                        INSERT INTO urls_fts(rowid, title, url, domain, notes)
                        VALUES (new.id, new.title, new.url, new.domain, new.notes);
                    END;
                """)
            except Exception:
                # Fallback if SQLite build lacks FTS5
                pass

    def close(self):
        """Closes thread-local database connection if open."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None

    def upsert_url(self, entry: HistoryEntry) -> Tuple[bool, bool]:
        """
        Inserts or updates a URL.
        Returns (is_new, is_updated).
        If the URL was previously marked as deleted, and now reappears, we unmark it.
        """
        conn = self.get_connection()
        now_str = datetime.now(timezone.utc).isoformat()

        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, visit_count, first_visit_utc, last_visit_utc, is_deleted_from_browser
                FROM urls
                WHERE browser_name = ? AND profile_name = ? AND url = ?
            """, (entry.browser_name, entry.profile_name, entry.url))
            existing = cursor.fetchone()

            if existing is None:
                # Fresh entry
                cursor.execute("""
                    INSERT INTO urls (
                        browser_name, profile_name, url, title, domain, category,
                        visit_count, first_visit_utc, last_visit_utc,
                        is_deleted_from_browser, deleted_detected_at, tags, notes,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, ?, ?, ?)
                """, (
                    entry.browser_name, entry.profile_name, entry.url, entry.title or "",
                    entry.domain, entry.category, max(1, entry.visit_count),
                    entry.first_visit_utc or now_str, entry.last_visit_utc or now_str,
                    entry.tags or "", entry.notes or "", now_str, now_str
                ))
                return (True, False)
            else:
                # Existing entry: update title if better, update visit_count, update dates
                current_id = existing["id"]
                current_visits = existing["visit_count"]
                current_first = existing["first_visit_utc"]
                current_last = existing["last_visit_utc"]
                was_deleted = existing["is_deleted_from_browser"]

                new_count = max(current_visits, entry.visit_count)
                new_title = entry.title if entry.title else None
                new_first = min(filter(None, [current_first, entry.first_visit_utc])) if (current_first or entry.first_visit_utc) else now_str
                new_last = max(filter(None, [current_last, entry.last_visit_utc])) if (current_last or entry.last_visit_utc) else now_str

                cursor.execute("""
                    UPDATE urls SET
                        title = COALESCE(?, title),
                        visit_count = ?,
                        first_visit_utc = ?,
                        last_visit_utc = ?,
                        is_deleted_from_browser = 0,
                        deleted_detected_at = NULL,
                        category = CASE WHEN category = 'Uncategorized' THEN ? ELSE category END,
                        updated_at = ?
                    WHERE id = ?
                """, (new_title, new_count, new_first, new_last, entry.category, now_str, current_id))
                return (False, True)

    def mark_missing_as_deleted(self, browser_name: str, profile_name: str, active_urls: Set[str]) -> int:
        """
        Compares active URLs present in the browser with the Vault.
        Any URL in the Vault that is absent in the browser's current database
        is flagged as is_deleted_from_browser = 1.
        NEVER drops or removes any data!
        Returns the number of newly detected deleted items.
        """
        conn = self.get_connection()
        now_str = datetime.now(timezone.utc).isoformat()
        newly_deleted_count = 0

        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, url, is_deleted_from_browser
                FROM urls
                WHERE browser_name = ? AND profile_name = ?
            """, (browser_name, profile_name))
            rows = cursor.fetchall()

            for row in rows:
                url = row["url"]
                row_id = row["id"]
                already_deleted = bool(row["is_deleted_from_browser"])

                if url not in active_urls and not already_deleted:
                    cursor.execute("""
                        UPDATE urls SET
                            is_deleted_from_browser = 1,
                            deleted_detected_at = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (now_str, now_str, row_id))
                    newly_deleted_count += 1

        return newly_deleted_count

    def search_urls(
        self,
        query: str = "",
        category: Optional[str] = None,
        browser: Optional[str] = None,
        deleted_only: bool = False,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[HistoryEntry]:
        """
        Search entries with keyword filtering, categories, and deletion flags.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT id, browser_name, profile_name, url, title, domain, category,
                   visit_count, first_visit_utc, last_visit_utc,
                   is_deleted_from_browser, deleted_detected_at, tags, notes
            FROM urls
            WHERE 1=1
        """
        params: List[Any] = []

        if query:
            clean_q = f"%{query.strip()}%"
            sql += " AND (title LIKE ? OR url LIKE ? OR domain LIKE ? OR notes LIKE ?)"
            params.extend([clean_q, clean_q, clean_q, clean_q])

        if category and category.lower() != "all":
            sql += " AND category = ?"
            params.append(category)

        if browser and browser.lower() != "all":
            sql += " AND LOWER(browser_name) = ?"
            params.append(browser.lower())

        if deleted_only:
            sql += " AND is_deleted_from_browser = 1"
        elif active_only:
            sql += " AND is_deleted_from_browser = 0"

        sql += " ORDER BY COALESCE(last_visit_utc, updated_at) DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        return [
            HistoryEntry(
                id=r["id"],
                browser_name=r["browser_name"],
                profile_name=r["profile_name"],
                url=r["url"],
                title=r["title"] or "",
                domain=r["domain"],
                category=r["category"],
                visit_count=r["visit_count"],
                first_visit_utc=r["first_visit_utc"],
                last_visit_utc=r["last_visit_utc"],
                is_deleted_from_browser=bool(r["is_deleted_from_browser"]),
                deleted_detected_at=r["deleted_detected_at"],
                tags=r["tags"] or "",
                notes=r["notes"] or "",
            )
            for r in rows
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Calculates vault statistical telemetry."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM urls;")
        total_urls = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS deleted_cnt FROM urls WHERE is_deleted_from_browser = 1;")
        deleted_urls = cursor.fetchone()["deleted_cnt"]

        cursor.execute("SELECT COUNT(DISTINCT domain) AS domain_cnt FROM urls;")
        unique_domains = cursor.fetchone()["domain_cnt"]

        cursor.execute("SELECT SUM(visit_count) AS total_visits FROM urls;")
        total_visits = cursor.fetchone()["total_visits"] or 0

        cursor.execute("""
            SELECT browser_name, COUNT(*) AS count
            FROM urls
            GROUP BY browser_name
            ORDER BY count DESC;
        """)
        browser_breakdown = {r["browser_name"]: r["count"] for r in cursor.fetchall()}

        cursor.execute("""
            SELECT category, COUNT(*) AS count
            FROM urls
            GROUP BY category
            ORDER BY count DESC;
        """)
        category_breakdown = {r["category"]: r["count"] for r in cursor.fetchall()}

        return {
            "total_urls": total_urls,
            "deleted_preserved_urls": deleted_urls,
            "active_urls": total_urls - deleted_urls,
            "unique_domains": unique_domains,
            "total_visits": total_visits,
            "browser_breakdown": browser_breakdown,
            "category_breakdown": category_breakdown,
        }

    def get_top_domains(self, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT domain, SUM(visit_count) AS total_visits, COUNT(*) AS entry_count
            FROM urls
            GROUP BY domain
            ORDER BY total_visits DESC
            LIMIT ?;
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]

    def log_sync(self, report: Any):
        conn = self.get_connection()
        with conn:
            conn.execute("""
                INSERT INTO sync_history (
                    timestamp, scanned_profiles, new_urls, updated_urls,
                    newly_detected_deleted, total_preserved_urls
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                report.timestamp, report.profiles_scanned, report.new_urls,
                report.updated_urls, report.newly_detected_deleted,
                report.total_preserved_urls
            ))
