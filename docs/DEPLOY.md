# Deploy

All deploy scripts load secrets from **repo root** `.env` via `scripts/load-env.ps1`.

## Prerequisites

- Node.js LTS, `npm` / `npx wrangler`
- Cloudflare API token with Workers + Pages + D1 for the **RootMC** account
- Android Studio + JDK (APK/AAB builds only — not available in Emergent preview containers)

## Secrets setup

```powershell
copy .env.example .env
# Edit .env — see ECOSYSTEM.md secrets section
```

`api/rootmc-api/deploy.ps1` also pushes Worker secrets: `JWT_SECRET`, Discord tokens, Grok keys, optional FCM JSON.

## API Worker

```powershell
cd api\rootmc-api
npm ci
powershell -File deploy.ps1
```

This applies remote D1 migrations (`d1-apply-remote.ps1`), bundles realm + account + shared sources, and deploys to `api.rootmc.net`.

**Verify:** `curl https://api.rootmc.net/api/rootmc/server/config`

## Website (Pages)

```powershell
cd web
npm ci
powershell -File deploy.ps1
```

Deploys project `rootmc-web` → https://rootmc.net

**Verify:** https://rootmc.net/economy/ loads reserve data.

## Android

Emergent containers typically **cannot** run `gradlew`. On a dev machine:

```bat
cd android
.\gradlew.bat assembleDebug
```

Release:

```bat
.\gradlew.bat bundleRelease assembleRelease
```

Requires `local.properties` (SDK path) and release signing config.

## Post-deploy checks

| Check | URL / action |
|-------|----------------|
| API health | `GET /api/rootmc/server/featured` |
| Daily report | https://rootmc.net/daily-report/ |
| Market chart | https://rootmc.net/market/ |
| Android sign-in | `/link` code → app auth screen |
| Discord slash | `/proposal` in test channel (staff) |

## Re-sync repo from workstation

```powershell
# From canonical RootMC Workspace
powershell -File scripts\export-emergent-repo.ps1
```

Then commit and push the emergent repo.

## What Emergent should not auto-deploy

- D1 migrations that alter treasury ledger history  
- Wrangler cron schedule changes without review  
- Production Discord command registration (script in realm-api `scripts/`)  
- Play Store releases  

Document deploy steps in PR/issue; human runs production deploy.
