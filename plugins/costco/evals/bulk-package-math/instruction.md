# Task

For Costco warehouse 144 and postal code 94080, I need at least 20 rolls of paper towels. Find the relevant product, use its package quantity, and report the product name, rolls per package, minimum packages to buy, total rolls purchased, and public Costco.com extended total.

Use the Costco integration tools available in this environment. All warehouse and
product data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "name": "<name>",
  "rolls_per_package": 0,
  "packages_to_buy": 0,
  "total_rolls": 0,
  "estimated_total": 0.0
}
```
