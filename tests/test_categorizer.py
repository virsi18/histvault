"""
Unit tests for DomainCategorizer.
"""

import unittest
from histvault.core.categorizer import DomainCategorizer


class TestDomainCategorizer(unittest.TestCase):

    def setUp(self):
        self.categorizer = DomainCategorizer()

    def test_extract_domain(self):
        self.assertEqual(
            self.categorizer.extract_domain("https://www.github.com/virsi18/histvault"),
            "github.com"
        )
        self.assertEqual(
            self.categorizer.extract_domain("http://docs.python.org:8080/3/library/"),
            "docs.python.org"
        )
        self.assertEqual(
            self.categorizer.extract_domain("https://sub.domain.tokopedia.com/product/123"),
            "sub.domain.tokopedia.com"
        )

    def test_categorize(self):
        self.assertEqual(self.categorizer.categorize("github.com"), "Development & Tech")
        self.assertEqual(self.categorizer.categorize("stackoverflow.com"), "Development & Tech")
        self.assertEqual(self.categorizer.categorize("youtube.com"), "Media & Streaming")
        self.assertEqual(self.categorizer.categorize("shopee.com"), "Shopping & Finance")
        self.assertEqual(self.categorizer.categorize("reddit.com"), "Social & Communication")
        self.assertEqual(self.categorizer.categorize("random-unknown-site.xyz"), "General Browsing")


if __name__ == "__main__":
    unittest.main()
