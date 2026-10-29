"""
Unit tests for HistoryExporter.
"""

import unittest
import tempfile
import json
from pathlib import Path
from histvault.core.database import VaultDatabase
from histvault.core.models import HistoryEntry
from histvault.service.exporter import HistoryExporter


class TestHistoryExporter(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)
        self.db = VaultDatabase(self.dir_path / "vault.db")

        # Insert sample data
        self.db.upsert_url(HistoryEntry(
            url="https://github.com",
            title="GitHub",
            browser_name="Chrome",
            profile_name="Default",
            domain="github.com",
            category="Development & Tech",
            visit_count=42
        ))
        self.exporter = HistoryExporter(self.db)

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def test_export_json(self):
        out = self.dir_path / "export.json"
        count = self.exporter.export_json(out)
        self.assertEqual(count, 1)
        self.assertTrue(out.exists())

        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertIn("history", data)
        self.assertEqual(data["history"][0]["domain"], "github.com")

    def test_export_csv(self):
        out = self.dir_path / "export.csv"
        count = self.exporter.export_csv(out)
        self.assertEqual(count, 1)
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("github.com", content)

    def test_export_html(self):
        out = self.dir_path / "export.html"
        count = self.exporter.export_html(out)
        self.assertEqual(count, 1)
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("HistVault Preservation Archive", content)

    def test_export_markdown(self):
        out = self.dir_path / "export.md"
        count = self.exporter.export_markdown(out)
        self.assertEqual(count, 1)
        self.assertTrue(out.exists())
        content = out.read_text(encoding="utf-8")
        self.assertIn("`github.com`", content)


if __name__ == "__main__":
    unittest.main()
