#!/usr/bin/env python3
"""Open/update one GitHub issue per domain+check on failure; comment + close on recovery.
Usage: issues.py findings-*.json   (needs GH_TOKEN and GITHUB_REPOSITORY; uses the gh CLI)
Issue title: "[monitor] <check>: <domain>"; label "monitor" + "check:<check>"."""
import json, os, subprocess, sys
from datetime import datetime, timezone

REPO = os.environ.get("GITHUB_REPOSITORY", "Blockchains/sites-monitor")
RUN = f"{os.environ.get('GITHUB_SERVER_URL','https://github.com')}/{REPO}/actions/runs/{os.environ.get('GITHUB_RUN_ID','')}"
DRY = os.environ.get("DRY_RUN") == "1"


def gh(*args, inp=None):
    if DRY and (args[0] != "api" or "--method" in args):
        print("DRY:", " ".join(args)); return ""
    r = subprocess.run(["gh", *args], input=inp, capture_output=True, text=True)
    if r.returncode != 0:
        print("gh error:", " ".join(args[:4]), r.stderr.strip()[:300], file=sys.stderr)
        return None
    return r.stdout


def ensure_label(name, color):
    gh("api", "--method", "POST", f"repos/{REPO}/labels", "-f", f"name={name}", "-f", f"color={color}")


def main():
    findings = []
    for p in sys.argv[1:]:
        findings += json.load(open(p))
    out = gh("api", "--paginate", f"repos/{REPO}/issues?state=open&labels=monitor&per_page=100",
             "--jq", ".[] | {number, title, body} | @json")
    if out is None:
        sys.exit("could not list issues")
    open_issues = {}
    for line in out.splitlines():
        if line.strip():
            i = json.loads(line)
            open_issues[i["title"]] = i
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    labels_done = set()
    for f in findings:
        title = f"[monitor] {f['check']}: {f['domain']}"
        cur = open_issues.get(title)
        if not f["ok"] and not f.get("skip_issue"):
            body = (f"**Domain:** https://{f['domain']}/\n**Check:** `{f['check']}`\n\n**Latest result ({ts}):** {f['detail']}\n\n"
                    f"Latest run: {RUN}\n\n_This issue is managed automatically by sites-monitor and closes itself when the check recovers._")
            if cur is None:
                for lab, col in (("monitor", "d73a4a"), (f"check:{f['check']}", "0e8a16")):
                    if lab not in labels_done:
                        ensure_label(lab, col); labels_done.add(lab)
                gh("issue", "create", "-R", REPO, "-t", title, "-b", body, "-l", "monitor", "-l", f"check:{f['check']}")
                print("opened:", title)
            elif cur.get("body", "").split("**Latest result")[-1].split("):", 1)[-1].split("\n")[0].strip() != f["detail"]:
                gh("issue", "edit", str(cur["number"]), "-R", REPO, "-b", body)
                print("updated:", title)
        elif cur is not None and f["ok"]:
            gh("issue", "close", str(cur["number"]), "-R", REPO, "-c", f"Recovered at {ts}: {f['detail']}\n\n{RUN}")
            print("closed:", title)


if __name__ == "__main__":
    main()
