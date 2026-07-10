"""
Shared foundation for the RootMC Mobile API.

Everything that used to live at the top of `server.py` — env config, Mongo
handles, helpers, models, JWT + link-code, seed data — moved here so the
router modules stay short and testable.
"""
from __future__ import annotations

import os
import uuid
import secrets
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from fastapi import HTTPException, Header
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

# ---------- config ----------
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGO = "HS256"
JWT_TTL_DAYS = 30
LINK_CODE_TTL_MIN = 15
CHECKIN_COOLDOWN_H = 22  # a little under 24 so daily reset feels friendly
VOTE_COOLDOWN_H = 24

# ---------- mongo ----------
client = AsyncIOMotorClient(MONGO_URL, tz_aware=True)
db = client[DB_NAME]

users = db["users"]
link_codes = db["link_codes"]
checkins = db["checkins"]
votes = db["vote_claims"]
market = db["market_items"]
kv = db["kv"]

# ---------- helpers ----------
def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def new_id() -> str:
    return str(uuid.uuid4())

def gen_link_code() -> str:
    """6 chars, avoids ambiguous glyphs (0/O/1/I)."""
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


# ---------- shared pydantic models ----------
class LinkStartRequest(BaseModel):
    minecraft_username: str = Field(..., min_length=3, max_length=16)


class LinkCompleteRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class VoteClaimBody(BaseModel):
    site_id: str


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


def generate_history(base: float, vol: float, trend: float, days: int = 30) -> List[Dict[str, Any]]:
    """Synthetic hourly price history: mean-reverting walk around `base`."""
    rng = random.Random(hash((base, vol, trend)) & 0xffffffff)
    points = []
    total_hours = days * 24
    price = base * (1 - trend * 0.4)
    for i in range(total_hours):
        reversion = 0.02 * (base - price) / base
        drift = (trend / days) * 0.5
        shock = rng.gauss(0, vol) * 0.35
        pct = drift + reversion + shock
        pct = max(-0.08, min(0.08, pct))
        price = max(base * 0.35, min(base * 2.0, price * (1 + pct)))
        t = now_utc() - timedelta(hours=(total_hours - i))
        points.append({"t": iso(t), "price": round(price, 3)})
    return points


async def seed_if_empty() -> None:
    """Idempotent seed. Runs at app startup via lifespan hook."""
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

    if not await kv.find_one({"_id": "economy"}):
        await kv.insert_one({
            "_id": "economy",
            "treasury_reserve": 187_432.50,
            "money_supply": 942_180.75,
            "gold_peg_g_per_ingot": 1.0,
            "reserve_ratio_pct": 19.87,
            "circulating_players": 148,
            "avg_daily_volume": 24_310.0,
            "24h_flows": {"in": 18_240.5, "out": 14_120.0},
            "updated_at": now_utc(),
        })

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
                {"rank": i + 1, "name": n, "value": nw, "delta_pct": round(random.uniform(-3, 8), 1)}
                for i, (n, nw, _, _, _) in enumerate(players)
            ],
            "playtime": [
                {"rank": i + 1, "name": n, "value": p, "unit": "h"}
                for i, (n, _, p, _, _) in enumerate(sorted(players, key=lambda x: -x[2]))
            ],
            "mint": [
                {"rank": i + 1, "name": n, "value": m, "unit": "G"}
                for i, (n, _, _, m, _) in enumerate(sorted(players, key=lambda x: -x[3]))
            ],
            "mcmmo": [
                {"rank": i + 1, "name": n, "value": lvl, "unit": "PL"}
                for i, (n, _, _, _, lvl) in enumerate(sorted(players, key=lambda x: -x[4]))
            ],
        })
