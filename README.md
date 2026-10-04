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

## Run locally

Python 3 standard library only (`gh` CLI for issue management):

```bash
python3 scripts/uptime.py --out /tmp/sm      # HTTP + TLS expiry for every domain in domains.json
python3 scripts/security.py --out /tmp/sm    # security headers / exposed files
python3 scripts/seo.py --out /tmp/sm         # SEO + link checks
DRY_RUN=1 python3 scripts/issues.py /tmp/sm/findings-uptime.json   # print issue actions without touching GitHub
```

<!-- blocks:start -->
## Use as a building block

> **For AI agents and builders:** read [`AGENTS.md`](AGENTS.md) (setup, commands, structure, rules), [`llms.txt`](llms.txt) (doc map) and the machine-readable [`blocks.json`](blocks.json) ([schema](https://github.com/Blockchains/.github/blob/main/docs/BLOCKS-SCHEMA.md)). How all Blockchains blocks fit together: **[Build with Blocks](https://github.com/Blockchains/.github/blob/main/docs/BUILD-WITH-BLOCKS.md)** · org catalogue: [https://blockchains.github.io/blocks.json](https://blockchains.github.io/blocks.json).

**What it exports**

| Export | Type | Install / access |
|---|---|---|
| `data/uptime/latest.json` | http | `also seo/, links/, lighthouse/, security/ latest.json and traffic.json` |
| `scripts/uptime.py` | cli | `python3 scripts/uptime.py --out DIR` |
| `domains.json` | file | `domains.json` |

**Minimal example**

```bash
python3 scripts/uptime.py --out /tmp/sm      # HTTP + TLS expiry for every domain
DRY_RUN=1 python3 scripts/issues.py /tmp/sm/findings-uptime.json   # print issue actions without touching GitHub
```

**Inputs → outputs**

- In: `domains.json` (JSON) domains, optional locked flag
- Out: `findings + latest.json` (JSON); `monitor issues` (GitHub issues)

**Composes with**

- [Blockchains/blockchains.github.io](https://github.com/Blockchains/blockchains.github.io): hub links the status page
- [Blockchains/.github](https://github.com/Blockchains/.github): STATUS.md audit

**Versioning & stability:** `stable`. Data files under gh-pages `data/` keep their shape; history is appended monthly (`uptime/history-YYYY-MM.jsonl`).
<!-- blocks:end -->

## Configuration

| Setting | Purpose |
|---|---|
| `domains.json` | Domains to monitor |
| `GH_TOKEN` | Token for `issues.py` (the workflows pass `github.token`) |
| `GITHUB_REPOSITORY` | Repo where findings become issues (default `Blockchains/sites-monitor`) |
| `DRY_RUN=1` | Don't open/close issues |

## Licence

No licence file has been added yet, so default copyright applies (all rights reserved).

## Contributing

Issues and pull requests are welcome. Please read the [contributing guide](https://github.com/Blockchains/.github/blob/main/CONTRIBUTING.md), [code of conduct](https://github.com/Blockchains/.github/blob/main/CODE_OF_CONDUCT.md) and [security policy](https://github.com/Blockchains/.github/blob/main/SECURITY.md) first.

---
Built by Blockchain Lab — [blockchainlab.com](https://blockchainlab.com/?utm_source=github&utm_medium=readme&utm_campaign=sites-monitor)
