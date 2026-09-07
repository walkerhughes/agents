from decimal import Decimal

import pytest

from src import shaping
from tests.fixtures import PRODUCT_ITEM, STORE_ITEM

pytestmark = pytest.mark.unit


def test_product_keeps_price_size_categories_and_url() -> None:
    result = shaping.product(PRODUCT_ITEM)

    assert result["name"] == "Costa Rica Coffee"
    assert result["price"] == "9.99"
    assert result["size"] == "12 Oz"
    assert result["categories"][-1] == "Coffee & Tea"
    assert result["url"].endswith("costa-rica-coffee-081522")
    assert shaping.decimal_price(result) == Decimal("9.99")


def test_product_falls_back_to_structured_price() -> None:
    item = {"item_title": "Milk", "price_range": {"minimum_price": {"final_price": {"value": 4.5}}}}
    assert shaping.product(item)["price"] == "4.5"


def test_store_keeps_code_and_hours() -> None:
    result = shaping.store(STORE_ITEM)

    assert result["store_code"] == "200"
    assert result["distance_miles"] == 0.38
    assert result["hours"]["monday"] == {"open": "09:00", "close": "21:00"}
    assert result["alcohol"] == ["beer", "wine", "liquor"]


def test_decimal_price_returns_none_for_bad_value() -> None:
    assert shaping.decimal_price({"price": "market"}) is None
