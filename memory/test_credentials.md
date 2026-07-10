# Test Credentials — RootMC Terminal

## Auth model
The PWA uses the RootMC in-game `/link` flow — a 6-character code exchanged for a JWT.  
**No email/password. No pre-seeded users.**

## Demo mode (current backend)
- Endpoint: `POST /api/auth/link/start` with `{ "minecraft_username": "<any 3-16 char name>" }`
- Response includes the 6-char code (in production it would be issued in-game and hidden).
- Endpoint: `POST /api/auth/link/complete` with `{ "code": "ABC123" }` returns `{ token, user }`.
- The Auth screen pre-fills the code from step 1, so you can complete the flow with two taps.

## To sign in as a test player
1. Open the app → tap **Sign in with /link**.
2. Enter any Minecraft username (e.g. `QaBot`, `Notch`, `TestPlayer`).
3. Tap **Request code** → the code auto-populates the code field.
4. Tap **Complete link** → you're in.

Each new username creates a fresh player with deterministic randomized wallet/inventory/shops/holdings (seeded from the username hash — same name always returns the same player).

## Suggested demo accounts for screenshots / demos
- `Notch` — largest starting portfolio
- `GoldMiner` — mid-tier player with 3 holdings
- `QaBot` — automated testing user
