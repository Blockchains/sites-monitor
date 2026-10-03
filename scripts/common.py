"""Shared helpers (Python 3 stdlib only)."""
import json, os, ssl, socket, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (X11; Linux x86_64) SitesMonitor/1.0 (+https://github.com/Blockchains/sites-monitor)"
CTX = ssl.create_default_context()


def domains():
    return json.loads((ROOT / "domains.json").read_text())["domains"]


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def fetch(url, timeout=20, max_bytes=2_000_000, follow=True, method="GET"):
    """Return dict(code, ms, url, headers, body(bytes), err)."""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX)) if follow else \
        urllib.request.build_opener(urllib.request.HTTPSHandler(context=CTX), _NoRedirect)
    t0 = time.monotonic()
    try:
        with opener.open(req, timeout=timeout) as r:
            body = r.read(max_bytes)
            return {"code": r.getcode(), "ms": int((time.monotonic() - t0) * 1000), "url": r.geturl(),
                    "headers": {k.lower(): v for k, v in r.headers.items()}, "body": body, "err": None}
    except urllib.error.HTTPError as e:
        try:
            body = e.read(max_bytes)
        except Exception:
            body = b""
        return {"code": e.code, "ms": int((time.monotonic() - t0) * 1000), "url": url,
                "headers": {k.lower(): v for k, v in (e.headers or {}).items()}, "body": body, "err": f"HTTP {e.code}"}
    except Exception as e:
        return {"code": None, "ms": int((time.monotonic() - t0) * 1000), "url": url, "headers": {}, "body": b"",
                "err": f"{type(e).__name__}: {e}"[:200]}


def tls_expiry(host, port=443, timeout=15):
    """Return (iso_expiry, days_left, err)."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            with CTX.wrap_socket(s, server_hostname=host) as ss:
                cert = ss.getpeercert()
        exp = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        days = (exp - datetime.now(timezone.utc)).total_seconds() / 86400
        return exp.isoformat().replace("+00:00", "Z"), round(days, 1), None
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"[:200]


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=False) + "\n")


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return default
