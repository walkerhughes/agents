from decimal import Decimal

import pytest

from src import shaping
from tests.fixtures import PRODUCT_ITEM, SEARCH_RESULT, WAREHOUSE_ITEM

pytestmark = pytest.mark.unit


def test_warehouse_keeps_selection_values_and_services() -> None:
    result = shaping.warehouse(WAREHOUSE_ITEM)

    assert result["warehouse_number"] == "144"
    assert result["postal_code"] == "94080"
    assert result["services"] == ["Gas Station", "Pharmacy"]


def test_search_document_keeps_item_identity() -> None:
    result = shaping.search_document(SEARCH_RESULT["results"][0])

    assert result["item_number"] == "1234567"
    assert result["image"].endswith("quinoa.jpg")


def test_product_keeps_price_programs_and_bulk_attributes() -> None:
    result = shaping.product(PRODUCT_ITEM)

    assert result["price"] == "18.99000"
    assert result["in_warehouse"] is True
    assert result["attributes"]["Package Quantity"] == ["4.5 lb"]
    assert shaping.decimal_price(result) == Decimal("18.99000")


def test_hidden_price_is_not_reported_as_free() -> None:
    item = {**PRODUCT_ITEM, "priceData": {"price": "0", "listPrice": "-1.00000"}}
    result = shaping.product(item)

    assert result["price"] is None
    assert "hidden" in result["price_note"]
    assert shaping.decimal_price(result) is None
