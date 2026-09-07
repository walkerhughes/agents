# Task

Find stores near ZIP code 94103 carrying Target TCIN 88888888. Report the nearest store ID, full store name, distance in miles, and pickup status.

Use the Target integration tools available in this environment. All store and product
data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "store_id": "<store_id>",
  "name": "<name>",
  "distance_miles": 0.0,
  "pickup_status": "<pickup_status>"
}
```
