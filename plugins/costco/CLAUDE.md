# costco

Read-only MCP server over public requests made by costco.com. Product search and
warehouse lookup use REST endpoints; product details and prices use GraphQL.

## Local rules

- Keep every tool read-only. Do not add cart, account, order, or purchase paths.
- Describe prices as published Costco.com prices for the selected warehouse context,
  not guaranteed walk-in warehouse prices.
- Do not describe catalog or program-type signals as live shelf inventory.
- Keep every upstream URL injectable so tests and evals remain deterministic.
- Treat the undocumented request and response shapes as unstable and fail with useful
  guidance when required containers disappear.
- Never add a workaround that bypasses site access controls.
