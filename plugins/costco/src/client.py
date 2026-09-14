"""Async client for Costco's public website request surface."""

import asyncio
import json
import os
from typing import Any

import httpx

from .errors import CostcoError

SEARCH_URL = "https://gdx-api.costco.com/catalog/search/api/v1/search"
PRODUCT_URL = "https://ecom-api.costco.com/ebusiness/product/v1/products/graphql"
WAREHOUSE_URL = "https://ecom-api.costco.com/core/warehouse-locator/v1/salesLocations.json"
GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

SEARCH_CLIENT_ID = "168287ea-1201-45f6-9b45-5bbea49f8ee7"
PRODUCT_CLIENT_ID = "4900eb1f-0c10-4bd9-99c3-c59e6c1ecebf"
WAREHOUSE_CLIENT_ID = "7c71124c-7bf1-44db-bc9d-498584cd66e5"

_RETRY_STATUSES = {429, 500, 502, 503, 504}
_BACKOFFS = (0.4, 1.0, 2.0)

PRODUCT_FIELDS = """
itemNumber
itemId
published
buyable
programTypes
priceData { price listPrice }
attributes { key value type }
description {
  shortDescription
  longDescription
  marketingStatement
  promotionalStatement
}
additionalFieldData {
  rating
  numberOfRating
  membershipReqd
  maxItemOrderQty
}
fieldData { mfPartNumber mfName }
"""


def product_query(item_numbers: list[str], warehouse_number: str) -> str:
    quoted = ", ".join(json.dumps(item) for item in item_numbers)
    return f'''query {{
  products(
    itemNumbers: [{quoted}],
    clientId: "{PRODUCT_CLIENT_ID}",
    locale: "en-us",
    warehouseNumber: "{warehouse_number}"
  ) {{
    catalogData {{ {PRODUCT_FIELDS} }}
  }}
}}'''


class CostcoClient:
    """Small read-only client with injectable transport for deterministic tests."""

    def __init__(
        self,
        *,
        search_url: str | None = None,
        product_url: str | None = None,
        warehouse_url: str | None = None,
        geocode_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.search_url = search_url or os.environ.get("COSTCO_SEARCH_URL") or SEARCH_URL
        self.product_url = product_url or os.environ.get("COSTCO_PRODUCT_URL") or PRODUCT_URL
        self.warehouse_url = warehouse_url or os.environ.get("COSTCO_WAREHOUSE_URL") or WAREHOUSE_URL
        self.geocode_url = geocode_url or os.environ.get("COSTCO_GEOCODE_URL") or GEOCODE_URL
        self._transport = transport
        self._http: httpx.AsyncClient | None = None

    async def _http_client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Origin": "https://www.costco.com",
                    "Referer": "https://www.costco.com/",
                    "User-Agent": "costco-mcp/0.1 (read-only catalog client)",
                },
                timeout=30.0,
                follow_redirects=True,
                transport=self._transport,
            )
        return self._http

    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        http = await self._http_client()
        response: httpx.Response | None = None
        for attempt in range(len(_BACKOFFS) + 1):
            response = await http.request(method, url, **kwargs)
            if response.status_code not in _RETRY_STATUSES or attempt == len(_BACKOFFS):
                break
            await asyncio.sleep(_BACKOFFS[attempt])
        assert response is not None
        response.raise_for_status()
        try:
            return response.json()
        except ValueError as exc:
            raise CostcoError("the site returned a response that was not JSON") from exc

    async def geocode(self, location: str) -> tuple[float, float]:
        data = await self._request(
            "GET",
            self.geocode_url,
            params={"q": location, "format": "jsonv2", "limit": 1, "countrycodes": "us"},
            headers={"Origin": "", "Referer": ""},
        )
        if not isinstance(data, list) or not data:
            raise CostcoError(f"no US map result found for {location!r}")
        try:
            return float(data[0]["lat"]), float(data[0]["lon"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CostcoError("the map service returned an unexpected location result") from exc

    async def find_warehouses(self, location: str, *, limit: int = 5) -> dict[str, Any]:
        latitude, longitude = await self.geocode(location)
        data = await self._request(
            "GET",
            self.warehouse_url,
            params={"latitude": latitude, "longitude": longitude, "limit": limit},
            headers={"client-identifier": WAREHOUSE_CLIENT_ID},
        )
        if not isinstance(data, dict) or not isinstance(data.get("salesLocations"), list):
            raise CostcoError("the warehouse locator omitted its salesLocations result")
        return data

    async def search_catalog(
        self,
        query: str,
        warehouse_number: str,
        postal_code: str,
        *,
        state: str = "",
        limit: int = 5,
    ) -> dict[str, Any]:
        body = {
            "visitorId": "0",
            "query": query,
            "pageSize": limit,
            "offset": 0,
            "orderBy": None,
            "searchMode": "page",
            "personalizationEnabled": False,
            "warehouseId": f"{warehouse_number}-wh",
            "shipToPostal": postal_code,
            "shipToState": state,
            "deliveryLocations": [f"{warehouse_number}-wh"],
            "filterBy": [],
            "pageCategories": [],
            "userInfo": {"userId": "0"},
        }
        data = await self._request(
            "POST",
            self.search_url,
            json=body,
            headers={
                "client-identifier": SEARCH_CLIENT_ID,
                "client_id": "USBC",
                "locale": "en-US",
                "searchresultprovider": "GRS",
            },
        )
        result = data.get("searchResult") if isinstance(data, dict) else None
        if not isinstance(result, dict) or not isinstance(result.get("results"), list):
            raise CostcoError("the catalog search omitted its searchResult")
        return result

    async def get_products(self, item_numbers: list[str], warehouse_number: str) -> list[dict[str, Any]]:
        data = await self._request(
            "POST",
            self.product_url,
            json={"query": product_query(item_numbers, warehouse_number)},
            headers={
                "client-identifier": PRODUCT_CLIENT_ID,
                "costco.env": "ecom",
                "costco.service": "restProduct",
            },
        )
        if isinstance(data, dict) and data.get("errors"):
            errors = data["errors"]
            message = errors[0].get("message") if isinstance(errors, list) and errors else None
            raise CostcoError(str(message or "the product API rejected the query"))
        products = ((data.get("data") or {}).get("products") if isinstance(data, dict) else None) or {}
        catalog = products.get("catalogData")
        if not isinstance(catalog, list):
            raise CostcoError("the product API omitted its catalogData result")
        return catalog

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()
