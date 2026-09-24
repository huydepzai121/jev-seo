"""Offline tests for the one-page inspector and the web app: no network, no spend."""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jevseo import i18n_vi, meta, web  # noqa: E402
from jevseo.checks import RULES  # noqa: E402
from jevseo.score import DFS_RULES, JEV_RULES  # noqa: E402

PAGE = """<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>Cà phê Hạt Mộc | Rang xay thủ công tại Đà Lạt</title>
<meta name="description" content="Hạt Mộc rang xay cà phê Arabica Cầu Đất theo mẻ nhỏ mỗi tuần, giao tận nơi toàn quốc.">
<meta name="robots" content="index, follow"><link rel="canonical" href="https://hatmoc.vn/"><link rel="icon" href="/favicon.ico">
<link rel="alternate" hreflang="en" href="https://hatmoc.vn/en/">
<meta property="og:title" content="Hạt Mộc"><meta property="og:image" content="/og.jpg"><meta name="twitter:card" content="summary">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Hạt Mộc"}</script>
<script type="application/ld+json">{ broken </script>
</head><body><h1>Cà phê rang xay</h1><h3>Bỏ cấp</h3><h2>Giao hàng</h2>
<img src="/a.jpg" alt="Bao cà phê" width="4" height="3"><img src="/b.jpg">
<a href="/blog">Blog</a><a href="https://facebook.com/hatmoc" rel="nofollow" title="Facebook">FB</a><a href="mailto:a@b.vn">Mail</a><a href="#top">Lên</a>
</body></html>"""


class InspectorTest(unittest.TestCase):
    def setUp(self):
        self.d = meta.extract("https://hatmoc.vn/", PAGE, status=200, headers={"Server": "nginx"}, ttfb_ms=120)

    def test_summary(self):
        s = self.d["summary"]
        self.assertEqual(s["title"], "Cà phê Hạt Mộc | Rang xay thủ công tại Đà Lạt")
        self.assertTrue(s["canonical_self"])
        self.assertEqual(s["lang"], "vi")
        self.assertEqual(s["favicon"], "https://hatmoc.vn/favicon.ico")
        self.assertEqual(s["hreflang"], [{"lang": "en", "href": "https://hatmoc.vn/en/"}])
        self.assertEqual(s["server"], "nginx")

    def test_headings_images_links(self):
        self.assertEqual(self.d["headings"]["counts"]["h1"], 1)
        self.assertEqual(self.d["headings"]["skips"], 1)
        self.assertEqual(self.d["images"]["total"], 2)
        self.assertEqual(self.d["images"]["missing_alt"], 1)
        L = self.d["links"]
        self.assertEqual((L["internal"], L["external"], L["nofollow"]), (1, 1, 1))
        self.assertIn("other", {x["kind"] for x in L["items"]})  # mailto kept, fragment-only link dropped
        self.assertEqual(L["total"], 3)

    def test_social_and_schema(self):
        self.assertEqual(self.d["social"]["og"]["og:image"], "https://hatmoc.vn/og.jpg")
        self.assertEqual(self.d["social"]["twitter"]["twitter:card"], "summary")
        blocks = self.d["schema"]["jsonld"]
        self.assertEqual([b["valid"] for b in blocks], [True, False])
        self.assertEqual(blocks[0]["types"], ["Organization"])

    def test_score(self):
        weights = sum(c["weight"] for c in self.d["checks"])
        self.assertEqual(weights, 100)
        by = {c["id"]: c["state"] for c in self.d["checks"]}
        self.assertEqual(by["structured_data"], "fail")  # one JSON-LD block does not parse
        self.assertEqual(by["open_graph"], "warn")  # og:description missing
        self.assertEqual(by["images_alt"], "fail")
        self.assertTrue(0 < self.d["score"] < 100)

    def test_noindex_fails(self):
        d = meta.extract("http://x.vn/", "<html><head><title>x</title></head><body></body></html>", headers={"X-Robots-Tag": "noindex"})
        self.assertEqual({c["id"]: c["state"] for c in d["checks"]}["indexable"], "fail")
        self.assertLess(d["score"], 40)

    def test_tools_are_encoded(self):
        hrefs = [t["href"] for t in self.d["tools"]]
        self.assertTrue(all(h.startswith("https://") for h in hrefs if "robots.txt" not in h and "sitemap.xml" not in h))
        self.assertIn("https://pagespeed.web.dev/analysis?url=https%3A%2F%2Fhatmoc.vn%2F", hrefs)


class VietnameseTest(unittest.TestCase):
    def test_every_rule_translated(self):
        ids = set(RULES) | set(JEV_RULES) | set(DFS_RULES) | {"cwv_field", "lab_performance"}
        self.assertEqual(ids - set(i18n_vi.RULES), set())

    def test_localize_falls_back(self):
        row = i18n_vi.localize_action({"id": "unknown", "title": "T", "fix": "F", "category": "crawl", "severity": "high"})
        self.assertEqual((row["title_vi"], row["fix_vi"], row["category_vi"], row["severity_vi"]), ("T", "F", "Thu thập và lập chỉ mục", "Cao"))


class WebTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.jobs = web.Jobs(Path(cls.tmp.name))
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), web.make_handler(cls.jobs))
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.tmp.cleanup()

    def call(self, path, body=None):
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode() if body is not None else None, headers={"Content-Type": "application/json"})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(req, timeout=10) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as err:
            return err.code, err.read()

    def test_index_served(self):
        code, body = self.call("/")
        self.assertEqual(code, 200)
        self.assertIn(b"Jev SEO Check", body)

    def test_inspect(self):
        with mock.patch.object(meta, "inspect", return_value={"score": 77}) as fake:
            code, body = self.call("/api/inspect", {"url": "hatmoc.vn"})
        self.assertEqual((code, json.loads(body)), (200, {"score": 77}))
        fake.assert_called_once_with("https://hatmoc.vn")

    def test_invalid_url(self):
        for bad in ("", "ftp://x.vn", "localhost", "javascript:alert(1)"):
            code, body = self.call("/api/inspect", {"url": bad})
            self.assertEqual(code, 400, bad)
            self.assertIn("message_vi", json.loads(body))

    def test_unreachable(self):
        with mock.patch.object(meta, "inspect", side_effect=ConnectionError("unreachable")):
            code, body = self.call("/api/inspect", {"url": "https://hatmoc.vn"})
        self.assertEqual(code, 502)

    def test_audit_error_reported(self):
        with mock.patch("jevseo.cli.audit", side_effect=SystemExit("Could not reach https://hatmoc.vn/.")):
            code, body = self.call("/api/audits", {"url": "https://hatmoc.vn", "pages": 10, "pagespeed": False})
            self.assertEqual(code, 202)
            jid = json.loads(body)["id"]
            for _ in range(100):
                view = json.loads(self.call(f"/api/audits/{jid}")[1])
                if view["status"] == "error":
                    break
                threading.Event().wait(0.05)
        self.assertEqual(view["status"], "error")
        self.assertTrue(view["error_vi"].startswith("Không truy cập được"))

    def test_files_whitelisted(self):
        self.assertEqual(self.call("/api/audits/nope/files/audit.json")[0], 404)
        self.assertEqual(self.call("/api/audits/nope")[0], 404)


class SummarizeTest(unittest.TestCase):
    def test_summarize(self):
        from test_jevseo import crawl_fixture  # noqa: PLC0415  reuse the engine fixture

        from jevseo import checks, score

        site = crawl_fixture()
        judged = {"available": False, "pages": {}, "site": None}
        findings = checks.run_checks(site)
        data = {"site": {k: v for k, v in site.items() if k != "pages"}, "pages": site["pages"], "passed_rules": checks.passed_rules(findings),
                "scores": score.score(site, findings, judged, None), "actions": score.actions(findings, judged, 4), "run": {"finished_at": "2026-09-24T00:00:00+00:00"}}
        r = web.summarize(data)
        self.assertEqual(r["overall"], data["scores"]["overall"])
        self.assertEqual(len(r["categories"]), 9)
        self.assertTrue(all(a["title_vi"] for a in r["actions"]))
        self.assertEqual(len(r["partial_vi"]), 2)
        self.assertTrue(all(p.startswith("Không có") for p in r["partial_vi"]))


if __name__ == "__main__":
    unittest.main()
