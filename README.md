# RootMC — Emergent deployment repo

Standalone GitHub repo for **Emergent AI** to own large, cross-surface updates to RootMC’s **website**, **API Worker**, and **Android app**. Minecraft plugin source and live Shockbyte deploy stay in the canonical workstation; this repo documents how they connect.

## What’s in this repo

| Path | Production | Role |
|------|------------|------|
| [`web/`](web/) | https://rootmc.net | Cloudflare Pages — static site, economy/market/governance UI |
| [`api/rootmc-api/`](api/rootmc-api/) | https://api.rootmc.net | Worker deploy target (gateway + crons) |
| [`api/rootmc-realm-api/`](api/rootmc-realm-api/) | *(bundled into worker)* | RootMC routes, Discord, economy sync, `/link` auth |
| [`api/shared/`](api/shared/) | — | Vendored TS helpers from RootRecord monorepo |
| [`api/rootrecord-api-account/`](api/rootrecord-api-account/) | — | Vendored account shard (auth, FCM, D1 migrations) |
| [`android/`](android/) | Play: `com.rootrecord.rootmc` | Kotlin / Compose companion app |
| [`frontend/`](frontend/) + [`backend/`](backend/) | Emergent preview / future `app.rootmc.net` | React PWA + FastAPI (**mock data today**) |

**Emergent final push:** [docs/EMERGENT-LAST-PUSH.md](docs/EMERGENT-LAST-PUSH.md) — merged Cursor + Grok checklist (wire live API, fix bugs, deploy).

## Live URLs

| Service | URL |
|---------|-----|
| Game | `play.rootmc.net` |
| Website | https://rootmc.net |
| API | https://api.rootmc.net |
| Map | https://map.rootmc.net |
| Constitution (wiki) | https://rootmc.net/wiki/constitution/ |
| Daily report archive | https://rootmc.net/daily-report/ |
| Economy dashboard | https://rootmc.net/economy/ |
| Stock market | https://rootmc.net/market/ |
| Discord | https://discord.gg/rFFQYrNaqS |

## Ecosystem (read before big changes)

- **[ECOSYSTEM.md](ECOSYSTEM.md)** — full map: plugins, server, treasury rules, RootRecord vs RootMC
- **[PROMPT.md](PROMPT.md)** — Emergent agent brief (scope, constraints, deliverables)
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — data flow web ↔ API ↔ Android ↔ game
- **[docs/DEPLOY.md](docs/DEPLOY.md)** — deploy commands and secrets
- **[docs/PLUGINS-AND-SERVER.md](docs/PLUGINS-AND-SERVER.md)** — Paper plugins + Shockbyte (outside this repo)

## Quick start

```powershell
# 1. Secrets
copy .env.example .env
# fill CLOUDFLARE_*, JWT_SECRET, DISCORD_*, GROK_*

# 2. API
cd api\rootmc-api
npm ci
powershell -File deploy.ps1

# 3. Website
cd ..\..\web
npm ci
powershell -File deploy.ps1

# 4. Android (local machine with Android SDK)
cd ..\android
.\gradlew.bat assembleDebug
```

## Sync from canonical workstation

If you maintain code in `RootMC Workspace` on a dev machine:

```powershell
powershell -File "..\scripts\export-emergent-repo.ps1"
```

That re-copies `web/`, `api/`, `android/` and patches deploy paths for this repo layout.

## Publish to GitHub / Emergent

See **[docs/GITHUB-SETUP.md](docs/GITHUB-SETUP.md)** — repo: **https://github.com/Rootmcnet/rootmc-emergent** — connect Emergent with **PROMPT.md** as the brief.

| Repo | What |
|------|------|
| https://github.com/Rootmcnet/MonoRepo | RootRecord product stack (Weather, Business, Account, Token) — **separate** from RootMC API |
| Canonical RootMC workstation | Plugins, live server YAML, FileZilla handoff — not in this export |

## Agent rules

- **Gold** not dollars in player-facing copy
- Automated payouts debit **treasury** — never mint wallet G directly
- Never commit `.env`, keystores, or `google-services.json`
- Production deploys need human approval; Emergent should implement + document, not silently ship treasury/D1 changes
