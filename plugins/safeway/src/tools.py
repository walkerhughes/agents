"""Task-shaped MCP tools for Safeway grocery workflows."""

import asyncio
import json
from decimal import Decimal
from typing import Any

from mcp.server import MCPServer

from . import shaping
from .client import SafewayClient
from .errors import SafewayError, guarded_tool

_client: SafewayClient | None = None


def get_client() -> SafewayClient:
    global _client
    if _client is None:
        _client = SafewayClient()
    return _client


def reset_state() -> None:
    global _client
    _client = None


def fmt(value: object) -> str:
    return json.dumps(value, indent=2, default=str)


def _digits(value: str, label: str) -> str:
    clean = value.strip()
    if not clean.isdigit():
        raise SafewayError(f"{label} must be numeric")
    return clean


async def _search(query: str, store_id: str, channel: str, limit: int) -> dict[str, Any]:
    if not query.strip():
        raise SafewayError("query cannot be empty")
    if channel not in {"pickup", "delivery", "instore"}:
        raise SafewayError("channel must be pickup, delivery, or instore")
    if not 1 <= limit <= 20:
        raise SafewayError("limit must be between 1 and 20")
    store = _digits(store_id, "store_id")
    response = await get_client().search_products(query.strip(), store, channel, limit)
    products = [shaping.product(item) for item in response.get("docs") or []]
    return {
        "store_id": store,
        "channel": channel,
        "query": query,
        "returned": len(products),
        "total": response.get("numFound", len(products)),
        "products": products,
        "price_context": (
            "Safeway's current public price for this store and channel. Compare base price and "
            "promotion fields; loyalty or digital-offer eligibility is not guaranteed."
        ),
        "inventory_note": "Point-in-time website signal, not a shelf guarantee or reservation.",
    }


def register_all(mcp: MCPServer) -> None:
    @mcp.tool()
    @guarded_tool
    async def find_stores(zip_code: str, limit: int = 5) -> str:
        """Find pickup-capable Safeway stores for a US ZIP code."""
        if not zip_code.strip() or not zip_code.strip().isdigit():
            raise SafewayError("zip_code must be numeric")
        if not 1 <= limit <= 10:
            raise SafewayError("limit must be between 1 and 10")
        results = await get_client().find_stores(zip_code.strip(), limit)
        return fmt(
            {
                "zip_code": zip_code,
                "returned": len(results),
                "stores": [shaping.store(item) for item in results],
            }
        )

    @mcp.tool()
    @guarded_tool
    async def search_products(query: str, store_id: str, channel: str = "pickup", limit: int = 5) -> str:
        """Search Safeway products with prices and inventory for one store and channel."""
        return fmt(await _search(query, store_id, channel, limit))

    @mcp.tool()
    @guarded_tool
    async def get_product(product_id: str, store_id: str, channel: str = "pickup") -> str:
        """Refresh a known Safeway product ID in one store and channel context."""
        item_id = _digits(product_id, "product_id")
        result = await _search(item_id, store_id, channel, 5)
        product = next((item for item in result["products"] if item["product_id"] == item_id), None)
        return fmt({"store_id": result["store_id"], "channel": channel, "product": product})

    @mcp.tool()
    @guarded_tool
    async def price_shopping_list(
        items: list[str],
        store_id: str,
        channel: str = "pickup",
        alternatives_per_item: int = 3,
    ) -> str:
        """Price a draft Safeway list using likely matches and alternatives."""
        clean = [item.strip() for item in items if item.strip()]
        if not clean:
            raise SafewayError("items must contain at least one non-empty product phrase")
        if len(clean) > 20:
            raise SafewayError("price at most 20 item phrases per call")
        if not 1 <= alternatives_per_item <= 5:
            raise SafewayError("alternatives_per_item must be between 1 and 5")
        store = _digits(store_id, "store_id")
        payloads = await asyncio.gather(*(_search(item, store, channel, alternatives_per_item) for item in clean))
        rows = []
        total = Decimal("0")
        priced = 0
        for requested, payload in zip(clean, payloads, strict=True):
            matches = payload["products"]
            selected = matches[0] if matches else None
            price = shaping.decimal_price(selected)
            if price is not None:
                total += price
                priced += 1
            rows.append({"requested": requested, "selected": selected, "alternatives": matches[1:]})
        return fmt(
            {
                "store_id": store,
                "channel": channel,
                "items": rows,
                "estimated_total": f"{total:.2f}",
                "priced_items": priced,
                "requested_items": len(clean),
                "estimate_note": (
                    "Assumes one unit of each first match at Safeway's current public price. "
                    "Confirm offer eligibility, quantities, and inventory."
                ),
            }
        )
