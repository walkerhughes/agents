#!/usr/bin/env python3
"""Deterministic local stand-in for Target's public website endpoints."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RICE = {
    "tcin": "88888888",
    "item": {
        "product_description": {
            "title": "Good & Gather Organic Jasmine Rice - 32oz",
            "downstream_description": "Organic long grain jasmine rice.",
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
    "enrichment": {"buy_url": "https://www.target.com/p/-/A-88888888", "images": {}},
    "ratings_and_reviews": {"statistics": {"rating": {"average": 4.7, "count": 120}}},
}
BEANS = {
    "tcin": "77777777",
    "item": {
        "product_description": {
            "title": "Good & Gather Black Beans - 15oz",
            "downstream_description": "Canned black beans.",
            "bullet_descriptions": ["15 ounces"],
        },
        "primary_brand": {"name": "Good & Gather"},
    },
    "price": {
        "current_retail": 1.99,
        "reg_retail": 1.99,
        "formatted_current_price": "$1.99",
        "formatted_current_price_type": "reg",
    },
    "enrichment": {"buy_url": "https://www.target.com/p/-/A-77777777", "images": {}},
    "ratings_and_reviews": {"statistics": {"rating": {"average": 4.6, "count": 80}}},
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


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/health":
            self._send({"ok": True})
            return
        if path == "/search":
            item = BEANS if "bean" in query.get("keyword", [""])[0].lower() else RICE
            self._send(
                {
                    "data": {
                        "search": {
                            "search_response": {"metadata": {"total_results": 1}},
                            "products": [item],
                        }
                    }
                }
            )
            return
        if path == "/product":
            item = BEANS if query.get("tcin", [""])[0] == "77777777" else RICE
            self._send({"data": {"product": item}})
            return
        if path == "/availability":
            self._send({"data": {"fulfillment_fiats": {"product_id": "88888888", "locations": [LOCATION]}}})
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
