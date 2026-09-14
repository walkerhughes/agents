"""Stable, compact result shaping for store and product data."""

from decimal import Decimal, InvalidOperation
from typing import Any


def product(item: dict[str, Any]) -> dict[str, Any]:
    """Keep fields useful for choosing, pricing, and cooking with a product."""
    price = item.get("retail_price")
    if not price:
        price = (((item.get("price_range") or {}).get("minimum_price") or {}).get("final_price") or {}).get("value")
    categories = [entry.get("name") for entry in item.get("category_hierarchy") or [] if entry.get("name")]
    url_key = item.get("url_key")
    out: dict[str, Any] = {
        "sku": item.get("sku"),
        "name": item.get("item_title") or item.get("name"),
        "price": str(price) if price is not None else None,
        "size": _size(item.get("sales_size"), item.get("sales_uom_description")),
        "availability": item.get("availability"),
        "categories": categories,
    }
    optional = {
        "description": item.get("item_description"),
        "characteristics": item.get("item_characteristics"),
        "country_of_origin": item.get("country_of_origin"),
        "new_product": item.get("new_product"),
        "promotion": item.get("promotion"),
        "image": item.get("primary_image"),
        "url": f"https://www.traderjoes.com/home/products/pdp/{url_key}" if url_key else None,
    }
    out.update({key: value for key, value in optional.items() if value not in (None, "", [], False)})
    return out


def _size(value: Any, unit: Any) -> str | None:
    if value in (None, ""):
        return None
    return " ".join(part for part in (str(value), str(unit or "")) if part).strip()


def store(item: dict[str, Any]) -> dict[str, Any]:
    hours = {
        day: {"open": item.get(f"{day}_open"), "close": item.get(f"{day}_close")}
        for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    }
    return {
        "store_code": str(item.get("clientkey") or item.get("remote_id") or ""),
        "name": item.get("name"),
        "address": ", ".join(
            part
            for part in (
                item.get("address1"),
                " ".join(part for part in (item.get("city"), item.get("state"), item.get("postalcode")) if part),
            )
            if part
        ),
        "distance_miles": item.get("_distance") or item.get("distance"),
        "phone": item.get("phone"),
        "alcohol": [name for name in ("beer", "wine", "liquor") if item.get(name) == "Yes"],
        "hours": hours,
        "url": item.get("website") or ((item.get("links") or [None])[0]),
    }


def decimal_price(item: dict[str, Any]) -> Decimal | None:
    try:
        value = item.get("price")
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None
