"""
Unit tests for VaultDatabase.
"""

import unittest
import tempfile
from pathlib import Path
from histvault.core.database import VaultDatabase
from histvault.core.models import HistoryEntry


class TestVaultDatabase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_vault.db"
        self.db = VaultDatabase(self.db_path)

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def test_upsert_and_retrieve(self):
        entry = HistoryEntry(
            url="https://github.com/virsi18/histvault",
            title="HistVault GitHub Repository",
            browser_name="Chrome",
            profile_name="Default",
            domain="github.com",
            category="Development & Tech",
            visit_count=5
        )

        is_new, is_updated = self.db.upsert_url(entry)
        self.assertTrue(is_new)
        self.assertFalse(is_updated)

        results = self.db.search_urls(query="HistVault")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].domain, "github.com")
        self.assertEqual(results[0].visit_count, 5)

    def test_preservation_when_deleted(self):
        # Insert 2 URLs
        e1 = HistoryEntry(url="https://google.com", title="Google", browser_name="Edge", profile_name="Default", domain="google.com")
        e2 = HistoryEntry(url="https://secret-link.com", title="Secret", browser_name="Edge", profile_name="Default", domain="secret-link.com")

        self.db.upsert_url(e1)
        self.db.upsert_url(e2)

        # Simulate browser purge: only google.com remains in browser
        active_in_browser = {"https://google.com"}
        newly_deleted = self.db.mark_missing_as_deleted("Edge", "Default", active_in_browser)
        self.assertEqual(newly_deleted, 1)

        # Verify that secret-link.com is STILL in Vault, marked as deleted from browser
        deleted_records = self.db.search_urls(deleted_only=True)
        self.assertEqual(len(deleted_records), 1)
        self.assertEqual(deleted_records[0].url, "https://secret-link.com")
        self.assertTrue(deleted_records[0].is_deleted_from_browser)
        self.assertIsNotNone(deleted_records[0].deleted_detected_at)

        # Verify total stats
        stats = self.db.get_stats()
        self.assertEqual(stats["total_urls"], 2)
        self.assertEqual(stats["deleted_preserved_urls"], 1)
        self.assertEqual(stats["active_urls"], 1)


if __name__ == "__main__":
    unittest.main()
