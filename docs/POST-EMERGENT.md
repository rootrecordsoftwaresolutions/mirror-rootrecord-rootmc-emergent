# Post-Emergent — path to peak

**Date:** July 9, 2026  
**Repo:** https://github.com/Rootmcnet/rootmc-emergent  
**After:** Emergent job `f71356dc` — React PWA + FastAPI/Mongo stack (`frontend/`, `backend/`)  
**Read first:** [memory/PRD.md](../memory/PRD.md) (Emergent’s own delivery notes)  
**Action checklist:** [EMERGENT-LAST-PUSH.md](EMERGENT-LAST-PUSH.md) (merged Cursor + Grok — **give this to Emergent for the final push**)

---

## What Emergent shipped

Emergent did **not** extend the existing Kotlin app, Cloudflare Worker, or `rootmc.net` static site. It added a **fourth surface**:

| Layer | Path | Status |
|-------|------|--------|
| FastAPI + MongoDB | `backend/server.py` | ✅ Runs; **synthetic seed data** |
| React PWA (trading-terminal UI) | `frontend/src/` | ✅ Home, Market, Portfolio, Rewards, Leaderboards, Auth |
| Tests | `backend/tests/`, Playwright reports | ✅ 31 pytest + 74 UI assertions (against mock API) |
| Design system | `design_guidelines.json` | ✅ Dark/gold terminal aesthetic |

**New product ideas (valuable):**

- **Daily check-in** — 7-day streak rewards (10→100 G), treasury-framed copy  
- **Vote sites tab** — 5 sites, 24h cooldown, claim flow  
- **Trading-app UX** — ticker strip, sparklines, portfolio breakdown, confetti claim  

**Explicitly mocked (Emergent PRD admits this):**

- Market prices, treasury, leaderboards, daily report, wallet balances  
- `/link` auth issues codes locally — **not** `api.rootmc.net`  
- Check-in / vote payouts — in-memory Mongo, **not** real treasury debit  

Until wired to production, this is a **high-fidelity prototype**, not a beta-ready companion for July 11.

---

## Architecture decision (pick one strategy)

You now have **two mobile clients**:

1. **`android/`** — Kotlin Compose, `com.rootrecord.rootmc`, talks to **`api.rootmc.net`** (real)  
2. **`frontend/`** — React PWA, talks to **`backend/`** (mock)

For **peak**, choose:

| Strategy | Pros | Cons |
|----------|------|------|
| **A. Kotlin primary** | Play Store beta, FCM, existing repos | Port Emergent UI/Features manually |
| **B. PWA at `app.rootmc.net`** | Emergent UI ships fast; installable | Second auth stack, needs Worker proxy |
| **C. Hybrid** | Android `WebView` loads PWA; native shell for push/deep links | Two codebases to maintain |
| **D. Merge** | Port Rewards + terminal UI into Compose; delete mock backend | Most work upfront; cleanest long-term |

**Recommendation:** **D for peak quality**, **B for fastest public demo** — but **never** run mock economy in production. If B, FastAPI becomes a thin **proxy** to `api.rootmc.net` only.

---

## P0 — Must fix before calling it “live”

### 1. Kill mock data in production paths

- [ ] `REACT_APP_ROOTMC_API=https://api.rootmc.net` — frontend calls Worker directly **or** via read-only proxy  
- [ ] Remove / gate Mongo seed on `ENV=production`  
- [ ] Market, economy, portfolio, leaderboards, daily report → existing routes (`/api/rootmc/stock-market`, `/economy/me`, `/daily-report`, etc.)  
- [ ] Display **sync timestamps** on every numeric card (Emergent UI has room in top bar / cards)

### 2. Real `/link` auth

- [ ] Replace `POST /api/auth/link/*` demo with proxy to  
  `POST https://api.rootmc.net/api/rootmc/realm/minecraft/link/app/complete`  
- [ ] JWT must be the **same** token family Android uses (`RootMcPreferences` / Worker `JWT_SECRET`)  
- [ ] Delete separate Mongo user bootstrap on link — player must exist on server

### 3. Treasury-backed rewards (check-in + vote)

Emergent’s Rewards tab is the right **UX**; production needs **policy + plumbing**:

- [ ] **Worker routes** on `rootmc-realm-api` (not FastAPI-only):  
  - `GET /api/rootmc/app/checkin/status`  
  - `POST /api/rootmc/app/checkin/claim`  
  - `GET /api/rootmc/app/vote/sites`  
  - `POST /api/rootmc/app/vote/claim`  
- [ ] All grants via **treasury debit** (`towny-server`) — same as vote/playtime Discord payouts  
- [ ] Rate limits + anti-abuse (one claim per account per window; optional link to listing-site vote verification later)  
- [ ] Constitution / staff sign-off on streak table (10→100 G)  
- [ ] Public reachout post on grant (existing economy announce pattern)

### 4. Beta July 11 alignment

- [ ] Decide ship vehicle: **Play (Kotlin)** vs **PWA link** vs both  
- [ ] If Play: port at minimum **Rewards** + **terminal Home** into Compose **or** ship WebView to hosted PWA with **live** API  
- [ ] `rootmc.net` / Discord download link must not point at mock backend

### 5. Restore handoff docs Emergent overwrote

Force-push removed pre-Emergent docs (`PROMPT.md`, `ECOSYSTEM.md`, `PRE-EMERGENT-*`). Re-export from workspace or restore from git history so agents keep economy/plugin boundaries.

---

## P1 — Peak product (Emergent UI + real data)

### Port Emergent’s best UX (whether PWA or Kotlin)

- [ ] **Ticker strip** on home — real top movers from `/api/rootmc/stock-market`  
- [ ] **Portfolio** screen — map to `economy/me` + net worth breakdown (wallet / inv / chest / shop)  
- [ ] **Market detail** — reuse period charts (`1H|1D|1W|1M`) against real history endpoint  
- [ ] **Rewards** — keep streak grid + confetti; wire real cooldown timers from Worker  
- [ ] **Server status pill** — `featured` / `config` API (version **26.2**, online, sync)  
- [ ] Pull-to-refresh on all tabs (Cursor + Grok pre-Emergent ask)

### Website parity gaps

- [ ] Governance proposals (read-only in-app; web has `/governance/`)  
- [ ] Player search / public profile (`/player/`)  
- [ ] Bluemap — embed `map.rootmc.net` (Emergent backlog)  
- [ ] Beta landing page on `rootmc.net` → Play or PWA

### Android native (if Kotlin stays primary)

- [ ] Apply `design_guidelines.json` palette to Compose theme (`Color.kt` / `Theme.kt`)  
- [ ] Add **Rewards** destination to bottom nav (or replace Economy tab merge — UX decision)  
- [ ] FCM shop alerts (already scaffolded; needs `google-services.json`)  
- [ ] Deep links from push → market item detail

---

## P2 — Peak engagement (Grok + Cursor roadmap)

| Feature | Blocker | Peak value |
|---------|---------|------------|
| Waypoints / notes sync | Plugin + API | High for explorers |
| Voting tracker (listing sites) | D1 aggregate API | Complements Rewards tab |
| Loan status chip | `economy/me` field | Traders |
| Towny panel | Town API / membership | Social glue |
| Weekly awards progress | Existing cron data | Retention |
| Offline cache + “last synced” | Room / service worker | Trust |
| Biometric app lock | Android only | Security polish |
| PWA service worker | `frontend/` | Offline shell |
| Widgets (balance, movers) | Android | Power users |

---

## P3 — Ops & quality at peak

- [ ] **Deploy PWA** → Cloudflare Pages project `rootmc-app` @ `app.rootmc.net` (or path on `rootmc.net/app/`)  
- [ ] **Delete or dockerize** standalone Mongo for prod — D1 is source of truth today  
- [ ] GitHub Action: pytest + `tsc` on Worker; optional Playwright against **staging** Worker  
- [ ] Feature flag: `MOCK_ECONOMY=false` enforced in CI for `main`  
- [ ] In-app changelog (More tab)  
- [ ] Analytics opt-in (Firebase) — Emergent PRD suggestion  
- [ ] Two-way sync: merge Emergent `frontend/` wins back into RootMC Workspace export script

---

## Do NOT ship as-is (peak killers)

| Issue | Why |
|-------|-----|
| Mongo wallet mint on check-in/vote | Violates treasury policy; double economy |
| Separate JWT secret from Worker | Players log in twice; stats don’t match |
| Synthetic market tickers (`DIAM`, `NETH`) | Misleading vs real `item_key` stock market |
| Fourth auth system (email, etc.) | `/link` is canonical |
| USD anywhere player-facing | Gold (G) only |
| Emergent preview URL as beta link | Must be `api.rootmc.net` + real domain |

---

## Suggested “peak” end state

```
play.rootmc.net (game)
       ↓ sync
api.rootmc.net (Worker + D1)  ← single source of truth
       ↓
├── rootmc.net (marketing + wiki + economy pages)
├── app.rootmc.net OR Play APK (one client, real data)
│      ├── Terminal UI (Emergent design)
│      ├── Rewards: check-in + vote (treasury)
│      └── /link auth
└── Discord / FCM nudges → deep link into app
```

**Kotlin vs PWA:** Peak player experience is **one** polished client on **real** data. Emergent gave the **visual and feature blueprint**; peak work is **integration**, not more mock endpoints.

---

## Priority checklist (copy for sprint board)

**Week 1 (beta)**  
1. Proxy PWA → `api.rootmc.net` OR WebView in Kotlin with live PWA  
2. Real `/link`  
3. Beta download page + Play upload  
4. Timestamps + server-offline states  

**Week 2–3**  
5. Worker: check-in + vote routes + treasury  
6. Port Rewards UI to chosen primary client  
7. Governance + player search link-out  

**Month 2**  
8. Waypoints/votes tracker APIs  
9. FCM + widgets  
10. Compose theme parity with `design_guidelines.json`  

---

## References

| Doc | Location |
|-----|----------|
| Emergent PRD + backlog | [memory/PRD.md](../memory/PRD.md) |
| Design spec | [design_guidelines.json](../design_guidelines.json) |
| Mock API surface | [backend/server.py](../backend/server.py) |
| Production Android | [android/](../android/) |
| Production Worker | [api/rootmc-realm-api/src/](../api/rootmc-realm-api/src/) |

*Cursor post-Emergent review — July 9, 2026. Update when mock backend is retired or Kotlin absorbs Rewards.*
