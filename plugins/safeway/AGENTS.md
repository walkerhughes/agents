# Safeway plugin

- Keep the integration read-only. Do not add account, coupon, cart, order, or checkout mutations.
- Tie product prices and inventory signals to the explicit store and fulfillment channel.
- Treat inventory as a website signal, not a shelf guarantee.
- Generate eval task directories from `evals/generate_tasks.py`; do not edit generated task files directly.
