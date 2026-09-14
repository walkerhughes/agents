import json

import pytest

from src import tools
from src.errors import TargetError, guarded_tool
from tests.fixtures import LOCATION, PRODUCT, SEARCH

pytestmark = pytest.mark.unit


class FakeClient:
    async def search_products(self, query, store_id, zip_code, limit):
        result = {**SEARCH, "products": [{**PRODUCT}]}
        result["products"][0]["item"] = {**PRODUCT["item"]}
        result["products"][0]["item"]["product_description"] = {
            **PRODUCT["item"]["product_description"],
            "title": f"{query.title()} Match",
        }
        return result

    async def get_product(self, tcin, store_id, zip_code="", state=""):
        return {**PRODUCT, "tcin": tcin}

    async def find_stores_with_item(self, tcin, zip_code, radius, limit, requested_quantity):
        return {"product_id": tcin, "locations": [LOCATION]}


@pytest.mark.asyncio
async def test_search_shapes_results(monkeypatch) -> None:
    monkeypatch.setattr(tools, "get_client", lambda: FakeClient())
    result = await tools._search("rice", "2766", "94103", 3)
    assert result["products"][0]["name"] == "Rice Match"
    assert result["products"][0]["current_price"] == 4.99
    assert result["store_id"] == "2766"


def test_server_registers_expected_tools() -> None:
    from src.server import mcp

    assert set(mcp._tool_manager._tools) == {
        "search_products",
        "get_product",
        "find_stores_with_item",
        "price_shopping_list",
    }


def test_manifest_versions_match() -> None:
    from pathlib import Path

    root = Path(__file__).parents[2]
    claude = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
    codex = json.loads((root / ".codex-plugin" / "plugin.json").read_text())
    assert claude["version"] == codex["version"]


@pytest.mark.asyncio
async def test_registered_handlers_cover_detail_availability_and_list(monkeypatch) -> None:
    from src.server import mcp

    monkeypatch.setattr(tools, "get_client", lambda: FakeClient())
    searched = json.loads(await mcp._tool_manager._tools["search_products"].fn("rice", "2766", "94103"))
    assert searched["products"][0]["current_price"] == 4.99
    detail = json.loads(await mcp._tool_manager._tools["get_product"].fn("88888888", "2766"))
    assert detail["product"]["tcin"] == "88888888"
    stores = json.loads(await mcp._tool_manager._tools["find_stores_with_item"].fn("88888888", "94103"))
    assert stores["stores"][0]["store_id"] == "2766"
    shopping = json.loads(await mcp._tool_manager._tools["price_shopping_list"].fn(["rice", "beans"], "2766", "94103"))
    assert shopping["estimated_total"] == "9.98"
    assert shopping["priced_items"] == 2


@pytest.mark.asyncio
async def test_registered_handlers_return_guided_validation_errors() -> None:
    from src.server import mcp

    assert "cannot be empty" in await mcp._tool_manager._tools["search_products"].fn("", "2766")
    assert "numeric" in await mcp._tool_manager._tools["get_product"].fn("rice", "2766")
    assert "at least one" in await mcp._tool_manager._tools["price_shopping_list"].fn([], "2766")
    assert "zip_code is required" in await mcp._tool_manager._tools["find_stores_with_item"].fn("88888888", "")


@pytest.mark.asyncio
async def test_guarded_tool_formats_expected_errors() -> None:
    @guarded_tool
    async def expected():
        raise TargetError("broken contract")

    assert "broken contract" in await expected()
