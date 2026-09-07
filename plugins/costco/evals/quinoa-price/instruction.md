# Task

For Costco warehouse 144 and postal code 94080, find organic quinoa and report the selected product name and public Costco.com price as a number.

Use the Costco integration tools available in this environment. All warehouse and
product data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "name": "<name>",
  "price": 0.0
}
```
