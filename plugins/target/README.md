# Target

An unofficial, read-only MCP plugin for Target's public website data. It searches
products with store context, checks published prices, finds nearby stores carrying
a selected item, prices draft shopping lists, and guides menu planning.

No Target account is required.

## What it can do

- Search products using a selected Target store and ZIP code.
- Look up product details and published prices by TCIN.
- Find nearby stores and pickup signals for a selected product.
- Batch-price shopping-list phrases and show alternatives.
- Build menus and trip plans from the matched products.

## Price and availability boundaries

Prices come from Target's public website APIs for the supplied pricing-store context.
They can differ by store, fulfillment method, promotion eligibility, sign-in state,
or Target Circle offer. Availability is a point-in-time website signal and does not
reserve an item or guarantee that it will be on the shelf when you arrive.

Target's Redsky service may present an automated-traffic challenge on some networks.
The plugin reports that condition directly instead of returning stale or invented data.

## Development

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```text
make check
make coverage
```

The implementation uses undocumented website request contracts that may change. This
project is not affiliated with or endorsed by Target Corporation.
