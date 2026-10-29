"""
Integration test verifying browser history preservation after browser history deletion.
"""

import unittest
import sqlite3
import tempfile
from pathlib import Path
from histvault.core.database import VaultDatabase
from histvault.core.extractor import BrowserExtractor
from histvault.core.models import BrowserProfile
from histvault.service.synchronizer import VaultSynchronizer


class TestSynchronizerDeletionPreservation(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        # 1. Setup mock Vault DB
        self.vault_db_path = self.dir_path / "vault.db"
        self.vault_db = VaultDatabase(self.vault_db_path)

        # 2. Setup mock Chromium browser history DB
        self.mock_browser_db = self.dir_path / "History"
        self._create_mock_chromium_db(self.mock_browser_db)

        self.mock_profile = BrowserProfile(
            browser_name="Chrome",
            profile_name="Default",
            history_file_path=str(self.mock_browser_db)
        )

        self.synchronizer = VaultSynchronizer(
            database=self.vault_db,
            extractor=BrowserExtractor()
        )

    def tearDown(self):
        self.vault_db.close()
        self.temp_dir.cleanup()

    def _create_mock_chromium_db(self, path: Path):
        conn = sqlite3.connect(str(path))
        with conn:
            conn.execute("""
                CREATE TABLE urls (
                    id INTEGER PRIMARY KEY,
                    url TEXT,
                    title TEXT,
                    visit_count INTEGER,
                    typed_count INTEGER,
                    last_visit_time INTEGER,
                    hidden INTEGER
                );
            """)
            # Insert 3 sample URLs
            conn.execute("""
                INSERT INTO urls (url, title, visit_count, last_visit_time) VALUES
                ('https://github.com', 'GitHub', 10, 13340000000000000),
                ('https://python.org', 'Python Software Foundation', 5, 13340000000000000),
                ('https://secret-site.com', 'Confidential Research', 2, 13340000000000000);
            """)
        conn.close()

    def test_full_deletion_preservation_lifecycle(self):
        # Step 1: Initial Sync
        report1 = self.synchronizer.sync_all([self.mock_profile])
        self.assertEqual(report1.new_urls, 3)
        self.assertEqual(report1.total_preserved_urls, 3)
        self.assertEqual(report1.newly_detected_deleted, 0)

        # All 3 records should be ACTIVE in Vault
        active_before = self.vault_db.search_urls(active_only=True)
        self.assertEqual(len(active_before), 3)

        # Step 2: Simulate User Clearing Browsing History in Browser!
        # User deletes 'https://secret-site.com' and 'https://python.org' in Chrome
        conn = sqlite3.connect(str(self.mock_browser_db))
        with conn:
            conn.execute("DELETE FROM urls WHERE url != 'https://github.com';")
        conn.close()

        # Step 3: Run Sync again
        report2 = self.synchronizer.sync_all([self.mock_profile])
        self.assertEqual(report2.new_urls, 0)
        self.assertEqual(report2.newly_detected_deleted, 2)
        # TOTAL IN VAULT MUST STILL BE 3! Zero data lost!
        self.assertEqual(report2.total_preserved_urls, 3)

        # Step 4: Verify that deleted items are flagged as DELETED FROM BROWSER, but safely kept
        deleted_records = self.vault_db.search_urls(deleted_only=True)
        self.assertEqual(len(deleted_records), 2)
        deleted_urls = {r.url for r in deleted_records}
        self.assertIn("https://secret-site.com", deleted_urls)
        self.assertIn("https://python.org", deleted_urls)

        # Only github.com is active
        active_after = self.vault_db.search_urls(active_only=True)
        self.assertEqual(len(active_after), 1)
        self.assertEqual(active_after[0].url, "https://github.com")

        print("\n [TEST VERIFIED] Browser history purged, but 100% preserved in HistVault!")


if __name__ == "__main__":
    unittest.main()
