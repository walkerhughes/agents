#!/usr/bin/env python3
"""Generate the Costco Harbor tasks from one compact specification."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TASKS = {
    "nearest-warehouse": {
        "description": "Find the nearest Costco warehouse to ZIP code 94109.",
        "instruction": (
            "Find the nearest Costco warehouse to ZIP code 94109. Report its numeric "
            "warehouse number and full warehouse name."
        ),
        "tools": ["find_warehouses"],
        "answer": {"warehouse_number": "144", "name": "South San Francisco"},
    },
    "quinoa-price": {
        "description": "Find the public price of organic quinoa for warehouse 144.",
        "instruction": (
            "For Costco warehouse 144 and postal code 94080, find organic quinoa and "
            "report the selected product name and public Costco.com price as a number."
        ),
        "tools": ["search_products"],
        "answer": {"name": "Kirkland Signature Organic Quinoa, 4.5 lb", "price": 18.99},
    },
    "product-by-item": {
        "description": "Look up a Costco product by item number for warehouse 144.",
        "instruction": (
            "For Costco warehouse 144, look up item number 1234567 and report its "
            "product name and public Costco.com price as a number."
        ),
        "tools": ["get_product"],
        "answer": {"name": "Kirkland Signature Organic Quinoa, 4.5 lb", "price": 18.99},
    },
    "shopping-list": {
        "description": "Price a two-item shopping list for Costco warehouse 144.",
        "instruction": (
            "For Costco warehouse 144 and postal code 94080, price a list containing "
            "one package of organic quinoa and one package of jasmine rice. Report the "
            "selected product names and combined public Costco.com total as a number."
        ),
        "tools": ["price_shopping_list"],
        "answer": {
            "items": [
                "Kirkland Signature Organic Quinoa, 4.5 lb",
                "Kirkland Signature Jasmine Rice, 25 lb",
            ],
            "estimated_total": 31.48,
        },
    },
    "two-dinner-run": {
        "description": "Turn a location and two dinners into one warehouse-specific Costco run.",
        "instruction": (
            "I am near ZIP code 94109 and want to make chicken tacos and chicken Caesar "
            "salad bowls for four people, reusing one rotisserie chicken across both meals. "
            "Find the nearest warehouse, then price one package each of rotisserie chicken, "
            "flour tortillas, shredded Mexican cheese, and a Caesar salad kit there. Report "
            "the warehouse number and name, selected product names, public Costco.com total, "
            "and the exact selected product reused across both dinners."
        ),
        "tools": ["find_warehouses", "price_shopping_list"],
        "answer": {
            "warehouse_number": "144",
            "warehouse_name": "South San Francisco",
            "items": [
                "Kirkland Signature Rotisserie Chicken, 3 lb",
                "Organic Flour Tortillas, 40 ct",
                "Mexican Style Blend Shredded Cheese, 2.5 lb",
                "Organic Caesar Salad Kit, 24 oz",
            ],
            "estimated_total": 31.46,
            "reused_product": "Kirkland Signature Rotisserie Chicken, 3 lb",
        },
    },
    "bulk-package-math": {
        "description": "Convert a household quantity into Costco packages and extended cost.",
        "instruction": (
            "For Costco warehouse 144 and postal code 94080, I need at least 20 rolls "
            "of paper towels. Find the relevant product, use its package quantity, and "
            "report the product name, rolls per package, minimum packages to buy, total "
            "rolls purchased, and public Costco.com extended total."
        ),
        "tools": ["search_products"],
        "answer": {
            "name": "Kirkland Signature Paper Towels, 12 rolls",
            "rolls_per_package": 12,
            "packages_to_buy": 2,
            "total_rolls": 24,
            "estimated_total": 47.98,
        },
    },
    "incomplete-estimate": {
        "description": "Keep hidden prices out of a Costco shopping-list estimate.",
        "instruction": (
            "For Costco warehouse 144 and postal code 94080, price one package of organic "
            "quinoa and one package of avocados. Report requested and priced item counts, "
            "the known subtotal, the selected product whose public price is hidden, and "
            "whether the estimate is complete. Never treat a hidden price as zero."
        ),
        "tools": ["price_shopping_list"],
        "answer": {
            "requested_items": 2,
            "priced_items": 1,
            "known_subtotal": 18.99,
            "unpriced_product": "Hass Avocados, 6 ct",
            "estimate_complete": False,
        },
    },
    "compare-alternatives": {
        "description": "Choose the least expensive warehouse-signaled catalog alternative.",
        "instruction": (
            "For Costco warehouse 144 and postal code 94080, search for olive oil. Of the "
            "returned products that are buyable and carry the InWarehouse catalog signal, "
            "choose the one with the lowest public Costco.com price. Report its item number, "
            "name, price, and savings versus the other qualifying result."
        ),
        "tools": ["search_products"],
        "answer": {
            "item_number": "2468101",
            "name": "Kirkland Signature Extra Virgin Olive Oil, 2 L",
            "price": 24.99,
            "savings": 7.0,
        },
    },
}

TASK_TOML = """schema_version = "1.1"

[task]
name = "costco/{name}"
description = {description}
authors = []
keywords = ["mcp", "costco", "eval"]

[metadata]
category = "mcp"
difficulty = "easy"

[agent]
timeout_sec = 300.0

[verifier]
timeout_sec = 60.0

[environment]
build_timeout_sec = 900.0
cpus = 1
memory_mb = 2048
storage_mb = 10240
gpus = 0
network_mode = "public"

[[environment.mcp_servers]]
name = "costco"
transport = "stdio"
command = "/opt/eval/start-mcp"
args = []
"""

INSTRUCTION = """# Task

{instruction}

Use the Costco integration tools available in this environment. All warehouse and
product data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{shape}
```
"""

DOCKERFILE = """FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \\
    ca-certificates curl git \\
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN git clone https://github.com/walkerhughes/claude.git /opt/claude \\
    && git -C /opt/claude checkout main \\
    && cd /opt/claude/plugins/costco \\
    && uv sync --frozen --no-dev

RUN python -m venv /opt/rewardkit \\
    && /opt/rewardkit/bin/pip install --no-cache-dir "harbor-rewardkit==0.1.*" \\
    && ln -s /opt/rewardkit/bin/rewardkit /usr/local/bin/rewardkit

COPY mock_server.py start-mcp /opt/eval/
RUN chmod +x /opt/eval/start-mcp

WORKDIR /app
ENV COSTCO_PRODUCT_URL=http://127.0.0.1:8091/graphql \\
    COSTCO_SEARCH_URL=http://127.0.0.1:8091/search \\
    COSTCO_WAREHOUSE_URL=http://127.0.0.1:8091/warehouses \\
    COSTCO_GEOCODE_URL=http://127.0.0.1:8091/geocode
"""

START_MCP = """#!/bin/sh
set -eu

python /opt/eval/mock_server.py >/tmp/costco-mock.log 2>&1 &
mock_pid=$!
trap 'kill "$mock_pid" 2>/dev/null || true' EXIT INT TERM

for attempt in $(seq 1 50); do
    if curl -sf http://127.0.0.1:8091/health >/dev/null; then
        cd /opt/claude/plugins/costco
        exec uv run --no-dev python -m src.server
    fi
    sleep 0.1
done

cat /tmp/costco-mock.log >&2
exit 1
"""

MOCK_SERVER = r'''#!/usr/bin/env python3
"""Deterministic local stand-in for Costco's public website endpoints."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

QUINOA = {
    "itemNumber": "1234567",
    "buyable": 1,
    "programTypes": "InWarehouse,ShipIt",
    "priceData": {"price": "18.99", "listPrice": "21.99"},
    "attributes": [
        {"key": "Brand", "value": "Kirkland Signature", "type": "string"},
        {"key": "Package Quantity", "value": "4.5 lb", "type": "string"},
    ],
    "description": {
        "shortDescription": "Kirkland Signature Organic Quinoa, 4.5 lb",
        "longDescription": "USDA organic white quinoa.",
    },
    "additionalFieldData": {"rating": "4.8", "numberOfRating": 321},
}
RICE = {
    "itemNumber": "7654321",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "12.49", "listPrice": "-1.00000"},
    "attributes": [
        {"key": "Brand", "value": "Kirkland Signature", "type": "string"},
        {"key": "Package Quantity", "value": "25 lb", "type": "string"},
    ],
    "description": {
        "shortDescription": "Kirkland Signature Jasmine Rice, 25 lb",
        "longDescription": "Long-grain jasmine rice.",
    },
    "additionalFieldData": {"rating": "4.7", "numberOfRating": 212},
}
CHICKEN = {
    "itemNumber": "1000001",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "4.99", "listPrice": "-1.00000"},
    "attributes": [{"key": "Package Quantity", "value": "3 lb", "type": "string"}],
    "description": {
        "shortDescription": "Kirkland Signature Rotisserie Chicken, 3 lb",
        "longDescription": "Prepared rotisserie chicken.",
    },
    "additionalFieldData": {},
}
TORTILLAS = {
    "itemNumber": "1000002",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "7.99", "listPrice": "-1.00000"},
    "attributes": [{"key": "Package Quantity", "value": "40 ct", "type": "string"}],
    "description": {
        "shortDescription": "Organic Flour Tortillas, 40 ct",
        "longDescription": "Organic flour tortillas.",
    },
    "additionalFieldData": {},
}
CHEESE = {
    "itemNumber": "1000003",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "11.49", "listPrice": "-1.00000"},
    "attributes": [{"key": "Package Quantity", "value": "2.5 lb", "type": "string"}],
    "description": {
        "shortDescription": "Mexican Style Blend Shredded Cheese, 2.5 lb",
        "longDescription": "Shredded Mexican-style cheese blend.",
    },
    "additionalFieldData": {},
}
SALAD = {
    "itemNumber": "1000004",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "6.99", "listPrice": "-1.00000"},
    "attributes": [{"key": "Package Quantity", "value": "24 oz", "type": "string"}],
    "description": {
        "shortDescription": "Organic Caesar Salad Kit, 24 oz",
        "longDescription": "Caesar salad kit.",
    },
    "additionalFieldData": {},
}
PAPER_TOWELS = {
    "itemNumber": "1000005",
    "buyable": 1,
    "programTypes": "InWarehouse,ShipIt",
    "priceData": {"price": "23.99", "listPrice": "27.99"},
    "attributes": [{"key": "Package Quantity", "value": "12 rolls", "type": "string"}],
    "description": {
        "shortDescription": "Kirkland Signature Paper Towels, 12 rolls",
        "longDescription": "Two-ply paper towels.",
    },
    "additionalFieldData": {},
}
AVOCADOS = {
    "itemNumber": "1000006",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "0.00000", "listPrice": "-1.00000"},
    "attributes": [{"key": "Package Quantity", "value": "6 ct", "type": "string"}],
    "description": {
        "shortDescription": "Hass Avocados, 6 ct",
        "longDescription": "Fresh Hass avocados.",
    },
    "additionalFieldData": {},
}
OLIVE_OIL_ORGANIC = {
    "itemNumber": "2468100",
    "buyable": 1,
    "programTypes": "InWarehouse,ShipIt",
    "priceData": {"price": "31.99", "listPrice": "34.99"},
    "attributes": [{"key": "Package Quantity", "value": "2 L", "type": "string"}],
    "description": {
        "shortDescription": "Kirkland Signature Organic Extra Virgin Olive Oil, 2 L",
        "longDescription": "Organic extra virgin olive oil.",
    },
    "additionalFieldData": {},
}
OLIVE_OIL = {
    "itemNumber": "2468101",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "24.99", "listPrice": "29.99"},
    "attributes": [{"key": "Package Quantity", "value": "2 L", "type": "string"}],
    "description": {
        "shortDescription": "Kirkland Signature Extra Virgin Olive Oil, 2 L",
        "longDescription": "Extra virgin olive oil.",
    },
    "additionalFieldData": {},
}
PRODUCTS = [
    QUINOA,
    RICE,
    CHICKEN,
    TORTILLAS,
    CHEESE,
    SALAD,
    PAPER_TOWELS,
    AVOCADOS,
    OLIVE_OIL_ORGANIC,
    OLIVE_OIL,
]
WAREHOUSE = {
    "salesLocationId": 144,
    "name": [{"localeCode": "en-US", "value": "South San Francisco"}],
    "phone": "650-872-2021",
    "distance": 8.2,
    "address": {
        "line1": "451 S Airport Blvd",
        "city": "South San Francisco",
        "territory": "CA",
        "postalCode": "94080",
        "latitude": 37.644,
        "longitude": -122.405,
    },
    "services": [],
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._send({"ok": True})
            return
        if path == "/geocode":
            self._send([{"lat": "37.7749", "lon": "-122.4194"}])
            return
        if path == "/warehouses":
            self._send({"salesLocations": [WAREHOUSE]})
            return
        self.send_error(404)

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(size) or b"{}")
        if self.path == "/search":
            query = str(request.get("query") or "").lower()
            if "rice" in query:
                matches = [RICE]
            elif "chicken" in query:
                matches = [CHICKEN]
            elif "tortilla" in query:
                matches = [TORTILLAS]
            elif "cheese" in query:
                matches = [CHEESE]
            elif "salad" in query:
                matches = [SALAD]
            elif "paper towel" in query:
                matches = [PAPER_TOWELS]
            elif "avocado" in query:
                matches = [AVOCADOS]
            elif "olive oil" in query:
                matches = [OLIVE_OIL_ORGANIC, OLIVE_OIL]
            else:
                matches = [QUINOA]
            self._send(
                {
                    "searchResult": {
                        "totalCount": len(matches),
                        "results": [
                            {
                                "id": item["itemNumber"],
                                "product": {
                                    "title": item["description"]["shortDescription"],
                                    "brands": ["Kirkland Signature"],
                                    "categories": ["Grocery"],
                                    "attributes": {},
                                },
                            }
                            for item in matches
                        ],
                    }
                }
            )
            return
        if self.path == "/graphql":
            query = str(request.get("query") or "")
            items = [item for item in PRODUCTS if item["itemNumber"] in query]
            self._send({"data": {"products": {"catalogData": items}}})
            return
        self.send_error(404)

    def _send(self, payload):
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


ThreadingHTTPServer(("127.0.0.1", 8091), Handler).serve_forever()
'''

PROCESS_CHECK = '''"""Verify that the answer came through the Costco MCP server."""

import json
import re
from pathlib import Path

from rewardkit import criterion

TRAJECTORY = Path("/logs/agent/trajectory.json")
SESSIONS = Path("/logs/agent/sessions")
EXPECTED_TOOLS = json.loads(r"""{tools}""")
BYPASS = re.compile(r":8091\\b|mock_server\\.py|/opt/eval", re.IGNORECASE)


def _calls():
    calls = []
    try:
        data = json.loads(TRAJECTORY.read_text())
        calls.extend(call for step in data.get("steps") or [] for call in step.get("tool_calls") or [])
    except (OSError, json.JSONDecodeError):
        pass
    for path in sorted(SESSIONS.rglob("*.jsonl")):
        try:
            lines = path.read_text().splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                blocks = (json.loads(line).get("message") or {{}}).get("content")
            except json.JSONDecodeError:
                continue
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    calls.append({{"function_name": block.get("name"), "arguments": block.get("input")}})
    return calls


@criterion(description="Agent called every expected Costco MCP tool")
def used_mcp_tool(workspace: Path) -> bool:
    called = {{str(call.get("function_name") or "") for call in _calls()}}
    return all(tool in called for tool in EXPECTED_TOOLS)


@criterion(description="Agent did not bypass the Costco MCP server")
def no_direct_endpoint_access(workspace: Path) -> bool:
    calls = _calls()
    if not calls:
        return False
    for call in calls:
        if str(call.get("function_name") or "").startswith("mcp__costco__"):
            continue
        if BYPASS.search(json.dumps(call.get("arguments") or {{}})):
            return False
    return True
'''

OUTCOME_CHECK = '''"""Compare the submitted answer with deterministic fixture truth."""

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from rewardkit import criterion

EXPECTED = json.loads(
    r"""{expected}"""
)


def _matches(actual, expected):
    if isinstance(expected, float):
        try:
            normalized = re.sub(r"[^0-9.-]", "", str(actual))
            return Decimal(normalized) == Decimal(str(expected))
        except (InvalidOperation, TypeError, ValueError):
            return False
    if isinstance(expected, list):
        if isinstance(actual, str) and all(isinstance(item, str) for item in expected):
            if actual == ", ".join(expected):
                actual = expected
            else:
                actual = [item.strip() for item in actual.split(";")]
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(
                _matches(actual_item, expected_item)
                for actual_item, expected_item in zip(actual, expected, strict=True)
            )
        )
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and actual.keys() == expected.keys()
            and all(_matches(actual[key], value) for key, value in expected.items())
        )
    return actual == expected


@criterion(description="Answer matches the mock catalog and warehouse data")
def answer_matches(workspace: Path) -> bool:
    try:
        answer = json.loads((workspace / "answer.json").read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return _matches(answer, EXPECTED)
'''


def answer_shape(answer: dict) -> dict:
    shape = {}
    for key, value in answer.items():
        if isinstance(value, list):
            shape[key] = [f"<item {index}>" for index in range(1, len(value) + 1)]
        elif isinstance(value, bool):
            shape[key] = False
        elif isinstance(value, int):
            shape[key] = 0
        elif isinstance(value, float):
            shape[key] = 0.0
        else:
            shape[key] = f"<{key}>"
    return shape


def main() -> None:
    for child in ROOT.iterdir():
        if child.is_dir() and child.name in TASKS:
            shutil.rmtree(child)

    for name, spec in TASKS.items():
        task = ROOT / name
        (task / "environment").mkdir(parents=True)
        (task / "solution").mkdir()
        (task / "tests" / "outcome").mkdir(parents=True)
        (task / "tests" / "process").mkdir()

        (task / "task.toml").write_text(TASK_TOML.format(name=name, description=json.dumps(spec["description"])))
        (task / "instruction.md").write_text(
            INSTRUCTION.format(
                instruction=spec["instruction"],
                shape=json.dumps(answer_shape(spec["answer"]), indent=2),
            )
        )
        (task / "environment" / "Dockerfile").write_text(DOCKERFILE)
        (task / "environment" / "mock_server.py").write_text(MOCK_SERVER)
        (task / "environment" / "start-mcp").write_text(START_MCP)
        (task / "solution" / "solve.sh").write_text(
            "#!/bin/sh\nset -eu\ncat > /app/answer.json <<'EOF'\n" + json.dumps(spec["answer"]) + "\nEOF\n"
        )
        (task / "tests" / "test.sh").write_text("#!/bin/sh\nset -eu\nrewardkit /tests\n")
        (task / "tests" / "outcome" / "check.py").write_text(
            OUTCOME_CHECK.format(expected=json.dumps(spec["answer"], indent=2))
        )
        expected_tools = [f"mcp__costco__{tool}" for tool in spec["tools"]]
        (task / "tests" / "process" / "check.py").write_text(PROCESS_CHECK.format(tools=json.dumps(expected_tools)))
        for executable in (
            task / "environment" / "start-mcp",
            task / "solution" / "solve.sh",
            task / "tests" / "test.sh",
        ):
            executable.chmod(0o755)


if __name__ == "__main__":
    main()
