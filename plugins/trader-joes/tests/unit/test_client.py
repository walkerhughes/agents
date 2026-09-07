import httpx
import pytest

from src.client import TraderJoesClient
from src.errors import TraderJoesError
from tests.fixtures import PRODUCT_ITEM, STORE_ITEM


@pytest.mark.unit
async def test_search_products_builds_store_scoped_graphql_request() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        body = __import__("json").loads(request.content)
        assert body["variables"]["storeCode"] == "200"
        assert body["variables"]["search"] == "coffee"
        assert "store_code" in body["query"]
        return httpx.Response(
            200,
            json={"data": {"products": {"items": [PRODUCT_ITEM], "total_count": 1, "page_info": {}}}},
        )

    client = TraderJoesClient(transport=httpx.MockTransport(handler))
    result = await client.search_products("coffee", "200")
    assert result["items"][0]["sku"] == "081522"


@pytest.mark.unit
async def test_get_product_zero_pads_sku() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        body = __import__("json").loads(request.content)
        assert body["variables"]["sku"] == "081522"
        return httpx.Response(200, json={"data": {"products": {"items": [PRODUCT_ITEM]}}})

    client = TraderJoesClient(transport=httpx.MockTransport(handler))
    assert (await client.get_product("81522", "200"))["sku"] == "081522"


@pytest.mark.unit
async def test_find_stores_uses_public_locator_contract() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        body = __import__("json").loads(request.content)
        assert body["request"]["appkey"]
        assert body["request"]["formdata"]["geolocs"]["geoloc"][0]["addressline"] == "94109"
        return httpx.Response(200, json={"code": 1, "response": {"collection": [STORE_ITEM]}})

    client = TraderJoesClient(transport=httpx.MockTransport(handler))
    result = await client.find_stores("94109")
    assert result["collection"][0]["clientkey"] == "200"


@pytest.mark.unit
async def test_graphql_errors_fail_with_upstream_message() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"errors": [{"message": "bad query"}]}))
    client = TraderJoesClient(transport=transport)
    with pytest.raises(TraderJoesError, match="bad query"):
        await client.search_products("coffee", "200")


@pytest.mark.unit
async def test_unexpected_shapes_fail_closed() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=[]))
    client = TraderJoesClient(transport=transport)
    with pytest.raises(TraderJoesError, match="unexpected response shape"):
        await client.search_products("coffee", "200")

    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"data": {}}))
    client = TraderJoesClient(transport=transport)
    with pytest.raises(TraderJoesError, match="omitted its products"):
        await client.search_products("coffee", "200")


@pytest.mark.unit
async def test_locator_failure_and_close() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"code": 0, "response": {"message": "bad location"}})
    )
    client = TraderJoesClient(transport=transport)
    with pytest.raises(TraderJoesError, match="bad location"):
        await client.find_stores("nowhere")
    await client.close()
    assert client._http is not None and client._http.is_closed
