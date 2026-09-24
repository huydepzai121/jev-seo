"""One-page SEO meta inspection, in the spirit of the SEO META in 1 CLICK browser extension.

Fetches a single URL through the crawler's guarded fetcher and returns everything a
reviewer looks at first: summary tags, headings, images, links, social cards, structured
data, robots.txt and sitemap, plus a weighted on-page score out of 100.
"""
from __future__ import annotations

import json
import re
import time
from urllib.parse import quote, urljoin, urlparse

from bs4 import BeautifulSoup

from jevseo.parse import WORD, host_key

MAX_ITEMS = 500


def _clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _meta(soup, **attrs) -> str | None:
    key, val = next(iter(attrs.items()))
    tag = soup.find("meta", attrs={key: re.compile(f"^{re.escape(val)}$", re.I)})
    return _clean(tag.get("content")) if tag and tag.get("content") is not None else None


def _rel(tag) -> list[str]:
    rel = tag.get("rel") or []
    return [r.lower() for r in (rel if isinstance(rel, list) else rel.split())]


def _schema(soup) -> dict:
    blocks = []
    for tag in soup.find_all("script", type=lambda v: v and "ld+json" in v.lower()):
        raw = (tag.string or tag.get_text() or "").strip()
        try:
            data = json.loads(raw)
            types = []

            def walk(node):
                if isinstance(node, dict):
                    t = node.get("@type")
                    types.extend([t] if isinstance(t, str) else [str(x) for x in t] if isinstance(t, list) else [])
                    for v in node.values():
                        walk(v)
                elif isinstance(node, list):
                    for v in node:
                        walk(v)

            walk(data)
            blocks.append({"valid": True, "types": list(dict.fromkeys(types)), "json": json.dumps(data, indent=2, ensure_ascii=False)[:20000]})
        except (json.JSONDecodeError, ValueError) as err:
            blocks.append({"valid": False, "types": [], "error": str(err)[:200], "json": raw[:5000]})
    microdata = sorted({i.get("itemtype", "").strip() for i in soup.find_all(itemtype=True)} - {""})
    rdfa = sorted({i.get("typeof", "").strip() for i in soup.find_all(attrs={"typeof": True})} - {""})
    return {"jsonld": blocks, "microdata": microdata, "rdfa": rdfa}


def extract(url: str, html: str, *, status: int = 200, headers: dict | None = None, redirects: list[dict] | None = None, ttfb_ms: int | None = None) -> dict:
    """Parse one HTML document into the tabs of the inspector. `url` is the final URL after redirects."""
    headers = {k.lower(): v for k, v in (headers or {}).items()}
    soup = BeautifulSoup(html, "lxml")
    p = urlparse(url)
    site = host_key(p.netloc)
    origin = f"{p.scheme}://{p.netloc}"
    html_tag = soup.find("html")

    titles = [_clean(t.get_text()) for t in soup.find_all("title") if not t.find_parent("svg")]
    canon = next((l for l in soup.find_all("link", href=True) if "canonical" in _rel(l)), None)
    canonical = urljoin(url, canon["href"]) if canon else None
    favicon = next((urljoin(url, l["href"]) for l in soup.find_all("link", href=True) if "icon" in " ".join(_rel(l))), None)
    hreflang = [{"lang": l.get("hreflang"), "href": urljoin(url, l.get("href", ""))} for l in soup.find_all("link", hreflang=True)]

    headings = [{"level": int(h.name[1]), "text": _clean(h.get_text(" "))} for h in soup.find_all(re.compile("^h[1-6]$"))]
    counts = {f"h{i}": sum(1 for h in headings if h["level"] == i) for i in range(1, 7)}
    skips, last = 0, 0
    for h in headings:
        if last and h["level"] > last + 1:
            skips += 1
        last = h["level"]

    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
        images.append({
            "src": urljoin(url, src) if src and not src.startswith("data:") else (src[:60] + "…" if src else ""),
            "alt": img.get("alt"), "title": img.get("title"),
            "width": img.get("width"), "height": img.get("height"), "loading": img.get("loading"),
        })

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("javascript:", "#")) or not href:
            continue
        absolute = urljoin(url, href)
        lp = urlparse(absolute)
        kind = "internal" if lp.scheme in ("http", "https") and host_key(lp.netloc) == site else "external" if lp.scheme in ("http", "https") else "other"
        anchor = _clean(a.get_text(" ")) or (_clean(a.find("img").get("alt")) if a.find("img") else "")
        links.append({"href": absolute, "anchor": anchor[:160], "title": a.get("title"), "rel": " ".join(_rel(a)), "kind": kind})

    og = {}
    twitter = {}
    for m in soup.find_all("meta"):
        key = (m.get("property") or m.get("name") or "").strip()
        val = _clean(m.get("content"))
        if key.lower().startswith(("og:", "article:", "fb:")) and key not in og:
            og[key] = urljoin(url, val) if key.lower() in ("og:image", "og:url", "og:image:url", "og:image:secure_url") and val else val
        elif key.lower().startswith("twitter:") and key not in twitter:
            twitter[key] = urljoin(url, val) if key.lower() in ("twitter:image", "twitter:image:src") and val else val

    body_soup = BeautifulSoup(html, "lxml")
    for tag in body_soup(["script", "style", "noscript", "template", "svg"]):
        tag.decompose()
    text = _clean((body_soup.body or body_soup).get_text(" "))
    words = len(WORD.findall(text))

    x_robots = headers.get("x-robots-tag")
    robots_meta = _meta(soup, name="robots")
    summary = {
        "url": url,
        "status": status,
        "redirects": redirects or [],
        "ttfb_ms": ttfb_ms,
        "bytes": len(html.encode("utf-8", "ignore")),
        "title": titles[0] if titles else None,
        "title_count": len(titles),
        "description": _meta(soup, name="description"),
        "keywords": _meta(soup, name="keywords"),
        "canonical": canonical,
        "canonical_self": bool(canonical) and canonical.rstrip("/") == url.rstrip("/"),
        "robots": robots_meta,
        "googlebot": _meta(soup, name="googlebot"),
        "x_robots_tag": x_robots,
        "author": _meta(soup, name="author"),
        "publisher": next((urljoin(url, l["href"]) for l in soup.find_all("link", href=True) if "publisher" in _rel(l)), None),
        "generator": _meta(soup, name="generator"),
        "lang": html_tag.get("lang") if html_tag else None,
        "charset": (soup.find("meta", charset=True) or {}).get("charset") if soup.find("meta", charset=True) else ("utf-8" if "charset=utf-8" in html[:3000].lower() else None),
        "viewport": _meta(soup, name="viewport"),
        "theme_color": _meta(soup, name="theme-color"),
        "favicon": favicon,
        "hreflang": hreflang,
        "word_count": words,
        "server": headers.get("server"),
        "content_type": headers.get("content-type"),
    }
    data = {
        "summary": summary,
        "headings": {"counts": counts, "skips": skips, "items": headings[:MAX_ITEMS]},
        "images": {
            "total": len(images),
            "missing_alt": sum(1 for i in images if i["alt"] is None),
            "empty_alt": sum(1 for i in images if i["alt"] is not None and not i["alt"].strip()),
            "missing_title": sum(1 for i in images if not i["title"]),
            "no_dimensions": sum(1 for i in images if not (i["width"] and i["height"])),
            "items": images[:MAX_ITEMS],
        },
        "links": {
            "total": len(links),
            "unique": len({l["href"] for l in links}),
            "internal": sum(1 for l in links if l["kind"] == "internal"),
            "external": sum(1 for l in links if l["kind"] == "external"),
            "nofollow": sum(1 for l in links if "nofollow" in l["rel"]),
            "missing_title": sum(1 for l in links if not l["title"]),
            "empty_anchor": sum(1 for l in links if not l["anchor"]),
            "items": links[:MAX_ITEMS],
        },
        "social": {"og": og, "twitter": twitter},
        "schema": _schema(soup),
        "tools": tools(url),
        "origin": origin,
    }
    data["checks"] = checks(data)
    data["score"] = page_score(data["checks"])
    return data


def tools(url: str) -> list[dict]:
    """Shortcuts to third-party checkers for this URL, like the extension's Tools tab."""
    p = urlparse(url)
    e = quote(url, safe="")
    host = p.netloc
    return [
        {"group": "google", "name": "Google: site:", "href": f"https://www.google.com/search?q=site%3A{quote(host)}"},
        {"group": "google", "name": "Google: info (URL)", "href": f"https://www.google.com/search?q={e}"},
        {"group": "google", "name": "PageSpeed Insights", "href": f"https://pagespeed.web.dev/analysis?url={e}"},
        {"group": "google", "name": "Rich Results Test", "href": f"https://search.google.com/test/rich-results?url={e}"},
        {"group": "google", "name": "Search Console", "href": f"https://search.google.com/search-console?resource_id={quote(p.scheme + '://' + host + '/', safe='')}"},
        {"group": "validators", "name": "Schema.org Validator", "href": f"https://validator.schema.org/#url={e}"},
        {"group": "validators", "name": "W3C HTML Validator", "href": f"https://validator.w3.org/nu/?doc={e}"},
        {"group": "validators", "name": "W3C CSS Validator", "href": f"https://jigsaw.w3.org/css-validator/validator?uri={e}"},
        {"group": "social", "name": "Facebook Sharing Debugger", "href": f"https://developers.facebook.com/tools/debug/?q={e}"},
        {"group": "social", "name": "LinkedIn Post Inspector", "href": f"https://www.linkedin.com/post-inspector/inspect/{e}"},
        {"group": "other", "name": "Bing: site:", "href": f"https://www.bing.com/search?q=site%3A{quote(host)}"},
        {"group": "other", "name": "Ahrefs Backlink Checker", "href": f"https://ahrefs.com/backlink-checker?input={quote(host)}"},
        {"group": "other", "name": "Wayback Machine", "href": f"https://web.archive.org/web/*/{host}"},
        {"group": "other", "name": "SecurityHeaders", "href": f"https://securityheaders.com/?q={e}&followRedirects=on"},
        {"group": "other", "name": "robots.txt", "href": f"{p.scheme}://{host}/robots.txt"},
        {"group": "other", "name": "sitemap.xml", "href": f"{p.scheme}://{host}/sitemap.xml"},
    ]


def _check(cid: str, weight: int, state: str, value, vi: str, en: str) -> dict:
    return {"id": cid, "weight": weight, "state": state, "value": value, "vi": vi, "en": en}


def checks(d: dict) -> list[dict]:
    """On-page checks with weights summing to 100. state: pass (full weight), warn (half), fail (none)."""
    s, h, im, so, sc = d["summary"], d["headings"], d["images"], d["social"], d["schema"]
    out = []
    ok = s["status"] == 200
    out.append(_check("status", 5, "pass" if ok else "fail", s["status"], f"Mã trạng thái HTTP {s['status']}", f"HTTP status {s['status']}"))
    robots = " ".join(filter(None, [s["robots"], s["googlebot"], s["x_robots_tag"]])).lower()
    out.append(_check("indexable", 10, "fail" if "noindex" in robots else "pass", robots or "index", "Trang bị chặn lập chỉ mục (noindex)" if "noindex" in robots else "Trang cho phép lập chỉ mục", "Page blocked with noindex" if "noindex" in robots else "Page can be indexed"))
    out.append(_check("https", 5, "pass" if s["url"].startswith("https://") else "fail", s["url"].split(":")[0], "Trang dùng HTTPS" if s["url"].startswith("https://") else "Trang không dùng HTTPS", "Served over HTTPS" if s["url"].startswith("https://") else "Not served over HTTPS"))
    tl = len(s["title"] or "")
    out.append(_check("title", 10, "pass" if tl else "fail", s["title"], "Có thẻ title" if tl else "Thiếu thẻ title", "Title present" if tl else "Title missing"))
    out.append(_check("title_length", 4, "pass" if 30 <= tl <= 65 else "warn" if tl else "fail", tl, f"Độ dài title {tl} ký tự (nên 30–65)", f"Title length {tl} characters (30–65 recommended)"))
    dl = len(s["description"] or "")
    out.append(_check("description", 8, "pass" if dl else "fail", s["description"], "Có meta description" if dl else "Thiếu meta description", "Meta description present" if dl else "Meta description missing"))
    out.append(_check("description_length", 4, "pass" if 70 <= dl <= 160 else "warn" if dl else "fail", dl, f"Độ dài description {dl} ký tự (nên 70–160)", f"Description length {dl} characters (70–160 recommended)"))
    h1 = h["counts"]["h1"]
    out.append(_check("h1", 8, "pass" if h1 == 1 else "warn" if h1 > 1 else "fail", h1, f"Số thẻ H1: {h1} (nên đúng 1)", f"H1 count: {h1} (exactly 1 recommended)"))
    out.append(_check("heading_order", 3, "pass" if not h["skips"] else "warn", h["skips"], "Thứ tự tiêu đề hợp lý" if not h["skips"] else f"Bỏ qua cấp tiêu đề {h['skips']} lần", "Heading levels in order" if not h["skips"] else f"Heading levels skipped {h['skips']} times"))
    out.append(_check("canonical", 5, "pass" if s["canonical"] else "fail", s["canonical"], "Có thẻ canonical" if s["canonical"] else "Thiếu thẻ canonical", "Canonical present" if s["canonical"] else "Canonical missing"))
    out.append(_check("lang", 3, "pass" if s["lang"] else "fail", s["lang"], f"Ngôn ngữ trang: {s['lang']}" if s["lang"] else "Thiếu thuộc tính lang", f"Page language: {s['lang']}" if s["lang"] else "lang attribute missing"))
    out.append(_check("viewport", 5, "pass" if s["viewport"] else "fail", s["viewport"], "Có meta viewport (thân thiện di động)" if s["viewport"] else "Thiếu meta viewport", "Viewport meta present" if s["viewport"] else "Viewport meta missing"))
    out.append(_check("charset", 1, "pass" if s["charset"] else "warn", s["charset"], "Có khai báo charset" if s["charset"] else "Thiếu khai báo charset", "Charset declared" if s["charset"] else "Charset not declared"))
    total, missing = im["total"], im["missing_alt"]
    share = 1 - missing / total if total else 1
    out.append(_check("images_alt", 6, "pass" if share == 1 else "warn" if share >= 0.8 else "fail", missing, f"{missing}/{total} ảnh thiếu alt", f"{missing}/{total} images without alt"))
    og = so["og"]
    has_og = all(og.get(k) for k in ("og:title", "og:description", "og:image"))
    out.append(_check("open_graph", 5, "pass" if has_og else "warn" if og else "fail", len(og), "Đủ og:title, og:description, og:image" if has_og else "Thiếu thẻ Open Graph quan trọng", "og:title, og:description and og:image present" if has_og else "Key Open Graph tags missing"))
    tc = so["twitter"].get("twitter:card")
    out.append(_check("twitter_card", 2, "pass" if tc else "warn", tc, f"Twitter card: {tc}" if tc else "Thiếu twitter:card", f"Twitter card: {tc}" if tc else "twitter:card missing"))
    blocks = sc["jsonld"]
    bad = sum(1 for b in blocks if not b["valid"])
    has_sd = bool(blocks or sc["microdata"])
    out.append(_check("structured_data", 6, "fail" if bad else "pass" if has_sd else "warn", len(blocks), f"{bad} khối JSON-LD bị lỗi cú pháp" if bad else "Có dữ liệu có cấu trúc" if has_sd else "Không có dữ liệu có cấu trúc", f"{bad} JSON-LD blocks fail to parse" if bad else "Structured data present" if has_sd else "No structured data"))
    out.append(_check("favicon", 2, "pass" if s["favicon"] else "warn", s["favicon"], "Có favicon" if s["favicon"] else "Chưa khai báo favicon", "Favicon declared" if s["favicon"] else "No favicon declared"))
    wc = s["word_count"]
    out.append(_check("content", 5, "pass" if wc >= 300 else "warn" if wc >= 100 else "fail", wc, f"{wc} từ nội dung (nên từ 300)", f"{wc} words of content (300+ recommended)"))
    ttfb = s["ttfb_ms"]
    out.append(_check("response_time", 3, "pass" if ttfb is not None and ttfb <= 800 else "warn" if ttfb is not None and ttfb <= 1800 else "fail", ttfb, f"Thời gian phản hồi {ttfb} ms (nên ≤ 800)", f"Response time {ttfb} ms (≤ 800 recommended)"))
    return out


def page_score(items: list[dict]) -> int:
    got = sum(c["weight"] * (1 if c["state"] == "pass" else 0.5 if c["state"] == "warn" else 0) for c in items)
    return round(100 * got / sum(c["weight"] for c in items))


def inspect(url: str) -> dict:
    """Fetch one URL with the guarded crawler fetcher, then read its robots.txt and sitemap."""
    from jevseo import crawl

    if "://" not in url:
        url = "https://" + url
    if urlparse(url).scheme not in ("http", "https") or not urlparse(url).hostname:
        raise ValueError("invalid_url")
    fetcher = crawl.Fetcher()
    t = time.monotonic()
    r = fetcher.get(url)
    if r is None:
        raise ConnectionError("unreachable")
    ttfb = round(r.elapsed.total_seconds() * 1000) if r.elapsed else round((time.monotonic() - t) * 1000)
    ctype = r.headers.get("content-type", "")
    if "html" not in ctype.lower() and "xml" not in ctype.lower():
        raise ValueError("not_html")
    redirects = [{"url": h.url, "status": h.status_code} for h in r.history]
    data = extract(r.url, crawl.decode(r), status=r.status_code, headers=dict(r.headers), redirects=redirects, ttfb_ms=ttfb)
    robots = crawl.read_robots(fetcher, data["origin"])
    data["robots_txt"] = {"url": robots["url"], "status": robots["status"], "present": robots["present"], "sitemaps": robots["sitemaps"], "disallow_all": robots["disallow_all"], "ai_bots": robots.get("ai_bots", {})}
    sitemap_urls = robots["sitemaps"] or [data["origin"] + "/sitemap.xml"]
    sm = crawl.read_sitemaps(fetcher, sitemap_urls[:3], limit=2000)
    data["sitemap"] = {"files": sm["files"][:10], "total_urls": sm["total_urls"]}
    return data
