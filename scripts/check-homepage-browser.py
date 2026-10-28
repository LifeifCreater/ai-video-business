#!/usr/bin/env python3
"""Local-only Chromium smoke checks; never submit the production inquiry form."""
import contextlib
import functools
import http.server
import os
from pathlib import Path
import threading

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get("BROWSER_CHECK_OUTPUT", "/tmp/framepact-browser-check"))
OUTPUT.mkdir(parents=True, exist_ok=True)

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

handler = functools.partial(QuietHandler, directory=str(ROOT))
server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for width, height in [(320, 568), (390, 844), (844, 390), (1440, 900)]:
            context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
            # Avoid third-party media, analytics and forms during the local test.
            context.route("**/*", lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(base, wait_until="networkidle")
            assert page.locator(".contact-shortcut").is_visible(), (width, "header consultation missing")
            assert page.locator(".contact-shortcut").get_attribute("href").startswith("https://docs.google.com/forms/")
            assert page.evaluate("window.FramepactAnalytics.isExcluded()"), "local preview must not send analytics"
            assert page.evaluate("window.dataLayer.length") == 0
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (width, "horizontal overflow")
            for index in range(6):
                page.locator(f'.timeline [data-go="{index}"]').click()
                page.wait_for_timeout(80)
                assert page.locator(".scene.active").get_attribute("id") in ["opening", "possibilities", "works", "human", "process", "contact"]
                assert page.locator(".scene:not(.active):not([inert])").count() == 0
                for link in page.locator(".scene.active a").all():
                    link.scroll_into_view_if_needed()
                    assert link.is_visible()
                    box = link.bounding_box()
                    assert box and box["y"] >= 0 and box["y"] < height, (width, index, "unreachable link")
                page.screenshot(path=str(OUTPUT / f"{width}x{height}-chapter-{index}.png"))
            # Scroll keys operate on overflowing content, not chapter navigation.
            page.goto(base + "/#opening", wait_until="networkidle")
            page.add_style_tag(content=".opening-copy{min-height:1200px}")
            page.locator('.timeline [data-go="0"]').focus()
            page.keyboard.press("End")
            assert page.locator(".scene.active").get_attribute("id") == "opening"
            assert page.evaluate("chapterScrollTarget().scrollTop > 0")
            # Deep links and dialog close / re-open flows.
            page.goto(base + "/#price", wait_until="networkidle")
            assert page.locator("#info-dialog").is_visible()
            page.keyboard.press("Escape")
            assert not page.locator("#info-dialog").is_visible()
            page.locator('[data-info="pricing"]').first.click()
            assert page.locator("#info-dialog").is_visible()
            page.locator("#info-dialog .dialog-close").click()
            page.locator('.timeline [data-go="1"]').click()
            page.locator('[data-service="0"]').click()
            contact = page.locator('#info-dialog .dialog-actions a[target="_blank"]')
            assert contact.count() == 1 and contact.get_attribute("rel") == "noopener"
            page.keyboard.press("Escape")
            # Disabling a navigation control must move focus to visible navigation.
            page.locator('.timeline [data-go="4"]').click()
            page.locator("#next-scene").focus()
            page.keyboard.press("Enter")
            assert page.locator('.timeline [data-go="5"]').evaluate("el => el === document.activeElement")
            assert not errors, errors
            context.close()
        browser.close()
    print("Homepage browser checks passed at four viewport sizes; no forms submitted.")
finally:
    server.shutdown()
    server.server_close()
