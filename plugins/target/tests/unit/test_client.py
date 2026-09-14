import httpx
import pytest

from src.client import TargetClient
from src.errors import TargetError
from tests.fixtures import LOCATION, PRODUCT, SEARCH

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_search_sends_store_and_zip_context() -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(206, json={"data": {"search": SEARCH}})

    client = TargetClient(transport=httpx.MockTransport(handler))
    result = await client.search_products("rice", "2766", "94103", 3)

    assert result["products"][0]["tcin"] == "88888888"
    assert requests[0].url.params["pricing_store_id"] == "2766"
    assert requests[0].url.params["zip"] == "94103"
    assert requests[0].url.params["include_sponsored"] == "false"
    await client.close()


@pytest.mark.asyncio
async def test_product_detail_sends_tcin_and_location() -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": {"product": PRODUCT}})

    client = TargetClient(transport=httpx.MockTransport(handler))
    result = await client.get_product("88888888", "2766", "94103", "ca")

    assert result == PRODUCT
    assert requests[0].url.params["tcin"] == "88888888"
    assert requests[0].url.params["state"] == "CA"
    await client.close()


@pytest.mark.asyncio
async def test_availability_uses_zip_radius_and_quantity() -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": {"fulfillment_fiats": {"locations": [LOCATION]}}})

    client = TargetClient(transport=httpx.MockTransport(handler))
    result = await client.find_stores_with_item("88888888", "94103", 25, 5, 2)

    assert result["locations"][0]["location_id"] == "2766"
    assert requests[0].url.params["nearby"] == "94103"
    assert requests[0].url.params["requested_quantity"] == "2"
    await client.close()


@pytest.mark.asyncio
async def test_challenge_fails_with_actionable_message() -> None:
    client = TargetClient(transport=httpx.MockTransport(lambda request: httpx.Response(403, text="captcha")))
    with pytest.raises(TargetError, match="automated-traffic challenge"):
        await client.search_products("rice", "2766", "94103", 3)


@pytest.mark.asyncio
async def test_non_json_and_unexpected_shapes_fail_closed() -> None:
    responses = iter([httpx.Response(200, text="nope"), httpx.Response(200, json={})])
    client = TargetClient(transport=httpx.MockTransport(lambda request: next(responses)))
    with pytest.raises(TargetError, match="non-JSON"):
        await client.search_products("rice", "2766", "94103", 3)
    with pytest.raises(TargetError, match="unexpected response shape"):
        await client.search_products("rice", "2766", "94103", 3)
