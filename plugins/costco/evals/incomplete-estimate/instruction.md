# Task

For Costco warehouse 144 and postal code 94080, price one package of organic quinoa and one package of avocados. Report requested and priced item counts, the known subtotal, the selected product whose public price is hidden, and whether the estimate is complete. Never treat a hidden price as zero.

Use the Costco integration tools available in this environment. All warehouse and
product data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "requested_items": 0,
  "priced_items": 0,
  "known_subtotal": 0.0,
  "unpriced_product": "<unpriced_product>",
  "estimate_complete": false
}
```
