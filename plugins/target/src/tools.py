"""Task-shaped MCP tools for Target shopping workflows."""

import asyncio
import json
from decimal import Decimal
from typing import Any

from mcp.server import MCPServer

from . import shaping
from .client import TargetClient
from .errors import TargetError, guarded_tool

_client: TargetClient | None = None


def get_client() -> TargetClient:
    global _client
    if _client is None:
        _client = TargetClient()
    return _client


def reset_state() -> None:
    global _client
    _client = None


def fmt(value: object) -> str:
    return json.dumps(value, indent=2, default=str)


def _digits(value: str, label: str) -> str:
    clean = value.strip()
    if not clean.isdigit():
        raise TargetError(f"{label} must be numeric")
    return clean


async def _search(query: str, store_id: str, zip_code: str, limit: int) -> dict[str, Any]:
    if not query.strip():
        raise TargetError("query cannot be empty")
    if not 1 <= limit <= 24:
        raise TargetError("limit must be between 1 and 24")
    store = _digits(store_id, "store_id")
    result = await get_client().search_products(query.strip(), store, zip_code.strip(), limit)
    metadata = result.get("search_response", {}).get("metadata", {})
    products = [shaping.product(item) for item in result.get("products") or []]
    return {
        "store_id": store,
        "zip_code": zip_code,
        "query": query,
        "returned": len(products),
        "total": metadata.get("total_results", len(products)),
        "products": products,
        "price_context": (
            "Public Target.com price for the supplied pricing store. Promotions, "
            "fulfillment method, sign-in, and Target Circle eligibility may change it."
        ),
    }


def register_all(mcp: MCPServer) -> None:
    @mcp.tool()
    @guarded_tool
    async def search_products(query: str, store_id: str, zip_code: str = "", limit: int = 5) -> str:
        """Search Target products and public prices for a selected pricing store."""
        return fmt(await _search(query, store_id, zip_code, limit))

    @mcp.tool()
    @guarded_tool
    async def get_product(tcin: str, store_id: str, zip_code: str = "", state: str = "") -> str:
        """Get Target product detail and price by TCIN for one store context."""
        item = _digits(tcin, "tcin")
        store = _digits(store_id, "store_id")
        result = await get_client().get_product(item, store, zip_code.strip(), state.strip())
        return fmt(
            {
                "store_id": store,
                "product": shaping.product(result) if result else None,
                "price_context": "Public Target.com price for the supplied pricing store.",
            }
        )

    @mcp.tool()
    @guarded_tool
    async def find_stores_with_item(
        tcin: str,
        zip_code: str,
        radius_miles: int = 25,
        limit: int = 5,
        requested_quantity: int = 1,
    ) -> str:
        """Find nearby Target stores and pickup signals for a selected TCIN.

        Results are point-in-time signals, not reservations or shelf guarantees.
        """
        item = _digits(tcin, "tcin")
        if not zip_code.strip():
            raise TargetError("zip_code is required")
        if not 1 <= radius_miles <= 100:
            raise TargetError("radius_miles must be between 1 and 100")
        if not 1 <= limit <= 20:
            raise TargetError("limit must be between 1 and 20")
        if not 1 <= requested_quantity <= 99:
            raise TargetError("requested_quantity must be between 1 and 99")
        result = await get_client().find_stores_with_item(
            item, zip_code.strip(), radius_miles, limit, requested_quantity
        )
        locations = [shaping.store_availability(row) for row in result.get("locations") or []]
        return fmt(
            {
                "tcin": item,
                "zip_code": zip_code,
                "returned": len(locations),
                "stores": locations,
                "availability_note": (
                    "Point-in-time Target website signal. Confirm before travel; this does not reserve stock."
                ),
            }
        )

    @mcp.tool()
    @guarded_tool
    async def price_shopping_list(
        items: list[str],
        store_id: str,
        zip_code: str = "",
        alternatives_per_item: int = 3,
    ) -> str:
        """Price a draft Target list with likely matches and alternatives."""
        clean = [item.strip() for item in items if item.strip()]
        if not clean:
            raise TargetError("items must contain at least one non-empty product phrase")
        if len(clean) > 20:
            raise TargetError("price at most 20 item phrases per call")
        if not 1 <= alternatives_per_item <= 5:
            raise TargetError("alternatives_per_item must be between 1 and 5")
        store = _digits(store_id, "store_id")
        payloads = await asyncio.gather(*(_search(item, store, zip_code, alternatives_per_item) for item in clean))
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
                "zip_code": zip_code,
                "items": rows,
                "estimated_total": f"{total:.2f}",
                "priced_items": priced,
                "requested_items": len(clean),
                "estimate_note": (
                    "Assumes one unit of each first match at the public Target.com price. "
                    "Confirm quantities, promotions, and availability."
                ),
            }
        )
