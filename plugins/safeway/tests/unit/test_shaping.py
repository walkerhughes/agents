import pytest

from src import shaping
from tests.fixtures import MILK, STORE_ADDRESS, STORE_RESOLVER

pytestmark = pytest.mark.unit


def test_product_keeps_trip_planning_fields() -> None:
    result = shaping.product(MILK)
    assert result["product_id"] == "136010013"
    assert result["name"] == "Lucerne Milk Whole - Half Gallon"
    assert result["price"] == 3.99
    assert result["base_price"] == 4.49
    assert result["aisle_location"] == "Aisle 16"
    assert result["inventory_available"] is True


def test_store_keeps_fulfillment_and_address_fields() -> None:
    item = {
        "resolver": STORE_RESOLVER["pickup"]["stores"][0],
        "address": STORE_ADDRESS["storeAddressModel"],
    }
    result = shaping.store(item)
    assert result["store_id"] == "1507"
    assert result["name"] == "Safeway - 2020 Market St"
    assert result["address"] == "2020 Market St, San Francisco CA 94114"
    assert result["pickup"] is True
    assert result["snap_eligible"] is True


def test_product_url_uses_stable_product_id() -> None:
    result = shaping.product(MILK)
    assert result["url"].endswith(".136010013.html")


def test_decimal_price_does_not_treat_missing_as_zero() -> None:
    assert shaping.decimal_price({"price": "3.99"}) is not None
    assert shaping.decimal_price({"price": None}) is None
    assert shaping.decimal_price({"price": "not-a-price"}) is None
