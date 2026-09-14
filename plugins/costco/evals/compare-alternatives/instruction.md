# Task

For Costco warehouse 144 and postal code 94080, search for olive oil. Of the returned products that are buyable and carry the InWarehouse catalog signal, choose the one with the lowest public Costco.com price. Report its item number, name, price, and savings versus the other qualifying result.

Use the Costco integration tools available in this environment. All warehouse and
product data must come through those tools, not shell commands, local files, direct
web requests, or Python imports. If a tool reports an error, use its guidance and try
the integration again rather than working around it.

Write the answer to `/app/answer.json` as one JSON object with exactly this shape:

```json
{
  "item_number": "<item_number>",
  "name": "<name>",
  "price": 0.0,
  "savings": 0.0
}
```
