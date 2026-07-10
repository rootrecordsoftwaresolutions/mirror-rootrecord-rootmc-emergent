"""Auth (/link flow): start, complete, me."""
from __future__ import annotations

import random
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException

from core import (
    LinkStartRequest,
    LinkCompleteRequest,
    LINK_CODE_TTL_MIN,
    get_current_user,
    link_codes,
    make_jwt,
    new_id,
    now_utc,
    gen_link_code,
    serialize_user,
    users,
    _seed_holdings,
)

router = APIRouter(tags=["auth"])


@router.post("/auth/link/start")
async def auth_link_start(body: LinkStartRequest):
    """
    Simulates the in-game /link flow.
    In production the player runs /link on play.rootmc.net and the plugin
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


@router.post("/auth/link/complete")
async def auth_link_complete(body: LinkCompleteRequest):
    code = body.code.strip().upper()
    rec = await link_codes.find_one({"code": code, "consumed": False})
    if not rec:
        raise HTTPException(status_code=404, detail="code_not_found_or_used")
    if now_utc() - rec["created_at"] > timedelta(minutes=LINK_CODE_TTL_MIN):
        raise HTTPException(status_code=410, detail="code_expired")
    await link_codes.update_one(
        {"_id": rec["_id"]},
        {"$set": {"consumed": True, "consumed_at": now_utc()}},
    )

    username = rec["minecraft_username"]
    user = await users.find_one({"minecraft_username_lc": username.lower()})
    if not user:
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


@router.get("/auth/me")
async def auth_me(user=Depends(get_current_user)):
    return serialize_user(user)
