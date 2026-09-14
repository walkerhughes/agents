"""Task-shaped MCP tools over Trader Joe's public website data."""

import asyncio
import json
from decimal import Decimal
from typing import Any

from mcp.server import MCPServer

from . import shaping
from .client import TraderJoesClient
from .errors import TraderJoesError, guarded_tool

_client: TraderJoesClient | None = None


def get_client() -> TraderJoesClient:
    global _client
    if _client is None:
        _client = TraderJoesClient()
    return _client


def reset_state() -> None:
    global _client
    _client = None


def fmt(value: object) -> str:
    return json.dumps(value, indent=2, default=str)


def _store_code(value: str) -> str:
    code = value.strip()
    if not code.isdigit():
        raise TraderJoesError("store_code must be the numeric code returned by find_stores")
    return code


async def _search(query: str, store_code: str, limit: int, page: int) -> dict[str, Any]:
    if not query.strip():
        raise TraderJoesError("query cannot be empty")
    if not 1 <= limit <= 50:
        raise TraderJoesError("limit must be between 1 and 50")
    if page < 1:
        raise TraderJoesError("page must be at least 1")
    payload = await get_client().search_products(query.strip(), _store_code(store_code), page=page, page_size=limit)
    page_info = payload.get("page_info") or {}
    return {
        "store_code": store_code,
        "query": query,
        "returned": len(payload.get("items") or []),
        "total": payload.get("total_count"),
        "page": page_info.get("current_page", page),
        "total_pages": page_info.get("total_pages"),
        "products": [shaping.product(item) for item in payload.get("items") or []],
        "catalog_note": (
            "Trader Joe's says its website does not represent every product. "
            "Availability is a catalog signal, not real-time shelf inventory."
        ),
    }


def register_all(mcp: MCPServer) -> None:
    @mcp.tool()
    @guarded_tool
    async def find_stores(
        location: str,
        limit: int = 5,
        beer: bool = False,
        wine: bool = False,
        liquor: bool = False,
    ) -> str:
        """Find nearby Trader Joe's stores and the store codes needed by product tools.

        location accepts a US ZIP code, city and state, or street address. Ask for a
        city or ZIP when the user has not supplied one; do not guess a precise location.
        Results are ordered nearest first and include distance, hours, phone, alcohol
        selection, and the official store page. Use the chosen store_code for prices.
        """
        if not location.strip():
            raise TraderJoesError("location cannot be empty; provide a US ZIP code, city/state, or address")
        if not 1 <= limit <= 20:
            raise TraderJoesError("limit must be between 1 and 20")
        payload = await get_client().find_stores(location.strip(), limit=limit, beer=beer, wine=wine, liquor=liquor)
        stores = [shaping.store(item) for item in payload.get("collection") or []]
        return fmt({"query": location, "returned": len(stores), "stores": stores})

    @mcp.tool()
    @guarded_tool
    async def search_products(query: str, store_code: str, limit: int = 10, page: int = 1) -> str:
        """Search products and current published prices for one Trader Joe's store.

        Find a store first unless its numeric code is already known. Search with food
        names, dietary terms, or meal concepts. Results can include descriptions,
        categories, package size, price, and catalog availability. They do not prove
        real-time shelf stock, and the website does not list every in-store product.
        """
        return fmt(await _search(query, store_code, limit, page))

    @mcp.tool()
    @guarded_tool
    async def get_product(sku: str, store_code: str) -> str:
        """Get one store-scoped product by the SKU returned from search_products."""
        clean_sku = sku.strip()
        if not clean_sku.isdigit() or len(clean_sku) > 6:
            raise TraderJoesError("sku must contain at most six digits")
        item = await get_client().get_product(clean_sku, _store_code(store_code))
        if item is None:
            return fmt(
                {
                    "store_code": store_code,
                    "sku": clean_sku.zfill(6),
                    "product": None,
                    "note": "No published catalog result for this SKU at this store.",
                }
            )
        return fmt({"store_code": store_code, "product": shaping.product(item)})

    @mcp.tool()
    @guarded_tool
    async def price_shopping_list(items: list[str], store_code: str, alternatives_per_item: int = 3) -> str:
        """Price a draft shopping list with matching products and useful alternatives.

        Pass ingredient or product phrases, not quantities, for example ["chicken
        thighs", "brown rice", "broccoli"]. The first result is the likely match, not
        an automatic purchase decision. Review alternatives when names are ambiguous.
        Totals use one package of each selected first result and exclude missing prices.
        """
        clean = [item.strip() for item in items if item.strip()]
        if not clean:
            raise TraderJoesError("items must contain at least one non-empty product phrase")
        if len(clean) > 30:
            raise TraderJoesError("price at most 30 item phrases per call")
        if not 1 <= alternatives_per_item <= 5:
            raise TraderJoesError("alternatives_per_item must be between 1 and 5")
        code = _store_code(store_code)
        payloads = await asyncio.gather(
            *(get_client().search_products(item, code, page_size=alternatives_per_item) for item in clean)
        )
        rows = []
        total = Decimal("0")
        priced = 0
        for requested, payload in zip(clean, payloads, strict=True):
            matches = [shaping.product(item) for item in payload.get("items") or []]
            selected = matches[0] if matches else None
            price = shaping.decimal_price(selected) if selected else None
            if price is not None:
                total += price
                priced += 1
            rows.append({"requested": requested, "selected": selected, "alternatives": matches[1:]})
        return fmt(
            {
                "store_code": code,
                "items": rows,
                "estimated_total": f"{total:.2f}",
                "priced_items": priced,
                "requested_items": len(clean),
                "estimate_note": (
                    "Assumes one package of each first match. Confirm ambiguous matches, "
                    "quantities, price, and shelf stock in store."
                ),
            }
        )
