#!/usr/bin/env python3
"""Validate role definitions only; never invoke agents or external services."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REGISTER = Path("agents/team-register.json")
NEW_ROLE_IDS = {
    "sales_business_development", "proposal_estimation", "production_producer",
    "growth_cro", "creative_director", "contracts_rights_risk",
    "management_accounting",
}
REQUIRED_SECTIONS = (
    "使命", "共通ルール", "入力", "担当範囲と手順", "成果物", "連携",
    "KPI", "停止条件・禁止事項", "完了条件", "初回依頼例",
)
POLICY_KEYS = (
    "commonPolicyPath", "businessRouterPath", "businessTaskTemplatePath",
    "publicOutputPolicyPath",
)
FALSE_RUNTIME_KEYS = (
    "scheduledTasksCreated", "independentAgentsProvisioned",
    "externalConnectionsProvisioned", "externalActionsAllowed",
    "directMainWritesAllowed", "automaticOwnerApprovalAllowed",
)


def checked_path(root: Path, value: object, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        errors.append(f"Invalid relative path: {value!r}")
        return None
    resolved = (root / value).resolve()
    if not resolved.is_relative_to(root.resolve()):
        errors.append(f"Path escapes repository: {value}")
        return None
    if not resolved.is_file():
        errors.append(f"Missing file: {value}")
        return None
    return resolved


def validate(root: Path, data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Register must be an object"]
    members = data.get("members")
    if not isinstance(members, list):
        return ["members must be an array"]
    if data.get("memberCount") != len(members):
        errors.append("memberCount does not match members")
    if data.get("finalApprover") != "owner":
        errors.append("finalApprover must be owner")
    if data.get("coordinatorId") != "secretary":
        errors.append("coordinatorId must be secretary")
    if data.get("definitionKind") != "role_prompts":
        errors.append("Definitions must not claim independently provisioned agents")
    if data.get("privateOutputRoot") is not None:
        errors.append("Do not commit private workspace locations to this public register")
    runtime = data.get("newRoleRuntime")
    if not isinstance(runtime, dict):
        errors.append("newRoleRuntime must be an object")
        runtime = {}
    if runtime.get("executionMode") != "on_demand":
        errors.append("New roles must remain on_demand")
    for key in FALSE_RUNTIME_KEYS:
        if runtime.get(key) is not False:
            errors.append(f"newRoleRuntime.{key} must be false")

    ids: set[str] = set()
    paths: set[str] = set()
    new_ids: set[str] = set()
    documents: set[Path] = set()
    for key in POLICY_KEYS:
        target = checked_path(root, data.get(key), errors)
        if target:
            documents.add(target)
    index = checked_path(root, "agents/README.md", errors)
    if index:
        documents.add(index)

    for member in members:
        if not isinstance(member, dict):
            errors.append("Each member must be an object")
            continue
        role_id = member.get("id")
        path = member.get("definitionPath")
        if not isinstance(role_id, str) or not role_id:
            errors.append("Member ID must be a non-empty string")
            continue
        if role_id in ids:
            errors.append(f"Duplicate role ID: {role_id}")
        ids.add(role_id)
        if isinstance(path, str):
            if path in paths:
                errors.append(f"Duplicate definition path: {path}")
            paths.add(path)
        if not isinstance(member.get("name"), str) or not member.get("name"):
            errors.append(f"Missing member name: {role_id}")
        if not isinstance(member.get("new"), bool):
            errors.append(f"Member new flag must be boolean: {role_id}")
        target = checked_path(root, path, errors)
        if member.get("new") is True:
            new_ids.add(role_id)
            if target:
                documents.add(target)
                text = target.read_text(encoding="utf-8")
                headings = set(re.findall(r"^## (.+)$", text, re.MULTILINE))
                for section in REQUIRED_SECTIONS:
                    if section not in headings:
                        errors.append(f"{path}: missing section {section}")
                if "../AGENTS.md" not in text:
                    errors.append(f"{path}: missing shared policy link")
                if f"`{role_id}`" not in text:
                    errors.append(f"{path}: missing role ID")
    if new_ids != NEW_ROLE_IDS:
        errors.append("New roles differ from the seven requested roles")
    if "coo" not in ids or "secretary" not in ids:
        errors.append("Existing leadership and coordination roles must be retained")

    # Check relative Markdown file targets in new documentation (not live websites).
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for raw_link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            parsed = urlsplit(raw_link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (document.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(root.resolve()) or not target.exists():
                errors.append(f"Broken or unsafe link in {document.name}: {raw_link}")
    return errors


def main() -> int:
    try:
        data = json.loads((ROOT / REGISTER).read_text(encoding="utf-8"))
        errors = validate(ROOT, data)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"AI team definitions: OK ({len(data['members'])} roles, 7 new; no agents executed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
