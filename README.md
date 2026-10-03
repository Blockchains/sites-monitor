# sites-monitor

Monitoring, status page and traffic dashboard for Ismail Malik's custom-domain sites.

**Status page:** https://blockchains.github.io/sites-monitor/

| Workflow | Schedule (UTC) | What it checks |
|---|---|---|
| [`uptime.yml`](.github/workflows/uptime.yml) | every 10 min | HTTP status (1 retry), response time, TLS certificate expiry (< 14 days = failing) |
| [`daily.yml`](.github/workflows/daily.yml) | daily 05:17 | SEO basics on the custom domain (title, description, canonical + og:url on the custom domain, og:title/description/image, robots.txt, sitemap, favicon, apple-touch-icon, manifest); broken links on each homepage ([lychee](https://github.com/lycheeverse/lychee), homepage links only, 180 s cap per site); Lighthouse CI (mobile, 1 run, any category < 50 = failing) |
| [`weekly-security.yml`](.github/workflows/weekly-security.yml) | Mondays 06:41 | Security headers (HSTS, X-Content-Type-Options, Referrer-Policy, clickjacking protection required; CSP & Permissions-Policy recommended) and an exposed-file probe for `/.env`, `/.git/HEAD`, `/.git/config` (bodies are never stored) |

On failure each workflow opens (or updates) **one issue per domain + check** titled `[monitor] <check>: <domain>` with label `monitor`, and closes it automatically when the check recovers.
`aisales.news` is marked `locked` in [`domains.json`](domains.json) (it currently serves Halcyon content), so only uptime/TLS/security issues are raised for it.

## Data

All results are JSON on the [`gh-pages`](../../tree/gh-pages) branch under `data/`:
`uptime/latest.json` (+ `uptime/history-YYYY-MM.jsonl`), `seo/latest.json`, `links/latest.json`, `lighthouse/latest.json`, `security/latest.json`, `traffic.json`.

`traffic.json` is pushed once a day from the digest box (`pulse-port/scripts/traffic_export.py`, run after the daily traffic digest). It holds **aggregate** daily visitors/pageviews per domain only — no IPs, events or visitor-level data.

## Layout

- `domains.json` – the monitored domains
- `scripts/` – stdlib-only Python checks, issue manager (`issues.py`, uses `gh`), `publish.sh` (commits to gh-pages)
- `site/` – the static status page (copied to gh-pages on every run)
