# Trader Joe's

An unofficial, read-only MCP plugin for Trader Joe's public website. It finds
nearby stores, searches the store-scoped catalog, pulls published prices, prices a
draft shopping list, and guides menu planning around products the site actually
shows.

No account or API key is required.

## What it can do

- Find stores by ZIP code, city/state, or street address.
- Return the numeric store code used for location-specific product results.
- Search products with package size, price, description, categories, and published
  catalog availability.
- Look up a known product SKU.
- Batch-price up to 30 shopping-list phrases and show alternatives for ambiguous
  matches.
- Build store-specific menus and organized shopping lists through the bundled
  planning skill.

Example prompts:

```
Find the closest Trader Joe's to 94109 and show me the price of oat milk.

Plan five vegetarian dinners for two from the Nob Hill store. Keep the grocery
estimate under $85 and reuse ingredients.

Price this list at store 200: chicken thighs, jasmine rice, broccoli, yogurt.
```

## Accuracy boundaries

Trader Joe's says its website does not represent every product available in its
stores. The site returns store-scoped catalog availability, not real-time shelf
counts. Treat prices as published website prices at lookup time and confirm
important availability in store.

The public product endpoint is protected by Trader Joe's delivery infrastructure.
If it returns HTTP 403 for an automated request, the plugin reports that plainly
instead of fabricating a result. Retrying later or checking traderjoes.com directly
is the safe fallback.

## Development

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```
make check
make coverage
```

Run the server directly:

```
uv run python -m src.server
```

Override either upstream only for tests or controlled development:

- `TRADER_JOES_PRODUCT_URL`
- `TRADER_JOES_LOCATOR_URL`

## Data sources and status

The implementation uses the unauthenticated GraphQL request made by the public
product catalog and the public SOCi store-locator request embedded on the official
site. Both are undocumented implementation details and may change.

This project is not affiliated with, endorsed by, or sponsored by Trader Joe's.
Trader Joe's is a trademark of its owner. Use the plugin in accordance with the
site's applicable terms.
