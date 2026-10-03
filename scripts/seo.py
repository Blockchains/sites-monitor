#!/usr/bin/env python3
"""Daily SEO basics on the custom domain homepage: title, meta description, canonical, Open Graph tags
(og:url / canonical must be on the custom domain), robots.txt, sitemap, favicon, apple-touch-icon, manifest."""
import argparse, re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
from common import domains, fetch, now_iso, write_json


class Head(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta, self.links, self.title, self._in_title = {}, [], None, False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key and key not in self.meta:
                self.meta[key] = a.get("content", "").strip()
        elif tag == "link":
            self.links.append(a)
        elif tag == "title" and self.title is None:
            self._in_title, self.title = True, ""

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def on_domain(url, dom):
    try:
        h = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return h in (dom, "www." + dom)


def ok_url(u):
    r = fetch(u, timeout=20, max_bytes=300_000)
    return bool(r["code"] and 200 <= r["code"] < 300), r


def looks_html(r):
    return b"<html" in r["body"][:2000].lower() or "text/html" in r["headers"].get("content-type", "")


def check(d):
    dom = d["domain"]
    base = f"https://{dom}/"
    r = fetch(base, timeout=25)
    res = {"domain": dom, "locked": bool(d.get("locked")), "status": r["code"], "checks": {}, "values": {}}
    p = Head()
    try:
        p.feed(r["body"].decode("utf-8", "replace"))
    except Exception:
        pass
    m, c = p.meta, res["checks"]
    title = (p.title or "").strip()
    desc = m.get("description", "")
    rel = lambda name: [l for l in p.links if name in l.get("rel", "").lower().split()]
    canon = (rel("canonical") or [{}])[0].get("href", "")
    res["values"] = {"title": title, "description": desc, "canonical": canon, "og:title": m.get("og:title", ""),
                     "og:description": m.get("og:description", ""), "og:image": m.get("og:image", ""),
                     "og:url": m.get("og:url", "")}
    c["title"] = bool(title)
    c["description"] = bool(desc)
    c["canonical_on_domain"] = bool(canon) and on_domain(urljoin(base, canon), dom)
    c["og_title"] = bool(m.get("og:title"))
    c["og_description"] = bool(m.get("og:description"))
    c["og_image"] = bool(m.get("og:image"))
    c["og_url_on_domain"] = bool(m.get("og:url")) and on_domain(m.get("og:url"), dom)
    # robots + sitemap (SPA fallbacks return index.html with 200 -> reject HTML bodies)
    ok, rr = ok_url(base + "robots.txt")
    robots_txt = rr["body"].decode("utf-8", "replace") if ok and not looks_html(rr) else ""
    c["robots_txt"] = bool(robots_txt.strip())
    sm_urls = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots_txt) or [base + "sitemap.xml"]
    sm_ok = False
    for u in sm_urls[:3]:
        ok, sr = ok_url(u)
        if ok and (b"<urlset" in sr["body"][:5000] or b"<sitemapindex" in sr["body"][:5000]):
            sm_ok = True
            break
    c["sitemap"] = sm_ok
    # favicon / apple-touch / manifest
    icon = [l for l in p.links if "icon" in l.get("rel", "").lower().split()]
    fav_url = urljoin(base, icon[0]["href"]) if icon and icon[0].get("href") else base + "favicon.ico"
    ok, fr = ok_url(fav_url)
    c["favicon"] = ok and not looks_html(fr)
    at = rel("apple-touch-icon")
    at_url = urljoin(base, at[0]["href"]) if at and at[0].get("href") else base + "apple-touch-icon.png"
    ok, ar = ok_url(at_url)
    c["apple_touch_icon"] = ok and not looks_html(ar)
    mf = rel("manifest")
    if mf and mf[0].get("href"):
        ok, mr = ok_url(urljoin(base, mf[0]["href"]))
        c["manifest"] = ok and mr["body"].lstrip()[:1] == b"{"
    else:
        c["manifest"] = False
    res["failed"] = [k for k, v in c.items() if not v]
    res["ok"] = not res["failed"] and r["code"] == 200
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(check, domains()))
    write_json(f"{a.out}/seo/latest.json", {"checked_at": now_iso(), "results": res})
    findings = [{"domain": x["domain"], "check": "seo", "ok": x["ok"], "skip_issue": x["locked"],
                 "detail": "All SEO basics present" if x["ok"] else
                 f"HTTP {x['status']}; failing: {', '.join(x['failed']) or 'homepage status'}"} for x in res]
    write_json(f"{a.out}/findings-seo.json", findings)
    for x in res:
        print(f"{x['domain']:28s} {'PASS' if x['ok'] else 'FAIL'} {','.join(x['failed'])}")


if __name__ == "__main__":
    main()
