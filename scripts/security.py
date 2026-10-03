#!/usr/bin/env python3
"""Weekly: security response headers + exposed-file probe (/.env, /.git/HEAD, /.git/config).
Never stores response bodies of probed files — only whether they look exposed."""
import argparse, re
from concurrent.futures import ThreadPoolExecutor
from common import domains, fetch, now_iso, write_json

REQUIRED = ["strict-transport-security", "x-content-type-options", "referrer-policy"]
RECOMMENDED = ["content-security-policy", "permissions-policy"]
PROBES = {
    "/.env": lambda b: bool(re.search(rb"(?m)^[A-Z][A-Z0-9_]{2,}\s*=", b)) and b"<html" not in b[:2000].lower(),
    "/.git/HEAD": lambda b: b.lstrip().startswith(b"ref:") or bool(re.fullmatch(rb"\s*[0-9a-f]{40}\s*", b[:100])),
    "/.git/config": lambda b: b"[core]" in b[:2000] and b"<html" not in b[:2000].lower(),
}


def check(d):
    dom = d["domain"]
    r = fetch(f"https://{dom}/", timeout=25, max_bytes=100_000)
    h = r["headers"]
    present = {k: (k in h) for k in REQUIRED + RECOMMENDED}
    csp = h.get("content-security-policy", "")
    present["clickjacking (x-frame-options or csp frame-ancestors)"] = "x-frame-options" in h or "frame-ancestors" in csp
    exposed = {}
    for path, looks in PROBES.items():
        pr = fetch(f"https://{dom}{path}", timeout=20, max_bytes=20_000, follow=False)
        exposed[path] = {"status": pr["code"], "exposed": bool(pr["code"] == 200 and looks(pr["body"]))}
    missing_required = [k for k in REQUIRED + ["clickjacking (x-frame-options or csp frame-ancestors)"] if not present[k]]
    missing_recommended = [k for k in RECOMMENDED if not present[k]]
    exp = [p for p, v in exposed.items() if v["exposed"]]
    return {"domain": dom, "locked": bool(d.get("locked")), "status": r["code"], "headers_present": present,
            "missing_required": missing_required, "missing_recommended": missing_recommended,
            "probes": exposed, "exposed_paths": exp, "ok_headers": not missing_required, "ok_exposed": not exp}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(check, domains()))
    write_json(f"{a.out}/security/latest.json", {"checked_at": now_iso(), "results": res})
    f = []
    for x in res:
        f.append({"domain": x["domain"], "check": "security-headers", "ok": x["ok_headers"],
                  "detail": "Required security headers present" + (f" (recommended missing: {', '.join(x['missing_recommended'])})" if x['missing_recommended'] else "")
                  if x["ok_headers"] else f"Missing required: {', '.join(x['missing_required'])}; recommended missing: {', '.join(x['missing_recommended']) or 'none'}"})
        f.append({"domain": x["domain"], "check": "exposed-files", "ok": x["ok_exposed"],
                  "detail": "No exposed /.env or /.git files" if x["ok_exposed"] else
                  "A sensitive path appears publicly readable - see the latest workflow run / data/security/latest.json. Rotate any credentials and block the path."})
    write_json(f"{a.out}/findings-security.json", f)
    for x in res:
        print(f"{x['domain']:28s} missing={x['missing_required']} exposed={x['exposed_paths']}")


if __name__ == "__main__":
    main()
