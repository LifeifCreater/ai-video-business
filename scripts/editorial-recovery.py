#!/usr/bin/env python3
"""One-time repository recovery for editorial state and approved planning."""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
JST = ZoneInfo("Asia/Tokyo")
NOW = datetime.now(JST).isoformat(timespec="seconds")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def append_note(item, note):
    current = (item.get("notes") or "").strip()
    if note not in current:
        item["notes"] = f"{current} {note}".strip()


def repair_publish_queue():
    path = ROOT / "distribution/publish-ready/publish-queue.json"
    queue = load_json(path)
    note_publications = {
        "PUB-NOTE-001": {
            "url": "https://note.com/framepact/n/n7c0acdcf4de2",
            "displayed": "2026-08-06 02:13",
        },
        "PUB-NOTE-002": {
            "url": "https://note.com/framepact/n/ne78117a5ace0",
            "displayed": "2026-08-06 02:06",
        },
        "PUB-NOTE-003": {
            "url": "https://note.com/framepact/n/nf6d1c30f3061",
            "displayed": "2026-08-06 02:27",
        },
    }

    for item in queue:
        item_id = item["id"]
        if item_id in note_publications:
            publication = note_publications[item_id]
            item["publishStatus"] = "published"
            # The account display has no confirmed timezone. Do not invent an ISO timestamp.
            item["publishedAt"] = ""
            item["publishedUrl"] = publication["url"]
            item["publicationVerificationStatus"] = "content_match_confirmed"
            item["publicationUrlStatus"] = "confirmed"
            item["publicationTimeStatus"] = "displayed_time_timezone_unknown"
            item["publicationDisplayedAt"] = publication["displayed"]
            item["publicationVerifiedAt"] = "2026-09-16"
            item["publicationDisposition"] = "published"
            item["ownerScheduleRequired"] = False
            append_note(
                item,
                "note.com/framepactの公開本文と一致を確認済み。"
                "画面表示時刻のタイムゾーンが未確定のため"
                "publishedAtは未取得のまま保持。",
            )
        elif item_id == "PUB-X-004":
            item["publishStatus"] = "published"
            item["publishedAt"] = ""
            item["publishedUrl"] = ""
            item["publicationVerificationStatus"] = "content_match_confirmed"
            item["publicationUrlStatus"] = "missing"
            item["publicationTimeStatus"] = "unknown"
            item["publicationObservedAt"] = "2026-08-14"
            item["publicationDisposition"] = "published_url_missing"
            item["ownerScheduleRequired"] = False
            append_note(
                item,
                "公開検索で本文一致を確認した記録のみを正本化。"
                "個別投稿URLと正確な公開時刻は未取得であり、推測しない。",
            )
        elif item.get("publishStatus") == "unpublished":
            recommendation = item.get("ownerDecisionRecommendation")
            item["publicationDisposition"] = (
                "hold_duplicate"
                if recommendation == "reject"
                else "candidate"
            )
            item["ownerScheduleRequired"] = (
                recommendation != "reject"
                and item.get("approvalStatus") == "approved"
                and item.get("reviewStatus") == "editor_in_chief_passed"
            )

    save_json(path, queue)


def fetch_approved_plans():
    subprocess.run(
        [
            "git",
            "fetch",
            "origin",
            "planning/weekly-2026-09-14:"
            "refs/remotes/origin/planning/weekly-2026-09-14",
        ],
        cwd=ROOT,
        check=True,
    )
    source_ref = "refs/remotes/origin/planning/weekly-2026-09-14"
    plans = {
        "PLAN-20260913-001-generative-insert-shot-register.md": (
            "採用。優先順位1。CTAは企業向けAI動画制作。"
            "台帳は実務テンプレートとして公開可能な項目に限定する。"
        ),
        "PLAN-20260913-002-ai-audio-processing-approval.md": (
            "採用。優先順位2。CTAは研修・教育動画。"
            "原音・加工版・本人同意・公開許諾の確認範囲を明記する。"
        ),
    }
    approved = ROOT / "planning/approved"
    approved.mkdir(parents=True, exist_ok=True)

    for filename, decision in plans.items():
        source_path = f"planning/drafts/{filename}"
        content = subprocess.check_output(
            ["git", "show", f"{source_ref}:{source_path}"],
            cwd=ROOT,
            text=True,
        )
        content = content.replace(
            "- ステータス: `オーナー判断待ち`",
            "- ステータス: `企画承認済み・執筆待ち`",
        )
        content = content.replace(
            "- オーナー承認状況: `未承認`",
            "- オーナー承認状況: `承認済み（2026-09-17、"
            "オーナー指示「全て対応」）`",
        )
        for line in content.splitlines():
            if line.startswith("- オーナー判断事項:"):
                content = content.replace(
                    line,
                    f"- オーナー判断: {decision}",
                )
                break
        destination = approved / filename
        destination.write_text(content, encoding="utf-8")


def update_idea_register():
    path = ROOT / "planning/idea-register.md"
    marker = "## 2026-09-17 オーナー承認"
    content = path.read_text(encoding="utf-8")
    if marker not in content:
        content = content.rstrip() + f"""

{marker}

| 企画ID | 状態 | 優先順位 | CTA | 承認根拠 |
|---|---|---:|---|---|
| `PLAN-20260913-001` | 企画承認済み・執筆待ち | 1 | 企業向けAI動画制作 | 2026-09-17 オーナー指示「全て対応」 |
| `PLAN-20260913-002` | 企画承認済み・執筆待ち | 2 | 研修・教育動画 | 2026-09-17 オーナー指示「全て対応」 |

公開承認、SNS投稿、予約投稿は別工程とし、この承認では実施しない。
"""
        path.write_text(content, encoding="utf-8")


def update_job_register():
    path = ROOT / "automation/cloud-editorial/job-register.json"
    data = load_json(path)
    jobs = data["jobs"]
    job_id = "WEEKLY-PLANNING-WEEK-2026-09-14"
    replacement = {
        "jobId": job_id,
        "workflowType": "weekly_planning",
        "sourceId": "WEEK-2026-09-14",
        "status": "completed",
        "scheduledFor": "2026-09-13T01:00:00+09:00",
        "startedAt": "2026-09-13T00:58:52+09:00",
        "completedAt": NOW,
        "branch": "planning/weekly-2026-09-14",
        "commitSha": "f8465e2daa1aca57582bb6860504a73f7284a5ee",
        "pullRequestUrl": "https://github.com/LifeifCreater/ai-video-business/pull/31",
        "approvalRequired": None,
        "errorCode": None,
        "errorSummary": None,
        "retryCount": 0,
        "lastUpdatedAt": NOW,
    }
    for index, job in enumerate(jobs):
        if job.get("jobId") == job_id:
            jobs[index] = replacement
            break
    else:
        jobs.append(replacement)
    save_json(path, data)


def write_owner_action_summary():
    path = ROOT / "distribution/publish-ready/owner-actions-20260917.md"
    path.write_text(
        """# 投稿・企画状態の修復記録（2026-09-17）

## 公開済みとして確定

- `PUB-NOTE-001`、`PUB-NOTE-002`、`PUB-NOTE-003`
  - note.com/framepactの本文一致と公開URLを確認
  - 表示時刻のタイムゾーンは未確定のため、`publishedAt`は推測せず未取得
- `PUB-X-004`
  - 公開検索による本文一致確認を維持
  - 個別投稿URLと正確な公開時刻は未取得

## 未公開候補

- `publishStatus: unpublished`の投稿に公開日時を自動設定していない
- `ownerDecisionRecommendation: reject`は重複保留として分類
- その他の承認済み候補は`ownerScheduleRequired: true`とし、投稿時刻はオーナー判断事項
- 自動投稿、予約投稿、公開済みへの推測変更は行っていない

## 企画承認

1. `PLAN-20260913-001`を優先順位1で承認
2. `PLAN-20260913-002`を優先順位2で承認

いずれも公開承認とは別で、夜間制作はレビュー用Draft PRまでで停止する。
""",
        encoding="utf-8",
    )


def update_morning_prompt():
    path = ROOT / "automation/cloud-editorial/prompts/morning-brief.md"
    content = path.read_text(encoding="utf-8")
    addition = """
runtime-stateの最新`completedAt`または`generatedAt`が現在のJSTから26時間を超えて古い場合は、「失敗0件」と断定せず「実行状態未取得／runtime-state更新停止」としてalertsへ1件表示する。過去分はScheduled Tasksの確定ログがある場合だけ復元し、推測で埋めない。

Search Consoleの`retryEligibleAt`はURL検査を再実行できる最短時刻、`nextScheduledRunAt`はワークフローの次回定期実行時刻として分けて表示する。両方がある場合は混同せず併記する。`monitoringMissingCount`が1以上ならsitemapと監視台帳の差分としてalertsへ表示する。
""".strip()
    if addition not in content:
        path.write_text(
            content.rstrip() + "\n\n" + addition + "\n",
            encoding="utf-8",
        )


def run_checks():
    commands = [
        ["python3", "scripts/check-publish-queue.py"],
        [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "automation/search-console",
            "-p",
            "test_*.py",
        ],
        ["python3", "scripts/sync-article-social.py", "--check"],
        ["ruby", "scripts/check-site.rb"],
        ["git", "diff", "--check"],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)


def finalize_commit():
    temp_files = [
        ROOT / ".github/workflows/editorial-recovery.yml",
        ROOT / "scripts/editorial-recovery.py",
    ]
    for path in temp_files:
        if path.exists():
            path.unlink()

    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    if not subprocess.check_output(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        text=True,
    ).strip():
        raise RuntimeError("recovery produced no changes")

    subprocess.run(
        [
            "git",
            "-c",
            "user.name=framepact-recovery-bot",
            "-c",
            "user.email=actions@users.noreply.github.com",
            "commit",
            "-m",
            "fix: editorial state, Search Console and planning recovery",
        ],
        cwd=ROOT,
        check=True,
    )
    branch = os.environ["GITHUB_REF_NAME"]
    subprocess.run(
        ["git", "push", "origin", f"HEAD:{branch}"],
        cwd=ROOT,
        check=True,
    )


def main():
    repair_publish_queue()
    fetch_approved_plans()
    update_idea_register()
    update_job_register()
    write_owner_action_summary()
    update_morning_prompt()
    run_checks()
    finalize_commit()


if __name__ == "__main__":
    main()
