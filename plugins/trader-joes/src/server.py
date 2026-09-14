"""Trader Joe's MCP server."""

import json
from pathlib import Path

from mcp.server import MCPServer

from .tools import register_all

_MANIFEST = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"

INSTRUCTIONS = (
    "Read-only access to Trader Joe's public website catalog and store locator. "
    "Start with find_stores when a store code is unknown, then use that store code "
    "for every product or list request because prices can vary by location. Use "
    "search_products to discover candidates, get_product for a known SKU, and "
    "price_shopping_list to batch a draft list. Never describe catalog availability "
    "as live inventory. Trader Joe's explicitly says the website does not represent "
    "every product, so label menu and shopping-list results as website-backed choices."
)


def version() -> str:
    try:
        return str(json.loads(_MANIFEST.read_text())["version"])
    except (OSError, ValueError, KeyError):
        return ""


def build_server() -> MCPServer:
    mcp = MCPServer("trader-joes", instructions=INSTRUCTIONS, version=version())
    register_all(mcp)
    return mcp


mcp = build_server()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
