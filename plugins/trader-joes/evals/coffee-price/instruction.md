# Task

At Trader Joe's store 200, find Costa Rica Coffee and report its product name and published price as a number.

Use the Trader Joe's integration tools available in this environment. All store and
product data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "name": "<name>",
  "price": "<price>"
}
```
