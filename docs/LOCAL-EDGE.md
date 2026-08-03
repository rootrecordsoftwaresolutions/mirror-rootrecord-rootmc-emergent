# Local-primary RootMC edge

Canonical ops: [`scripts/local-edge/RUNBOOK.md`](../../scripts/local-edge/RUNBOOK.md) in the RootMC Workspace.

## Summary

- PC runs API / api2 / map / site via `scripts/local-edge/Start-LocalEdge.ps1`
- Cloudflare Tunnel for public hostnames; Workers/Pages remain warm backup
- `current_connection_preference` drives cutover (health + HST schedule)
- Read-only disk cache + Cache-Control/ETag + optional HMAC signatures

## Phase 0

`api.rootmc.net` returned **429 Too Many Requests** (2026-07-24) — empty site data is CF throttling.
