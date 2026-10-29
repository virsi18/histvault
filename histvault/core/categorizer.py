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

from urllib.parse import urlparse
from histvault.constants import DEFAULT_CATEGORY_RULES


class DomainCategorizer:
    def __init__(self, rules: dict = None):
        self.rules = rules or DEFAULT_CATEGORY_RULES

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extracts normalized hostname from a URL."""
        if not url:
            return ""
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            if ":" in netloc:
                netloc = netloc.split(":")[0]
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc or parsed.path.split("/")[0].lower()
        except Exception:
            return ""

    def categorize(self, domain: str) -> str:
        """Determines the appropriate high-level category for a domain."""
        if not domain:
            return "Uncategorized"

        for category, domain_list in self.rules.items():
            for d in domain_list:
                if domain == d or domain.endswith("." + d):
                    return category

        # Common heuristics
        if domain.endswith(".edu") or domain.endswith(".ac.id") or "learn" in domain:
            return "Education & Academic"
        if domain.endswith(".gov") or domain.endswith(".go.id"):
            return "Government & Public"

        return "General Browsing"
