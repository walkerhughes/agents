"""Target MCP server."""

import json
from pathlib import Path

from mcp.server import MCPServer

from .tools import register_all

_MANIFEST = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"

INSTRUCTIONS = (
    "Read-only access to Target's public catalog, product-detail, and nearby "
    "availability requests. Keep every price tied to a supplied store ID. Use "
    "search_products to discover TCINs, find_stores_with_item to choose among nearby "
    "stores for a product, get_product for detail, and price_shopping_list for a "
    "draft list. Treat availability as a point-in-time signal, not a reservation."
)


def version() -> str:
    try:
        return str(json.loads(_MANIFEST.read_text())["version"])
    except (OSError, ValueError, KeyError):
        return ""


def build_server() -> MCPServer:
    server = MCPServer("target", instructions=INSTRUCTIONS, version=version())
    register_all(server)
    return server


mcp = build_server()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
