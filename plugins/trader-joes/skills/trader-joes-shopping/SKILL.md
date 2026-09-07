---
name: trader-joes-shopping
description: This skill should be used when the user asks to "find Trader Joe's products", "check Trader Joe's prices", "make a Trader Joe's shopping list", "plan Trader Joe's meals", "build a weekly menu from Trader Joe's", or find a nearby Trader Joe's store.
---

# Trader Joe's Shopping and Menu Planning

Build store-specific grocery plans from Trader Joe's public website data. Use the
plugin tools as evidence for products and prices, then apply ordinary cooking
knowledge to turn those products into useful meals and lists.

## Establish the Store

Use a store code already selected in the conversation. Otherwise:

1. Ask for a ZIP code or city and state when no approximate location was supplied.
2. Call `find_stores` with that location.
3. Present the closest few stores when the nearest result is not an obvious choice.
4. Carry the selected `store_code` through every product and list lookup.

Never guess a user's precise location or imply that the plugin reads device
location. A ZIP code or city is normally enough.

## Search and Price Products

Call `search_products` for specific products, ingredients, dietary needs, or meal
concepts. Prefer several focused searches over one broad query when assembling a
menu. Use `get_product` only after a search returns a useful SKU.

Treat a result as evidence that the product is published in the website catalog for
the selected store. Do not call it live inventory. Trader Joe's states that its
website does not represent every item carried in stores, and the API exposes no
shelf quantity.

Include package size beside price. Distinguish a per-pound price from a package
price. Preserve the selected store in any price summary because prices can vary by
location.

## Build a Shopping List

Start from the user's requested meals, dietary constraints, serving count, pantry
staples, budget, and number of days. Make reasonable defaults when harmless, and
state them briefly.

1. Break meals into purchasable ingredient phrases.
2. Remove pantry items the user says are already available.
3. Call `price_shopping_list` once with the remaining phrases.
4. Review every first match. Replace obviously wrong or ambiguous matches with a
   candidate from `alternatives`, or run a more specific product search.
5. Adjust quantities in the written list from servings and package sizes.
6. Compute a practical estimate from package counts rather than repeating the
   tool's one-package baseline when more than one package is needed.
7. Group the final list by useful store sections such as produce, refrigerated,
   frozen, pantry, bakery, snacks, and beverages.

Call out unmatched items instead of inventing a Trader Joe's product. Label items
that may need substitution in store.

## Plan Menus

Design meals around products actually found for the selected store. Balance reuse
without making every meal repetitive. Prefer ingredients that cross over between
meals when the user wants a low-waste or budget plan.

For each meal, provide:

- the dish and serving count;
- the matched Trader Joe's products;
- ordinary pantry ingredients kept separate;
- concise preparation steps;
- substitutions for dietary constraints;
- an estimated cost when the catalog prices and package quantities support one.

Do not infer that a product is safe for an allergy from its name, category, or
dietary label alone. Ask the user to verify the current package label for severe
allergies. Avoid nutritional or medical claims unsupported by product data.

## Handle Uncertainty

State these boundaries when material:

- Prices are current published website prices at lookup time and can change.
- Catalog availability is not live shelf inventory.
- The website omits some items sold in stores.
- Seasonal and limited products may disappear quickly.
- Shopping totals depend on chosen matches and package quantities.

Keep the caveat compact. Do not bury a useful plan under repeated warnings.
