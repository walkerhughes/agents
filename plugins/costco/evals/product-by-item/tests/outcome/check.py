"""Compare the submitted answer with deterministic fixture truth."""

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from rewardkit import criterion

EXPECTED = json.loads(
    r"""{
  "name": "Kirkland Signature Organic Quinoa, 4.5 lb",
  "price": 18.99
}"""
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
