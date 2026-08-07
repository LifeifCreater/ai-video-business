#!/usr/bin/env python3
import argparse
import json
from datetime import datetime
from pathlib import Path


WORKFLOWS = {"weekly_planning", "nightly_production", "approved_article_implementation"}
STATUSES = {"completed", "skipped", "waiting_owner", "failed"}
RESULTS = {"draft_pr_created", "existing_result", "no_target", "waiting_owner", "failed"}
RUN_FIELDS = {
    "runId", "workflowType", "sourceId", "startedAt", "completedAt", "status", "result",
    "branch", "commitSha", "pullRequestNumber", "pullRequestUrl", "pullRequestState", "draft", "errorCode",
}


def validate_run(run):
    if set(run) != RUN_FIELDS:
        raise ValueError(f"runtime state fields must be exactly: {sorted(RUN_FIELDS)}")
    if not run["runId"] or run["workflowType"] not in WORKFLOWS:
        raise ValueError("runId or workflowType is invalid")
    if run["status"] not in STATUSES or run["result"] not in RESULTS:
        raise ValueError("status or result is invalid")
    for field in ("startedAt", "completedAt"):
        if datetime.fromisoformat(run[field]).tzinfo is None:
            raise ValueError(f"{field} requires a timezone")
    if run["status"] == "failed" and run["result"] != "failed":
        raise ValueError("failed status requires failed result")
    if run["status"] == "waiting_owner" and run["result"] not in {"waiting_owner", "draft_pr_created"}:
        raise ValueError("waiting_owner status has an invalid result")
    if run["pullRequestNumber"] is not None and not isinstance(run["pullRequestNumber"], int):
        raise ValueError("pullRequestNumber must be an integer or null")


def update(state, run):
    validate_run(run)
    existing = state if state else {"schemaVersion": 1, "generatedAt": run["completedAt"], "runs": []}
    if existing.get("schemaVersion") != 1 or not isinstance(existing.get("runs"), list):
        raise ValueError("runtime state has an invalid structure")
    runs = [item for item in existing["runs"] if item.get("runId") != run["runId"]]
    runs.append(run)
    runs.sort(key=lambda item: datetime.fromisoformat(item["completedAt"]), reverse=True)
    generated = max((existing.get("generatedAt", run["completedAt"]), run["completedAt"]), key=datetime.fromisoformat)
    return {"schemaVersion": 1, "generatedAt": generated, "runs": runs[:100]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--run-file", required=True, type=Path)
    args = parser.parse_args()
    state = json.loads(args.state.read_text(encoding="utf-8")) if args.state.exists() else None
    run = json.loads(args.run_file.read_text(encoding="utf-8"))
    result = update(state, run)
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
