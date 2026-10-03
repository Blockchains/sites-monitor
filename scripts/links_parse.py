#!/usr/bin/env python3
"""Parse lychee JSON output (one file per domain) into <out>/links/latest.json + findings."""
import argparse, json, os
from common import domains, now_iso, write_json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = []
    for d in domains():
        dom = d["domain"]
        p = f"{a.reports}/{dom}.json"
        try:
            j = json.load(open(p))
        except Exception as e:
            res.append({"domain": dom, "locked": bool(d.get("locked")), "error": f"no lychee report ({type(e).__name__})"}); continue
        broken = []
        for src, items in (j.get("error_map") or j.get("fail_map") or {}).items():
            for it in items:
                st = it.get("status", {})
                broken.append({"url": it.get("url"), "status": st.get("text") if isinstance(st, dict) else str(st)})
        res.append({"domain": dom, "locked": bool(d.get("locked")), "error": None, "total": j.get("total"),
                    "successful": j.get("successful"), "errors": j.get("errors", len(broken)),
                    "excludes": j.get("excludes"), "timeouts": j.get("timeouts"), "broken": broken[:50]})
    write_json(f"{a.out}/links/latest.json", {"checked_at": now_iso(), "results": res})
    findings = []
    for x in res:
        ok = x.get("error") is None and not x.get("broken")
        detail = x["error"] if x.get("error") else (f"{x['total']} links checked, none broken" if ok else
                 f"{len(x['broken'])} broken of {x['total']}: " + "; ".join(f"{b['url']} ({b['status']})" for b in x["broken"][:10]))
        findings.append({"domain": x["domain"], "check": "broken-links", "ok": ok, "skip_issue": x["locked"], "detail": detail[:1500]})
    write_json(f"{a.out}/findings-links.json", findings)
    for x in res:
        print(x["domain"], x.get("error") or f"total={x['total']} broken={len(x['broken'])}")


if __name__ == "__main__":
    main()
