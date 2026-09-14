import json

import pytest

from src import tools
from src.errors import SafewayError, guarded_tool
from tests.fixtures import BEANS, MILK, STORE_ADDRESS, STORE_RESOLVER

pytestmark = pytest.mark.unit


class FakeClient:
    async def find_stores(self, zip_code, limit):
        return [
            {
                "resolver": STORE_RESOLVER["pickup"]["stores"][0],
                "address": STORE_ADDRESS["storeAddressModel"],
            }
        ]

    async def search_products(self, query, store_id, channel, rows):
        product = BEANS if "bean" in query.lower() else MILK
        return {"numFound": 1, "docs": [{**product}]}


@pytest.mark.asyncio
async def test_search_shapes_results(monkeypatch) -> None:
    monkeypatch.setattr(tools, "get_client", lambda: FakeClient())
    result = await tools._search("milk", "1507", "pickup", 3)
    assert result["products"][0]["name"] == "Lucerne Milk Whole - Half Gallon"
    assert result["products"][0]["price"] == 3.99
    assert result["store_id"] == "1507"


def test_server_registers_expected_tools() -> None:
    from src.server import mcp

    assert set(mcp._tool_manager._tools) == {
        "find_stores",
        "search_products",
        "get_product",
        "price_shopping_list",
    }


def test_manifest_versions_match() -> None:
    from pathlib import Path

    root = Path(__file__).parents[2]
    claude = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
    codex = json.loads((root / ".codex-plugin" / "plugin.json").read_text())
    assert claude["version"] == codex["version"]


@pytest.mark.asyncio
async def test_registered_handlers_cover_store_detail_and_list(monkeypatch) -> None:
    from src.server import mcp

    monkeypatch.setattr(tools, "get_client", lambda: FakeClient())
    stores = json.loads(await mcp._tool_manager._tools["find_stores"].fn("94109"))
    assert stores["stores"][0]["store_id"] == "1507"
    searched = json.loads(await mcp._tool_manager._tools["search_products"].fn("milk", "1507"))
    assert searched["products"][0]["price"] == 3.99
    detail = json.loads(await mcp._tool_manager._tools["get_product"].fn("136010013", "1507"))
    assert detail["product"]["product_id"] == "136010013"
    shopping = json.loads(await mcp._tool_manager._tools["price_shopping_list"].fn(["milk", "black beans"], "1507"))
    assert shopping["estimated_total"] == "5.98"
    assert shopping["priced_items"] == 2


@pytest.mark.asyncio
async def test_registered_handlers_return_guided_validation_errors() -> None:
    from src.server import mcp

    assert "numeric" in await mcp._tool_manager._tools["find_stores"].fn("941xx")
    assert "cannot be empty" in await mcp._tool_manager._tools["search_products"].fn("", "1507")
    assert "numeric" in await mcp._tool_manager._tools["get_product"].fn("milk", "1507")
    assert "at least one" in await mcp._tool_manager._tools["price_shopping_list"].fn([], "1507")


@pytest.mark.asyncio
async def test_guarded_tool_formats_expected_errors() -> None:
    @guarded_tool
    async def expected():
        raise SafewayError("broken contract")

    assert "broken contract" in await expected()
