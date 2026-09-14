import pytest

from src import shaping
from tests.fixtures import LOCATION, PRODUCT

pytestmark = pytest.mark.unit


def test_product_keeps_identity_price_brand_and_rating() -> None:
    result = shaping.product(PRODUCT)
    assert result["tcin"] == "88888888"
    assert result["name"] == "Good & Gather Organic Jasmine Rice - 32oz"
    assert result["brand"] == "Good & Gather"
    assert result["current_price"] == 4.99
    assert result["regular_price"] == 5.49
    assert result["rating"] == 4.7


def test_child_price_is_used_for_variant_parent() -> None:
    result = shaping.product({**PRODUCT, "price": {}, "children": [{"price": {"current_retail": 3.25}}]})
    assert result["current_price"] == 3.25


def test_store_availability_keeps_trip_planning_fields() -> None:
    result = shaping.store_availability(LOCATION)
    assert result["store_id"] == "2766"
    assert result["name"] == "San Francisco Central"
    assert result["pickup_status"] == "IN_STOCK"
    assert result["distance_miles"] == 1.8
    assert result["available_quantity"] == 7


def test_decimal_price_does_not_treat_missing_as_zero() -> None:
    assert shaping.decimal_price({"current_price": "4.99"}) is not None
    assert shaping.decimal_price({"current_price": None}) is None
    assert shaping.decimal_price({"current_price": "not-a-price"}) is None
