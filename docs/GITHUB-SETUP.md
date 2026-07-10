# GitHub setup for Emergent

## 1. Create the remote repo

On GitHub: **Rootmcnet/rootmc-emergent** (private recommended):

- Description: `RootMC website + API + Android — Emergent AI deployment`
- Do **not** initialize with README (this export already has one)

## 2. Push from this folder

```powershell
cd "F:\RootMC Workspace\emergent-repo"
git init
git add .
git commit -m "Initial RootMC emergent export (web, API, Android, ecosystem docs)"
git branch -M main
git remote add origin https://github.com/Rootmcnet/rootmc-emergent.git
git push -u origin main
```

## 3. Connect Emergent

Point Emergent at the new repo and set **PROMPT.md** as the project brief (or paste its contents into Emergent’s system prompt).

Recommended Emergent env secrets (mirror `.env.example`):

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `JWT_SECRET`
- `DISCORD_ROOTMC_BOT_TOKEN`
- `DISCORD_ROOTMC_CLIENT_SECRET`
- `GROK_API_BEARER_TOKEN`

Android release builds still require a local machine with Android SDK — Emergent preview can work on web + API only.

## 4. Keep in sync with canonical workspace

After editing in `RootMC Workspace`:

```powershell
powershell -File "F:\RootMC Workspace\scripts\export-emergent-repo.ps1"
cd "F:\RootMC Workspace\emergent-repo"
git add -A
git commit -m "Sync from RootMC Workspace"
git push
```

## 5. What stays outside this repo

| Area | Why |
|------|-----|
| Paper plugins | Large Gradle tree; separate handoff — see `docs/PLUGINS-AND-SERVER.md` |
| Live Shockbyte YAML | Secrets + ops |
| RootRecord MonoRepo | Different product/API account |

Emergent can still **design** plugin/API contract changes; implementation happens in the plugin workspace or via documented follow-up.
