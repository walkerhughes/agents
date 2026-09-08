# Safeway

An unofficial, read-only MCP plugin for Safeway's public website data. It finds
nearby stores, searches store-scoped groceries and prices, refreshes known products,
prices draft shopping lists, and guides menu planning.

No Safeway account is required.

## What it can do

- Find pickup-capable Safeway stores from a ZIP code.
- Search products for a selected store and pickup, delivery, or in-store channel.
- Refresh a known product by Safeway product ID.
- Return current and base prices, unit prices, promotion dates, aisle details, and inventory signals.
- Price shopping-list phrases and show alternatives.

## Price and availability boundaries

The website's `price` field can represent a current shelf, member, or sale price.
The plugin also preserves `basePrice` and promotion end dates when present. A displayed
price does not prove that a user qualifies for a loyalty or digital-coupon discount.
Inventory is a point-in-time website signal and not a shelf or reservation guarantee.

## Development

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```text
make check
make coverage
```

The implementation uses undocumented browser-facing contracts that may change. This
project is not affiliated with or endorsed by Safeway or Albertsons Companies.
