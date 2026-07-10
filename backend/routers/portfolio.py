"""Player portfolio: wallet, inventory, holdings, net-worth curve."""
from __future__ import annotations

import random
from datetime import timedelta

from fastapi import APIRouter, Depends

from core import get_current_user, iso, market, now_utc

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio/me")
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

    # tiny synthetic 30d net-worth curve — deterministic per-user
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
