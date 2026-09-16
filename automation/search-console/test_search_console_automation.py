import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import search_console_automation as automation


class SearchConsoleSummaryTests(unittest.TestCase):
    def test_recent_success_skips_network_but_metadata_errors_still_fail(self):
        timestamp = datetime.fromisoformat("2026-09-16T15:30:00+09:00")
        data = {"lastSitemapSubmissionAt": "2026-09-16T15:09:00+09:00",
                "pages": [{"url": "https://framepact.jp/", "lastModified": "2026-09-16"}]}
        with patch.object(automation, "load_register", return_value=data), \
             patch.object(automation, "now", return_value=timestamp), \
             patch.object(automation, "sitemap_rows", return_value=[("https://framepact.jp/", "2026-09-16")]), \
             patch.object(automation, "credentials") as credentials, \
             patch.object(automation, "save") as save:
            automation.submit(True)
            credentials.assert_not_called()
            save.assert_not_called()
            data["pages"][0]["lastModified"] = "2026-09-15"
            with self.assertRaisesRegex(RuntimeError, "metadata mismatch"):
                automation.submit(True)

    def test_future_retry_date_suppresses_owner_action_retry(self):
        page = {
            "ownerActionRequired": True,
            "retryAfter": "2026-08-20T09:00:00+09:00",
            "inspectionStatus": None,
            "publishedAt": None,
            "inspectedAt": "2026-08-14T09:00:00+09:00",
        }
        self.assertFalse(automation.eligible(page, datetime.fromisoformat("2026-08-14T09:00:00+09:00")))
        self.assertTrue(automation.eligible(page, datetime.fromisoformat("2026-08-20T09:00:00+09:00")))

    def test_403_becomes_an_immediate_owner_action(self):
        page = {
            "url": "https://example.com/",
            "sitemapIncluded": True,
            "robotsTxtState": None,
            "indexingState": None,
            "googleCanonical": None,
            "userCanonical": None,
            "pageFetchState": None,
            "consecutiveApiFailures": 1,
            "errorInfo": "HTTPError:HTTP 403",
            "publishedAt": None,
            "inspectionStatus": None,
            "coverageState": None,
            "notes": "",
        }
        automation.judge(page, datetime.fromisoformat("2026-08-14T09:00:00+09:00"))
        self.assertTrue(page["ownerActionRequired"])
        self.assertIn("API認証・権限エラー", page["notes"])

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
