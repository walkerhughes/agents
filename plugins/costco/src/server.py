"""Costco MCP server."""

import json
from pathlib import Path

from mcp.server import MCPServer

from .tools import register_all

_MANIFEST = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"

INSTRUCTIONS = (
    "Read-only access to Costco's public warehouse, catalog, and product-detail "
    "requests. Start with find_warehouses when location values are unknown, then use "
    "the chosen warehouse number and postal code for product searches. Use "
    "search_products to discover products, get_product for a known item number, and "
    "price_shopping_list for a draft list. Treat prices as public Costco.com prices "
    "for the selected warehouse context, not guaranteed walk-in or member prices. "
    "Never describe catalog program types as real-time inventory."
)


def version() -> str:
    try:
        return str(json.loads(_MANIFEST.read_text())["version"])
    except (OSError, ValueError, KeyError):
        return ""


def build_server() -> MCPServer:
    mcp = MCPServer("costco", instructions=INSTRUCTIONS, version=version())
    register_all(mcp)
    return mcp


mcp = build_server()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
