"""Homepage inquiry regression checks; no network, form submission or analytics hits."""
import json
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
FORM = "https://docs.google.com/forms/d/e/1FAIpQLSeS-G-8U9p5-zMiFGaH3Y0TZjswVbvKOLl1Rg1_uK2GKw0blg/viewform"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.nodes, self.stack = [], []
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "text": "",
                "parents": tuple((n["tag"], n["attrs"].get("id")) for n in self.stack)}
        self.nodes.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        for node in self.stack:
            node["text"] += data

    def select(self, tag=None, **attrs):
        return [n for n in self.nodes if (tag is None or n["tag"] == tag)
                and all(n["attrs"].get(k) == v for k, v in attrs.items())]


class HomepageInquiryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = Page((ROOT / "index.html").read_text(encoding="utf-8"))

    def test_search_and_social_metadata_match_visible_service(self):
        p = self.page
        titles = p.select("title")
        self.assertEqual(len(titles), 1)
        title = titles[0]["text"]
        self.assertIn("企業向けAI動画制作", title)
        for attr, key in [("property", "og:title"), ("name", "twitter:title")]:
            self.assertEqual(p.select("meta", **{attr: key})[0]["attrs"]["content"], title)
        description = p.select("meta", name="description")[0]["attrs"]["content"]
        for attr, key in [("property", "og:description"), ("name", "twitter:description")]:
            self.assertEqual(p.select("meta", **{attr: key})[0]["attrs"]["content"], description)
        data = json.loads(p.select("script", type="application/ld+json")[0]["text"])
        webpage = next(n for n in data["@graph"] if n["@type"] == "WebPage")
        self.assertEqual(webpage["name"], title)
        self.assertEqual(webpage["description"], description)
        self.assertEqual([n["attrs"]["href"] for n in p.select("link", rel="canonical")], ["https://framepact.jp/"])

    def test_opening_has_direct_consultation_and_pricing_links(self):
        opening = self.page.select("section", id="opening")[0]
        self.assertIn("active", opening["attrs"]["class"].split())
        self.assertNotIn("inert", opening["attrs"])
        links = [n for n in self.page.select("a") if ("section", "opening") in n["parents"]]
        primary = [n for n in links if "gold-button" in n["attrs"].get("class", "").split()]
        self.assertEqual(len(primary), 1)
        self.assertEqual(primary[0]["attrs"]["href"], FORM)
        self.assertEqual(primary[0]["attrs"]["target"], "_blank")
        self.assertIn("noopener", primary[0]["attrs"]["rel"].split())
        self.assertIn("制作を相談する", primary[0]["text"])
        self.assertIn("別タブ", primary[0]["attrs"]["aria-label"])
        self.assertTrue(any(n["attrs"].get("href") == "/ai-video-price.html" for n in links))
        self.assertIn("15万円〜（税抜）", opening["text"])

    def test_cinema_structure_and_brand_heading_are_preserved(self):
        p = self.page
        scenes = [n["attrs"]["id"] for n in p.select("section") if "scene" in n["attrs"].get("class", "").split()]
        self.assertEqual(scenes, ["opening", "possibilities", "works", "human", "process", "contact"])
        self.assertEqual(len(p.select("h1")), 1)
        self.assertEqual(p.select("h1")[0]["text"], "その想像は、フレームを超える。")
        self.assertEqual({n["attrs"]["data-go"] for n in p.nodes if "data-go" in n["attrs"]}, set("012345"))
        self.assertEqual({n["attrs"]["data-service"] for n in p.nodes if "data-service" in n["attrs"]}, set("012345"))
        self.assertTrue(p.select("button", **{"data-work": "0"}))
        self.assertTrue(p.select("a", href="/customer-voices.html"))

    def test_contact_explains_what_to_share_without_new_form(self):
        contact = self.page.select("section", id="contact")[0]
        for label in ["用途", "希望納期", "ご予算", "分かる範囲"]:
            self.assertIn(label, contact["text"])
        self.assertFalse(self.page.select("form"))
        self.assertTrue(self.page.select("script", src="/framepact-analytics.js?v=20261010"))
        self.assertTrue(self.page.select("script", src="/framepact-cinema.js?v=20261003-pricing"))

    def test_no_javascript_fallback_has_real_destinations(self):
        links = [n for n in self.page.select("a") if ("noscript", None) in n["parents"]]
        hrefs = {n["attrs"]["href"] for n in links}
        self.assertIn("/ai-video-price.html", hrefs)
        self.assertIn(FORM, hrefs)
        self.assertFalse(hrefs.intersection({"/", "https://framepact.jp/", "#"}))


if __name__ == "__main__":
    unittest.main()
