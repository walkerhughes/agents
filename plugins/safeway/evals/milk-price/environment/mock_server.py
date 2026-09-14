#!/usr/bin/env python3
"""Deterministic local stand-in for Safeway's public website endpoints."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STORE = {
    "locationId": "1507",
    "locationZipcode": "94114",
    "ecomStore": {
        "isPickupStore": True,
        "isDeliveryStore": True,
        "storeFeatures": {"isSNAP2Eligible": True},
    },
}
ADDRESS = {
    "address": {
        "line1": "2020 Market St",
        "city": "San Francisco",
        "state": "CA",
        "zipcode": "94114",
    },
    "storeRewards": {"storeId": "1507", "storeName": "Market Street"},
    "localPage": "https://local.safeway.com/safeway/ca/san-francisco/2020-market-st.html",
}
MILK = {
    "pid": "136010013",
    "upc": "0021130100130",
    "name": "Lucerne Milk Whole - Half Gallon",
    "storeId": "1507",
    "price": 3.99,
    "basePrice": 4.49,
    "pricePer": "$0.06/Fl Oz",
    "basePricePer": "$0.07/Fl Oz",
    "promoEndDate": "2026-09-08",
    "inventoryAvailable": "1",
    "departmentName": "Dairy, Eggs & Cheese",
    "aisleName": "Milk & Cream",
    "aisleLocation": "Aisle 16",
    "dispItemSizeQty": "64",
    "dispItemPackageQty": "1",
    "dispUnitOfMeasure": "Fl Oz",
    "snapEligible": True,
    "channelEligibility": {"pickup": True, "delivery": True},
    "channelInventory": {"pickup": "1", "delivery": "1"},
}
BEANS = {
    **MILK,
    "pid": "960077184",
    "upc": "0002113003000",
    "name": "Signature Select Black Beans - 15 Oz",
    "price": 1.99,
    "basePrice": 1.99,
    "departmentName": "Canned Goods & Soups",
    "aisleName": "Canned Beans",
    "aisleLocation": "Aisle 5",
    "dispItemSizeQty": "15",
    "dispUnitOfMeasure": "Oz",
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
        if path == "/stores":
            self._send({"pickup": {"stores": [STORE]}, "instore": {"stores": []}}, 206)
            return
        if path == "/address":
            self._send({"storeAddressModel": ADDRESS})
            return
        if path == "/search":
            phrase = query.get("q", [""])[0].lower()
            item = BEANS if "bean" in phrase or phrase == BEANS["pid"] else MILK
            self._send({"response": {"numFound": 1, "docs": [item]}})
            return
        self.send_error(404)

    def _send(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


ThreadingHTTPServer(("127.0.0.1", 8091), Handler).serve_forever()
