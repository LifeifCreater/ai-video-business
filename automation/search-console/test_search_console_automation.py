import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import search_console_automation as automation


class SearchConsoleSummaryTests(unittest.TestCase):
    def test_recent_success_skips_network_and_repairs_metadata(self):
        timestamp = datetime.fromisoformat("2026-09-16T15:30:00+09:00")
        data = {
            "lastSitemapSubmissionAt": "2026-09-16T15:09:00+09:00",
            "pages": [
                {
                    **automation.new_page(
                        "https://framepact.jp/",
                        "2026-09-15",
                        {"lastSitemapSubmissionAt": None},
                    ),
                    "lastModified": "2026-09-15",
                }
            ],
        }
        with patch.object(automation, "load_register", return_value=data), \
             patch.object(automation, "now", return_value=timestamp), \
             patch.object(
                 automation,
                 "sitemap_rows",
                 return_value=[("https://framepact.jp/", "2026-09-16")],
             ), \
             patch.object(automation, "credentials") as credentials, \
             patch.object(automation, "save") as save, \
             patch.object(automation, "update_morning") as update_morning:
            automation.submit(True)
            credentials.assert_not_called()
            save.assert_called_once()
            update_morning.assert_called_once()
            self.assertEqual(
                data["pages"][0]["lastModified"],
                "2026-09-16",
            )

    def test_future_retry_date_suppresses_owner_action_retry(self):
        page = {
            "ownerActionRequired": True,
            "retryAfter": "2026-08-20T09:00:00+09:00",
            "inspectionStatus": None,
            "publishedAt": None,
            "inspectedAt": "2026-08-14T09:00:00+09:00",
        }
        self.assertFalse(
            automation.eligible(
                page,
                datetime.fromisoformat("2026-08-14T09:00:00+09:00"),
            )
        )
        self.assertTrue(
            automation.eligible(
                page,
                datetime.fromisoformat("2026-08-20T09:00:00+09:00"),
            )
        )

    def test_uninspected_sitemap_page_is_immediately_eligible(self):
        page = automation.new_page(
            "https://framepact.jp/exhibition-video.html",
            "2026-09-08",
            {"lastSitemapSubmissionAt": None},
        )
        self.assertTrue(
            automation.eligible(
                page,
                datetime.fromisoformat("2026-09-17T09:00:00+09:00"),
            )
        )

    def test_sync_pages_adds_sitemap_url_without_deleting_history(self):
        data = {
            "lastSitemapSubmissionAt": None,
            "pages": [
                automation.new_page(
                    "https://framepact.jp/",
                    "2026-09-15",
                    {"lastSitemapSubmissionAt": None},
                ),
                automation.new_page(
                    "https://framepact.jp/legacy.html",
                    "2026-08-01",
                    {"lastSitemapSubmissionAt": None},
                ),
            ],
        }
        added = automation.sync_pages(
            data,
            [
                ("https://framepact.jp/", "2026-09-15"),
                (
                    "https://framepact.jp/exhibition-video.html",
                    "2026-09-08",
                ),
            ],
        )
        self.assertEqual(
            added,
            ["https://framepact.jp/exhibition-video.html"],
        )
        by_url = {page["url"]: page for page in data["pages"]}
        self.assertIn(
            "https://framepact.jp/exhibition-video.html",
            by_url,
        )
        self.assertFalse(
            by_url["https://framepact.jp/legacy.html"]["sitemapIncluded"]
        )

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
        automation.judge(
            page,
            datetime.fromisoformat("2026-08-14T09:00:00+09:00"),
        )
        self.assertTrue(page["ownerActionRequired"])
        self.assertIn("API認証・権限エラー", page["notes"])

    def test_success_clears_stale_error_note(self):
        page = {
            "url": "https://example.com/",
            "sitemapIncluded": True,
            "robotsTxtState": "ALLOWED",
            "indexingState": "INDEXING_ALLOWED",
            "googleCanonical": "https://example.com/",
            "userCanonical": "https://example.com/",
            "pageFetchState": "SUCCESSFUL",
            "consecutiveApiFailures": 0,
            "errorInfo": None,
            "publishedAt": None,
            "inspectionStatus": "PASS",
            "coverageState": "送信して登録されました",
            "notes": "API認証・権限エラー",
        }
        automation.judge(
            page,
            datetime.fromisoformat("2026-09-17T09:00:00+09:00"),
        )
        self.assertFalse(page["ownerActionRequired"])
        self.assertEqual(page["notes"], "")

    def test_unindexed_age_and_localized_coverage(self):
        timestamp = datetime.fromisoformat("2026-09-17T09:00:00+09:00")
        cases = [
            (None, "検出 - インデックス未登録", False, "公開日不明"),
            ("2026-09-16T09:00:00+09:00", "Discovered", False, "公開7日未満"),
            ("2026-09-10T09:00:00+09:00", "Discovered", True, "公開7日後"),
            (None, "クロール済み - インデックス未登録", True, "クロール済み"),
            (None, "Crawled - currently not indexed", True, "クロール済み"),
        ]
        for published, coverage, action, note in cases:
            with self.subTest(published=published, coverage=coverage):
                page = automation.new_page("https://example.com/", None, {})
                page.update(publishedAt=published, coverageState=coverage,
                            inspectionStatus="NEUTRAL")
                automation.judge(page, timestamp)
                self.assertEqual(page["ownerActionRequired"], action)
                self.assertIn(note, page["notes"])

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
            morning.write_text(
                '{"searchConsole": null}\n',
                encoding="utf-8",
            )
            original = automation.MORNING
            automation.MORNING = morning
            try:
                automation.update_morning(
                    {"pages": pages},
                    datetime.fromisoformat(
                        "2026-08-07T09:00:00+09:00"
                    ),
                    sitemap_count=15,
                )
            finally:
                automation.MORNING = original
            summary = json.loads(
                morning.read_text(encoding="utf-8")
            )["searchConsole"]
        self.assertEqual(summary["status"], "取得失敗")
        self.assertEqual(summary["errorCount"], 15)
        self.assertEqual(summary["apiFailureCount"], 15)
        self.assertIsNone(summary["indexedCount"])
        self.assertIsNone(summary["notIndexedCount"])
        self.assertEqual(
            summary["nextScheduledRunAt"],
            "2026-08-08T08:30:00+09:00",
        )


if __name__ == "__main__":
    unittest.main()
