# Agent instructions (Cursor / Emergent)

Use [PROMPT.md](PROMPT.md) as the primary brief. This file is a short index for automated agents.

## Before coding

1. Read [ECOSYSTEM.md](ECOSYSTEM.md) for URLs, treasury rules, and Discord IDs.  
2. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for route and data-flow boundaries.  
3. Grep the three surfaces (`web/`, `api/rootmc-realm-api/src/`, `android/`) for existing patterns.

## Hard rules

- Never commit `.env`, keystores, `google-services.json`, or tokens.  
- Player-facing currency: **Gold (G)**, not dollars.  
- Automated payouts: **treasury debit**, not wallet mint.  
- No client-side fake economy numbers.  
- RootMC API is `api.rootmc.net` — not RootRecord shards.

## Cross-surface checklist

When shipping a feature that shows player or server data:

- [ ] API route + types in `rootmc-realm-api`  
- [ ] D1 migration if schema changes (MANIFEST.txt)  
- [ ] Web page or JS module under `web/public/`  
- [ ] Android repository + screen if user-facing in app  
- [ ] Update ECOSYSTEM.md table if new public URL  

## Deploy

Human runs production deploy — see [docs/DEPLOY.md](docs/DEPLOY.md). Emergent implements and documents commands.

## Plugin / server changes

This repo does not contain plugin source. Document required plugin work in PR description and [docs/PLUGINS-AND-SERVER.md](docs/PLUGINS-AND-SERVER.md).
