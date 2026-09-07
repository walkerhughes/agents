#!/usr/bin/env python3
"""Deterministic local stand-in for the two public website endpoints."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

COFFEE = {
    "sku": "081522",
    "item_title": "Costa Rica Coffee",
    "retail_price": "9.99",
    "sales_size": 12,
    "sales_uom_description": "Oz",
    "availability": "1",
    "url_key": "costa-rica-coffee-081522",
    "category_hierarchy": [{"id": 194, "name": "Coffee & Tea"}],
}
OAT = {
    "sku": "099001",
    "item_title": "Non-Dairy Oat Beverage",
    "retail_price": "2.49",
    "sales_size": 32,
    "sales_uom_description": "Fl Oz",
    "availability": "1",
    "url_key": "non-dairy-oat-beverage-099001",
    "category_hierarchy": [{"id": 183, "name": "Non-Dairy Beverages"}],
}
STORE = {
    "clientkey": "200",
    "name": "San Francisco - Nob Hill (200)",
    "address1": "1095 Hyde St",
    "city": "San Francisco",
    "state": "CA",
    "postalcode": "94109",
    "_distance": "0.24",
    "phone": "415-292-7665",
    "website": "https://locations.traderjoes.com/ca/san-francisco/200/",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/health":
            self._send({"ok": True})
            return
        self.send_error(404)

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(size) or b"{}")
        if self.path == "/locator":
            self._send({"code": 1, "response": {"collection": [STORE]}})
            return
        if self.path == "/graphql":
            variables = request.get("variables") or {}
            search = str(variables.get("search") or "").lower()
            sku = str(variables.get("sku") or "")
            if sku:
                items = [COFFEE] if sku == COFFEE["sku"] else []
            elif "oat" in search:
                items = [OAT]
            elif "coffee" in search:
                items = [COFFEE]
            else:
                items = []
            self._send(
                {
                    "data": {
                        "products": {
                            "items": items,
                            "total_count": len(items),
                            "page_info": {
                                "current_page": 1,
                                "page_size": len(items),
                                "total_pages": 1,
                            },
                        }
                    }
                }
            )
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
