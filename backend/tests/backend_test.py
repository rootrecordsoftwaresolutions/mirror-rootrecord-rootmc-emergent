"""
RootMC Mobile Companion - Backend API tests (pytest)
Covers: health, /link auth flow, server status, economy, market list/detail,
leaderboards, portfolio, checkin, vote sites, daily report.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback via loading frontend/.env directly for pytest runs
    from dotenv import dotenv_values
    _env = dotenv_values("/app/frontend/.env")
    BASE_URL = (_env.get("REACT_APP_BACKEND_URL") or "").rstrip("/")

API = f"{BASE_URL}/api"

TEST_USERNAME = f"QaBot{int(time.time()) % 10000}"


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def s():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def auth(s):
    """Complete the /link demo flow and return (token, user)."""
    r = s.post(f"{API}/auth/link/start", json={"minecraft_username": TEST_USERNAME})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "code" in body and len(body["code"]) == 6
    code = body["code"]

    r2 = s.post(f"{API}/auth/link/complete", json={"code": code})
    assert r2.status_code == 200, r2.text
    j = r2.json()
    assert "token" in j and "user" in j
    return j["token"], j["user"]


@pytest.fixture
def auth_client(s, auth):
    token, _ = auth
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    })
    return session


# ---------- health ----------
class TestHealth:
    def test_health_ok(self, s):
        r = s.get(f"{API}/health")
        assert r.status_code == 200
        j = r.json()
        assert j["status"] == "ok"
        assert "time" in j


# ---------- server status / economy / daily report ----------
class TestPublicSnapshots:
    def test_server_status(self, s):
        r = s.get(f"{API}/server/status")
        assert r.status_code == 200
        j = r.json()
        assert "_id" not in j
        assert isinstance(j["online"], bool)
        assert isinstance(j["players_online"], int)
        assert isinstance(j["players_max"], int)

    def test_economy_overview(self, s):
        r = s.get(f"{API}/economy/overview")
        assert r.status_code == 200
        j = r.json()
        assert "_id" not in j
        for k in ["treasury_reserve", "money_supply", "gold_peg_g_per_ingot", "24h_flows"]:
            assert k in j
        assert set(j["24h_flows"].keys()) >= {"in", "out"}

    def test_daily_report(self, s):
        r = s.get(f"{API}/daily-report/latest")
        assert r.status_code == 200
        j = r.json()
        assert "_id" not in j
        assert "title" in j and "summary" in j
        assert isinstance(j["highlights"], list) and len(j["highlights"]) > 0


# ---------- auth /link flow ----------
class TestAuth:
    def test_link_start_returns_code(self, s):
        r = s.post(f"{API}/auth/link/start", json={"minecraft_username": "TestQA"})
        assert r.status_code == 200
        j = r.json()
        assert len(j["code"]) == 6
        assert j["demo_mode"] is True

    def test_link_complete_invalid_code(self, s):
        r = s.post(f"{API}/auth/link/complete", json={"code": "ZZZZZZ"})
        assert r.status_code == 404

    def test_link_complete_short_code_validation(self, s):
        r = s.post(f"{API}/auth/link/complete", json={"code": "ABC"})
        assert r.status_code in (400, 422)

    def test_full_link_flow_and_me(self, s):
        r = s.post(f"{API}/auth/link/start", json={"minecraft_username": "FlowUser"})
        code = r.json()["code"]
        r2 = s.post(f"{API}/auth/link/complete", json={"code": code})
        assert r2.status_code == 200
        token = r2.json()["token"]
        r3 = s.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r3.status_code == 200
        me = r3.json()
        assert me["minecraft_username"] == "FlowUser"
        assert "avatar_url" in me and "wallet_gold" in me
        assert "net_worth" in me

    def test_me_without_token(self, s):
        r = s.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_me_invalid_token(self, s):
        r = s.get(f"{API}/auth/me", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401

    def test_code_cannot_be_reused(self, s):
        r = s.post(f"{API}/auth/link/start", json={"minecraft_username": "Reuse"})
        code = r.json()["code"]
        r1 = s.post(f"{API}/auth/link/complete", json={"code": code})
        assert r1.status_code == 200
        r2 = s.post(f"{API}/auth/link/complete", json={"code": code})
        assert r2.status_code == 404


# ---------- market ----------
class TestMarket:
    def test_market_items_default(self, s):
        r = s.get(f"{API}/market/items")
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) >= 10
        # verify no mongo _id leaks
        assert all("_id" not in it for it in items)
        assert all({"ticker", "name", "current_price", "change_24h_pct", "sparkline"}.issubset(it.keys()) for it in items)

    def test_market_sort_gainers_desc(self, s):
        r = s.get(f"{API}/market/items", params={"sort": "gainers"})
        items = r.json()["items"]
        changes = [it["change_24h_pct"] for it in items]
        assert changes == sorted(changes, reverse=True)

    def test_market_sort_losers_asc(self, s):
        r = s.get(f"{API}/market/items", params={"sort": "losers"})
        changes = [it["change_24h_pct"] for it in r.json()["items"]]
        assert changes == sorted(changes)

    def test_market_category_filter(self, s):
        r = s.get(f"{API}/market/items", params={"category": "gem"})
        items = r.json()["items"]
        assert len(items) > 0
        assert all(it["category"] == "gem" for it in items)

    def test_market_item_detail_ranges(self, s):
        for rng in ["1H", "1D", "1W", "1M", "ALL"]:
            r = s.get(f"{API}/market/item/DIAM", params={"range": rng})
            assert r.status_code == 200, f"range {rng} failed"
            j = r.json()
            assert j["ticker"] == "DIAM"
            assert j["range"] == rng
            assert isinstance(j["history"], list) and len(j["history"]) > 0
            assert j["high"] >= j["low"]

    def test_market_item_unknown(self, s):
        r = s.get(f"{API}/market/item/ZZZZ")
        assert r.status_code == 404


# ---------- leaderboards ----------
class TestLeaderboards:
    @pytest.mark.parametrize("cat", ["net_worth", "playtime", "mint", "mcmmo"])
    def test_leaderboard_categories(self, s, cat):
        r = s.get(f"{API}/leaderboards", params={"category": cat})
        assert r.status_code == 200
        j = r.json()
        assert j["category"] == cat
        assert len(j["entries"]) > 0
        first = j["entries"][0]
        assert first["rank"] == 1
        assert "name" in first and "value" in first

    def test_leaderboard_unknown_category(self, s):
        r = s.get(f"{API}/leaderboards", params={"category": "bogus"})
        assert r.status_code == 404


# ---------- portfolio ----------
class TestPortfolio:
    def test_portfolio_requires_auth(self, s):
        r = s.get(f"{API}/portfolio/me")
        assert r.status_code == 401

    def test_portfolio_shape(self, auth_client):
        r = auth_client.get(f"{API}/portfolio/me")
        assert r.status_code == 200
        j = r.json()
        for k in ["net_worth", "delta_24h_pct", "breakdown", "holdings", "history"]:
            assert k in j
        for k in ["wallet", "inventory", "shops", "chests", "market_holdings"]:
            assert k in j["breakdown"]
        assert isinstance(j["holdings"], list)
        assert len(j["history"]) == 30


# ---------- check-in ----------
class TestCheckin:
    def test_status_before_claim(self, auth_client):
        r = auth_client.get(f"{API}/checkin/status")
        assert r.status_code == 200
        j = r.json()
        assert j["can_claim"] is True
        assert j["streak"] == 0
        assert isinstance(j["week"], list) and len(j["week"]) == 7
        assert j["next_reward"]["gold"] == 10

    def test_claim_and_wallet_updates(self, auth_client):
        # get pre-balance
        me = auth_client.get(f"{API}/auth/me").json()
        pre_wallet = me["wallet_gold"]

        r = auth_client.post(f"{API}/checkin/claim")
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["success"] is True
        assert j["reward"]["gold"] == 10
        assert j["new_streak"] == 1

        # verify via /auth/me
        me2 = auth_client.get(f"{API}/auth/me").json()
        assert round(me2["wallet_gold"] - pre_wallet, 2) == 10.00
        assert me2["streak_count"] == 1

    def test_claim_cooldown(self, auth_client):
        r = auth_client.post(f"{API}/checkin/claim")
        assert r.status_code == 429


# ---------- vote sites ----------
class TestVote:
    def test_sites_requires_auth(self, s):
        r = s.get(f"{API}/vote/sites")
        assert r.status_code == 401

    def test_list_sites(self, auth_client):
        r = auth_client.get(f"{API}/vote/sites")
        assert r.status_code == 200
        j = r.json()
        assert len(j["sites"]) == 5
        for site in j["sites"]:
            assert {"id", "name", "reward", "url", "can_claim"}.issubset(site.keys())

    def test_claim_vote_and_cooldown(self, auth_client):
        # Use planetminecraft (isolate from other tests)
        me_before = auth_client.get(f"{API}/auth/me").json()
        pre_wallet = me_before["wallet_gold"]

        r = auth_client.post(f"{API}/vote/claim", json={"site_id": "planetminecraft"})
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["success"] is True
        assert j["reward_gold"] == 20

        me_after = auth_client.get(f"{API}/auth/me").json()
        assert round(me_after["wallet_gold"] - pre_wallet, 2) == 20.00

        # cooldown
        r2 = auth_client.post(f"{API}/vote/claim", json={"site_id": "planetminecraft"})
        assert r2.status_code == 429

    def test_unknown_site(self, auth_client):
        r = auth_client.post(f"{API}/vote/claim", json={"site_id": "not-a-real-site"})
        assert r.status_code == 404


# ---------- cleanup ----------
@pytest.fixture(scope="session", autouse=True)
def _cleanup():
    yield
    # No dedicated cleanup endpoint; test users are prefixed with QaBot/FlowUser/Reuse
    # and are harmless (demo mode).
