# Task

I am near ZIP code 94109 and want to make chicken tacos and chicken Caesar salad bowls for four people, reusing one rotisserie chicken across both meals. Find the nearest warehouse, then price one package each of rotisserie chicken, flour tortillas, shredded Mexican cheese, and a Caesar salad kit there. Report the warehouse number and name, selected product names, public Costco.com total, and the exact selected product reused across both dinners.

Use the Costco integration tools available in this environment. All warehouse and
product data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "warehouse_number": "<warehouse_number>",
  "warehouse_name": "<warehouse_name>",
  "items": [
    "<item 1>",
    "<item 2>",
    "<item 3>",
    "<item 4>"
  ],
  "estimated_total": 0.0,
  "reused_product": "<reused_product>"
}
```
