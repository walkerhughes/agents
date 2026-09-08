"""Async client for Safeway's public browser-facing contracts."""

import asyncio
import os
import uuid
from typing import Any

import httpx

from .errors import SafewayError

BASE = "https://www.safeway.com/abs/pub/xapi"
SEARCH_URL = os.getenv("SAFEWAY_SEARCH_URL", f"{BASE}/search/substitute")
STORES_URL = os.getenv("SAFEWAY_STORES_URL", f"{BASE}/storeresolver/v2/all")
ADDRESS_URL = os.getenv("SAFEWAY_ADDRESS_URL", f"{BASE}/storeresolver/storeaddress")
SEARCH_KEY = os.getenv("SAFEWAY_SEARCH_KEY", "e914eec9448c4d5eb672debf5011cf8f")
STORE_KEY = os.getenv("SAFEWAY_STORE_KEY", "7bad9afbb87043b28519c4443106db06")


class SafewayClient:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.http = httpx.AsyncClient(
            timeout=25,
            transport=transport,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 AppleWebKit/537.36 Chrome/144 Safari/537.36",
                "Referer": "https://www.safeway.com/shop/search-results.html",
                "x-swy-banner": "safeway",
                "x-swy-client-id": "web-portal",
            },
        )

    async def close(self) -> None:
        await self.http.aclose()

    async def _get(self, url: str, params: dict[str, Any], key: str) -> dict[str, Any]:
        response = await self.http.get(url, params=params, headers={"Ocp-Apim-Subscription-Key": key})
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError as exc:
            raise SafewayError("Safeway returned a non-JSON response") from exc
        if not isinstance(payload, dict):
            raise SafewayError("Safeway returned an unexpected response shape")
        return payload

    async def find_stores(self, zip_code: str, limit: int) -> list[dict[str, Any]]:
        payload = await self._get(STORES_URL, {"zipcode": zip_code, "banner": "safeway"}, STORE_KEY)
        group = payload.get("pickup") or payload.get("instore") or {}
        stores = group.get("stores") if isinstance(group, dict) else None
        if not isinstance(stores, list):
            raise SafewayError("Safeway store resolver did not include a store list")
        selected = stores[:limit]
        addresses = await asyncio.gather(
            *(self.store_address(str(store.get("locationId") or "")) for store in selected)
        )
        return [{"resolver": store, "address": address} for store, address in zip(selected, addresses, strict=True)]

    async def store_address(self, store_id: str) -> dict[str, Any]:
        payload = await self._get(ADDRESS_URL, {"storeid": store_id, "banner": "safeway"}, STORE_KEY)
        model = payload.get("storeAddressModel")
        if not isinstance(model, dict):
            raise SafewayError("Safeway store response did not include an address")
        return model

    async def search_products(self, query: str, store_id: str, channel: str, rows: int) -> dict[str, Any]:
        payload = await self._get(
            SEARCH_URL,
            {
                "request-id": str(uuid.uuid4()),
                "url": "https://www.safeway.com",
                "pageurl": "https://www.safeway.com",
                "pagename": "search",
                "rows": rows,
                "start": 0,
                "search-type": "keyword",
                "storeid": store_id,
                "featured": "true",
                "search-uid": "",
                "q": query,
                "channel": channel,
                "banner": "safeway",
            },
            SEARCH_KEY,
        )
        response = payload.get("response")
        if not isinstance(response, dict) or not isinstance(response.get("docs"), list):
            raise SafewayError("Safeway search did not include a product list")
        return response
