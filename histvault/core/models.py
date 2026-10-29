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

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


@dataclass
class BrowserProfile:
    browser_name: str
    profile_name: str
    history_file_path: str
    is_accessible: bool = True

    @property
    def identifier(self) -> str:
        return f"{self.browser_name.lower()}:{self.profile_name.lower()}"


@dataclass
class HistoryEntry:
    url: str
    title: str
    browser_name: str
    profile_name: str
    domain: str
    category: str = "Uncategorized"
    visit_count: int = 1
    first_visit_utc: Optional[str] = None
    last_visit_utc: Optional[str] = None
    is_deleted_from_browser: bool = False
    deleted_detected_at: Optional[str] = None
    tags: str = ""
    notes: str = ""
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "browser_name": self.browser_name,
            "profile_name": self.profile_name,
            "domain": self.domain,
            "category": self.category,
            "visit_count": self.visit_count,
            "first_visit_utc": self.first_visit_utc,
            "last_visit_utc": self.last_visit_utc,
            "is_deleted_from_browser": self.is_deleted_from_browser,
            "deleted_detected_at": self.deleted_detected_at,
            "tags": self.tags,
            "notes": self.notes,
        }


@dataclass
class SyncReport:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    profiles_scanned: int = 0
    new_urls: int = 0
    updated_urls: int = 0
    newly_detected_deleted: int = 0
    total_preserved_urls: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "profiles_scanned": self.profiles_scanned,
            "new_urls": self.new_urls,
            "updated_urls": self.updated_urls,
            "newly_detected_deleted": self.newly_detected_deleted,
            "total_preserved_urls": self.total_preserved_urls,
            "errors": self.errors,
        }
