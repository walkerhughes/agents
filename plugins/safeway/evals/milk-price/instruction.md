# Task

For Safeway store 1507 using pickup, search for whole milk. Report the selected product name, product ID, current public price as a number, and aisle.

Use the Safeway integration tools available in this environment. All store and product
data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "name": "<name>",
  "product_id": "<product_id>",
  "price": 0.0,
  "aisle": "<aisle>"
}
```
