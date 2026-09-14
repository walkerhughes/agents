import json

import pytest

from src import tools
from src.errors import CostcoError, guarded_tool
from tests.fixtures import PRODUCT_ITEM, SEARCH_RESULT, WAREHOUSE_ITEM

pytestmark = pytest.mark.unit


class FakeClient:
    async def find_warehouses(self, location, **kwargs):
        return {"salesLocations": [WAREHOUSE_ITEM]}

    async def search_catalog(self, query, warehouse_number, postal_code, **kwargs):
        result = dict(SEARCH_RESULT)
        result["results"] = [dict(SEARCH_RESULT["results"][0])]
        result["results"][0]["product"] = dict(result["results"][0]["product"])
        result["results"][0]["product"]["title"] = f"{query.title()} Match"
        return result

    async def get_products(self, item_numbers, warehouse_number):
        return [{**PRODUCT_ITEM, "itemNumber": item_numbers[0]}]


@pytest.mark.asyncio
async def test_search_combines_catalog_and_price(monkeypatch) -> None:
    monkeypatch.setattr(tools, "get_client", lambda: FakeClient())
    result = await tools._search("quinoa", "144", "94080", "CA", 3)

    assert result["products"][0]["name"] == "Kirkland Signature Organic Quinoa, 4.5 lb"
    assert result["products"][0]["price"] == "18.99000"
    assert "not real-time" in result["availability_note"]


def test_server_registers_expected_tools() -> None:
    from src.server import mcp

    assert set(mcp._tool_manager._tools) == {
        "find_warehouses",
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
async def test_registered_handlers_cover_warehouse_product_and_list(monkeypatch) -> None:
    from src.server import mcp

    monkeypatch.setattr(tools, "get_client", lambda: FakeClient())

    found = json.loads(await mcp._tool_manager._tools["find_warehouses"].fn("94109"))
    assert found["warehouses"][0]["warehouse_number"] == "144"

    searched = json.loads(await mcp._tool_manager._tools["search_products"].fn("quinoa", "144", "94080"))
    assert searched["products"][0]["price"] == "18.99000"

    detailed = json.loads(await mcp._tool_manager._tools["get_product"].fn("1234567", "144"))
    assert detailed["product"]["item_number"] == "1234567"

    shopping = json.loads(await mcp._tool_manager._tools["price_shopping_list"].fn(["quinoa", "rice"], "144", "94080"))
    assert shopping["estimated_total"] == "37.98"
    assert shopping["priced_items"] == 2


@pytest.mark.asyncio
async def test_registered_handlers_return_guided_validation_errors() -> None:
    from src.server import mcp

    assert "cannot be empty" in await mcp._tool_manager._tools["find_warehouses"].fn("")
    assert "numeric" in await mcp._tool_manager._tools["get_product"].fn("quinoa", "144")
    assert "at least one" in await mcp._tool_manager._tools["price_shopping_list"].fn([], "144", "94080")


@pytest.mark.asyncio
async def test_guarded_tool_formats_expected_and_http_errors() -> None:
    @guarded_tool
    async def expected():
        raise CostcoError("broken contract")

    assert "broken contract" in await expected()
