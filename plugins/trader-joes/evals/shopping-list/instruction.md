# Task

At Trader Joe's store 200, price a list containing one package of Costa Rica Coffee and one package of Oat Beverage. Report the selected product names and the combined estimated total as a number.

Use the Trader Joe's integration tools available in this environment. All store and
product data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "items": "<items>",
  "estimated_total": "<estimated_total>"
}
```
