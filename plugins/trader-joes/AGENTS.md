# trader-joes

Read-only MCP server over the public requests made by traderjoes.com. The product
catalog is GraphQL; the store locator is a SOCi/Where2GetIt JSON endpoint.

## Upstream references

| What | Where |
| --- | --- |
| Product catalog | https://www.traderjoes.com/home/products/category |
| Product GraphQL endpoint | https://www.traderjoes.com/api/graphql |
| Store locator | https://www.traderjoes.com/home/store-search |
| Embedded locator | https://hosted.where2getit.com/traderjoes/locator.html |
| Website terms | https://www.traderjoes.com/home/terms-of-use |

## Local rules

- Keep every tool read-only. This plugin has no cart, order, account, or purchase
  path.
- Preserve the explicit catalog-versus-inventory distinction in tool descriptions
  and shaped results.
- Keep upstream URLs injectable so integration tests never need the real site.
- Treat the GraphQL schema and locator payload as unstable. Shape responses at the
  boundary and fail with a useful message when required containers disappear.
- Never add a workaround that bypasses site access controls.
