PRODUCT = {
    "tcin": "88888888",
    "item": {
        "product_description": {
            "title": "Good & Gather Organic Jasmine Rice - 32oz",
            "downstream_description": "Long grain jasmine rice.",
            "bullet_descriptions": ["Organic", "32 ounces"],
        },
        "primary_brand": {"name": "Good & Gather"},
    },
    "price": {
        "current_retail": 4.99,
        "reg_retail": 5.49,
        "formatted_current_price": "$4.99",
        "formatted_current_price_type": "sale",
    },
    "enrichment": {
        "buy_url": "https://www.target.com/p/-/A-88888888",
        "images": {"primary_image_url": "https://target.scene7.com/example"},
    },
    "ratings_and_reviews": {"statistics": {"rating": {"average": 4.7, "count": 120}}},
}

SEARCH = {
    "search_response": {"metadata": {"total_results": 1, "keyword": "rice"}},
    "products": [PRODUCT],
}

LOCATION = {
    "location_id": "2766",
    "distance": 1.8,
    "location_available_to_promise_quantity": 7,
    "order_pickup": {"availability_status": "IN_STOCK", "pickup_date": "2026-09-07", "guest_pick_sla": 120},
    "curbside": {"availability_status": "IN_STOCK"},
    "in_store_only": {"availability_status": "IN_STOCK"},
    "store": {
        "store_id": "2766",
        "location_name": "San Francisco Central",
        "mailing_address": {
            "address_line1": "789 Mission St",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94103",
        },
    },
}
