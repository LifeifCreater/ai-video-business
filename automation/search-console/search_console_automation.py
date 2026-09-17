#!/usr/bin/env python3
"""Search Console sitemap/inspection automation. Dry-run is the default."""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET

JST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "automation/search-console/search-console-register.json"
CONFIG = ROOT / "automation/search-console/search-console-config.json"
SITEMAP = ROOT / "sitemap.xml"
MORNING = ROOT / "automation/cloud-editorial/morning-brief.json"


def now():
    return datetime.now(JST)


def iso(dt):
    return dt.isoformat(timespec="seconds")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_register():
    # Configuration stays on main; restored monitoring state must not override it.
    data, config = load(REGISTER), load(CONFIG)
    if data["siteUrl"] != config["siteUrl"]:
        # Retry failures from the old property once, retaining diagnostic history.
        for page in data["pages"]:
            error = page.get("errorInfo") or ""
            if "HTTP 401" in error or "HTTP 403" in error:
                page["retryAfter"] = None
    data.update(siteUrl=config["siteUrl"], sitemapUrl=config["sitemapUrl"])
    return data


def sitemap_rows():
    root = ET.parse(SITEMAP).getroot()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [
        (
            node.findtext("s:loc", namespaces=ns),
            node.findtext("s:lastmod", namespaces=ns),
        )
        for node in root.findall("s:url", ns)
    ]


def infer_page_type(url):
    path = urlparse(url).path
    name = Path(path).name
    if path in ("", "/"):
        return "home"
    if name == "column.html":
        return "column_index"
    if name == "operator.html":
        return "operator"
    if name in {
        "what-is-ai-video-production.html",
        "ai-video-vs-traditional-video.html",
        "ai-video-outsourcing-checklist.html",
        "ai-video-ad-disclosure.html",
        "ai-video-data-management.html",
        "multi-platform-video-production.html",
        "ai-avatar-training-video-operations.html",
        "youtube-shorts-thumbnail-approval.html",
    }:
        return "column"
    return "service"


def new_page(url, last_modified, data):
    return {
        "url": url,
        "pageType": infer_page_type(url),
        "publishedAt": None,
        "lastModified": last_modified,
        "sitemapIncluded": True,
        "sitemapSubmittedAt": data.get("lastSitemapSubmissionAt"),
        "inspectionStatus": None,
        "coverageState": None,
        "indexingState": None,
        "robotsTxtState": None,
        "googleCanonical": None,
        "userCanonical": None,
        "lastCrawlTime": None,
        "referringUrls": None,
        "pageFetchState": None,
        "errorInfo": None,
        "inspectedAt": None,
        "retryAfter": None,
        "consecutiveApiFailures": 0,
        "ownerActionRequired": False,
        "notes": "sitemap.xmlから自動登録。初回URL検査待ち。",
    }


def sync_pages(data, rows):
    """Synchronize the monitoring register with sitemap.xml without deleting history."""
    ordered_urls = [url for url, _ in rows if url]
    sitemap = {url: last_modified for url, last_modified in rows if url}
    existing = {page["url"]: page for page in data["pages"]}
    added = []

    for url in ordered_urls:
        if url not in existing:
            page = new_page(url, sitemap[url], data)
            data["pages"].append(page)
            existing[url] = page
            added.append(url)
        page = existing[url]
        page["sitemapIncluded"] = True
        page["lastModified"] = sitemap[url]

    for page in data["pages"]:
        if page["url"] not in sitemap:
            page["sitemapIncluded"] = False

    order = {url: index for index, url in enumerate(ordered_urls)}
    data["pages"].sort(
        key=lambda page: (
            page["url"] not in order,
            order.get(page["url"], len(order)),
            page["url"],
        )
    )
    return added


def credentials(scopes):
    raw = os.environ.get("GSC_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GSC_SERVICE_ACCOUNT_JSON is not configured")
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession

    return AuthorizedSession(
        service_account.Credentials.from_service_account_info(
            json.loads(raw),
            scopes=scopes,
        )
    )


def eligible(page, ts):
    # retryAfterがある間はownerActionRequiredでも期日前に再試行しない。
    if page["retryAfter"]:
        return datetime.fromisoformat(page["retryAfter"]) <= ts
    if page["ownerActionRequired"]:
        return True
    if page["inspectionStatus"] is None and not page["inspectedAt"]:
        return True
    if page["inspectionStatus"] != "PASS":
        return True
    return bool(
        page["publishedAt"]
        and datetime.fromisoformat(page["publishedAt"]) <= ts - timedelta(days=1)
        and not page["inspectedAt"]
    )


def judge(page, ts):
    reasons = []
    if not page["sitemapIncluded"]:
        reasons.append("sitemapに未掲載")
    if page["robotsTxtState"] == "DISALLOWED":
        reasons.append("robots.txtでブロック")
    if page["indexingState"] in ("BLOCKED_BY_META_TAG", "BLOCKED_BY_HTTP_HEADER"):
        reasons.append("noindex検出")
    if (
        page["googleCanonical"]
        and page["userCanonical"]
        and page["googleCanonical"] != page["userCanonical"]
    ):
        reasons.append("canonical不一致")
    if page["pageFetchState"] in ("NOT_FOUND", "SERVER_ERROR"):
        reasons.append(page["pageFetchState"])
    if page.get("errorInfo") and (
        "HTTP 401" in page["errorInfo"] or "HTTP 403" in page["errorInfo"]
    ):
        reasons.append("API認証・権限エラー")
    elif page["consecutiveApiFailures"] >= 3:
        reasons.append("API取得3回連続失敗")
    if (
        page["publishedAt"]
        and ts - datetime.fromisoformat(page["publishedAt"]) >= timedelta(days=7)
        and page["inspectionStatus"] != "PASS"
    ):
        reasons.append("公開7日後も未登録")
    if (
        page["coverageState"]
        and "Crawled" in page["coverageState"]
        and page["inspectionStatus"] != "PASS"
    ):
        reasons.append("クロール済みだが未登録継続")

    page["ownerActionRequired"] = bool(reasons)
    if reasons:
        page["notes"] = "、".join(reasons)
    elif page["inspectionStatus"] == "PASS":
        # Clear stale authentication/error notes after recovery.
        page["notes"] = ""
    elif page["inspectionStatus"] not in (None, "PASS"):
        page["notes"] = "公開7日未満の未登録は経過観察。"


def inspect(live):
    data, ts = load_register(), now()
    rows = sitemap_rows()
    added = sync_pages(data, rows)
    targets = [page for page in data["pages"] if eligible(page, ts)]

    if not live:
        print(
            json.dumps(
                {
                    "mode": "dry-run",
                    "property": data["siteUrl"],
                    "sitemap": data["sitemapUrl"],
                    "sitemapUrls": len(rows),
                    "newRegisterUrls": added,
                    "inspectionTargets": [page["url"] for page in targets],
                    "authentication": "not tested",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if not targets:
        data["generatedAt"] = iso(ts)
        save(REGISTER, data)
        update_morning(data, ts, len(rows))
        return

    session = credentials(
        ["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    for page in targets:
        try:
            response = session.post(
                "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
                json={
                    "inspectionUrl": page["url"],
                    "siteUrl": data["siteUrl"],
                    "languageCode": "ja-JP",
                },
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()["inspectionResult"]["indexStatusResult"]
            page.update(
                inspectionStatus=result.get("verdict"),
                coverageState=result.get("coverageState"),
                indexingState=result.get("indexingState"),
                robotsTxtState=result.get("robotsTxtState"),
                googleCanonical=result.get("googleCanonical"),
                userCanonical=result.get("userCanonical"),
                lastCrawlTime=result.get("lastCrawlTime"),
                referringUrls=result.get("referringUrls"),
                pageFetchState=result.get("pageFetchState"),
                errorInfo=None,
                inspectedAt=iso(ts),
                retryAfter=iso(ts + timedelta(days=1)),
                consecutiveApiFailures=0,
            )
        except Exception as exc:
            page["consecutiveApiFailures"] += 1
            status_code = getattr(
                getattr(exc, "response", None),
                "status_code",
                None,
            )
            page["errorInfo"] = (
                f"{type(exc).__name__}:HTTP {status_code}"
                if status_code
                else type(exc).__name__
            )
            cooldown_days = (
                7
                if status_code in (401, 403)
                or page["consecutiveApiFailures"] >= 3
                else 1
            )
            page["inspectedAt"] = iso(ts)
            page["retryAfter"] = iso(ts + timedelta(days=cooldown_days))
        judge(page, ts)

    data["generatedAt"] = iso(ts)
    save(REGISTER, data)
    update_morning(data, ts, len(rows))
    failed = [page for page in targets if page.get("errorInfo")]
    if failed:
        raise RuntimeError(
            f"URL inspection failed for {len(failed)}/{len(targets)} targets"
        )


def submit(live):
    data, ts = load_register(), now()
    rows = sitemap_rows()
    sync_pages(data, rows)
    sitemap = dict(rows)
    invalid = [
        page["url"]
        for page in data["pages"]
        if page["url"] in sitemap
        and sitemap[page["url"]] != page["lastModified"]
    ]
    recent = (
        data["lastSitemapSubmissionAt"]
        and datetime.fromisoformat(data["lastSitemapSubmissionAt"])
        > ts - timedelta(hours=6)
    )

    if not live:
        print(
            json.dumps(
                {
                    "mode": "dry-run",
                    "deploymentVerification": "required",
                    "sitemapUrls": len(rows),
                    "registerUrls": len(data["pages"]),
                    "metadataMismatches": invalid,
                    "wouldSubmit": not invalid and not recent,
                    "authentication": "not tested",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if invalid:
        raise RuntimeError("sitemap metadata mismatch")
    if recent:
        data["generatedAt"] = iso(ts)
        save(REGISTER, data)
        update_morning(data, ts, len(rows))
        print("Sitemap submission skipped: successful submission within the last 6 hours.")
        return

    session = credentials(["https://www.googleapis.com/auth/webmasters"])
    endpoint = (
        "https://www.googleapis.com/webmasters/v3/sites/{}/sitemaps/{}"
        .format(
            quote(data["siteUrl"], safe=""),
            quote(data["sitemapUrl"], safe=""),
        )
    )
    response = session.put(endpoint, timeout=30)
    response.raise_for_status()
    data["lastSitemapSubmissionAt"] = iso(ts)
    data["generatedAt"] = iso(ts)
    for page in data["pages"]:
        if page["sitemapIncluded"]:
            page["sitemapSubmittedAt"] = iso(ts)
    save(REGISTER, data)
    update_morning(data, ts, len(rows))


def next_scheduled_run(ts):
    target = ts.astimezone(JST).replace(
        hour=8,
        minute=30,
        second=0,
        microsecond=0,
    )
    if target <= ts.astimezone(JST):
        target += timedelta(days=1)
    return target


def update_morning(data, ts, sitemap_count=None):
    brief = load(MORNING)
    pages = data["pages"]
    indexed = [page for page in pages if page["inspectionStatus"] == "PASS"]
    known = [page for page in pages if page["inspectionStatus"] is not None]
    api_failures = [page for page in pages if page.get("errorInfo")]
    errors = [
        page
        for page in pages
        if page["ownerActionRequired"] or page.get("errorInfo")
    ]
    canonical = [
        page
        for page in pages
        if page["googleCanonical"]
        and page["userCanonical"]
        and page["googleCanonical"] != page["userCanonical"]
    ]
    priority = sorted(
        errors,
        key=lambda page: (
            "API" not in (page["notes"] or ""),
            page["url"],
        ),
    )[:5]

    if api_failures and len(api_failures) == len(pages) and not known:
        status = "取得失敗"
    elif api_failures:
        status = "一部取得"
    elif known:
        status = "取得済み"
    else:
        status = "未取得"

    recently_published = 0
    for page in pages:
        if not page["publishedAt"]:
            continue
        try:
            if datetime.fromisoformat(page["publishedAt"]) >= ts - timedelta(days=7):
                recently_published += 1
        except ValueError:
            # Invalid or date-only values are data-quality issues, not recent URLs.
            continue

    retry_eligible = min(
        (
            page["retryAfter"]
            for page in pages
            if page["retryAfter"]
        ),
        default=None,
    )
    sitemap_urls = (
        sitemap_count
        if sitemap_count is not None
        else sum(1 for page in pages if page["sitemapIncluded"])
    )
    brief["searchConsole"] = {
        "generatedAt": iso(ts),
        "status": status,
        "newPublishedUrlCount": recently_published,
        "indexedCount": len(indexed) if known else None,
        "notIndexedCount": (
            sum(
                1
                for page in known
                if page["inspectionStatus"] != "PASS"
            )
            if known
            else None
        ),
        "errorCount": len(errors),
        "apiFailureCount": len(api_failures),
        "canonicalMismatchCount": len(canonical) if known else None,
        "sitemapMissingCount": sum(
            1 for page in pages if not page["sitemapIncluded"]
        ),
        "sitemapUrlCount": sitemap_urls,
        "registerUrlCount": len(pages),
        "monitoringMissingCount": max(sitemap_urls - sum(
            1 for page in pages if page["sitemapIncluded"]
        ), 0),
        "ownerActionRequired": [
            {
                "url": page["url"],
                "reason": (
                    page["notes"]
                    or page.get("errorInfo")
                    or "取得失敗"
                ),
            }
            for page in priority
        ],
        # Backward-compatible alias. New consumers should use retryEligibleAt.
        "nextInspectionAt": retry_eligible,
        "retryEligibleAt": retry_eligible,
        "nextScheduledRunAt": iso(next_scheduled_run(ts)),
    }
    save(MORNING, brief)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["inspect", "submit"])
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    try:
        (inspect if args.command == "inspect" else submit)(args.live)
    except Exception as exc:
        print(
            f"ERROR: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
