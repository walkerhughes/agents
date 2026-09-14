"""Compare the submitted answer with deterministic fixture truth."""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from rewardkit import criterion

EXPECTED = json.loads(
    r"""{
  "name": "Costa Rica Coffee",
  "size": "12 Oz",
  "price": 9.99
}"""
)


def _matches(actual, expected):
    if isinstance(expected, float):
        try:
            return Decimal(str(actual)) == Decimal(str(expected))
        except (InvalidOperation, TypeError, ValueError):
            return False
    if isinstance(expected, list):
        if isinstance(actual, str) and all(isinstance(item, str) for item in expected):
            actual = [item.strip() for item in actual.split(",")]
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
