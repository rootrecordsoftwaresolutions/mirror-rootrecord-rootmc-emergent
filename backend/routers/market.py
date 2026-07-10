"""Player-shop stock market: /market/items, /market/item/{ticker}."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from core import iso, market

router = APIRouter(tags=["market"])


@router.get("/market/items")
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


@router.get("/market/item/{ticker}")
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
