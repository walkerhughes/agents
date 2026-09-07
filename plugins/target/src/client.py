"""Async client for Target's public Redsky website contracts."""

import os
from typing import Any

import httpx

from .errors import TargetError

BASE = "https://redsky.target.com/redsky_aggregations/v1/web"
SEARCH_URL = os.getenv("TARGET_SEARCH_URL", f"{BASE}/plp_search_v2")
PRODUCT_URL = os.getenv("TARGET_PRODUCT_URL", f"{BASE}/pdp_client_v1")
AVAILABILITY_URL = os.getenv("TARGET_AVAILABILITY_URL", f"{BASE}/fiats_v1")
REDSKY_KEY = os.getenv("TARGET_REDSKY_KEY", "9f36aeafbe60771e321a7cc95a78140772ab3e96")
VISITOR_ID = "0000000000000000000000000000000000"


class TargetClient:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.http = httpx.AsyncClient(
            timeout=20,
            transport=transport,
            headers={
                "Accept": "application/json",
                "Origin": "https://www.target.com",
                "Referer": "https://www.target.com/",
                "User-Agent": "Mozilla/5.0 AppleWebKit/537.36 Chrome/144 Safari/537.36",
            },
        )

    async def close(self) -> None:
        await self.http.aclose()

    async def _get(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        response = await self.http.get(url, params=params)
        if response.status_code == 403:
            raise TargetError(
                "Redsky presented an automated-traffic challenge on this network. "
                "Retry from a normal residential connection; no product data was returned."
            )
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise TargetError("Target returned a non-JSON response") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            raise TargetError("Target returned an unexpected response shape")
        return payload["data"]

    async def search_products(self, query: str, store_id: str, zip_code: str, limit: int) -> dict[str, Any]:
        params: dict[str, Any] = {
            "key": REDSKY_KEY,
            "channel": "WEB",
            "keyword": query,
            "page": f"/s/{query}",
            "visitor_id": VISITOR_ID,
            "pricing_store_id": store_id,
            "store_ids": store_id,
            "default_purchasability_filter": "true",
            "include_sponsored": "false",
            "platform": "desktop",
            "count": limit,
            "offset": 0,
        }
        if zip_code:
            params["zip"] = zip_code
        data = await self._get(SEARCH_URL, params)
        search = data.get("search")
        if not isinstance(search, dict) or not isinstance(search.get("products"), list):
            raise TargetError("Target search did not include a product list")
        return search

    async def get_product(self, tcin: str, store_id: str, zip_code: str = "", state: str = "") -> dict[str, Any] | None:
        params = {
            "key": REDSKY_KEY,
            "channel": "WEB",
            "tcin": tcin,
            "store_id": store_id,
            "pricing_store_id": store_id,
            "has_pricing_store_id": "true",
            "visitor_id": VISITOR_ID,
            "page": f"/p/A-{tcin}",
        }
        if zip_code:
            params["zip"] = zip_code
        if state:
            params["state"] = state.upper()
        data = await self._get(PRODUCT_URL, params)
        product = data.get("product")
        return product if isinstance(product, dict) else None

    async def find_stores_with_item(
        self, tcin: str, zip_code: str, radius: int, limit: int, requested_quantity: int
    ) -> dict[str, Any]:
        data = await self._get(
            AVAILABILITY_URL,
            {
                "key": REDSKY_KEY,
                "channel": "WEB",
                "tcin": tcin,
                "nearby": zip_code,
                "radius": radius,
                "limit": limit,
                "requested_quantity": requested_quantity,
                "include_only_available_stores": "false",
                "visitor_id": VISITOR_ID,
            },
        )
        fiats = data.get("fulfillment_fiats")
        if not isinstance(fiats, dict) or not isinstance(fiats.get("locations"), list):
            raise TargetError("Target availability did not include store locations")
        return fiats
