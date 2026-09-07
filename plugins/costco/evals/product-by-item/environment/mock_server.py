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
            item = RICE if "rice" in query else QUINOA
            self._send(
                {
                    "searchResult": {
                        "totalCount": 1,
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
                        ],
                    }
                }
            )
            return
        if self.path == "/graphql":
            query = str(request.get("query") or "")
            items = []
            if QUINOA["itemNumber"] in query:
                items.append(QUINOA)
            if RICE["itemNumber"] in query:
                items.append(RICE)
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
