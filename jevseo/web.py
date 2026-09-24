"""Web app: type a URL, get the one-page meta inspector at once and the full site audit score as it runs.

Standard library HTTP server, no extra dependencies. Audits run one at a time in a
background worker (the engine logs through module globals and the paid APIs have
per-run caps), while one-page inspections run concurrently.

  GET  /                                  the app
  POST /api/inspect        {"url"}        one-page meta inspection and on-page score
  POST /api/audits         {"url", "pages", "pagespeed"}  queue a site audit, returns {"id"}
  GET  /api/audits/<id>                   progress, then scores and ranked actions
  GET  /api/audits/<id>/files/<name>      report.pdf, report.xlsx or report.md
"""
from __future__ import annotations

import json
import queue
import re
import secrets
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from jevseo import VERSION, i18n_vi

TEMPLATE = Path(__file__).parent / "templates" / "web.html"
FILES = {"report.pdf": "application/pdf", "report.xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "report.md": "text/markdown; charset=utf-8"}
PAGE_CHOICES = {10, 30, 60}
MAX_QUEUE = 20
STAGE = re.compile(r"== (\d)/(\d) ")
PARTIAL_VI = {
    "Jev judgments unavailable, so content quality was not assessed": "Không có đánh giá Jev (thiếu TYPESAFE_API_KEY), nên chưa chấm chất lượng nội dung",
    "PageSpeed Insights unavailable, so performance used crawl timings only": "Không có PageSpeed Insights, nên hiệu năng chỉ dựa trên thời gian tải khi thu thập",
}
ERRORS_VI = {
    "invalid_url": "URL không hợp lệ. Hãy nhập dạng https://ten-mien.com",
    "unreachable": "Không truy cập được trang này (lỗi mạng, hết thời gian chờ, hoặc địa chỉ nội bộ bị chặn).",
    "not_html": "URL này không trả về trang HTML.",
    "queue_full": "Hàng đợi đang đầy, hãy thử lại sau ít phút.",
}


def error_vi(msg: str) -> str:
    """Vietnamese wording for the engine's fatal audit errors."""
    for en, vi in (("Could not reach", "Không truy cập được"), ("Refusing to crawl", "Từ chối thu thập (địa chỉ nội bộ hoặc không phân giải được):")):
        if msg.startswith(en):
            return vi + msg[len(en):]
    return msg


def normalize_input(url: str) -> str:
    url = (url or "").strip()
    if url and "://" not in url:
        url = "https://" + url
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname or "." not in p.hostname or len(url) > 2000:
        raise ValueError("invalid_url")
    return url


class Jobs:
    """Site audits, run one at a time by a single worker thread."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.jobs: dict[str, dict] = {}
        self.order: list[str] = []
        self.lock = threading.Lock()
        self.queue: queue.Queue[str] = queue.Queue()
        threading.Thread(target=self._worker, daemon=True).start()

    def submit(self, url: str, pages: int, pagespeed: bool) -> dict:
        with self.lock:
            waiting = sum(1 for j in self.jobs.values() if j["status"] in ("queued", "running"))
            if waiting >= MAX_QUEUE:
                raise OverflowError("queue_full")
            jid = secrets.token_urlsafe(9)
            self.jobs[jid] = {"id": jid, "url": url, "pages": pages, "pagespeed": pagespeed, "status": "queued", "stage": 0, "stages": 7,
                              "log": [], "created": time.time(), "error": None, "error_vi": None, "result": None, "files": []}
            self.order.append(jid)
        self.queue.put(jid)
        return self.view(jid)

    def view(self, jid: str) -> dict | None:
        with self.lock:
            j = self.jobs.get(jid)
            if not j:
                return None
            ahead = sum(1 for k in self.order if self.jobs[k]["status"] == "queued" and self.jobs[k]["created"] < j["created"])
            return {k: v for k, v in j.items() if k != "dir"} | {"log": j["log"][-80:], "queue_position": ahead if j["status"] == "queued" else 0}

    def file(self, jid: str, name: str) -> Path | None:
        j = self.jobs.get(jid)
        if not j or name not in FILES or name not in j["files"]:
            return None
        path = j["dir"] / name
        return path if path.is_file() else None

    def _log(self, jid: str, msg: str) -> None:
        msg = msg.replace(str(self.jobs[jid].get("dir", "")), "").replace(str(self.data_dir.resolve()), "").replace(str(self.data_dir), "")  # no server paths
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        with self.lock:
            j = self.jobs[jid]
            j["log"].append(line)
            m = STAGE.search(msg)
            if m:
                j["stage"] = int(m.group(1))

    def _worker(self) -> None:
        while True:
            jid = self.queue.get()
            try:
                self._run(jid)
            except BaseException as err:  # noqa: BLE001  the engine raises SystemExit for unreachable sites
                with self.lock:
                    self.jobs[jid]["status"] = "error"
                    self.jobs[jid]["error"] = str(err) or type(err).__name__
                    self.jobs[jid]["error_vi"] = error_vi(self.jobs[jid]["error"])
                if not isinstance(err, SystemExit):
                    traceback.print_exc()

    def _run(self, jid: str) -> None:
        from jevseo import cli

        j = self.jobs[jid]
        out = self.data_dir / f"{urlparse(j['url']).hostname}-{time.strftime('%Y%m%d-%H%M%S')}-{jid[:6]}"
        j["dir"] = out
        with self.lock:
            j["status"] = "running"
        argv = ["audit", j["url"], "--out", str(out), "--max-pages", str(j["pages"]), "--jev-pages", str(j["pages"]), "--time-budget", "300"]
        if not j["pagespeed"]:
            argv.append("--no-psi")
        args = cli.build_parser().parse_args(argv)
        original = cli.log
        cli.log = lambda msg: (self._log(jid, msg), original(msg))  # noqa: E731  one worker thread, so one audit patches at a time
        try:
            cli.audit(args)
            data = json.loads((out / "audit.json").read_text())
            with self.lock:
                j["result"] = summarize(data)
            try:
                cli.stage(7, "pdf,xlsx,md")
                from jevseo.report import build

                written = build(out, formats=["pdf", "xlsx", "md"], log=cli.log)
                j["files"] = [Path(p).name for p in written.values()]
            except Exception as err:  # noqa: BLE001  the score stands even if a report format fails
                self._log(jid, f"report rendering failed: {type(err).__name__}: {err}")
                j["files"] = [n for n in FILES if (out / n).is_file()]
            with self.lock:
                j["status"] = "done"
                j["stage"] = 7
        finally:
            cli.log = original


def summarize(d: dict) -> dict:
    """The parts of audit.json the web page shows, with Vietnamese labels alongside."""
    s = d["scores"]
    acts = []
    for a in d["actions"][:150]:
        row = {k: a[k] for k in ("action_id", "id", "priority", "impact", "effort", "quick_win", "origin", "category", "severity", "title", "fix", "source", "count", "evidence", "heuristic", "needs_review")}
        row["urls"] = a["urls"][:12]
        acts.append(i18n_vi.localize_action(row))
    pages = [p for p in d["pages"] if p.get("kind") == "page"]
    return {
        "domain": d["site"]["domain"],
        "final_url": d["site"]["final_url"],
        "overall": s["overall"],
        "grade": s["grade"],
        "categories": [{"id": c, "score": v, "weight": s["weights"][c], "name": s["category_names"][c], "name_vi": i18n_vi.CATEGORIES.get(c, c), "note": s["notes"].get(c)} for c, v in s["categories"].items()],
        "partial": s.get("partial") or [],
        "partial_vi": [PARTIAL_VI.get(p, p) for p in s.get("partial") or []],
        "caps": s.get("caps") or [],
        "completeness": s["completeness"],
        "pages_crawled": len(d["pages"]),
        "html_pages": len(pages),
        "hit_page_cap": d["site"].get("limits", {}).get("hit_page_cap"),
        "passed_rules": len(d.get("passed_rules") or []),
        "actions": acts,
        "counts": {p: sum(1 for a in d["actions"] if a["priority"] == p) for p in ("P1", "P2", "P3")},
        "finished_at": d["run"]["finished_at"],
    }


def make_handler(jobs: Jobs):
    class Handler(BaseHTTPRequestHandler):
        server_version = f"jevseo/{VERSION}"

        def log_message(self, fmt, *args):  # quieter access log
            if not self.path.startswith("/api/audits/"):
                super().log_message(fmt, *args)

        def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, payload) -> None:
            self._send(code, json.dumps(payload, ensure_ascii=False, default=str).encode(), "application/json; charset=utf-8", {"Cache-Control": "no-store"})

        def _error(self, code: int, key: str) -> None:
            self._json(code, {"error": key, "message_vi": ERRORS_VI.get(key, key), "message": key.replace("_", " ")})

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 10_000:
                raise ValueError("invalid_url")
            try:
                return json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError as err:
                raise ValueError("invalid_url") from err

        def do_GET(self):  # noqa: N802
            path = urlparse(self.path).path
            if path == "/":
                return self._send(200, TEMPLATE.read_bytes(), "text/html; charset=utf-8", {"Cache-Control": "no-cache"})
            if path == "/healthz":
                return self._json(200, {"ok": True, "version": VERSION})
            m = re.fullmatch(r"/api/audits/([\w-]+)", path)
            if m:
                v = jobs.view(m.group(1))
                return self._json(200, v) if v else self._error(404, "not_found")
            m = re.fullmatch(r"/api/audits/([\w-]+)/files/([\w.]+)", path)
            if m:
                f = jobs.file(m.group(1), m.group(2))
                if not f:
                    return self._error(404, "not_found")
                return self._send(200, f.read_bytes(), FILES[f.name], {"Content-Disposition": f'attachment; filename="jev-seo-{f.parent.name}-{f.name}"'})
            self._error(404, "not_found")

        def do_POST(self):  # noqa: N802
            path = urlparse(self.path).path
            try:
                body = self._body()
                url = normalize_input(body.get("url", ""))
                if path == "/api/inspect":
                    from jevseo import meta

                    return self._json(200, meta.inspect(url))
                if path == "/api/audits":
                    pages = int(body.get("pages") or 30)
                    pages = pages if pages in PAGE_CHOICES else 30
                    return self._json(202, jobs.submit(url, pages, bool(body.get("pagespeed", True))))
                self._error(404, "not_found")
            except ValueError as err:
                self._error(400, str(err) if str(err) in ERRORS_VI else "invalid_url")
            except ConnectionError:
                self._error(502, "unreachable")
            except OverflowError:
                self._error(429, "queue_full")

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8000, data_dir: Path = Path("jev-seo-reports/web")) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((host, port), make_handler(Jobs(data_dir)))
    shown = "localhost" if host in ("0.0.0.0", "127.0.0.1", "") else host
    print(f"jev-seo web {VERSION}: http://{shown}:{port}/  (Ctrl+C to stop)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
