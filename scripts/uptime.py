#!/usr/bin/env python3
"""Every-10-min check: HTTP status, response time, TLS expiry. Writes <out>/uptime/latest.json,
appends to <out>/uptime/history-YYYY-MM.jsonl, and emits findings for the issue manager."""
import argparse, json, sys, time
from concurrent.futures import ThreadPoolExecutor
from common import domains, fetch, tls_expiry, now_iso, write_json, read_json

TLS_WARN_DAYS = 14
SLOW_MS = 5000


def check(d):
    dom = d["domain"]
    r = fetch(f"https://{dom}/", timeout=20, max_bytes=200_000)
    if not (r["code"] and 200 <= r["code"] < 400):
        time.sleep(5)  # one retry to avoid flapping on a single blip
        r = fetch(f"https://{dom}/", timeout=25, max_bytes=200_000)
    exp, days, terr = tls_expiry(dom)
    up = bool(r["code"] and 200 <= r["code"] < 400)
    return {"domain": dom, "locked": bool(d.get("locked")), "up": up, "status": r["code"], "ms": r["ms"],
            "final_url": r["url"], "error": r["err"], "tls_expires": exp, "tls_days_left": days, "tls_error": terr}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ts = now_iso()
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(check, domains()))
    write_json(f"{a.out}/uptime/latest.json", {"checked_at": ts, "results": res})
    with open(f"{a.out}/uptime/history-{ts[:7]}.jsonl", "a") as f:
        f.write(json.dumps({"t": ts, "r": {x["domain"]: [x["status"], x["ms"]] for x in res}}, separators=(",", ":")) + "\n")
    findings = []
    for x in res:
        http_fail = not x["up"]
        findings.append({"domain": x["domain"], "check": "uptime", "ok": not http_fail,
                         "detail": f"HTTP status {x['status']} ({x['error'] or 'no error'}) after retry; {x['ms']} ms" if http_fail
                         else f"HTTP {x['status']} in {x['ms']} ms"})
        tls_fail = x["tls_error"] is not None or (x["tls_days_left"] is not None and x["tls_days_left"] < TLS_WARN_DAYS)
        findings.append({"domain": x["domain"], "check": "tls", "ok": not tls_fail,
                         "detail": f"TLS error: {x['tls_error']}" if x["tls_error"] else
                         f"Certificate expires {x['tls_expires']} ({x['tls_days_left']} days left; threshold {TLS_WARN_DAYS})"})
    write_json(f"{a.out}/findings-uptime.json", findings)
    for x in res:
        print(f"{x['domain']:28s} {str(x['status']):>4} {x['ms']:>6}ms tls={x['tls_days_left']}d {x['error'] or ''}")


if __name__ == "__main__":
    main()
