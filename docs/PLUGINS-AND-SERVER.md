# Minecraft plugins & live server

**Not included in this GitHub repo.** RootMC game behavior is implemented in Paper plugins and live YAML on Shockbyte. Emergent must treat this doc as the contract when changing economy, sync, or in-game commands that affect the API.

## Canonical workstation paths (developer machine)

| Path | Role |
|------|------|
| `Plugin Building/Minecraft/` | Gradle monorepo — all Paper plugins |
| `Server Files (Handoff Off)/` | FileZilla upload source (jars + live YAML) |
| `plugins/RootRecord/rootmc.yml` | RootMC plugin cloud + MySQL + game version |
| `plugins/RootRecord/cloud.yml` | RootRecord cloud API auth to Worker |

Build plugins:

```bat
cd "Plugin Building\Minecraft"
.\build-with-server-jdk.bat publishPlugins
```

Outputs jars to handoff `plugins/`, `rootmc-web/public/plugins/`, and `manifest.json`.

## Plugin ↔ API contract

| Plugin area | Pushes to API | D1 / tables |
|-------------|---------------|-------------|
| RootMC core | Server heartbeat, featured config | `blocknotes_server`, live stats |
| Economy / treasury | Wallet snapshots, transfers, reserve | economy + treasury tables |
| Stock market | Listings, trades | `rootmc` market tables |
| McMMO / playtime | Per-player stats | `rootstat_*` |
| Towny / Discord | Town/nation channels | Discord channel IDs in wrangler vars |

Worker env `ROOTMC_MYSQL_TABLE_PREFIX = "root_"` must match `rootmc.yml` MySQL prefix.

## Live deploy (human ops)

1. Bump plugin `version` in `build.gradle.kts`.  
2. `publishPlugins`.  
3. FileZilla upload from handoff folder to Shockbyte.  
4. Restart server if required.  
5. Update `web/public/plugins/manifest.json` if publishing new jar URLs.

## Game version

Set consistently:

- `rootmc.yml` → `game-version: '26.2'`
- API `rootmc-server.ts` default
- Website wiki player page
- Android seeder fallbacks

## When Emergent changes API fields

If you add a new stat or economy field:

1. Add D1 migration (manifest + SQL).  
2. Add realm API route + cron ingest if needed.  
3. Update web JS + Android repository models.  
4. **File a plugin task** (or implement in plugin repo) to emit the new data — clients must not invent values.

## Shockbyte

- Host: Shockbyte (MySQL + Paper)  
- Play address: `play.rootmc.net`  
- Hyperdrive binding on Worker connects cron jobs to MySQL  

Do not commit `cloud.yml` API keys or MySQL passwords.

## Related docs on website

- https://rootmc.net/wiki/constitution/ — player law & economy  
- https://rootmc.net/wiki/player/ — gameplay reference  
- https://rootmc.net/wiki/economy/ — public economy explainer  
