#!/usr/bin/env python3
"""Deterministic local stand-in for Costco's public website endpoints."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

QUINOA = {
    "itemNumber": "1234567",
    "buyable": 1,
    "programTypes": "InWarehouse,ShipIt",
    "priceData": {"price": "18.99", "listPrice": "21.99"},
    "attributes": [
        {"key": "Brand", "value": "Kirkland Signature", "type": "string"},
        {"key": "Package Quantity", "value": "4.5 lb", "type": "string"},
    ],
    "description": {
        "shortDescription": "Kirkland Signature Organic Quinoa, 4.5 lb",
        "longDescription": "USDA organic white quinoa.",
    },
    "additionalFieldData": {"rating": "4.8", "numberOfRating": 321},
}
RICE = {
    "itemNumber": "7654321",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "12.49", "listPrice": "-1.00000"},
    "attributes": [
        {"key": "Brand", "value": "Kirkland Signature", "type": "string"},
        {"key": "Package Quantity", "value": "25 lb", "type": "string"},
    ],
    "description": {
        "shortDescription": "Kirkland Signature Jasmine Rice, 25 lb",
        "longDescription": "Long-grain jasmine rice.",
    },
    "additionalFieldData": {"rating": "4.7", "numberOfRating": 212},
}
CHICKEN = {
    "itemNumber": "1000001",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "4.99", "listPrice": "-1.00000"},
    "attributes": [{"key": "Package Quantity", "value": "3 lb", "type": "string"}],
    "description": {
        "shortDescription": "Kirkland Signature Rotisserie Chicken, 3 lb",
        "longDescription": "Prepared rotisserie chicken.",
    },
    "additionalFieldData": {},
}
TORTILLAS = {
    "itemNumber": "1000002",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "7.99", "listPrice": "-1.00000"},
    "attributes": [{"key": "Package Quantity", "value": "40 ct", "type": "string"}],
    "description": {
        "shortDescription": "Organic Flour Tortillas, 40 ct",
        "longDescription": "Organic flour tortillas.",
    },
    "additionalFieldData": {},
}
CHEESE = {
    "itemNumber": "1000003",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "11.49", "listPrice": "-1.00000"},
    "attributes": [{"key": "Package Quantity", "value": "2.5 lb", "type": "string"}],
    "description": {
        "shortDescription": "Mexican Style Blend Shredded Cheese, 2.5 lb",
        "longDescription": "Shredded Mexican-style cheese blend.",
    },
    "additionalFieldData": {},
}
SALAD = {
    "itemNumber": "1000004",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "6.99", "listPrice": "-1.00000"},
    "attributes": [{"key": "Package Quantity", "value": "24 oz", "type": "string"}],
    "description": {
        "shortDescription": "Organic Caesar Salad Kit, 24 oz",
        "longDescription": "Caesar salad kit.",
    },
    "additionalFieldData": {},
}
PAPER_TOWELS = {
    "itemNumber": "1000005",
    "buyable": 1,
    "programTypes": "InWarehouse,ShipIt",
    "priceData": {"price": "23.99", "listPrice": "27.99"},
    "attributes": [{"key": "Package Quantity", "value": "12 rolls", "type": "string"}],
    "description": {
        "shortDescription": "Kirkland Signature Paper Towels, 12 rolls",
        "longDescription": "Two-ply paper towels.",
    },
    "additionalFieldData": {},
}
AVOCADOS = {
    "itemNumber": "1000006",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "0.00000", "listPrice": "-1.00000"},
    "attributes": [{"key": "Package Quantity", "value": "6 ct", "type": "string"}],
    "description": {
        "shortDescription": "Hass Avocados, 6 ct",
        "longDescription": "Fresh Hass avocados.",
    },
    "additionalFieldData": {},
}
OLIVE_OIL_ORGANIC = {
    "itemNumber": "2468100",
    "buyable": 1,
    "programTypes": "InWarehouse,ShipIt",
    "priceData": {"price": "31.99", "listPrice": "34.99"},
    "attributes": [{"key": "Package Quantity", "value": "2 L", "type": "string"}],
    "description": {
        "shortDescription": "Kirkland Signature Organic Extra Virgin Olive Oil, 2 L",
        "longDescription": "Organic extra virgin olive oil.",
    },
    "additionalFieldData": {},
}
OLIVE_OIL = {
    "itemNumber": "2468101",
    "buyable": 1,
    "programTypes": "InWarehouse",
    "priceData": {"price": "24.99", "listPrice": "29.99"},
    "attributes": [{"key": "Package Quantity", "value": "2 L", "type": "string"}],
    "description": {
        "shortDescription": "Kirkland Signature Extra Virgin Olive Oil, 2 L",
        "longDescription": "Extra virgin olive oil.",
    },
    "additionalFieldData": {},
}
PRODUCTS = [
    QUINOA,
    RICE,
    CHICKEN,
    TORTILLAS,
    CHEESE,
    SALAD,
    PAPER_TOWELS,
    AVOCADOS,
    OLIVE_OIL_ORGANIC,
    OLIVE_OIL,
]
WAREHOUSE = {
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
    "services": [],
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._send({"ok": True})
            return
        if path == "/geocode":
            self._send([{"lat": "37.7749", "lon": "-122.4194"}])
            return
        if path == "/warehouses":
            self._send({"salesLocations": [WAREHOUSE]})
            return
        self.send_error(404)

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(size) or b"{}")
        if self.path == "/search":
            query = str(request.get("query") or "").lower()
            if "rice" in query:
                matches = [RICE]
            elif "chicken" in query:
                matches = [CHICKEN]
            elif "tortilla" in query:
                matches = [TORTILLAS]
            elif "cheese" in query:
                matches = [CHEESE]
            elif "salad" in query:
                matches = [SALAD]
            elif "paper towel" in query:
                matches = [PAPER_TOWELS]
            elif "avocado" in query:
                matches = [AVOCADOS]
            elif "olive oil" in query:
                matches = [OLIVE_OIL_ORGANIC, OLIVE_OIL]
            else:
                matches = [QUINOA]
            self._send(
                {
                    "searchResult": {
                        "totalCount": len(matches),
                        "results": [
                            {
                                "id": item["itemNumber"],
                                "product": {
                                    "title": item["description"]["shortDescription"],
                                    "brands": ["Kirkland Signature"],
                                    "categories": ["Grocery"],
                                    "attributes": {},
                                },
                            }
                            for item in matches
                        ],
                    }
                }
            )
            return
        if self.path == "/graphql":
            query = str(request.get("query") or "")
            items = [item for item in PRODUCTS if item["itemNumber"] in query]
            self._send({"data": {"products": {"catalogData": items}}})
            return
        self.send_error(404)

    def _send(self, payload):
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


ThreadingHTTPServer(("127.0.0.1", 8091), Handler).serve_forever()
