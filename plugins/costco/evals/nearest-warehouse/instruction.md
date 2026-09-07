# Task

Find the nearest Costco warehouse to ZIP code 94109. Report its numeric warehouse number and full warehouse name.

Use the Costco integration tools available in this environment. All warehouse and
product data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "warehouse_number": "<warehouse_number>",
  "name": "<name>"
}
```
