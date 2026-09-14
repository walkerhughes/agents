import httpx
import pytest

from src.client import SafewayClient
from src.errors import SafewayError
from tests.fixtures import SEARCH, STORE_ADDRESS, STORE_RESOLVER

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_find_stores_resolves_pickup_addresses() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/v2/all"):
            return httpx.Response(206, json=STORE_RESOLVER)
        return httpx.Response(200, json=STORE_ADDRESS)

    client = SafewayClient(transport=httpx.MockTransport(handler))
    result = await client.find_stores("94109", 1)

    assert result[0]["resolver"]["locationId"] == "1507"
    assert result[0]["address"]["address"]["line1"] == "2020 Market St"
    assert requests[0].url.params["zipcode"] == "94109"
    assert requests[1].url.params["storeid"] == "1507"
    await client.close()


@pytest.mark.asyncio
async def test_search_sends_store_channel_and_browser_contract() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=SEARCH)

    client = SafewayClient(transport=httpx.MockTransport(handler))
    result = await client.search_products("milk", "1507", "pickup", 3)

    assert result["docs"][0]["pid"] == "136010013"
    assert requests[0].url.params["storeid"] == "1507"
    assert requests[0].url.params["channel"] == "pickup"
    assert requests[0].url.params["rows"] == "3"
    assert requests[0].headers["ocp-apim-subscription-key"]
    assert requests[0].headers["x-swy-banner"] == "safeway"
    await client.close()


@pytest.mark.asyncio
async def test_partial_content_is_a_success() -> None:
    client = SafewayClient(transport=httpx.MockTransport(lambda request: httpx.Response(206, json=SEARCH)))
    result = await client.search_products("milk", "1507", "pickup", 1)
    assert result["numFound"] == 1
    await client.close()


@pytest.mark.asyncio
async def test_non_json_and_unexpected_shapes_fail_closed() -> None:
    responses = iter([httpx.Response(200, text="nope"), httpx.Response(200, json={})])
    client = SafewayClient(transport=httpx.MockTransport(lambda request: next(responses)))
    with pytest.raises(SafewayError, match="non-JSON"):
        await client.search_products("milk", "1507", "pickup", 1)
    with pytest.raises(SafewayError, match="product list"):
        await client.search_products("milk", "1507", "pickup", 1)
    await client.close()


@pytest.mark.asyncio
async def test_missing_store_list_and_address_fail_closed() -> None:
    responses = iter([httpx.Response(200, json={}), httpx.Response(200, json={})])
    client = SafewayClient(transport=httpx.MockTransport(lambda request: next(responses)))
    with pytest.raises(SafewayError, match="store list"):
        await client.find_stores("94109", 1)
    with pytest.raises(SafewayError, match="address"):
        await client.store_address("1507")
    await client.close()
