STORE_RESOLVER = {
    "pickup": {
        "stores": [
            {
                "locationId": "1507",
                "locationZipcode": "94114",
                "ecomStore": {
                    "isPickupStore": True,
                    "isDeliveryStore": True,
                    "storeFeatures": {"isSNAP2Eligible": True},
                },
            }
        ]
    },
    "instore": {"stores": []},
}

STORE_ADDRESS = {
    "storeAddressModel": {
        "address": {
            "line1": "2020 Market St",
            "city": "San Francisco",
            "state": "CA",
            "zipcode": "94114",
        },
        "storeRewards": {"storeId": "1507", "storeName": "Market Street"},
        "localPage": "https://local.safeway.com/safeway/ca/san-francisco/2020-market-st.html",
    }
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
    "imageUrl": "https://images.albertsons-media.com/is/image/ABS/example",
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

SEARCH = {"response": {"numFound": 1, "docs": [MILK]}}
