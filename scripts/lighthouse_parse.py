#!/usr/bin/env python3
"""Parse Lighthouse JSON reports (lhci collect output, mobile preset) into <out>/lighthouse/latest.json + findings."""
import argparse, glob, json
from urllib.parse import urlparse
from common import domains, now_iso, write_json

THRESH = 0.5  # any category below 50 => failing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", required=True, help="dir containing <domain>/lhr-*.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = []
    for d in domains():
        dom = d["domain"]
        files = sorted(glob.glob(f"{a.reports}/{dom}/lhr-*.json"))
        if not files:
            res.append({"domain": dom, "locked": bool(d.get("locked")), "error": "no report", "scores": None}); continue
        runs = [json.load(open(f)) for f in files]
        cats = {}
        for k in ("performance", "accessibility", "best-practices", "seo"):
            vals = [r["categories"][k]["score"] for r in runs if r.get("categories", {}).get(k, {}).get("score") is not None]
            cats[k] = round(sorted(vals)[len(vals) // 2] * 100) if vals else None
        audits = runs[0].get("audits", {})
        metric = lambda k: audits.get(k, {}).get("displayValue")
        res.append({"domain": dom, "locked": bool(d.get("locked")), "error": None, "scores": cats,
                    "metrics": {"LCP": metric("largest-contentful-paint"), "CLS": metric("cumulative-layout-shift"),
                                "TBT": metric("total-blocking-time"), "FCP": metric("first-contentful-paint")},
                    "form_factor": runs[0].get("configSettings", {}).get("formFactor"), "runs": len(runs)})
    write_json(f"{a.out}/lighthouse/latest.json", {"checked_at": now_iso(), "threshold": int(THRESH * 100), "results": res})
    findings = []
    for x in res:
        low = [f"{k} {v}" for k, v in (x["scores"] or {}).items() if v is None or v < THRESH * 100]
        ok = x["error"] is None and not low
        findings.append({"domain": x["domain"], "check": "lighthouse", "ok": ok, "skip_issue": x["locked"],
                         "detail": (f"Mobile scores: " + ", ".join(f"{k} {v}" for k, v in x["scores"].items())) if ok else
                         (x["error"] or f"Below {int(THRESH*100)}: {', '.join(low)}")})
    write_json(f"{a.out}/findings-lighthouse.json", findings)
    for x in res:
        print(x["domain"], x["scores"], x["error"] or "")


if __name__ == "__main__":
    main()
