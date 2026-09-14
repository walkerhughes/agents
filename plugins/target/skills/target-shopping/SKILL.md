---
name: target-shopping
description: Plan Target shopping lists and menus using store-scoped products, public prices, package details, and nearby pickup availability. Use for Target searches, price checks, store selection, shopping trips, and meal planning.
---

# Target Shopping and Menu Planning

Build store-specific shopping plans from Target's public website data while keeping
price and pickup claims tied to the location the user selected.

## Establish Store Context

Use a store already selected in the conversation. Otherwise search for the first
needed product and call `find_stores_with_item` with the user's ZIP code. Let the user
choose when distance, availability, and pickup options conflict. Carry the chosen
`store_id` and ZIP code into product searches. Never imply device-location access.

## Search and Verify

Use focused `search_products` calls to discover candidates and `get_product` for a
known TCIN. Use `find_stores_with_item` when pickup availability matters. Preserve
package details, current and regular prices, promotion context, and the selected store.

Treat availability and quantities as point-in-time website signals. Do not describe
them as reservations or guarantees. Distinguish current public prices from prices that
require sign-in, Target Circle eligibility, a particular fulfillment method, or an
in-store visit.

## Build Lists and Menus

Call `price_shopping_list`, inspect every first match and its alternatives, and flag
unmatched or unpriced requests. Adjust written quantities for servings and package
sizes. Reuse perishable ingredients across meals and call out likely surplus.

Separate pantry staples from purchases and group the final list by practical
departments. Do not infer allergy safety from product names. For severe allergies,
ask the user to verify the current package label.
