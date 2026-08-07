import unittest

from update_runtime_state import RUN_FIELDS, update


def run(run_id="nightly:1", status="waiting_owner", result="draft_pr_created"):
    values = {
        "runId": run_id,
        "workflowType": "nightly_production",
        "sourceId": "PLAN-1",
        "startedAt": "2026-08-07T02:00:00+09:00",
        "completedAt": "2026-08-07T02:10:00+09:00",
        "status": status,
        "result": result,
        "branch": "writing/WR-1",
        "commitSha": "1" * 40,
        "pullRequestNumber": 21,
        "pullRequestUrl": "https://github.com/LifeifCreater/ai-video-business/pull/21",
        "pullRequestState": "open",
        "draft": True,
        "errorCode": None,
    }
    assert set(values) == RUN_FIELDS
    return values


class RuntimeStateTests(unittest.TestCase):
    def test_upserts_by_run_id_without_content_fields(self):
        first = update(None, run())
        replacement = run(status="failed", result="failed")
        replacement["errorCode"] = "TEST_FAILED"
        second = update(first, replacement)
        self.assertEqual(len(second["runs"]), 1)
        self.assertEqual(second["runs"][0]["status"], "failed")

    def test_rejects_unapproved_content_fields(self):
        invalid = run()
        invalid["body"] = "本文を保存してはいけない"
        with self.assertRaises(ValueError):
            update(None, invalid)

    def test_retry_upserts_own_run_into_refetched_latest_state(self):
        weekly = run("weekly:1", status="completed", result="draft_pr_created")
        weekly["workflowType"] = "weekly_planning"
        latest = update(None, weekly)

        nightly = run("nightly:1")
        retried = update(latest, nightly)

        self.assertEqual({item["runId"] for item in retried["runs"]}, {"weekly:1", "nightly:1"})

    def test_same_run_id_is_idempotent_after_retry(self):
        state = update(None, run("nightly:retry"))
        state = update(state, run("nightly:retry"))

        self.assertEqual([item["runId"] for item in state["runs"]], ["nightly:retry"])

    def test_interleaved_tasks_do_not_remove_existing_runs(self):
        weekly = run("weekly:1", status="completed", result="existing_result")
        weekly["workflowType"] = "weekly_planning"
        publish = run("publish:1", status="failed", result="failed")
        publish["workflowType"] = "approved_article_implementation"
        publish["errorCode"] = "IMPLEMENTATION_FAILED"

        state = update(None, weekly)
        state = update(state, run("nightly:1"))
        state = update(state, publish)

        self.assertEqual(
            {item["runId"] for item in state["runs"]},
            {"weekly:1", "nightly:1", "publish:1"},
        )


if __name__ == "__main__":
    unittest.main()
