# Task

Find the nearest Trader Joe's to ZIP code 94109. Report its numeric store code and full store name.

Use the Trader Joe's integration tools available in this environment. All store and
product data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "store_code": "<store_code>",
  "name": "<name>"
}
```
