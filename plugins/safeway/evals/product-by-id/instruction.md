# Task

For Safeway store 1507 using pickup, look up product ID 136010013. Report its product name, current public price as a number, base price as a number, and whether the website reports inventory available.

Use the Safeway integration tools available in this environment. All store and product
data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "name": "<name>",
  "price": 0.0,
  "base_price": 0.0,
  "inventory_available": false
}
```
