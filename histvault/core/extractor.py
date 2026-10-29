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
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from histvault.constants import get_browser_search_paths, WEBKIT_EPOCH_DIFF_SECONDS
from histvault.core.models import BrowserProfile, HistoryEntry
from histvault.core.categorizer import DomainCategorizer


class BrowserExtractor:
    """
    Discovers installed browsers and extracts history snapshots
    without triggering file-lock conflicts.
    """

    def __init__(self, categorizer: Optional[DomainCategorizer] = None):
        self.categorizer = categorizer or DomainCategorizer()

    def discover_profiles(self) -> List[BrowserProfile]:
        """Scans filesystem to locate all accessible browser profiles."""
        profiles = []
        search_paths = get_browser_search_paths()

        for browser_name, roots in search_paths.items():
            for root in roots:
                if not root.exists():
                    continue

                if browser_name in ("chrome", "edge", "brave", "vivaldi"):
                    # Scan Default, Profile 1, Profile 2, etc.
                    for item in root.iterdir():
                        if item.is_dir():
                            hist_file = item / "History"
                            if hist_file.exists() and hist_file.is_file():
                                profiles.append(BrowserProfile(
                                    browser_name=browser_name.capitalize(),
                                    profile_name=item.name,
                                    history_file_path=str(hist_file)
                                ))
                elif browser_name == "firefox":
                    # Scan Firefox profiles directory
                    for item in root.iterdir():
                        if item.is_dir():
                            places_file = item / "places.sqlite"
                            if places_file.exists() and places_file.is_file():
                                profiles.append(BrowserProfile(
                                    browser_name="Firefox",
                                    profile_name=item.name,
                                    history_file_path=str(places_file)
                                ))
                elif browser_name == "opera":
                    hist_file = root / "History"
                    if hist_file.exists() and hist_file.is_file():
                        profiles.append(BrowserProfile(
                            browser_name="Opera",
                            profile_name="Default",
                            history_file_path=str(hist_file)
                        ))

        return profiles

    def extract_from_profile(self, profile: BrowserProfile) -> List[HistoryEntry]:
        """
        Extracts history entries by safely snapshotting the database file.
        """
        source_path = Path(profile.history_file_path)
        if not source_path.exists():
            return []

        entries: List[HistoryEntry] = []
        temp_fd, temp_path = tempfile.mkstemp(prefix=f"histvault_{profile.browser_name}_", suffix=".db")
        os.close(temp_fd)

        try:
            # Safe shadow copy to bypass active browser file lock
            shutil.copyfile(str(source_path), temp_path)

            if profile.browser_name.lower() == "firefox":
                entries = self._extract_firefox(temp_path, profile)
            else:
                entries = self._extract_chromium(temp_path, profile)

        except Exception as e:
            # If database copy or read failed (e.g. permission or corruption)
            print(f"[EXTRACTOR] Error extracting from {profile.identifier}: {e}")
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

        return entries

    def _extract_chromium(self, db_path: str, profile: BrowserProfile) -> List[HistoryEntry]:
        entries = []
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url, title, visit_count, last_visit_time
                FROM urls
                WHERE url IS NOT NULL AND url != ''
                ORDER BY last_visit_time DESC;
            """)
            rows = cursor.fetchall()

            for r in rows:
                raw_url = r["url"]
                # Skip internal scheme URLs if desired, or keep them
                title = r["title"] or ""
                visit_count = r["visit_count"] or 1
                raw_time = r["last_visit_time"] or 0

                # Convert WebKit timestamp (microseconds since 1601) to ISO UTC
                last_visit_iso = None
                if raw_time > 0:
                    try:
                        seconds = (raw_time / 1_000_000) - WEBKIT_EPOCH_DIFF_SECONDS
                        if seconds > 0:
                            last_visit_iso = datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
                    except (OverflowError, ValueError):
                        pass

                domain = self.categorizer.extract_domain(raw_url)
                category = self.categorizer.categorize(domain)

                entries.append(HistoryEntry(
                    url=raw_url,
                    title=title,
                    browser_name=profile.browser_name,
                    profile_name=profile.profile_name,
                    domain=domain,
                    category=category,
                    visit_count=visit_count,
                    first_visit_utc=last_visit_iso,
                    last_visit_utc=last_visit_iso
                ))
        finally:
            conn.close()

        return entries

    def _extract_firefox(self, db_path: str, profile: BrowserProfile) -> List[HistoryEntry]:
        entries = []
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url, title, visit_count, last_visit_date
                FROM moz_places
                WHERE url IS NOT NULL AND url != '' AND visit_count > 0
                ORDER BY last_visit_date DESC;
            """)
            rows = cursor.fetchall()

            for r in rows:
                raw_url = r["url"]
                title = r["title"] or ""
                visit_count = r["visit_count"] or 1
                raw_time = r["last_visit_date"] or 0

                # Firefox uses microseconds since Jan 1, 1970
                last_visit_iso = None
                if raw_time > 0:
                    try:
                        seconds = raw_time / 1_000_000
                        last_visit_iso = datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
                    except (OverflowError, ValueError):
                        pass

                domain = self.categorizer.extract_domain(raw_url)
                category = self.categorizer.categorize(domain)

                entries.append(HistoryEntry(
                    url=raw_url,
                    title=title,
                    browser_name=profile.browser_name,
                    profile_name=profile.profile_name,
                    domain=domain,
                    category=category,
                    visit_count=visit_count,
                    first_visit_utc=last_visit_iso,
                    last_visit_utc=last_visit_iso
                ))
        finally:
            conn.close()

        return entries
