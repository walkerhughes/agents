import json

import pytest

from src import tools
from src.errors import TraderJoesError, guarded_tool
from tests.fixtures import PRODUCT_ITEM, STORE_ITEM


class FakeClient:
    async def find_stores(self, *args, **kwargs):
        return {"collection": [STORE_ITEM]}

    async def search_products(self, query, store_code, **kwargs):
        item = dict(PRODUCT_ITEM)
        item["item_title"] = f"{query.title()} Match"
        return {"items": [item], "total_count": 1, "page_info": {"current_page": 1, "total_pages": 1}}

    async def get_product(self, sku, store_code):
        return PRODUCT_ITEM


@pytest.mark.unit
async def test_search_shaping(monkeypatch) -> None:
    monkeypatch.setattr(tools, "get_client", lambda: FakeClient())
    result = await tools._search("coffee", "200", 10, 1)
    assert result["products"][0]["name"] == "Coffee Match"
    assert "not real-time shelf inventory" in result["catalog_note"]


@pytest.mark.unit
async def test_search_rejects_bad_store_code() -> None:
    with pytest.raises(Exception, match="numeric code"):
        await tools._search("coffee", "Nob Hill", 10, 1)


@pytest.mark.unit
def test_server_registers_expected_tools() -> None:
    from src.server import mcp

    assert set(mcp._tool_manager._tools) == {
        "find_stores",
        "search_products",
        "get_product",
        "price_shopping_list",
    }


@pytest.mark.unit
def test_manifest_versions_match() -> None:
    from pathlib import Path

    root = Path(__file__).parents[2]
    claude = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
    codex = json.loads((root / ".codex-plugin" / "plugin.json").read_text())
    assert claude["version"] == codex["version"]


@pytest.mark.unit
def test_fmt_is_json() -> None:
    assert json.loads(tools.fmt({"price": "9.99"})) == {"price": "9.99"}


@pytest.mark.unit
async def test_registered_handlers_exercise_store_product_and_list_flows(monkeypatch) -> None:
    from src.server import mcp

    monkeypatch.setattr(tools, "get_client", lambda: FakeClient())

    found = json.loads(await mcp._tool_manager._tools["find_stores"].fn("94109"))
    assert found["stores"][0]["store_code"] == "200"

    searched = json.loads(await mcp._tool_manager._tools["search_products"].fn("coffee", "200"))
    assert searched["products"][0]["price"] == "9.99"

    detailed = json.loads(await mcp._tool_manager._tools["get_product"].fn("81522", "200"))
    assert detailed["product"]["sku"] == "081522"

    shopping = json.loads(await mcp._tool_manager._tools["price_shopping_list"].fn(["coffee", "tea"], "200", 2))
    assert shopping["estimated_total"] == "19.98"
    assert shopping["priced_items"] == 2


@pytest.mark.unit
async def test_registered_handlers_return_guided_validation_errors() -> None:
    from src.server import mcp

    assert "cannot be empty" in await mcp._tool_manager._tools["find_stores"].fn("")
    assert "at most six digits" in await mcp._tool_manager._tools["get_product"].fn("coffee", "200")
    assert "at least one" in await mcp._tool_manager._tools["price_shopping_list"].fn([], "200")


@pytest.mark.unit
async def test_guarded_tool_formats_expected_and_http_errors() -> None:
    @guarded_tool
    async def expected():
        raise TraderJoesError("broken contract")

    @guarded_tool
    async def forbidden():
        request = __import__("httpx").Request("POST", "https://example.test")
        response = __import__("httpx").Response(403, request=request)
        raise __import__("httpx").HTTPStatusError("forbidden", request=request, response=response)

    assert "broken contract" in await expected()
    assert "HTTP 403" in await forbidden()
