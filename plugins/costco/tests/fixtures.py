SEARCH_RESULT = {
    "totalCount": 1,
    "results": [
        {
            "id": "1234567",
            "product": {
                "title": "Kirkland Signature Organic Quinoa",
                "brands": ["Kirkland Signature"],
                "categories": ["Grocery"],
                "attributes": {"primary_image": {"text": ["https://images.test/quinoa.jpg"]}},
            },
        }
    ],
}

PRODUCT_ITEM = {
    "itemNumber": "1234567",
    "buyable": 1,
    "programTypes": "InWarehouse,ShipIt",
    "priceData": {"price": "18.99000", "listPrice": "21.99000"},
    "attributes": [
        {"key": "Brand", "value": "Kirkland Signature", "type": "string"},
        {"key": "Package Quantity", "value": "4.5 lb", "type": "string"},
    ],
    "description": {
        "shortDescription": "Kirkland Signature Organic Quinoa, 4.5 lb",
        "longDescription": "USDA organic white quinoa.",
        "marketingStatement": "A versatile pantry staple.",
    },
    "additionalFieldData": {"rating": "4.8", "numberOfRating": 321},
}

WAREHOUSE_ITEM = {
    "salesLocationId": 144,
    "name": [{"localeCode": "en-US", "value": "South San Francisco"}],
    "phone": "650-872-2021",
    "distance": 8.2,
    "address": {
        "line1": "451 S Airport Blvd",
        "city": "South San Francisco",
        "territory": "CA",
        "postalCode": "94080",
        "latitude": 37.644,
        "longitude": -122.405,
    },
    "services": [
        {"name": [{"localeCode": "en-US", "value": "Gas Station"}]},
        {"name": [{"localeCode": "en-US", "value": "Pharmacy"}]},
    ],
}
