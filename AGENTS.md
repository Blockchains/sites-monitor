# AGENTS.md: sites-monitor

Instructions for AI coding agents (Grok, Cursor, Claude Code, Codex, Copilot and others) working **in** this repo or **using it as a building block**. Humans: see [README.md](README.md).

## What this is

Uptime, TLS, SEO, broken-link, Lighthouse and security-header monitoring for the custom-domain sites, with a public status page, JSON results on gh-pages and one auto-managed GitHub issue per failing domain + check.

- Kind: automation, dataset, web-app · stability: `stable` · licence: NOASSERTION
- Machine-readable manifest: [`blocks.json`](blocks.json) (schema: [BLOCKS-SCHEMA](https://github.com/Blockchains/.github/blob/main/docs/BLOCKS-SCHEMA.md))
- How it fits with the other Blockchains repos: [Build with Blocks](https://github.com/Blockchains/.github/blob/main/docs/BUILD-WITH-BLOCKS.md)

## Setup

```bash
python3 --version
```

## Build and test

```bash
python3 scripts/uptime.py --out /tmp/sm
python3 scripts/security.py --out /tmp/sm
python3 scripts/seo.py --out /tmp/sm
```

Tests hit **live** public networks/APIs (the org rule is no mocks). A failure can be an upstream outage: re-run before changing code.

## Structure

| Path | What |
|---|---|
| `domains.json` | monitored domains |
| `scripts/` | checks, issue manager, publish.sh |
| `site/` | status page |
| `.github/workflows/` | uptime, daily, weekly-security |

## Conventions

- Locked domains only raise uptime/TLS/security issues.
- Traffic data is aggregate only.

## Extension points

- New check: `scripts/<check>.py --out DIR` writing findings-<check>.json, wired into a workflow and `issues.py`.

## Do

- Use DRY_RUN=1 when testing the issue manager.

## Don't

- Open issues from local runs.
- Edit the private site mirrors from here.
- Commit secrets, keys or `.env` files. Run `gitleaks` before pushing; CI and the org policy reject leaks.

## Using it from another project

- **data/uptime/latest.json** (http): `also seo/, links/, lighthouse/, security/ latest.json and traffic.json`
- **scripts/uptime.py** (cli): `python3 scripts/uptime.py --out DIR`
- **domains.json** (file): `domains.json`

See the README section [Use as a building block](README.md#use-as-a-building-block) for a copy-paste example.

## Related blocks

- [Blockchains/blockchains.github.io](https://github.com/Blockchains/blockchains.github.io): hub links the status page
- [Blockchains/.github](https://github.com/Blockchains/.github): STATUS.md audit
