# Task

Find the nearest Safeway store for ZIP code 94109. Report its store ID, full store name, street address, and whether pickup is supported.

Use the Safeway integration tools available in this environment. All store and product
data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "store_id": "<store_id>",
  "name": "<name>",
  "address": "<address>",
  "pickup": false
}
```
