#!/usr/bin/env python3
"""Search Console sitemap/inspection automation. Dry-run is the default."""
import argparse, json, os, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

JST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "automation/search-console/search-console-register.json"
SITEMAP = ROOT / "sitemap.xml"
MORNING = ROOT / "automation/cloud-editorial/morning-brief.json"

def now(): return datetime.now(JST)
def iso(dt): return dt.isoformat(timespec="seconds")
def load(path): return json.loads(path.read_text())
def save(path, data): path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

def sitemap_rows():
    root = ET.parse(SITEMAP).getroot()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [(n.findtext("s:loc", namespaces=ns), n.findtext("s:lastmod", namespaces=ns)) for n in root.findall("s:url", ns)]

def credentials(scopes):
    raw = os.environ.get("GSC_SERVICE_ACCOUNT_JSON")
    if not raw: raise RuntimeError("GSC_SERVICE_ACCOUNT_JSON is not configured")
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    return AuthorizedSession(service_account.Credentials.from_service_account_info(json.loads(raw), scopes=scopes))

def eligible(page, ts):
    # retryAfterがある間はownerActionRequiredでも期日前に再試行しない。
    if page["retryAfter"]: return datetime.fromisoformat(page["retryAfter"]) <= ts
    if page["ownerActionRequired"]: return True
    if page["inspectionStatus"] not in (None, "PASS"): return True
    return bool(page["publishedAt"] and datetime.fromisoformat(page["publishedAt"]) <= ts - timedelta(days=1) and not page["inspectedAt"])

def judge(page, ts):
    reasons = []
    if not page["sitemapIncluded"]: reasons.append("sitemapに未掲載")
    if page["robotsTxtState"] == "DISALLOWED": reasons.append("robots.txtでブロック")
    if page["indexingState"] in ("BLOCKED_BY_META_TAG", "BLOCKED_BY_HTTP_HEADER"): reasons.append("noindex検出")
    if page["googleCanonical"] and page["userCanonical"] and page["googleCanonical"] != page["userCanonical"]: reasons.append("canonical不一致")
    if page["pageFetchState"] in ("NOT_FOUND", "SERVER_ERROR"): reasons.append(page["pageFetchState"])
    if page.get("errorInfo") and ("HTTP 401" in page["errorInfo"] or "HTTP 403" in page["errorInfo"]): reasons.append("API認証・権限エラー")
    elif page["consecutiveApiFailures"] >= 3: reasons.append("API取得3回連続失敗")
    if page["publishedAt"] and ts - datetime.fromisoformat(page["publishedAt"]) >= timedelta(days=7) and page["inspectionStatus"] != "PASS": reasons.append("公開7日後も未登録")
    if page["coverageState"] and "Crawled" in page["coverageState"] and page["inspectionStatus"] != "PASS": reasons.append("クロール済みだが未登録継続")
    page["ownerActionRequired"] = bool(reasons)
    page["notes"] = "、".join(reasons) if reasons else ("公開7日未満の未登録は経過観察。" if page["inspectionStatus"] not in (None, "PASS") else page["notes"])

def inspect(live):
    data, ts = load(REGISTER), now()
    rows = dict(sitemap_rows())
    targets = []
    for p in data["pages"]:
        p["sitemapIncluded"] = p["url"] in rows
        if p["url"] in rows: p["lastModified"] = rows[p["url"]]
        if eligible(p, ts): targets.append(p)
    if not live:
        print(json.dumps({"mode":"dry-run","property":data["siteUrl"],"sitemap":data["sitemapUrl"],"sitemapUrls":len(rows),"inspectionTargets":[p["url"] for p in targets],"authentication":"not tested"}, ensure_ascii=False, indent=2)); return
    if not targets:
        data["generatedAt"] = iso(ts); save(REGISTER, data); update_morning(data, ts)
        return
    session = credentials(["https://www.googleapis.com/auth/webmasters.readonly"])
    for p in targets:
        try:
            response = session.post("https://searchconsole.googleapis.com/v1/urlInspection/index:inspect", json={"inspectionUrl":p["url"],"siteUrl":data["siteUrl"],"languageCode":"ja-JP"}, timeout=30)
            response.raise_for_status()
            result = response.json()["inspectionResult"]["indexStatusResult"]
            p.update(inspectionStatus=result.get("verdict"),coverageState=result.get("coverageState"),indexingState=result.get("indexingState"),robotsTxtState=result.get("robotsTxtState"),googleCanonical=result.get("googleCanonical"),userCanonical=result.get("userCanonical"),lastCrawlTime=result.get("lastCrawlTime"),referringUrls=result.get("referringUrls"),pageFetchState=result.get("pageFetchState"),errorInfo=None,inspectedAt=iso(ts),retryAfter=iso(ts+timedelta(days=1)),consecutiveApiFailures=0)
        except Exception as exc:
            p["consecutiveApiFailures"] += 1
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            p["errorInfo"] = f"{type(exc).__name__}:HTTP {status_code}" if status_code else type(exc).__name__
            cooldown_days = 7 if status_code in (401, 403) or p["consecutiveApiFailures"] >= 3 else 1
            p["inspectedAt"] = iso(ts); p["retryAfter"] = iso(ts + timedelta(days=cooldown_days))
        judge(p, ts)
    data["generatedAt"] = iso(ts); save(REGISTER, data); update_morning(data, ts)
    failed = [p for p in targets if p.get("errorInfo")]
    if failed:
        raise RuntimeError(f"URL inspection failed for {len(failed)}/{len(targets)} targets")

def submit(live):
    data, ts = load(REGISTER), now(); rows = dict(sitemap_rows())
    invalid = [p["url"] for p in data["pages"] if p["url"] not in rows or rows[p["url"]] != p["lastModified"]]
    recent = data["lastSitemapSubmissionAt"] and datetime.fromisoformat(data["lastSitemapSubmissionAt"]) > ts - timedelta(hours=6)
    if not live:
        print(json.dumps({"mode":"dry-run","deploymentVerification":"required","sitemapUrls":len(rows),"metadataMismatches":invalid,"wouldSubmit":not invalid and not recent,"authentication":"not tested"}, ensure_ascii=False, indent=2)); return
    if invalid or recent: raise RuntimeError("sitemap metadata mismatch or submission cooldown active")
    session = credentials(["https://www.googleapis.com/auth/webmasters"])
    endpoint = "https://www.googleapis.com/webmasters/v3/sites/{}/sitemaps/{}".format(quote(data["siteUrl"], safe=""), quote(data["sitemapUrl"], safe=""))
    response = session.put(endpoint, timeout=30); response.raise_for_status()
    data["lastSitemapSubmissionAt"] = iso(ts); data["generatedAt"] = iso(ts)
    for p in data["pages"]:
        if p["sitemapIncluded"]: p["sitemapSubmittedAt"] = iso(ts)
    save(REGISTER, data)

def update_morning(data, ts):
    brief = load(MORNING); pages = data["pages"]
    indexed = [p for p in pages if p["inspectionStatus"] == "PASS"]
    known = [p for p in pages if p["inspectionStatus"] is not None]
    api_failures = [p for p in pages if p.get("errorInfo")]
    errors = [p for p in pages if p["ownerActionRequired"] or p.get("errorInfo")]
    canonical = [p for p in pages if p["googleCanonical"] and p["userCanonical"] and p["googleCanonical"] != p["userCanonical"]]
    priority = sorted(errors, key=lambda p: ("API" not in (p["notes"] or ""), p["url"]))[:5]
    if api_failures and len(api_failures) == len(pages) and not known:
        status = "取得失敗"
    elif api_failures:
        status = "一部取得"
    elif known:
        status = "取得済み"
    else:
        status = "未取得"
    brief["searchConsole"]={"generatedAt":iso(ts),"status":status,"newPublishedUrlCount":sum(1 for p in pages if p["publishedAt"] and datetime.fromisoformat(p["publishedAt"]) >= ts-timedelta(days=7)),"indexedCount":len(indexed) if known else None,"notIndexedCount":sum(1 for p in known if p["inspectionStatus"] != "PASS") if known else None,"errorCount":len(errors),"apiFailureCount":len(api_failures),"canonicalMismatchCount":len(canonical) if known else None,"sitemapMissingCount":sum(1 for p in pages if not p["sitemapIncluded"]),"ownerActionRequired":[{"url":p["url"],"reason":p["notes"] or p.get("errorInfo") or "取得失敗"} for p in priority],"nextInspectionAt":min((p["retryAfter"] for p in pages if p["retryAfter"]),default=None)}
    save(MORNING, brief)

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("command",choices=["inspect","submit"]); ap.add_argument("--live",action="store_true"); args=ap.parse_args()
    try: (inspect if args.command=="inspect" else submit)(args.live)
    except Exception as exc: print(f"ERROR: {type(exc).__name__}: {exc}",file=sys.stderr); sys.exit(1)
