"""Task-shaped MCP tools over Costco's public website data."""

import asyncio
import json
from decimal import Decimal
from typing import Any

from mcp.server import MCPServer

from . import shaping
from .client import CostcoClient
from .errors import CostcoError, guarded_tool

_client: CostcoClient | None = None


def get_client() -> CostcoClient:
    global _client
    if _client is None:
        _client = CostcoClient()
    return _client


def reset_state() -> None:
    global _client
    _client = None


def fmt(value: object) -> str:
    return json.dumps(value, indent=2, default=str)


def _number(value: str, label: str) -> str:
    clean = value.strip()
    if not clean.isdigit():
        raise CostcoError(f"{label} must be the numeric value returned by the Costco tools")
    return clean


def _search_documents(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [shaping.search_document(item) for item in result.get("results") or []]


async def _search(
    query: str,
    warehouse_number: str,
    postal_code: str,
    state: str,
    limit: int,
) -> dict[str, Any]:
    if not query.strip():
        raise CostcoError("query cannot be empty")
    if not postal_code.strip():
        raise CostcoError("postal_code is required; use the value returned by find_warehouses")
    if not 1 <= limit <= 10:
        raise CostcoError("limit must be between 1 and 10")
    number = _number(warehouse_number, "warehouse_number")
    result = await get_client().search_catalog(
        query.strip(), number, postal_code.strip(), state=state.strip().upper(), limit=limit
    )
    documents = _search_documents(result)
    item_numbers = [item["item_number"] for item in documents if item["item_number"]]
    details = await get_client().get_products(item_numbers, number) if item_numbers else []
    detail_by_number = {str(item.get("itemNumber")): item for item in details}
    products = [shaping.product(detail_by_number.get(document["item_number"], {}), document) for document in documents]
    return {
        "warehouse_number": number,
        "postal_code": postal_code,
        "query": query,
        "returned": len(products),
        "total": result.get("totalCount", len(products)),
        "products": products,
        "price_context": (
            "Published Costco.com price for this warehouse context. It may differ from "
            "walk-in, signed-in member, and Same-Day prices."
        ),
        "availability_note": "Catalog program types are not real-time shelf inventory.",
    }


def register_all(mcp: MCPServer) -> None:
    @mcp.tool()
    @guarded_tool
    async def find_warehouses(location: str, limit: int = 5) -> str:
        """Find nearby US Costco warehouses and location values used by product tools.

        location accepts a ZIP code, city and state, or street address. Ask for an
        approximate location when the user has not supplied one; never guess a precise
        location. Results include warehouse_number, postal_code, state, distance, and
        services. Pass the selected values to product and shopping-list tools.
        """
        if not location.strip():
            raise CostcoError("location cannot be empty; provide a US ZIP code, city/state, or address")
        if not 1 <= limit <= 20:
            raise CostcoError("limit must be between 1 and 20")
        payload = await get_client().find_warehouses(location.strip(), limit=limit)
        warehouses = [shaping.warehouse(item) for item in payload.get("salesLocations") or []]
        return fmt({"query": location, "returned": len(warehouses), "warehouses": warehouses})

    @mcp.tool()
    @guarded_tool
    async def search_products(
        query: str,
        warehouse_number: str,
        postal_code: str,
        state: str = "",
        limit: int = 5,
    ) -> str:
        """Search Costco products and published prices for one warehouse context.

        Find a warehouse first unless its number and postal code are already known.
        Results include public Costco.com pricing and InWarehouse catalog signals.
        Neither is a guarantee of the walk-in price or current shelf inventory.
        """
        return fmt(await _search(query, warehouse_number, postal_code, state, limit))

    @mcp.tool()
    @guarded_tool
    async def get_product(item_number: str, warehouse_number: str) -> str:
        """Get one warehouse-context product by an item number returned from search."""
        item = _number(item_number, "item_number")
        warehouse = _number(warehouse_number, "warehouse_number")
        products = await get_client().get_products([item], warehouse)
        if not products:
            return fmt({"warehouse_number": warehouse, "item_number": item, "product": None})
        return fmt(
            {
                "warehouse_number": warehouse,
                "product": shaping.product(products[0]),
                "price_context": (
                    "Published Costco.com price for this warehouse context, not a guaranteed walk-in warehouse price."
                ),
            }
        )

    @mcp.tool()
    @guarded_tool
    async def price_shopping_list(
        items: list[str],
        warehouse_number: str,
        postal_code: str,
        state: str = "",
        alternatives_per_item: int = 3,
    ) -> str:
        """Price a draft Costco list with likely matches and alternatives.

        Pass product phrases rather than quantities. The estimate assumes one Costco
        package of each first match. Review package sizes and alternatives because
        bulk quantities can materially change a menu or budget.
        """
        clean = [item.strip() for item in items if item.strip()]
        if not clean:
            raise CostcoError("items must contain at least one non-empty product phrase")
        if len(clean) > 20:
            raise CostcoError("price at most 20 item phrases per call")
        if not 1 <= alternatives_per_item <= 5:
            raise CostcoError("alternatives_per_item must be between 1 and 5")
        warehouse = _number(warehouse_number, "warehouse_number")
        payloads = await asyncio.gather(
            *(_search(item, warehouse, postal_code, state, alternatives_per_item) for item in clean)
        )
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
                "warehouse_number": warehouse,
                "postal_code": postal_code,
                "items": rows,
                "estimated_total": f"{total:.2f}",
                "priced_items": priced,
                "requested_items": len(clean),
                "estimate_note": (
                    "Assumes one package of each first match at the public Costco.com "
                    "price. Confirm package quantities, membership pricing, and shelf "
                    "availability."
                ),
            }
        )
