---
name: costco-shopping
description: Plan Costco shopping lists and menus using warehouse-context products, public prices, package sizes, and location selection. Use for Costco product searches, price checks, warehouse lookup, bulk shopping, and meal planning.
---

# Costco Shopping and Menu Planning

Build warehouse-specific plans from Costco's public website data while accounting
for bulk package sizes and the difference between online and walk-in pricing.

## Select a Warehouse

Use a warehouse already selected in the conversation. Otherwise ask for a ZIP code
or city/state and call `find_warehouses`. Carry the selected `warehouse_number`,
`postal_code`, and `state` into product searches. Never imply device-location access.

## Search and Price

Use focused `search_products` calls to discover candidates. Use `get_product` for a
known item number. Preserve package details, public price, and warehouse context.

Treat `InWarehouse` as a catalog signal, not live inventory. Label prices as public
Costco.com prices. Do not present them as guaranteed walk-in, member-only, or Same-Day
prices.

## Build Lists and Menus

Call `price_shopping_list` for the user's ingredients, then inspect each selected
match and its alternatives. Adjust the written quantities for servings and Costco's
bulk sizes. Reuse perishable ingredients across meals and call out likely surplus.

Separate pantry staples from purchases. Group the final list by useful departments.
For each meal, give concise preparation guidance, the matched Costco products, and a
cost estimate only when published prices support one.

Do not infer allergy safety from product names or attributes. For severe allergies,
ask the user to verify the current package label.
