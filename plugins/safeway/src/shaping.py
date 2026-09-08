"""Compact stable views over Safeway website responses."""

from decimal import Decimal, InvalidOperation
from typing import Any


def store(item: dict[str, Any]) -> dict[str, Any]:
    resolver = item.get("resolver") or {}
    model = item.get("address") or {}
    address = model.get("address") or {}
    rewards = model.get("storeRewards") or {}
    line = address.get("line1")
    return {
        "store_id": str(resolver.get("locationId") or rewards.get("storeId") or ""),
        "name": f"Safeway - {line}" if line else rewards.get("storeName"),
        "address": ", ".join(
            str(value)
            for value in (
                line,
                " ".join(
                    str(value) for value in (address.get("city"), address.get("state"), address.get("zipcode")) if value
                ),
            )
            if value
        ),
        "postal_code": address.get("zipcode") or resolver.get("locationZipcode"),
        "pickup": bool((resolver.get("ecomStore") or {}).get("isPickupStore")),
        "delivery": bool((resolver.get("ecomStore") or {}).get("isDeliveryStore")),
        "snap_eligible": bool((resolver.get("ecomStore") or {}).get("storeFeatures", {}).get("isSNAP2Eligible")),
        "local_page": model.get("localPage"),
    }


def product(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_id": str(item.get("pid") or item.get("id") or ""),
        "upc": item.get("upc"),
        "name": item.get("name"),
        "store_id": str(item.get("storeId") or ""),
        "price": item.get("price"),
        "base_price": item.get("basePrice"),
        "unit_price": item.get("pricePer"),
        "base_unit_price": item.get("basePricePer"),
        "promo_end_date": item.get("promoEndDate"),
        "inventory_available": str(item.get("inventoryAvailable") or "0") == "1",
        "department": item.get("departmentName"),
        "aisle": item.get("aisleName"),
        "aisle_location": item.get("aisleLocation"),
        "size": item.get("dispItemSizeQty"),
        "package_quantity": item.get("dispItemPackageQty"),
        "unit_of_measure": item.get("dispUnitOfMeasure"),
        "snap_eligible": item.get("snapEligible"),
        "channel_eligibility": item.get("channelEligibility") or {},
        "channel_inventory": item.get("channelInventory") or {},
        "image": item.get("imageUrl"),
        "url": f"https://www.safeway.com/shop/product-details.{item.get('pid')}.html",
    }


def decimal_price(item: dict[str, Any] | None) -> Decimal | None:
    if not item:
        return None
    try:
        value = item.get("price")
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None
