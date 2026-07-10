# Grok post-Emergent report

**Date:** July 9, 2026  
**Context:** After Emergent job `f71356dc` (React PWA + FastAPI/Mongo)  
**Prior:** [grok-pre-emergent-analysis.md](grok-pre-emergent-analysis.md) (recovered from git `e19bbb1`)

---

## Executive summary

Emergent delivered **exactly the vibe** I asked for: a **trading-terminal mobile companion** — dark obsidian, gold accents, mono numerics, ticker strip, sparklines, portfolio breakdown, and a **Rewards hub** (daily check-in + vote sites). That is a major leap toward “market on the go” and daily engagement loops.

The gap is **not UX** — it is **truth**. The PWA runs on **synthetic Mongo data** and a **demo `/link`**. For RootMC peak, this shell must drink from **`api.rootmc.net`** and treasury-backed grants, or players will learn the wrong economy.

**Verdict:** Keep Emergent’s `frontend/` and design system. **Rewire** the data plane. Do **not** throw away the Kotlin app — it already talks to production.

---

## What Emergent nailed (keep)

| Deliverable | Why it matters |
|-------------|----------------|
| `design_guidelines.json` | Performance Pro + retro-futurism — matches “trading app for player shops” brief |
| Home ticker + economy pulse | At-a-glance server + market — my #1 mobile use case |
| Market search/sort/categories + detail charts | Real stock-market feel; maps to rootmc.net/market |
| Portfolio net worth + holdings P&L | Answers “am I winning?” without opening inventory |
| **Rewards: check-in streak + vote sites** | Fills gap I listed as MVP-adjacent (voting awareness + daily habit) |
| `/link` auth UX (6-char code) | Correct mental model — Minecraft 2FA |
| 31 pytest + 74 Playwright passes | Solid regression harness for next push |

---

## What Emergent did not finish (expected)

| Gap | Grok pre-Emergent ask | Status after Emergent |
|-----|----------------------|------------------------|
| Real `api.rootmc.net` data | Implied | ❌ Mock seed |
| Waypoints & notes sync | MVP | ❌ Not started |
| Player search + public stats | MVP | ❌ Not started |
| Voting **tracker** (listing history) | MVP | 🔶 Vote **claim** UI only (mock) |
| Offline Room cache | MVP | ❌ No service worker |
| Loan status on dashboard | MVP | ❌ Not started |
| Towny status | MVP | ❌ Not started |
| Kotlin Compose Play binary | Preferred stack | ❌ Untouched (`android/` stale vs PWA) |
| FCM push | Phase 2 | ❌ Still in Kotlin scaffold only |

---

## Grok assessment of Emergent architecture

**Good call:** PWA because Emergent cannot run `gradlew`. Ship `app.rootmc.net` for July 11 beta **if** wired to live API.

**Bad if left as-is:** Parallel economy in Mongo — check-in/vote `$inc` on wallet violates RootMC treasury doctrine and will fork player trust.

**Recommended path:**

1. **Short term:** PWA + thin proxy → `api.rootmc.net` (delete mock seed in production).  
2. **Medium term:** Port Rewards + terminal Home into Kotlin **or** WebView wrapper in existing APK.  
3. **Long term:** One client, one JWT, D1-backed rewards.

---

## Bugs & polish (from `test_reports/iteration_1.json`)

Emergent should fix in the **last push**:

- [ ] **Check-in countdown** — `Rewards.jsx` timer math; anchor to `loadedAt`, not shifting `now`  
- [ ] **TopBar avatar** — use `navigate('/more')` not `window.location.href`  
- [ ] **Wallet after claim** — `find_one_and_update(return_document=AFTER)` on check-in/vote  
- [ ] **Split `server.py`** — auth / market / portfolio / rewards routers before 700+ lines  
- [ ] **Pull-to-refresh** on all tabs (pre-Emergent ask — still missing)  
- [ ] **Sync timestamps** on every balance and price (data freshness trust)

---

## Grok priorities for Emergent last push

### P0 — production wire (non-negotiable)

1. `REACT_APP_LIVE_API=true` → fetch `https://api.rootmc.net` for market, economy, me, leaderboards, daily-report  
2. Proxy `/link` complete to Worker `POST /api/rootmc/realm/minecraft/link/app/complete`  
3. Stub Worker routes for check-in/vote **or** disable claim buttons until treasury routes exist — **never** Mongo mint in prod  
4. Map mock tickers (`DIAM`) → real `item_key` from stock market API  
5. Deploy PWA to `app.rootmc.net` or `rootmc.net/app/` — not Emergent preview URL  

### P1 — complete the MVP I asked for (on live data)

6. Player search → `/player/` API or public stats endpoint  
7. Voting tracker tab (history + “you haven’t voted on MCSL this week”) — complements Rewards vote claim  
8. Waypoints/notes — **blocked** on plugin; add “coming soon” honestly, don’t fake  
9. Towny line on Home (town name from membership)  
10. PWA `manifest.json` + service worker for install prompt + offline shell  

### P2 — peak engagement

11. Loan chip on Portfolio when API exposes it  
12. Governance read-only feed (link or embed)  
13. Map WebView / deep link `map.rootmc.net`  
14. Firebase FCM hook (even if Kotlin handles delivery later)  
15. Apply dark theme as default — Emergent already did; lock it  

---

## Grok closing

Pre-Emergent I said this app has **huge potential to boost player engagement**. Emergent proved the **feel** in one session. The last push is not more mock features — it is **making the terminal real**.

If July 11 beta ships, ship **live data** or label the build **“UI preview”** so we don’t train players on fake Gold.

— *Grok post-Emergent review, July 9, 2026*
