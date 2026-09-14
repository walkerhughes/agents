"""Compact stable views over Target Redsky responses."""

from decimal import Decimal, InvalidOperation
from typing import Any


def _price(item: dict[str, Any]) -> dict[str, Any]:
    price = item.get("price") or {}
    if not price and item.get("children"):
        price = (item["children"][0] or {}).get("price") or {}
    return price


def product(item: dict[str, Any]) -> dict[str, Any]:
    details = item.get("item") or {}
    description = details.get("product_description") or {}
    enrichment = item.get("enrichment") or {}
    images = enrichment.get("images") or {}
    brand = details.get("primary_brand") or item.get("primary_brand") or {}
    price = _price(item)
    ratings = ((item.get("ratings_and_reviews") or {}).get("statistics") or {}).get("rating") or {}
    return {
        "tcin": str(item.get("tcin") or ""),
        "name": description.get("title"),
        "brand": brand.get("name") if isinstance(brand, dict) else brand,
        "current_price": price.get("current_retail"),
        "regular_price": price.get("reg_retail"),
        "formatted_price": price.get("formatted_current_price"),
        "price_type": price.get("formatted_current_price_type"),
        "promotion": price.get("promotion_description"),
        "rating": ratings.get("average"),
        "rating_count": ratings.get("count"),
        "description": description.get("downstream_description"),
        "bullets": description.get("bullet_descriptions") or [],
        "image": images.get("primary_image_url"),
        "url": enrichment.get("buy_url") or f"https://www.target.com/p/-/A-{item.get('tcin')}",
    }


def store_availability(item: dict[str, Any]) -> dict[str, Any]:
    store = item.get("store") or {}
    address = store.get("mailing_address") or {}
    pickup = item.get("order_pickup") or {}
    curbside = item.get("curbside") or {}
    in_store = item.get("in_store_only") or {}
    return {
        "store_id": str(store.get("store_id") or item.get("location_id") or ""),
        "name": store.get("location_name"),
        "address": ", ".join(
            str(value)
            for value in (
                address.get("address_line1"),
                " ".join(
                    str(value)
                    for value in (address.get("city"), address.get("state"), address.get("postal_code"))
                    if value
                ),
            )
            if value
        ),
        "distance_miles": item.get("distance"),
        "available_quantity": item.get("location_available_to_promise_quantity"),
        "pickup_status": pickup.get("availability_status"),
        "pickup_date": pickup.get("pickup_date"),
        "pickup_sla_minutes": pickup.get("guest_pick_sla"),
        "drive_up_status": curbside.get("availability_status"),
        "in_store_status": in_store.get("availability_status"),
    }


def decimal_price(item: dict[str, Any] | None) -> Decimal | None:
    if not item:
        return None
    try:
        value = item.get("current_price")
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None
