# Costco

An unofficial, read-only MCP plugin for Costco's public website. It finds nearby
warehouses, searches the catalog with warehouse context, checks published prices,
prices a draft shopping list, and guides bulk-friendly menu planning.

No Costco account or API key is required.

## What it can do

- Find nearby US warehouses from a ZIP code, city/state, or address.
- Search products for a selected warehouse and delivery postal code.
- Look up product details and Costco.com prices by item number.
- Batch-price shopping-list phrases and show alternatives.
- Build menus that account for Costco package sizes and ingredient reuse.

## Price and availability boundaries

The public product APIs provide Costco.com prices in a selected warehouse context.
Those prices can differ from walk-in warehouse prices, member-only prices, Same-Day
delivery prices, and prices shown after sign-in. Program types such as `InWarehouse`
are catalog signals, not real-time shelf counts.

Costco's Same-Day pages state that delivery prices are higher than local warehouse
prices because they include service and delivery costs. This plugin does not estimate
or reverse that markup.

## Development

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```text
make check
make coverage
```

The implementation uses undocumented website request contracts that may change. This
project is not affiliated with or endorsed by Costco Wholesale Corporation.
