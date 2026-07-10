"""Daily check-in + vote-site rewards.

NOTE for prod: when the Cloudflare Worker exposes /api/rootmc/app/checkin/*
and /api/rootmc/app/vote/*, the frontend flips REACT_APP_LIVE_REWARDS=true
and stops calling these routes. Grants there must go through
rootmc_gold_transfers with sources app_checkin / app_vote — never via
Mongo $inc on wallet_gold like this mock router does.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument

from core import (
    CHECKIN_COOLDOWN_H,
    VOTE_COOLDOWN_H,
    VOTE_SITES,
    VoteClaimBody,
    checkins,
    get_current_user,
    iso,
    kv,
    new_id,
    now_utc,
    users,
    votes,
)

router = APIRouter(tags=["rewards"])


def _checkin_reward(streak: int) -> Dict[str, Any]:
    """Tiered rewards, treasury-backed in prod."""
    tiers = [10, 15, 20, 25, 35, 50, 100]
    idx = min(streak, 6)
    return {"gold": tiers[idx], "tier": idx + 1, "tier_label": f"Day {idx + 1}"}


@router.get("/checkin/status")
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


@router.post("/checkin/claim")
async def checkin_claim(user=Depends(get_current_user)):
    last = user.get("last_checkin_at")
    streak = user.get("streak_count", 0)
    if last:
        elapsed = now_utc() - last
        if elapsed < timedelta(hours=CHECKIN_COOLDOWN_H):
            raise HTTPException(
                429,
                {
                    "error": "cooldown",
                    "seconds": int((timedelta(hours=CHECKIN_COOLDOWN_H) - elapsed).total_seconds()),
                },
            )
        if elapsed > timedelta(hours=48):
            streak = 0
    new_streak = streak + 1 if streak < 7 else 1  # weekly loop
    reward = _checkin_reward(streak)
    updated = await users.find_one_and_update(
        {"_id": user["_id"]},
        {
            "$set": {"streak_count": new_streak, "last_checkin_at": now_utc()},
            "$inc": {"wallet_gold": reward["gold"]},
        },
        return_document=ReturnDocument.AFTER,
    )
    await checkins.insert_one({
        "_id": new_id(),
        "user_id": user["_id"],
        "claimed_at": now_utc(),
        "reward_gold": reward["gold"],
        "streak_after": new_streak,
    })
    await kv.update_one(
        {"_id": "economy"},
        {"$inc": {"treasury_reserve": -reward["gold"], "24h_flows.out": reward["gold"]}},
    )
    return {
        "success": True,
        "reward": reward,
        "new_streak": new_streak,
        "new_wallet_balance": round(updated.get("wallet_gold", 0), 2),
    }


@router.get("/vote/sites")
async def vote_sites_list(user=Depends(get_current_user)):
    recent = await votes.find({"user_id": user["_id"]}).to_list(200)
    last_by_site: Dict[str, Any] = {}
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
        out.append({**s, "can_claim": can_claim, "seconds_until": seconds_until,
                    "last_claimed_at": iso(last) if last else None})
    total_earned_today = sum(
        v["reward_gold"] for v in recent
        if v["claimed_at"] > now_utc() - timedelta(hours=24)
    )
    return {"sites": out, "earned_today": round(total_earned_today, 2)}


@router.post("/vote/claim")
async def vote_claim(body: VoteClaimBody, user=Depends(get_current_user)):
    site = next((s for s in VOTE_SITES if s["id"] == body.site_id), None)
    if not site:
        raise HTTPException(404, "unknown_site")
    last = await votes.find_one(
        {"user_id": user["_id"], "site_id": site["id"]},
        sort=[("claimed_at", -1)],
    )
    if last:
        elapsed = now_utc() - last["claimed_at"]
        if elapsed < timedelta(hours=VOTE_COOLDOWN_H):
            raise HTTPException(
                429,
                {"error": "cooldown", "seconds": int((timedelta(hours=VOTE_COOLDOWN_H) - elapsed).total_seconds())},
            )
    reward_g = site["reward"]
    await votes.insert_one({
        "_id": new_id(),
        "user_id": user["_id"],
        "site_id": site["id"],
        "claimed_at": now_utc(),
        "reward_gold": reward_g,
    })
    updated = await users.find_one_and_update(
        {"_id": user["_id"]},
        {"$inc": {"wallet_gold": reward_g}},
        return_document=ReturnDocument.AFTER,
    )
    await kv.update_one(
        {"_id": "economy"},
        {"$inc": {"treasury_reserve": -reward_g, "24h_flows.out": reward_g}},
    )
    return {
        "success": True,
        "reward_gold": reward_g,
        "site": site["name"],
        "new_wallet_balance": round(updated.get("wallet_gold", 0), 2),
    }
