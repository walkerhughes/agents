# Task

For Target store 2766 and ZIP code 94103, price a list containing one package of jasmine rice and one can of black beans. Report the selected product names and combined public Target.com total as a number.

Use the Target integration tools available in this environment. All store and product
data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "items": [
    "<item 1>",
    "<item 2>"
  ],
  "estimated_total": 0.0
}
```
