# Emergent — last push brief (merged)

**Date:** July 9, 2026  
**Repo:** https://github.com/Rootmcnet/rootmc-emergent  
**Audience:** Emergent agent — **one final commit push** before human beta (July 11)  
**Sources merged:** [grok-post-emergent.md](grok-post-emergent.md) + [POST-EMERGENT.md](POST-EMERGENT.md) + [memory/PRD.md](../memory/PRD.md) + `test_reports/iteration_1.json`

---

## Mission

You built a **trading-terminal PWA** (`frontend/` + `backend/`) with Rewards, Market, Portfolio, and tests. **Cursor and Grok agree:** keep the UI; **replace the mock data plane** with `api.rootmc.net`; fix the polish bugs; deploy to a real RootMC domain.

**Do not** add new mock endpoints. **Do not** extend Mongo wallet mint in production mode.

---

## Consensus (both AIs)

| Topic | Agreement |
|-------|-----------|
| Keep Emergent UI + `design_guidelines.json` | ✅ |
| Wire to `https://api.rootmc.net` | ✅ P0 |
| Real `/link` JWT (same as Kotlin Worker) | ✅ P0 |
| Check-in + vote UX stays; grants via **treasury on Worker** | ✅ P0 design, Worker may be human-deployed |
| Mock economy off in production | ✅ |
| Player-facing **Gold (G)** only | ✅ |
| July 11 needs **live data** or explicit “UI preview” label | ✅ |
| Waypoints/notes need plugin — don’t fake | ✅ |
| Pull-to-refresh + sync timestamps | ✅ P1 |
| Fix countdown + SPA navigation bugs | ✅ this push |

| Topic | Cursor | Grok |
|-------|--------|------|
| Primary long-term client | Port UI → Kotlin Compose | PWA OK for beta; Kotlin later |
| Fastest beta path | WebView in APK **or** `app.rootmc.net` PWA | PWA @ `app.rootmc.net` |
| Delete mock backend | Proxy-only or remove in prod | Same |

**Pick for this push:** **PWA on live API** (Strategy B). Kotlin port is human/Phase 2.

---

## Your last push — task list (execute in order)

### Block 1 — Live API layer (P0)

- [ ] **1.1** Add `frontend/src/lib/rootmc-api.js` — axios client to `process.env.REACT_APP_ROOTMC_API || 'https://api.rootmc.net'` with Bearer from `rootmc_token`  
- [ ] **1.2** Add env toggle: `REACT_APP_USE_MOCK=false` (default **false** on `main`). When false, **do not seed** Mongo market/treasury for public reads  
- [ ] **1.3** Map screens to **real** endpoints:

| PWA screen | Production endpoint(s) |
|------------|------------------------|
| Home server card | `GET /api/rootmc/server/featured` or `/config` |
| Home economy pulse | `GET /api/rootmc/treasury/rootmc` + stock summary |
| Ticker / Market list | `GET /api/rootmc/stock-market?server_id=…` |
| Market detail history | existing history route used by web `market.js` |
| Portfolio | `GET /api/rootmc/server/{id}/economy/me` |
| Leaderboards | `GET /api/rootmc/server/{id}/economy/net-worth?limit=20` + playtime/mint routes |
| Daily report card | `GET /api/rootmc/daily-report` |
| Auth complete | `POST /api/rootmc/realm/minecraft/link/app/complete` |

- [ ] **1.4** Remove synthetic tickers (`DIAM`, `NETH`) from production UI — use real `item_key` + display names from API  
- [ ] **1.5** Delete or gate `backend/server.py` public economy routes when `USE_MOCK=false` (backend becomes auth-proxy + optional dev-only)

### Block 2 — Auth (P0)

- [ ] **2.1** `/auth` flow: user enters username + 6-char code only — **no** local code generation in prod  
- [ ] **2.2** Optional dev mode: `REACT_APP_DEMO_LINK=true` keeps current demo for pytest  
- [ ] **2.3** Store Worker JWT in `localStorage` as today; document shared `JWT_SECRET` requirement

### Block 3 — Rewards (P0 / honest)

- [ ] **3.1** If Worker check-in/vote routes **do not exist yet**: show Rewards UI with **“Coming soon — treasury wiring”** and **disable Claim** in production — do not Mongo-mint  
- [ ] **3.2** If you implement Worker stubs in `api/rootmc-realm-api/src/` (preferred sketch):

```
GET  /api/rootmc/app/checkin/status
POST /api/rootmc/app/checkin/claim
GET  /api/rootmc/app/vote/sites
POST /api/rootmc/app/vote/claim
```

  — all grants debit treasury; document in PR comment for human deploy

- [ ] **3.3** Keep streak UI + confetti for when live claims work

### Block 4 — Bugs from your own test report (P0 polish)

- [ ] **4.1** `Rewards.jsx` — fix check-in countdown (fixed `loadedAt` anchor)  
- [ ] **4.2** `TopBar.jsx` — `navigate('/more')` instead of full page reload  
- [ ] **4.3** `server.py` — `find_one_and_update(return_document=AFTER)` for wallet display on claims (mock mode only)  
- [ ] **4.4** Split `server.py` into `routers/auth.py`, `market.py`, `portfolio.py`, `rewards.py`

### Block 5 — UX completeness (P1 — both AIs)

- [ ] **5.1** Pull-to-refresh on Home, Market, Portfolio, Leaderboards, Rewards  
- [ ] **5.2** “Last synced …” on portfolio, market, home economy tiles  
- [ ] **5.3** Server offline / API error banner — Grok risk mitigation  
- [ ] **5.4** Player search entry on Home or More → open `https://rootmc.net/player/?u=` until in-app API exists  
- [ ] **5.5** PWA: `service-worker.js` + install prompt; update `frontend/public/manifest.json` name/icons for RootMC  
- [ ] **5.6** More tab: link Discord, Constitution, Wiki, Map, **Beta feedback** (Discord)

### Block 6 — Deploy & docs (P1)

- [ ] **6.1** Add `frontend/.env.example` with `REACT_APP_ROOTMC_API`, `REACT_APP_USE_MOCK`, `REACT_APP_DEMO_LINK`  
- [ ] **6.2** Document deploy to Cloudflare Pages (`app.rootmc.net`) in `docs/DEPLOY.md` section  
- [ ] **6.3** Update `memory/PRD.md` — mark mock phase complete, list live endpoints wired  
- [ ] **6.4** Restore or link `ECOSYSTEM.md` / `PROMPT.md` from git `6f66fae..df59317` if deleted — economy rules for future agents

### Block 7 — Tests (P0)

- [ ] **7.1** Keep pytest green with `REACT_APP_DEMO_LINK=true` mock path  
- [ ] **7.2** Add one integration test (skipped in CI without token) that hits **sandbox** or documents manual prod smoke: `/link` → market list returns non-empty when server online  
- [ ] **7.3** Re-run Playwright; fix any regressions from API switch

---

## Explicitly out of scope for this push

- Full Kotlin Compose port (`android/` — human SDK build)  
- Waypoints/notes (plugin not in repo)  
- D1 migration apply to production (human)  
- Treasury ledger backfills  
- AdMob / Play Store upload (human)  
- Email/password auth  

---

## Definition of done

Emergent’s last push is **done** when:

1. `REACT_APP_USE_MOCK=false` builds a PWA that loads **real** market + portfolio + leaderboards from `api.rootmc.net` for a `/link`-authenticated session  
2. No production path mints Gold in Mongo  
3. Test report bugs (countdown, TopBar navigation) are fixed  
4. `memory/PRD.md` updated with live vs mock status  
5. README points to this file as the final Emergent checklist  

---

## File map (where to work)

```
frontend/src/lib/rootmc-api.js   ← CREATE (live API)
frontend/src/lib/api.js          ← mock backend (dev only)
frontend/src/pages/*.jsx         ← switch data source by env
backend/server.py                  ← split + gate mock
api/rootmc-realm-api/src/        ← optional checkin/vote routes
memory/PRD.md                      ← update status
docs/DEPLOY.md                     ← PWA deploy steps
```

---

## References

| Doc | Purpose |
|-----|---------|
| [grok-post-emergent.md](grok-post-emergent.md) | Grok’s post-delivery review |
| [POST-EMERGENT.md](POST-EMERGENT.md) | Cursor peak roadmap |
| [design_guidelines.json](../design_guidelines.json) | Do not regress visual system |
| [android/](../android/) | Production API client reference (`ServerRepository.kt`) |
| [web/public/scripts/market.js](../web/public/scripts/market.js) | Real market fetch patterns |

---

*Merged Cursor + Grok briefing for Emergent’s final push — July 9, 2026.*
