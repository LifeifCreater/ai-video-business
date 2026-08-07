import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import search_console_automation as automation


class SearchConsoleSummaryTests(unittest.TestCase):
    def test_api_failures_are_not_reported_as_zero_errors(self):
        pages = [
            {
                "url": f"https://example.com/{index}",
                "publishedAt": None,
                "inspectionStatus": None,
                "errorInfo": "HTTPError",
                "ownerActionRequired": False,
                "notes": "",
                "googleCanonical": None,
                "userCanonical": None,
                "sitemapIncluded": True,
                "retryAfter": "2026-08-08T09:00:00+09:00",
            }
            for index in range(15)
        ]
        with tempfile.TemporaryDirectory() as directory:
            morning = Path(directory) / "morning-brief.json"
            morning.write_text('{"searchConsole": null}\n', encoding="utf-8")
            original = automation.MORNING
            automation.MORNING = morning
            try:
                automation.update_morning({"pages": pages}, datetime.fromisoformat("2026-08-07T09:00:00+09:00"))
            finally:
                automation.MORNING = original
            summary = json.loads(morning.read_text(encoding="utf-8"))["searchConsole"]
        self.assertEqual(summary["status"], "取得失敗")
        self.assertEqual(summary["errorCount"], 15)
        self.assertEqual(summary["apiFailureCount"], 15)
        self.assertIsNone(summary["indexedCount"])
        self.assertIsNone(summary["notIndexedCount"])


if __name__ == "__main__":
    unittest.main()
