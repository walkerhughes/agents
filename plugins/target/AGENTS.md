# Target plugin

- Keep the integration read-only. Do not add cart, account, order, or checkout mutations.
- Treat Redsky availability as a point-in-time signal, not a reservation or guarantee.
- Preserve explicit store and ZIP context for every price or availability claim.
- Generate eval task directories from `evals/generate_tasks.py`; do not edit generated task files directly.
