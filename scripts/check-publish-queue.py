#!/usr/bin/env python3
"""Validate publish-queue invariants without changing publication state."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "distribution/publish-ready/publish-queue.json"

ALLOWED_APPROVAL = {"owner_review", "approved", "rejected", "hold"}
ALLOWED_REVIEW = {
    "editor_in_chief_passed",
    "editor_in_chief_rejected",
    "pending",
}
ALLOWED_PUBLISH = {"unpublished", "published"}


def nonempty(value):
    return value not in (None, "")


def parse_datetime(value, field, item_id, errors):
    if not nonempty(value):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{item_id}: {field} is not ISO-8601: {value}")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{item_id}: {field} must include timezone: {value}")
    return parsed


def validate(payload):
    errors = []
    alerts = []
    ids = set()
    now = datetime.now(timezone.utc)

    if not isinstance(payload, list):
        return ["publish queue must be an array"], alerts

    for index, item in enumerate(payload):
        item_id = item.get("id") or f"index:{index}"
        if item_id in ids:
            errors.append(f"{item_id}: duplicate id")
        ids.add(item_id)

        approval = item.get("approvalStatus")
        review = item.get("reviewStatus")
        publish = item.get("publishStatus")

        if approval not in ALLOWED_APPROVAL:
            errors.append(f"{item_id}: invalid approvalStatus={approval}")
        if review not in ALLOWED_REVIEW:
            errors.append(f"{item_id}: invalid reviewStatus={review}")
        if publish not in ALLOWED_PUBLISH:
            errors.append(f"{item_id}: invalid publishStatus={publish}")

        scheduled = parse_datetime(
            item.get("scheduledAt"),
            "scheduledAt",
            item_id,
            errors,
        )
        parse_datetime(
            item.get("publishedAt"),
            "publishedAt",
            item_id,
            errors,
        )

        if publish == "unpublished":
            if nonempty(item.get("publishedAt")):
                errors.append(
                    f"{item_id}: unpublished item has publishedAt"
                )
            if nonempty(item.get("publishedUrl")):
                errors.append(
                    f"{item_id}: unpublished item has publishedUrl"
                )
            if scheduled and scheduled.astimezone(timezone.utc) < now:
                alerts.append(
                    f"{item_id}: 期限超過の未公開投稿 "
                    f"({item.get('scheduledAt')})"
                )

        if publish == "published":
            verified = (
                item.get("publicationVerificationStatus")
                == "content_match_confirmed"
            )
            if not nonempty(item.get("publishedUrl")) and not verified:
                errors.append(
                    f"{item_id}: published item needs URL or "
                    "content_match_confirmed verification"
                )
            has_time_evidence = any(
                nonempty(item.get(field))
                for field in (
                    "publishedAt",
                    "publicationDisplayedAt",
                    "publicationObservedAt",
                )
            )
            if not has_time_evidence and not verified:
                errors.append(
                    f"{item_id}: published item needs publication-time "
                    "evidence or verified exception"
                )

    return errors, alerts


def main():
    payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    errors, alerts = validate(payload)
    for alert in alerts:
        print(f"ALERT: {alert}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"publish queue: OK "
        f"({len(payload)} records, {len(alerts)} alerts)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
