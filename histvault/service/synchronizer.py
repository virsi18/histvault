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

from typing import Optional, List
from histvault.core.database import VaultDatabase
from histvault.core.extractor import BrowserExtractor
from histvault.core.models import SyncReport, BrowserProfile


class VaultSynchronizer:
    """
    Coordinates multi-browser extraction, upserts new/updated history,
    and identifies deleted browser history while preserving it permanently.
    """

    def __init__(self, database: Optional[VaultDatabase] = None, extractor: Optional[BrowserExtractor] = None):
        self.database = database or VaultDatabase()
        self.extractor = extractor or BrowserExtractor()

    def sync_all(self, custom_profiles: Optional[List[BrowserProfile]] = None) -> SyncReport:
        """
        Executes a complete synchronization across all detected or specified profiles.
        """
        profiles = custom_profiles if custom_profiles is not None else self.extractor.discover_profiles()
        report = SyncReport(profiles_scanned=len(profiles))

        for profile in profiles:
            try:
                entries = self.extractor.extract_from_profile(profile)
                active_urls = set()

                for entry in entries:
                    active_urls.add(entry.url)
                    is_new, is_updated = self.database.upsert_url(entry)
                    if is_new:
                        report.new_urls += 1
                    elif is_updated:
                        report.updated_urls += 1

                # Detect if any previously recorded URLs have been deleted from this profile
                newly_deleted = self.database.mark_missing_as_deleted(
                    profile.browser_name, profile.profile_name, active_urls
                )
                report.newly_detected_deleted += newly_deleted

            except Exception as e:
                report.errors.append(f"Failed sync for {profile.identifier}: {e}")

        stats = self.database.get_stats()
        report.total_preserved_urls = stats["total_urls"]

        # Record synchronization event
        self.database.log_sync(report)

        return report
