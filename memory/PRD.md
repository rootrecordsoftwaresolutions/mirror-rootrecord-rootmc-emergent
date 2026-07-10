# RootMC Terminal — Mobile Companion PWA

## Original problem statement
> Look at our android mobile app. I am looking to make the android app a mirror of the website, but in a condensed form. I also want to add in daily checkin features that utilize our economy and sends a reward for checking in. it should also have the vote sites. rootmc.net. I want a modern fresh clean mobile app for the server. Fully lock into the economy, and provide a unique app that feels like a trading app, but for player shops, data, stats.

## Delivery approach
The RootMC repo ships three surfaces: `web/` (Cloudflare Pages), `api/` (Cloudflare Workers), and `android/` (Kotlin/Compose native).  
The Emergent build environment cannot compile Kotlin APKs, so we shipped a **mobile-first React PWA at the repo root (`/app/frontend`)** backed by a new **FastAPI service (`/app/backend`)** that mirrors the RootMC data model. This PWA is deployable to `app.rootmc.net`, embeddable in the existing Android WebView, and directly installable to the home screen.

## User personas
- **Active RootMC player** — checks server status, prices, portfolio, and claims rewards from their phone during their commute.
- **Shop owner / trader** — watches item price movements and sees whether their listings need adjusting.
- **Casual voter / grinder** — opens the app once a day to click daily check-in + all vote sites for their free Gold.

## Core requirements (static)
- Trading-app aesthetic: dark obsidian (#050505) base, gold (#FFB800) accent, mono numerics.
- Mirror of rootmc.net in condensed form: server status, economy pulse, stock market, player-shop prices, portfolio, leaderboards, daily report.
- Daily check-in with treasury-backed rewards (10 → 15 → 20 → 25 → 35 → 50 → 100 G over a 7-day streak).
- 5 vote sites with 24h cooldowns and reward tracking.
- In-game `/link` 6-character code auth (JWT, ~30-day TTL).
- All player-facing amounts in **Gold (G)**, never USD.

## Architecture (this repo)
```
/app/backend/       FastAPI + Motor + JWT (all /api/* routes, seeded on startup)
/app/frontend/      React (CRA) + Tailwind + Framer Motion + Recharts + Sonner
/app/design_guidelines.json   JSON spec followed for the visual system
```

Existing repo surfaces (`web/`, `api/rootmc-*`, `android/`) are **untouched** — the PWA is additive.

## What's been implemented (2026-07-10)

### Backend (`/app/backend/server.py`)
- `POST /api/auth/link/start` — creates 6-char link code (dev-mode returns it).
- `POST /api/auth/link/complete` — consumes code, mints JWT + bootstraps a believable player.
- `GET  /api/auth/me` — current user snapshot.
- `GET  /api/server/status` — online/offline, players, TPS, version, MOTD.
- `GET  /api/economy/overview` — treasury reserve, money supply, gold peg, 24h flows.
- `GET  /api/market/items?sort=&category=` — 18 tickers with sparkline + change_24h/7d.
- `GET  /api/market/item/{ticker}?range=1H|1D|1W|1M|ALL` — full price history.
- `GET  /api/portfolio/me` — net worth, wealth breakdown, holdings, 30-day history curve.
- `GET  /api/leaderboards?category=net_worth|playtime|mint|mcmmo` — top 20.
- `GET  /api/checkin/status` + `POST /api/checkin/claim` — streak + cooldown + treasury debit.
- `GET  /api/vote/sites` + `POST /api/vote/claim` — 5 sites, 24h cooldowns.
- `GET  /api/daily-report/latest` — AI report card.
- Auto-seeds market, treasury, server status, daily report, leaderboards on startup.
- **MOCKED** — market/treasury/leaderboards use realistic synthetic data. Real `api.rootmc.net` proxying is a next step.

### Frontend (`/app/frontend/src`)
- Bottom-nav shell (5 tabs) inside `max-w-md` container with gold-underlined active tab.
- Persistent top bar with live server-status pill + auto-scrolling ticker strip (all 18 tickers).
- **Home** — server card, 4-tile economy pulse, quick-action tiles (check-in + vote), top gainers/losers, daily report card.
- **Market** — search, sort (volume/gainers/losers/price), category chips (all/gems/ores/gear/farm/rare), sparkline rows.
- **Market Detail** — 5xl mono price, area chart with tooltip, 5 range tabs, high/low/volume/listings grid, trade info card.
- **Portfolio** — big net-worth ticker, delta, 30d curve, wealth pie + breakdown, holdings list with P&L.
- **Rewards** — Daily Check-in tab (pulsing gold Claim button, confetti burst, 7-day streak grid, live countdown) + Vote Sites tab (5 sites, Vote→Claim state machine, cooldown timers).
- **Leaderboards** — 4 category tabs, rank medallions, avatars.
- **More** — profile card, external links (Discord/Wiki/Constitution/Live Map), logout.
- **Auth** — /link username → 6-char code (Minecraft-2FA feel) → JWT.
- Sonner toasts + Framer Motion route + micro-interactions throughout.

## Testing status
- **31/31** backend pytest suites pass (auth flow, market sort/filter, portfolio, checkin+cooldown, vote+cooldown, leaderboards).
- **74/74** Playwright UI assertions pass end-to-end.
- Manual screenshot review confirms design guideline adherence.

## Phase 2 additions (2026-01 — Emergent last push)

### Bug fixes from `test_reports/iteration_1.json`
- ✅ `TopBar.jsx` — avatar now uses `navigate('/more')` (react-router SPA nav) instead of `window.location.href`.
- ✅ `server.py` — `/checkin/claim` and `/vote/claim` now return the post-update wallet balance via `find_one_and_update(return_document=AFTER)` (fresh value, no race).
- ✅ Countdown math (`Rewards.jsx`) — already fixed with `loadedAtRef` anchor; verified.

### Live API scaffolding (Block 1–2)
- ✅ New `frontend/src/lib/rootmc-api.js` — axios client for `api.rootmc.net`, exports the production endpoint map (server/economy/market/me/leaderboards/daily-report/link-complete/checkin/vote).
- ✅ Env toggles in `frontend/.env` + `frontend/.env.example`:
  - `REACT_APP_ROOTMC_API` — Cloudflare Worker base URL.
  - `REACT_APP_USE_MOCK` — default `true` for preview; flip to `false` on `main` to switch to live worker.
  - `REACT_APP_DEMO_LINK` — controls local demo `/link` code issuance.
  - `REACT_APP_LIVE_REWARDS` — feature flag for the treasury-backed check-in/vote routes.

### Rewards guarding (Block 3)
- ✅ When `USE_MOCK=false` **and** `LIVE_REWARDS=false`, the Rewards screen shows a warn banner ("Coming soon — treasury wiring") and disables both check-in and vote claim buttons in production. **Never mints Gold in Mongo in prod.**

### UX polish (Block 5)
- ✅ `usePullToRefresh` hook + `PullIndicator` — Home, Market, Portfolio now support the mobile gesture.
- ✅ `SyncBadge` — "Synced Ns/m/h ago" pill on Home (Economy Pulse), Market (header), Portfolio (Net worth header).
- ✅ `ServerHealthBanner` — sticky banner under top bar when API is unreachable or server offline.
- ✅ PWA install prompt: `public/service-worker.js` (network-first for HTML, cache-first for assets, skips `/api/*`), registered in `src/index.js`. `manifest.json` updated with description, categories, and SVG icons (`icon-192.svg`, `icon-512.svg`).
- ✅ More tab: **Player Search** field (opens `rootmc.net/player/?u=…` in a new tab) + **Beta Feedback** row (Discord).

### Deploy docs
- ✅ `frontend/.env.example` documents every flag for Cloudflare Pages deploy at `app.rootmc.net`.

## What's NOT wired (backlog)

### P0 — production wiring
- [ ] Swap seed data for real Cloudflare Worker (`api.rootmc.net`) — market prices, treasury, leaderboards, daily report, player wallet.
- [ ] Real `/link` bridge: replace demo-mode code issuance with a call to `POST /api/rootmc/realm/minecraft/link/app/complete` on `api.rootmc.net`.
- [ ] Treasury debit for check-in/vote must call `RootMcTreasuryService` webhook, not in-memory KV.
- [ ] Push notifications (FCM) for shop-price alerts (already scaffolded in Android app).

### P1 — parity with website
- [ ] Governance (proposals + voting) — currently link-out.
- [ ] Player wiki search / detail.
- [ ] Discord verify OAuth path (alternative to /link).
- [ ] Bluemap embed (WebView / iframe from `map.rootmc.net`).
- [ ] Deep-link routes for existing Android app's shop-alert push payloads.

### P2 — Kotlin/Compose native parity
- [ ] Port the same screens as Compose to `/app/android/app/src/main/java/com/rootrecord/rootmc/ui/*` so the Play Store binary matches this PWA. (Requires local Android SDK build — out of scope for this environment.)

## Next tasks — **see [docs/EMERGENT-LAST-PUSH.md](../docs/EMERGENT-LAST-PUSH.md)**

Human + Cursor + Grok merged the final push into `docs/EMERGENT-LAST-PUSH.md`. Execute that file block-by-block. Do not add new mock features.

Quick recap:
1. `REACT_APP_ROOTMC_API=https://api.rootmc.net` + `REACT_APP_USE_MOCK=false`
2. Real `/link` via Worker `POST /api/rootmc/realm/minecraft/link/app/complete`
3. Disable Mongo wallet mint in prod; treasury on Worker for check-in/vote
4. Fix Rewards countdown + TopBar SPA nav (see `test_reports/iteration_1.json`)
5. Pull-to-refresh, sync timestamps, PWA service worker
6. Update this PRD when done
