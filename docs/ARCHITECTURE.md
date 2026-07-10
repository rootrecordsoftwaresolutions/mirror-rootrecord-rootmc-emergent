# Architecture

## Repo layout

```
rootmc-emergent/
├── web/                          # Cloudflare Pages (rootmc-web)
├── api/
│   ├── rootmc-api/               # Deployable Worker (gateway + wrangler + D1 migrations apply)
│   ├── rootmc-realm-api/         # Business logic (imported by worker)
│   ├── shared/                   # Vendored RootRecord shared TS
│   └── rootrecord-api-account/   # Vendored account shard (auth, FCM, SQL migrations)
├── android/                      # Kotlin Compose app
└── docs/
```

## Request routing

1. **Browser** → `rootmc.net` (Pages static + Functions).  
2. **Pages Function** `functions/api/[[path]].ts` forwards `/api/*` to `https://api.rootmc.net`.  
3. **Android** calls `https://api.rootmc.net/api/...` directly with Bearer JWT.  
4. **Worker** `api/rootmc-api/src/index.ts` rewrites paths via `gateway.ts`, then delegates to `realm-index.ts`.

Realm router entry: `api/rootmc-realm-api/src/realm-router.ts`.

## Key API route families

| Prefix | Module area | Consumers |
|--------|-------------|-----------|
| `/api/rootmc/server/*` | `rootmc-server.ts` | Featured server, membership, per-server stats |
| `/api/rootmc/realm/minecraft/link/*` | `rootmc-minecraft-link.ts` | Android `/link` auth |
| `/api/rootmc/stock-market` | stock market handlers | web market, Android |
| `/api/rootmc/treasury/*` | treasury / reserve | web economy/reserve |
| `/api/rootmc/daily-report` | `rootmc-daily-report-public.ts` | web + Android archive |
| `/v1/discord/rootmc/*` | Discord OAuth + interactions | Discord, verify page |
| `/api/mobile/*` | mobile config push | Android |

## Storage

| Store | Binding | Use |
|-------|---------|-----|
| D1 `rootmc` | `DB` | Accounts, stats, economy snapshots, governance, reports |
| R2 `rootmc-bluemap` | `ASSETS` | Map tiles / assets |
| Hyperdrive `ROOTMC_MYSQL` | MySQL | Live Towny/economy tables on Shockbyte |

Migrations: `api/rootmc-api/migrations/MANIFEST.txt` → files in `api/rootrecord-api-account/migrations/`.

## Android layers

```
ui/          → Compose screens + ViewModels
data/repository/ServerRepository.kt  → REST to api.rootmc.net
data/repository/RootRecordAuthRepository.kt → /link + session
data/local/RootMcPreferences.kt      → JWT + expiry
di/          → Hilt modules, ROOTRECORD_BLOCKNOTES_BASE
```

Navigation: `ui/RootMcApp.kt`, `ui/navigation/RootMcNavRoutes.kt`.

## Web build

```bash
cd web && node scripts/build.mjs   # outputs web/build/
npx wrangler pages deploy build --project-name rootmc-web
```

Static assets live in `web/public/`; build may bundle/minify into `build/`.

## Scheduled work

`rootmc-api` `wrangler.toml` `[triggers] crons` invoke `realmWorker.scheduled`. Economy MySQL→D1 sync, Discord digests, and weekly awards run here — change schedules only with ops awareness.

## Version alignment

Keep in sync when bumping Minecraft version:

- `api/rootmc-realm-api/src/rootmc-server.ts` (`game_version` default)
- `android/.../DatabaseSeeder.kt`, `ServerRepository.kt` fallbacks
- `web/public/wiki/player/index.html` and related wiki pages
- Plugin `rootmc.yml` `game-version` (outside repo)

Current: **26.2**.
