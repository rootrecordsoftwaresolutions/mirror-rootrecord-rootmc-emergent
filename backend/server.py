"""
RootMC Mobile Companion API
Mirrors rootmc.net endpoints in condensed form for the mobile PWA.
- /link-style auth (6-char code)
- Economy overview (treasury, gold peg, movers)
- Player-shop stock market (items with sparklines + candle history)
- Portfolio (wallet / inventory / shops / chests + holdings)
- Leaderboards
- Daily check-in with streak + treasury-backed rewards
- Vote site cooldown tracking
- Daily AI report card
"""
from fastapi import FastAPI, HTTPException, Depends, Header, APIRouter, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta, date
from contextlib import asynccontextmanager
from jose import jwt, JWTError
import os
import uuid
import secrets
import string
import random
import math
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGO = "HS256"
JWT_TTL_DAYS = 30
LINK_CODE_TTL_MIN = 15
CHECKIN_COOLDOWN_H = 22  # a little under 24 so daily reset feels friendly
VOTE_COOLDOWN_H = 24

client = AsyncIOMotorClient(MONGO_URL, tz_aware=True)
db = client[DB_NAME]

# --- collections ---
users = db["users"]
link_codes = db["link_codes"]
checkins = db["checkins"]
votes = db["vote_claims"]
market = db["market_items"]
kv = db["kv"]  # generic key/value for treasury etc

# ---------- helpers ----------
def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def new_id() -> str:
    return str(uuid.uuid4())

def gen_link_code() -> str:
    # 6 chars, avoid ambiguous (0/O/1/I)
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))

def make_jwt(user_id: str, username: str) -> str:
    payload = {
        "sub": user_id,
        "u": username,
        "iat": int(now_utc().timestamp()),
        "exp": int((now_utc() + timedelta(days=JWT_TTL_DAYS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing_bearer")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid_token")
    user = await users.find_one({"_id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="user_gone")
    return user

def serialize_user(u: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": u["_id"],
        "minecraft_username": u["minecraft_username"],
        "minecraft_uuid": u.get("minecraft_uuid"),
        "avatar_url": f"https://mc-heads.net/avatar/{u['minecraft_username']}/128",
        "head_url": f"https://mc-heads.net/head/{u['minecraft_username']}/128",
        "wallet_gold": round(u.get("wallet_gold", 0), 2),
        "inventory_value": round(u.get("inventory_value", 0), 2),
        "shop_stock_value": round(u.get("shop_stock_value", 0), 2),
        "chest_value": round(u.get("chest_value", 0), 2),
        "net_worth": round(
            u.get("wallet_gold", 0)
            + u.get("inventory_value", 0)
            + u.get("shop_stock_value", 0)
            + u.get("chest_value", 0),
            2,
        ),
        "streak_count": u.get("streak_count", 0),
        "last_checkin_at": iso(u["last_checkin_at"]) if u.get("last_checkin_at") else None,
        "playtime_hours": u.get("playtime_hours", 0),
        "mcmmo_power_level": u.get("mcmmo_power_level", 0),
        "town": u.get("town"),
        "created_at": iso(u["created_at"]),
    }

# ---------- seed data ----------
MARKET_SEED = [
    # (ticker, name, category, base_price, volatility, trend)
    ("DIAM", "Diamond", "gem", 32.0, 0.06, 0.02),
    ("NETH", "Netherite Ingot", "gem", 180.0, 0.09, 0.04),
    ("EMER", "Emerald", "gem", 14.0, 0.07, -0.01),
    ("IRON", "Iron Block", "ore", 3.5, 0.04, 0.005),
    ("GOLD", "Gold Block", "ore", 9.0, 0.02, 0.0),
    ("COAL", "Coal Block", "ore", 1.2, 0.05, -0.02),
    ("REDS", "Redstone Block", "ore", 4.8, 0.06, 0.01),
    ("LAPS", "Lapis Block", "ore", 3.2, 0.05, -0.005),
    ("ANCT", "Ancient Debris", "gem", 55.0, 0.10, 0.06),
    ("ELYT", "Elytra", "gear", 620.0, 0.12, 0.03),
    ("TSHT", "Totem of Undying", "gear", 220.0, 0.08, 0.02),
    ("ENDR", "Ender Pearl", "misc", 5.0, 0.09, 0.01),
    ("SHUL", "Shulker Shell", "gear", 85.0, 0.10, 0.04),
    ("BEAC", "Beacon", "gear", 480.0, 0.05, 0.0),
    ("WHEA", "Wheat (stack)", "farm", 0.8, 0.03, 0.002),
    ("SGCN", "Sugar Cane (stack)", "farm", 0.9, 0.04, -0.01),
    ("MELN", "Glistering Melon", "farm", 6.5, 0.07, 0.015),
    ("SPWN", "Mob Spawner", "rare", 950.0, 0.14, 0.08),
]

VOTE_SITES = [
    {"id": "minecraftservers-org", "name": "MinecraftServers.org", "reward": 25, "url": "https://minecraftservers.org/vote/rootmc"},
    {"id": "planetminecraft", "name": "PlanetMinecraft", "reward": 20, "url": "https://planetminecraft.com/server/rootmc/vote/"},
    {"id": "topg", "name": "TopG", "reward": 20, "url": "https://topg.org/minecraft-servers/server-rootmc"},
    {"id": "minecraft-mp", "name": "Minecraft-MP", "reward": 15, "url": "https://minecraft-mp.com/server-rootmc/vote/"},
    {"id": "minecraftmaps", "name": "Minecraft-Server-List", "reward": 15, "url": "https://minecraft-server-list.com/server/rootmc/vote/"},
]

def generate_history(base: float, vol: float, trend: float, days: int = 30) -> List[Dict[str, Any]]:
    """Synthetic hourly price history: mean-reverting walk around `base`."""
    rng = random.Random(hash((base, vol, trend)) & 0xffffffff)
    points = []
    total_hours = days * 24
    # Start ~ 8% below/above base biased by trend sign
    price = base * (1 - trend * 0.4)
    for i in range(total_hours):
        # mean reversion toward base with mild trend drift & bounded shock
        reversion = 0.02 * (base - price) / base
        drift = (trend / days) * 0.5
        shock = rng.gauss(0, vol) * 0.35
        pct = drift + reversion + shock
        # clamp per-hour move
        pct = max(-0.08, min(0.08, pct))
        price = max(base * 0.35, min(base * 2.0, price * (1 + pct)))
        t = now_utc() - timedelta(hours=(total_hours - i))
        points.append({"t": iso(t), "price": round(price, 3)})
    return points


async def seed_if_empty():
    # Market items
    if await market.count_documents({}) == 0:
        docs = []
        for ticker, name, cat, base, vol, trend in MARKET_SEED:
            hist = generate_history(base, vol, trend)
            current = hist[-1]["price"]
            day_ago = hist[-24]["price"] if len(hist) >= 24 else hist[0]["price"]
            week_ago = hist[-24 * 7]["price"] if len(hist) >= 24 * 7 else hist[0]["price"]
            docs.append({
                "_id": ticker,
                "ticker": ticker,
                "name": name,
                "category": cat,
                "current_price": current,
                "change_24h_pct": round((current - day_ago) / day_ago * 100, 2),
                "change_7d_pct": round((current - week_ago) / week_ago * 100, 2),
                "volume_24h": round(random.uniform(500, 5000) * base, 1),
                "listings": random.randint(3, 40),
                "history": hist,
                "sparkline": [round(h["price"], 3) for h in hist[-48:]],
                "updated_at": now_utc(),
            })
        await market.insert_many(docs)

    # Treasury / economy snapshot
    if not await kv.find_one({"_id": "economy"}):
        await kv.insert_one({
            "_id": "economy",
            "treasury_reserve": 187_432.50,
            "money_supply": 942_180.75,
            "gold_peg_g_per_ingot": 1.0,
            "reserve_ratio_pct": 19.87,
            "circulating_players": 148,
            "avg_daily_volume": 24_310.0,
            "24h_flows": {
                "in": 18_240.5,   # into treasury (fees, taxes)
                "out": 14_120.0,  # payouts (checkins, votes, dividends)
            },
            "updated_at": now_utc(),
        })

    # Server status
    if not await kv.find_one({"_id": "server_status"}):
        await kv.insert_one({
            "_id": "server_status",
            "online": True,
            "players_online": 27,
            "players_max": 100,
            "tps": 19.8,
            "version": "26.2",
            "motd": "RootMC — real economy, real gold",
            "updated_at": now_utc(),
        })

    # Daily AI report
    if not await kv.find_one({"_id": "daily_report"}):
        await kv.insert_one({
            "_id": "daily_report",
            "date": iso(now_utc()),
            "title": "Diamond markets rally as Netherite miners strike new veins",
            "summary": (
                "Treasury inflows climbed 12% overnight on the back of "
                "increased Netherite volume from the Nether Frontier. "
                "The stock market saw Diamond (DIAM) up 4.2% and Ancient "
                "Debris (ANCT) posting a fresh 30-day high. Vote turnout "
                "hit 82% — highest weekday reading this month."
            ),
            "highlights": [
                {"label": "Top mover", "value": "SPWN +14.3%"},
                {"label": "Volume leader", "value": "DIAM 4.1k G"},
                {"label": "New players", "value": "6"},
                {"label": "Blocks placed", "value": "184,271"},
            ],
        })

    # Leaderboards
    if not await kv.find_one({"_id": "leaderboards"}):
        players = [
            ("Notch", 42500, 812.5, 45210, 128.4),
            ("EnderQueen", 38900, 720.0, 39120, 118.7),
            ("PixelPaladin", 33200, 665.3, 33450, 104.9),
            ("CobbleKing", 28450, 590.1, 29100, 99.2),
            ("GhastBuster", 24100, 512.7, 24010, 91.3),
            ("Shroomlight", 21870, 480.6, 22300, 87.8),
            ("VoidWalker", 19420, 445.2, 20110, 82.4),
            ("SkyBastion", 17650, 402.1, 18540, 76.9),
            ("BlazeRider", 15900, 361.4, 16820, 71.2),
            ("StoneMason", 14210, 320.9, 15100, 66.5),
            ("MoonMiner", 12980, 289.7, 13920, 61.8),
            ("GoldenGoat", 11500, 250.4, 12610, 57.1),
        ]
        await kv.insert_one({
            "_id": "leaderboards",
            "net_worth": [
                {"rank": i+1, "name": n, "value": nw, "delta_pct": round(random.uniform(-3, 8), 1)}
                for i, (n, nw, _, _, _) in enumerate(players)
            ],
            "playtime": [
                {"rank": i+1, "name": n, "value": p, "unit": "h"}
                for i, (n, _, p, _, _) in enumerate(sorted(players, key=lambda x: -x[2]))
            ],
            "mint": [
                {"rank": i+1, "name": n, "value": m, "unit": "G"}
                for i, (n, _, _, m, _) in enumerate(sorted(players, key=lambda x: -x[3]))
            ],
            "mcmmo": [
                {"rank": i+1, "name": n, "value": lvl, "unit": "PL"}
                for i, (n, _, _, _, lvl) in enumerate(sorted(players, key=lambda x: -x[4]))
            ],
        })

# ---------- API ----------
api = APIRouter(prefix="/api")

@api.get("/health")
async def health():
    return {"status": "ok", "time": iso(now_utc())}

# --- Auth (/link flow) ---
class LinkStartRequest(BaseModel):
    minecraft_username: str = Field(..., min_length=3, max_length=16)

@api.post("/auth/link/start")
async def auth_link_start(body: LinkStartRequest):
    """
    Simulates the in-game /link flow.
    In production, the player runs /link on play.rootmc.net and the plugin
    generates the code. Here we issue the code back (dev/demo mode).
    """
    code = gen_link_code()
    await link_codes.insert_one({
        "_id": new_id(),
        "code": code,
        "minecraft_username": body.minecraft_username.strip(),
        "created_at": now_utc(),
        "consumed": False,
    })
    return {
        "code": code,
        "expires_in_min": LINK_CODE_TTL_MIN,
        "instructions": f"Run /link {code} in-game on play.rootmc.net within {LINK_CODE_TTL_MIN} minutes.",
        "demo_mode": True,
    }

class LinkCompleteRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)

@api.post("/auth/link/complete")
async def auth_link_complete(body: LinkCompleteRequest):
    code = body.code.strip().upper()
    rec = await link_codes.find_one({"code": code, "consumed": False})
    if not rec:
        raise HTTPException(status_code=404, detail="code_not_found_or_used")
    if now_utc() - rec["created_at"] > timedelta(minutes=LINK_CODE_TTL_MIN):
        raise HTTPException(status_code=410, detail="code_expired")
    await link_codes.update_one({"_id": rec["_id"]}, {"$set": {"consumed": True, "consumed_at": now_utc()}})

    username = rec["minecraft_username"]
    user = await users.find_one({"minecraft_username_lc": username.lower()})
    if not user:
        # bootstrap a fresh, believable RootMC player
        rng = random.Random(hash(username.lower()) & 0xffffffff)
        user = {
            "_id": new_id(),
            "minecraft_username": username,
            "minecraft_username_lc": username.lower(),
            "minecraft_uuid": str(uuid.UUID(int=rng.getrandbits(128))),
            "created_at": now_utc(),
            "last_login": now_utc(),
            "wallet_gold": round(rng.uniform(120, 2400), 2),
            "inventory_value": round(rng.uniform(200, 3200), 2),
            "shop_stock_value": round(rng.uniform(0, 5000), 2),
            "chest_value": round(rng.uniform(50, 1800), 2),
            "playtime_hours": round(rng.uniform(12, 380), 1),
            "mcmmo_power_level": rng.randint(120, 1400),
            "town": rng.choice(["Ashfall", "Emberhold", "Rootspire", "Goldreach", None, None]),
            "streak_count": 0,
            "last_checkin_at": None,
            "holdings": _seed_holdings(rng),
        }
        await users.insert_one(user)
    else:
        await users.update_one({"_id": user["_id"]}, {"$set": {"last_login": now_utc()}})

    token = make_jwt(user["_id"], user["minecraft_username"])
    return {"token": token, "user": serialize_user(user)}


def _seed_holdings(rng: random.Random) -> List[Dict[str, Any]]:
    picks = rng.sample([m[0] for m in MARKET_SEED], k=rng.randint(3, 6))
    return [
        {
            "ticker": t,
            "quantity": rng.randint(1, 40),
            "avg_cost": round(rng.uniform(0.5, 200), 2),
        }
        for t in picks
    ]


@api.get("/auth/me")
async def auth_me(user=Depends(get_current_user)):
    return serialize_user(user)


# --- Server status ---
@api.get("/server/status")
async def server_status():
    doc = await kv.find_one({"_id": "server_status"})
    doc["updated_at"] = iso(doc["updated_at"])
    doc.pop("_id", None)
    return doc


# --- Economy ---
@api.get("/economy/overview")
async def economy_overview():
    doc = await kv.find_one({"_id": "economy"})
    doc["updated_at"] = iso(doc["updated_at"])
    doc.pop("_id", None)
    # add small live jitter so it feels alive
    doc["treasury_reserve"] = round(doc["treasury_reserve"] + random.uniform(-40, 60), 2)
    return doc


# --- Market ---
@api.get("/market/items")
async def market_items(category: Optional[str] = None, sort: str = "volume"):
    q = {}
    if category:
        q["category"] = category
    docs = await market.find(q, {"history": 0}).to_list(200)
    key_map = {
        "volume": lambda d: -d["volume_24h"],
        "gainers": lambda d: -d["change_24h_pct"],
        "losers": lambda d: d["change_24h_pct"],
        "price": lambda d: -d["current_price"],
        "name": lambda d: d["name"],
    }
    docs.sort(key=key_map.get(sort, key_map["volume"]))
    for d in docs:
        d["id"] = d.pop("_id")
        d["updated_at"] = iso(d["updated_at"])
    return {"items": docs}


@api.get("/market/item/{ticker}")
async def market_item(ticker: str, range: str = "1D"):
    doc = await market.find_one({"_id": ticker.upper()})
    if not doc:
        raise HTTPException(404, "not_found")
    hist = doc["history"]
    range_map = {"1H": 1, "1D": 24, "1W": 24 * 7, "1M": 24 * 30, "ALL": len(hist)}
    n = range_map.get(range.upper(), 24)
    trimmed = hist[-n:]
    return {
        "id": doc["_id"],
        "ticker": doc["ticker"],
        "name": doc["name"],
        "category": doc["category"],
        "current_price": doc["current_price"],
        "change_24h_pct": doc["change_24h_pct"],
        "change_7d_pct": doc["change_7d_pct"],
        "volume_24h": doc["volume_24h"],
        "listings": doc["listings"],
        "range": range.upper(),
        "history": trimmed,
        "high": max(h["price"] for h in trimmed),
        "low": min(h["price"] for h in trimmed),
    }


# --- Leaderboards ---
@api.get("/leaderboards")
async def leaderboards(category: str = "net_worth"):
    doc = await kv.find_one({"_id": "leaderboards"})
    if category not in doc:
        raise HTTPException(404, "unknown_category")
    return {"category": category, "entries": doc[category][:20]}


# --- Portfolio ---
@api.get("/portfolio/me")
async def portfolio_me(user=Depends(get_current_user)):
    holdings = user.get("holdings", [])
    market_lookup = {m["_id"]: m async for m in market.find({}, {"history": 0})}
    enriched = []
    total_value = 0.0
    for h in holdings:
        mi = market_lookup.get(h["ticker"])
        if not mi:
            continue
        value = h["quantity"] * mi["current_price"]
        cost = h["quantity"] * h["avg_cost"]
        pl = value - cost
        pl_pct = (pl / cost * 100) if cost > 0 else 0
        total_value += value
        enriched.append({
            "ticker": h["ticker"],
            "name": mi["name"],
            "quantity": h["quantity"],
            "avg_cost": round(h["avg_cost"], 2),
            "current_price": mi["current_price"],
            "value": round(value, 2),
            "pl": round(pl, 2),
            "pl_pct": round(pl_pct, 2),
            "change_24h_pct": mi["change_24h_pct"],
            "sparkline": mi["sparkline"],
        })
    enriched.sort(key=lambda x: -x["value"])

    wallet = user.get("wallet_gold", 0)
    inv = user.get("inventory_value", 0)
    shops = user.get("shop_stock_value", 0)
    chest = user.get("chest_value", 0)
    net_worth = wallet + inv + shops + chest + total_value

    # tiny synthetic 30d net worth curve
    rng = random.Random(hash(user["_id"]) & 0xffffffff)
    curve = []
    v = net_worth * 0.85
    for i in range(30):
        v = v * (1 + rng.gauss(0.006, 0.02))
        curve.append({"t": iso(now_utc() - timedelta(days=29 - i)), "value": round(v, 2)})
    curve[-1]["value"] = round(net_worth, 2)

    return {
        "net_worth": round(net_worth, 2),
        "delta_24h_pct": round(rng.uniform(-3, 7), 2),
        "breakdown": {
            "wallet": round(wallet, 2),
            "inventory": round(inv, 2),
            "shops": round(shops, 2),
            "chests": round(chest, 2),
            "market_holdings": round(total_value, 2),
        },
        "holdings": enriched,
        "history": curve,
    }


# --- Daily check-in ---
def _checkin_reward(streak: int) -> Dict[str, Any]:
    # tiered rewards, treasury-backed
    tiers = [10, 15, 20, 25, 35, 50, 100]
    idx = min(streak, 6)
    reward = tiers[idx]
    return {"gold": reward, "tier": idx + 1, "tier_label": f"Day {idx + 1}"}


@api.get("/checkin/status")
async def checkin_status(user=Depends(get_current_user)):
    last = user.get("last_checkin_at")
    streak = user.get("streak_count", 0)
    can_claim = True
    seconds_until = 0
    if last:
        elapsed = now_utc() - last
        if elapsed < timedelta(hours=CHECKIN_COOLDOWN_H):
            can_claim = False
            seconds_until = int((timedelta(hours=CHECKIN_COOLDOWN_H) - elapsed).total_seconds())
        # reset streak if >48h gap
        if elapsed > timedelta(hours=48):
            streak = 0
    next_reward = _checkin_reward(streak)
    week = [_checkin_reward(i) for i in range(7)]
    return {
        "can_claim": can_claim,
        "seconds_until_next": seconds_until,
        "streak": streak,
        "next_reward": next_reward,
        "week": week,
        "last_claimed_at": iso(last) if last else None,
    }


@api.post("/checkin/claim")
async def checkin_claim(user=Depends(get_current_user)):
    last = user.get("last_checkin_at")
    streak = user.get("streak_count", 0)
    if last:
        elapsed = now_utc() - last
        if elapsed < timedelta(hours=CHECKIN_COOLDOWN_H):
            raise HTTPException(429, {"error": "cooldown", "seconds": int((timedelta(hours=CHECKIN_COOLDOWN_H) - elapsed).total_seconds())})
        if elapsed > timedelta(hours=48):
            streak = 0
    new_streak = streak + 1 if streak < 7 else 1  # weekly loop
    reward = _checkin_reward(streak)  # reward for current tier
    await users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"streak_count": new_streak, "last_checkin_at": now_utc()},
            "$inc": {"wallet_gold": reward["gold"]},
        },
    )
    await checkins.insert_one({
        "_id": new_id(),
        "user_id": user["_id"],
        "claimed_at": now_utc(),
        "reward_gold": reward["gold"],
        "streak_after": new_streak,
    })
    # treasury debit (mocked)
    await kv.update_one({"_id": "economy"}, {"$inc": {"treasury_reserve": -reward["gold"], "24h_flows.out": reward["gold"]}})
    return {
        "success": True,
        "reward": reward,
        "new_streak": new_streak,
        "new_wallet_balance": round(user.get("wallet_gold", 0) + reward["gold"], 2),
    }


# --- Vote sites ---
@api.get("/vote/sites")
async def vote_sites_list(user=Depends(get_current_user)):
    # for each site, compute cooldown
    recent = await votes.find({"user_id": user["_id"]}).to_list(200)
    last_by_site: Dict[str, datetime] = {}
    for v in recent:
        prev = last_by_site.get(v["site_id"])
        if not prev or v["claimed_at"] > prev:
            last_by_site[v["site_id"]] = v["claimed_at"]
    out = []
    for s in VOTE_SITES:
        last = last_by_site.get(s["id"])
        can_claim = True
        seconds_until = 0
        if last:
            elapsed = now_utc() - last
            if elapsed < timedelta(hours=VOTE_COOLDOWN_H):
                can_claim = False
                seconds_until = int((timedelta(hours=VOTE_COOLDOWN_H) - elapsed).total_seconds())
        out.append({**s, "can_claim": can_claim, "seconds_until": seconds_until, "last_claimed_at": iso(last) if last else None})
    total_earned_today = sum(
        v["reward_gold"] for v in recent
        if v["claimed_at"] > now_utc() - timedelta(hours=24)
    )
    return {"sites": out, "earned_today": round(total_earned_today, 2)}


class VoteClaimBody(BaseModel):
    site_id: str

@api.post("/vote/claim")
async def vote_claim(body: VoteClaimBody, user=Depends(get_current_user)):
    site = next((s for s in VOTE_SITES if s["id"] == body.site_id), None)
    if not site:
        raise HTTPException(404, "unknown_site")
    # cooldown check
    last = await votes.find_one({"user_id": user["_id"], "site_id": site["id"]}, sort=[("claimed_at", -1)])
    if last:
        elapsed = now_utc() - last["claimed_at"]
        if elapsed < timedelta(hours=VOTE_COOLDOWN_H):
            raise HTTPException(429, {"error": "cooldown", "seconds": int((timedelta(hours=VOTE_COOLDOWN_H) - elapsed).total_seconds())})
    reward_g = site["reward"]
    await votes.insert_one({
        "_id": new_id(),
        "user_id": user["_id"],
        "site_id": site["id"],
        "claimed_at": now_utc(),
        "reward_gold": reward_g,
    })
    await users.update_one({"_id": user["_id"]}, {"$inc": {"wallet_gold": reward_g}})
    await kv.update_one({"_id": "economy"}, {"$inc": {"treasury_reserve": -reward_g, "24h_flows.out": reward_g}})
    return {"success": True, "reward_gold": reward_g, "site": site["name"]}


# --- Daily report ---
@api.get("/daily-report/latest")
async def daily_report_latest():
    doc = await kv.find_one({"_id": "daily_report"})
    doc.pop("_id", None)
    return doc


# ---------- app wiring ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_if_empty()
    yield

app = FastAPI(title="RootMC Mobile API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api)
