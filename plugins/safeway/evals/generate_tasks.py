#!/usr/bin/env python3
"""Generate the Safeway Harbor tasks from one compact specification."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TASKS = {
    "nearest-store": {
        "description": "Find the nearest Safeway store for a ZIP code.",
        "instruction": (
            "Find the nearest Safeway store for ZIP code 94109. Report its store ID, "
            "full store name, street address, and whether pickup is supported."
        ),
        "tool": "find_stores",
        "answer": {
            "store_id": "1507",
            "name": "Safeway - 2020 Market St",
            "address": "2020 Market St, San Francisco CA 94114",
            "pickup": True,
        },
    },
    "milk-price": {
        "description": "Find the store-scoped Safeway price of milk.",
        "instruction": (
            "For Safeway store 1507 using pickup, search for whole milk. Report the "
            "selected product name, product ID, current public price as a number, and aisle."
        ),
        "tool": "search_products",
        "answer": {
            "name": "Lucerne Milk Whole - Half Gallon",
            "product_id": "136010013",
            "price": 3.99,
            "aisle": "Milk & Cream",
        },
    },
    "product-by-id": {
        "description": "Refresh a Safeway product by ID in one store context.",
        "instruction": (
            "For Safeway store 1507 using pickup, look up product ID 136010013. "
            "Report its product name, current public price as a number, base price as a "
            "number, and whether the website reports inventory available."
        ),
        "tool": "get_product",
        "answer": {
            "name": "Lucerne Milk Whole - Half Gallon",
            "price": 3.99,
            "base_price": 4.49,
            "inventory_available": True,
        },
    },
    "shopping-list": {
        "description": "Price a two-item shopping list for one Safeway store.",
        "instruction": (
            "For Safeway store 1507 using pickup, price a list containing one half gallon "
            "of whole milk and one can of black beans. Report the selected product names "
            "and combined public Safeway total as a number."
        ),
        "tool": "price_shopping_list",
        "answer": {
            "items": [
                "Lucerne Milk Whole - Half Gallon",
                "Signature Select Black Beans - 15 Oz",
            ],
            "estimated_total": 5.98,
        },
    },
}

TASK_TOML = """schema_version = "1.1"

[task]
name = "safeway/{name}"
description = {description}
authors = []
keywords = ["mcp", "safeway", "eval"]

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
name = "safeway"
transport = "stdio"
command = "/opt/eval/start-mcp"
args = []
"""

INSTRUCTION = """# Task

{instruction}

Use the Safeway integration tools available in this environment. All store and product
data must come through those tools, not shell commands, local files, direct
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
    && cd /opt/claude/plugins/safeway \\
    && uv sync --frozen --no-dev

RUN python -m venv /opt/rewardkit \\
    && /opt/rewardkit/bin/pip install --no-cache-dir "harbor-rewardkit==0.1.*" \\
    && ln -s /opt/rewardkit/bin/rewardkit /usr/local/bin/rewardkit

COPY mock_server.py start-mcp /opt/eval/
RUN chmod +x /opt/eval/start-mcp

WORKDIR /app
ENV SAFEWAY_SEARCH_URL=http://127.0.0.1:8091/search \\
    SAFEWAY_STORES_URL=http://127.0.0.1:8091/stores \\
    SAFEWAY_ADDRESS_URL=http://127.0.0.1:8091/address
"""

START_MCP = """#!/bin/sh
set -eu

python /opt/eval/mock_server.py >/tmp/safeway-mock.log 2>&1 &
mock_pid=$!
trap 'kill "$mock_pid" 2>/dev/null || true' EXIT INT TERM

for attempt in $(seq 1 50); do
    if curl -sf http://127.0.0.1:8091/health >/dev/null; then
        cd /opt/claude/plugins/safeway
        exec uv run --no-dev python -m src.server
    fi
    sleep 0.1
done

cat /tmp/safeway-mock.log >&2
exit 1
"""

MOCK_SERVER = r'''#!/usr/bin/env python3
"""Deterministic local stand-in for Safeway's public website endpoints."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STORE = {
    "locationId": "1507",
    "locationZipcode": "94114",
    "ecomStore": {
        "isPickupStore": True,
        "isDeliveryStore": True,
        "storeFeatures": {"isSNAP2Eligible": True},
    },
}
ADDRESS = {
    "address": {
        "line1": "2020 Market St",
        "city": "San Francisco",
        "state": "CA",
        "zipcode": "94114",
    },
    "storeRewards": {"storeId": "1507", "storeName": "Market Street"},
    "localPage": "https://local.safeway.com/safeway/ca/san-francisco/2020-market-st.html",
}
MILK = {
    "pid": "136010013",
    "upc": "0021130100130",
    "name": "Lucerne Milk Whole - Half Gallon",
    "storeId": "1507",
    "price": 3.99,
    "basePrice": 4.49,
    "pricePer": "$0.06/Fl Oz",
    "basePricePer": "$0.07/Fl Oz",
    "promoEndDate": "2026-09-08",
    "inventoryAvailable": "1",
    "departmentName": "Dairy, Eggs & Cheese",
    "aisleName": "Milk & Cream",
    "aisleLocation": "Aisle 16",
    "dispItemSizeQty": "64",
    "dispItemPackageQty": "1",
    "dispUnitOfMeasure": "Fl Oz",
    "snapEligible": True,
    "channelEligibility": {"pickup": True, "delivery": True},
    "channelInventory": {"pickup": "1", "delivery": "1"},
}
BEANS = {
    **MILK,
    "pid": "960077184",
    "upc": "0002113003000",
    "name": "Signature Select Black Beans - 15 Oz",
    "price": 1.99,
    "basePrice": 1.99,
    "departmentName": "Canned Goods & Soups",
    "aisleName": "Canned Beans",
    "aisleLocation": "Aisle 5",
    "dispItemSizeQty": "15",
    "dispUnitOfMeasure": "Oz",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/health":
            self._send({"ok": True})
            return
        if path == "/stores":
            self._send({"pickup": {"stores": [STORE]}, "instore": {"stores": []}}, 206)
            return
        if path == "/address":
            self._send({"storeAddressModel": ADDRESS})
            return
        if path == "/search":
            phrase = query.get("q", [""])[0].lower()
            item = BEANS if "bean" in phrase or phrase == BEANS["pid"] else MILK
            self._send({"response": {"numFound": 1, "docs": [item]}})
            return
        self.send_error(404)

    def _send(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


ThreadingHTTPServer(("127.0.0.1", 8091), Handler).serve_forever()
'''

PROCESS_CHECK = '''"""Verify that the answer came through the Safeway MCP server."""

import json
import re
from pathlib import Path

from rewardkit import criterion

TRAJECTORY = Path("/logs/agent/trajectory.json")
SESSIONS = Path("/logs/agent/sessions")
EXPECTED_TOOL = "mcp__safeway__{tool}"
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


@criterion(description="Agent called the expected Safeway MCP tool")
def used_mcp_tool(workspace: Path) -> bool:
    return any(str(call.get("function_name") or "") == EXPECTED_TOOL for call in _calls())


@criterion(description="Agent did not bypass the Safeway MCP server")
def no_direct_endpoint_access(workspace: Path) -> bool:
    calls = _calls()
    if not calls:
        return False
    for call in calls:
        if str(call.get("function_name") or "").startswith("mcp__safeway__"):
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


@criterion(description="Answer matches the mock catalog and store data")
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
            shape[key] = ["<item 1>", "<item 2>"]
        elif isinstance(value, bool):
            shape[key] = False
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
        (task / "tests" / "process" / "check.py").write_text(PROCESS_CHECK.format(tool=spec["tool"]))
        for executable in (
            task / "environment" / "start-mcp",
            task / "solution" / "solve.sh",
            task / "tests" / "test.sh",
        ):
            executable.chmod(0o755)


if __name__ == "__main__":
    main()
