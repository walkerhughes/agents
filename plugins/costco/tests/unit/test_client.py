import json

import httpx
import pytest

from src.client import CostcoClient
from src.errors import CostcoError
from tests.fixtures import PRODUCT_ITEM, SEARCH_RESULT, WAREHOUSE_ITEM

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_find_warehouses_geocodes_then_uses_locator_contract() -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/geocode":
            return httpx.Response(200, json=[{"lat": "37.77", "lon": "-122.42"}])
        return httpx.Response(200, json={"salesLocations": [WAREHOUSE_ITEM]})

    client = CostcoClient(
        geocode_url="https://mock.test/geocode",
        warehouse_url="https://mock.test/warehouses",
        transport=httpx.MockTransport(handler),
    )
    result = await client.find_warehouses("94109", limit=3)

    assert result["salesLocations"][0]["salesLocationId"] == 144
    assert requests[0].url.params["q"] == "94109"
    assert requests[1].url.params["latitude"] == "37.77"
    assert requests[1].headers["client-identifier"]
    await client.close()


@pytest.mark.asyncio
async def test_search_catalog_sends_location_context() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"searchResult": SEARCH_RESULT})

    client = CostcoClient(search_url="https://mock.test/search", transport=httpx.MockTransport(handler))
    result = await client.search_catalog("quinoa", "144", "94080", state="CA", limit=3)

    assert result["totalCount"] == 1
    assert captured["warehouseId"] == "144-wh"
    assert captured["shipToPostal"] == "94080"


@pytest.mark.asyncio
async def test_get_products_builds_warehouse_scoped_graphql() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"data": {"products": {"catalogData": [PRODUCT_ITEM]}}})

    client = CostcoClient(product_url="https://mock.test/products", transport=httpx.MockTransport(handler))
    result = await client.get_products(["1234567"], "144")

    assert result[0]["itemNumber"] == "1234567"
    assert 'warehouseNumber: "144"' in captured["query"]
    assert 'itemNumbers: ["1234567"]' in captured["query"]


@pytest.mark.asyncio
async def test_upstream_shape_and_graphql_errors_fail_closed() -> None:
    responses = iter(
        [
            httpx.Response(200, json={}),
            httpx.Response(200, json={"errors": [{"message": "bad query"}]}),
        ]
    )
    client = CostcoClient(transport=httpx.MockTransport(lambda request: next(responses)))

    with pytest.raises(CostcoError, match="searchResult"):
        await client.search_catalog("rice", "144", "94080")
    with pytest.raises(CostcoError, match="bad query"):
        await client.get_products(["1"], "144")


@pytest.mark.asyncio
async def test_missing_geocode_and_non_json_fail_usefully() -> None:
    responses = iter([httpx.Response(200, json=[]), httpx.Response(200, text="nope")])
    client = CostcoClient(transport=httpx.MockTransport(lambda request: next(responses)))

    with pytest.raises(CostcoError, match="no US map result"):
        await client.geocode("Atlantis")
    with pytest.raises(CostcoError, match="not JSON"):
        await client.search_catalog("rice", "144", "94080")
