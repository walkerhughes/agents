"""Stable, compact result shaping for Costco website data."""

from decimal import Decimal, InvalidOperation
from typing import Any


def _localized(values: Any) -> Any:
    if not isinstance(values, list):
        return values
    for entry in values:
        if isinstance(entry, dict) and entry.get("localeCode") == "en-US":
            return entry.get("value")
    return values[0].get("value") if values and isinstance(values[0], dict) else None


def warehouse(item: dict[str, Any]) -> dict[str, Any]:
    address = item.get("address") or {}
    services = [_localized(service.get("name")) for service in item.get("services") or []]
    return {
        "warehouse_number": str(item.get("salesLocationId") or ""),
        "name": _localized(item.get("name")),
        "address": ", ".join(
            str(part)
            for part in (
                address.get("line1"),
                " ".join(
                    str(part)
                    for part in (address.get("city"), address.get("territory"), address.get("postalCode"))
                    if part
                ),
            )
            if part
        ),
        "postal_code": address.get("postalCode"),
        "state": address.get("territory"),
        "latitude": address.get("latitude"),
        "longitude": address.get("longitude"),
        "distance": item.get("distance"),
        "phone": item.get("phone"),
        "services": [service for service in services if service],
    }


def search_document(item: dict[str, Any]) -> dict[str, Any]:
    product = item.get("product") or {}
    attributes = product.get("attributes") or {}
    return {
        "item_number": str(item.get("id") or ""),
        "title": product.get("title"),
        "brands": product.get("brands") or [],
        "categories": product.get("categories") or [],
        "image": ((attributes.get("primary_image") or {}).get("text") or [None])[0],
    }


def product(item: dict[str, Any], search: dict[str, Any] | None = None) -> dict[str, Any]:
    description = item.get("description") or {}
    price_data = item.get("priceData") or {}
    additional = item.get("additionalFieldData") or {}
    attributes: dict[str, list[str]] = {}
    for attribute in item.get("attributes") or []:
        key = str(attribute.get("key") or "")
        if key:
            attributes.setdefault(key, []).append(str(attribute.get("value") or ""))
    programs = item.get("programTypes") or []
    if isinstance(programs, str):
        programs = [value.strip() for value in programs.split(",") if value.strip()]
    price = price_data.get("price")
    public_price = None if str(price or "") in ("", "0", "0.0", "0.00000") else str(price)
    brands = attributes.get("Brand") or []
    return {
        "item_number": str(item.get("itemNumber") or (search or {}).get("item_number") or ""),
        "name": description.get("shortDescription") or (search or {}).get("title"),
        "brand": brands[0] if brands else None,
        "price": public_price,
        "list_price": None
        if str(price_data.get("listPrice") or "") in ("", "-1", "-1.00000")
        else str(price_data["listPrice"]),
        "buyable": item.get("buyable") in (1, True),
        "in_warehouse": "InWarehouse" in programs,
        "program_types": programs,
        "rating": additional.get("rating"),
        "rating_count": additional.get("numberOfRating"),
        "description": description.get("marketingStatement") or description.get("longDescription"),
        "attributes": attributes,
        "price_note": "Price is hidden until cart or sign-in." if public_price is None else None,
        "url": f"https://www.costco.com/.product.{item.get('itemNumber')}.html",
    }


def decimal_price(item: dict[str, Any] | None) -> Decimal | None:
    if not item:
        return None
    try:
        value = item.get("price")
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None
