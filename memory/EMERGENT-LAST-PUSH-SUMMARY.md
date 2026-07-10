# Emergent last push (memory copy)

Full checklist: **`docs/EMERGENT-LAST-PUSH.md`** (repo root relative).

## Do now
1. Wire `frontend/` to `https://api.rootmc.net` — `REACT_APP_USE_MOCK=false`
2. Real `/link` JWT (Worker endpoint, not local code gen)
3. No Mongo Gold mint in production — disable Claim or Worker treasury routes
4. Fix: Rewards countdown, TopBar `navigate()` not `window.location`
5. Pull-to-refresh + "last synced" labels
6. Keep `design_guidelines.json` visual system

## Do not
- Add mock tickers in prod
- Mint wallet G in Mongo for check-in/vote
- Rewrite Kotlin app this sprint

Beta: **July 11, 2026**
