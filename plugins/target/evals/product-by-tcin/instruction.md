# Task

For Target store 2766 and ZIP code 94103, look up TCIN 88888888. Report its product name, brand, and current public price as a number.

Use the Target integration tools available in this environment. All store and product
data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "name": "<name>",
  "brand": "<brand>",
  "price": 0.0
}
```
