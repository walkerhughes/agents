---
name: safeway-shopping
description: Plan Safeway shopping lists and menus using nearby stores, store-scoped products, public prices, unit prices, aisle details, and inventory signals. Use for Safeway searches, price checks, grocery trips, and meal planning.
---

# Safeway Shopping and Menu Planning

Build store-specific plans from Safeway's public website data while distinguishing
current prices, base prices, promotions, and loyalty eligibility.

## Select a Store

Use a store already selected in the conversation. Otherwise ask for a ZIP code and
call `find_stores`. Carry the chosen `store_id` into every search. Never imply
device-location access.

## Search and Price

Use focused `search_products` calls to discover candidates. Use `get_product` for a
known Safeway product ID. Preserve package details, current and base prices, unit
prices, promotion end dates, department, aisle, and fulfillment channel.

Do not claim that a current price is available to every shopper when the response
could reflect membership, a promotion, or a digital offer. Treat inventory fields as
point-in-time signals and not as shelf guarantees.

## Build Lists and Menus

Call `price_shopping_list`, inspect first matches and alternatives, and flag unpriced
or unavailable requests. Adjust quantities for servings and package sizes. Reuse
perishable ingredients across meals and call out likely surplus.

Group the final list by returned department or aisle when possible. Separate pantry
staples from purchases. Do not infer allergy safety from product names; for severe
allergies, ask the user to verify the current package label.
