"""Public endpoints: /health, /server/status, /economy/overview,
/leaderboards, /daily-report/latest."""
from __future__ import annotations

import random

from fastapi import APIRouter, HTTPException

from core import iso, kv, now_utc

router = APIRouter(tags=["public"])


@router.get("/health")
async def health():
    return {"status": "ok", "time": iso(now_utc())}


@router.get("/server/status")
async def server_status():
    doc = await kv.find_one({"_id": "server_status"})
    doc["updated_at"] = iso(doc["updated_at"])
    doc.pop("_id", None)
    return doc


@router.get("/economy/overview")
async def economy_overview():
    doc = await kv.find_one({"_id": "economy"})
    doc["updated_at"] = iso(doc["updated_at"])
    doc.pop("_id", None)
    # small live jitter so numbers feel alive
    doc["treasury_reserve"] = round(doc["treasury_reserve"] + random.uniform(-40, 60), 2)
    return doc


@router.get("/leaderboards")
async def leaderboards(category: str = "net_worth"):
    doc = await kv.find_one({"_id": "leaderboards"})
    if category not in doc:
        raise HTTPException(404, "unknown_category")
    return {"category": category, "entries": doc[category][:20]}


@router.get("/daily-report/latest")
async def daily_report_latest():
    doc = await kv.find_one({"_id": "daily_report"})
    doc.pop("_id", None)
    return doc
