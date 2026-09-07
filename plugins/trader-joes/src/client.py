"""Async clients for Trader Joe's public product and store-locator endpoints."""

import asyncio
import os
import time
from typing import Any

import httpx

from .errors import TraderJoesError

PRODUCT_URL = "https://www.traderjoes.com/api/graphql"
LOCATOR_URL = "https://hosted.where2getit.com/traderjoes/rest/locatorsearch"
LOCATOR_APP_KEY = "8559C922-54E3-11E7-8321-40B4F48ECC77"

_RETRY_STATUSES = {429, 500, 502, 503, 504}
_BACKOFFS = (0.4, 1.0, 2.0)

PRODUCT_FIELDS = """
sku
item_title
item_description
item_characteristics
primary_image
url_key
retail_price
sales_size
sales_uom_description
availability
new_product
promotion
country_of_origin
category_hierarchy { id name }
price_range {
  minimum_price { final_price { currency value } }
}
"""

SEARCH_QUERY = f"""
query SearchProducts(
  $search: String,
  $pageSize: Int,
  $currentPage: Int,
  $storeCode: String,
  $published: String = "1"
) {{
  products(
    search: $search,
    filter: {{store_code: {{eq: $storeCode}}, published: {{eq: $published}}}},
    pageSize: $pageSize,
    currentPage: $currentPage
  ) {{
    items {{ {PRODUCT_FIELDS} }}
    total_count
    page_info {{ current_page page_size total_pages }}
  }}
}}
"""

PRODUCT_QUERY = f"""
query ProductBySku($sku: String!, $storeCode: String!, $published: String = "1") {{
  products(
    filter: {{
      sku: {{eq: $sku}},
      store_code: {{eq: $storeCode}},
      published: {{eq: $published}}
    }},
    pageSize: 1,
    currentPage: 1
  ) {{
    items {{ {PRODUCT_FIELDS} }}
    total_count
  }}
}}
"""


class TraderJoesClient:
    """Small read-only client with injectable transport for deterministic tests."""

    def __init__(
        self,
        *,
        product_url: str | None = None,
        locator_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.product_url = product_url or os.environ.get("TRADER_JOES_PRODUCT_URL") or PRODUCT_URL
        self.locator_url = locator_url or os.environ.get("TRADER_JOES_LOCATOR_URL") or LOCATOR_URL
        self._transport = transport
        self._http: httpx.AsyncClient | None = None

    async def _http_client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cache-Control": "no-cache",
                    "Origin": "https://www.traderjoes.com",
                    "Pragma": "no-cache",
                    "Referer": "https://www.traderjoes.com/home/products/category",
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/136.0.0.0 Safari/537.36"
                    ),
                },
                timeout=30.0,
                follow_redirects=True,
                transport=self._transport,
            )
        return self._http

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        http = await self._http_client()
        response: httpx.Response | None = None
        for attempt in range(len(_BACKOFFS) + 1):
            start = time.monotonic()
            response = await http.post(url, json=payload)
            _ = time.monotonic() - start
            if response.status_code not in _RETRY_STATUSES or attempt == len(_BACKOFFS):
                break
            await asyncio.sleep(_BACKOFFS[attempt])

        assert response is not None
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            raise TraderJoesError("the site returned a response that was not JSON") from exc
        if not isinstance(data, dict):
            raise TraderJoesError("the site returned an unexpected response shape")
        return data

    async def search_products(
        self, query: str, store_code: str, *, page: int = 1, page_size: int = 10
    ) -> dict[str, Any]:
        payload = {
            "operationName": "SearchProducts",
            "variables": {
                "search": query,
                "storeCode": store_code,
                "published": "1",
                "currentPage": page,
                "pageSize": page_size,
            },
            "query": SEARCH_QUERY,
        }
        data = await self._post(self.product_url, payload)
        return self._graphql_products(data)

    async def get_product(self, sku: str, store_code: str) -> dict[str, Any] | None:
        payload = {
            "operationName": "ProductBySku",
            "variables": {"sku": sku.zfill(6), "storeCode": store_code, "published": "1"},
            "query": PRODUCT_QUERY,
        }
        data = await self._post(self.product_url, payload)
        products = self._graphql_products(data)
        items = products.get("items") or []
        return items[0] if items else None

    @staticmethod
    def _graphql_products(data: dict[str, Any]) -> dict[str, Any]:
        errors = data.get("errors")
        if errors:
            message = errors[0].get("message") if isinstance(errors, list) and errors else None
            raise TraderJoesError(str(message or "the product API rejected the query"))
        products = (data.get("data") or {}).get("products")
        if not isinstance(products, dict):
            raise TraderJoesError("the product API omitted its products result")
        return products

    async def find_stores(
        self,
        location: str,
        *,
        limit: int = 5,
        beer: bool = False,
        wine: bool = False,
        liquor: bool = False,
    ) -> dict[str, Any]:
        where: dict[str, Any] = {"name": {"distinctfrom": "World Class Distribution"}}
        selected = {
            name: {"eq": "Yes"} for name, enabled in (("beer", beer), ("wine", wine), ("liquor", liquor)) if enabled
        }
        if selected:
            where.update(selected)
        payload = {
            "request": {
                "appkey": LOCATOR_APP_KEY,
                "formdata": {
                    "geoip": False,
                    "dataview": "store_default",
                    "limit": limit,
                    "geolocs": {
                        "geoloc": [
                            {
                                "addressline": location,
                                "country": "US",
                                "latitude": "",
                                "longitude": "",
                            }
                        ]
                    },
                    "searchradius": "3000",
                    "where": where,
                },
            }
        }
        data = await self._post(self.locator_url, payload)
        if data.get("code") not in (1, "1"):
            response = data.get("response") or {}
            raise TraderJoesError(str(response.get("message") or "the store locator rejected the search"))
        response = data.get("response")
        if not isinstance(response, dict):
            raise TraderJoesError("the store locator omitted its result")
        return response

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()
