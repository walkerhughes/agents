# rbac-todo

Personal to-dos in Supabase Postgres, exposed by one Edge Function using
`mcp-lite` over Streamable HTTP. Sign in through the browser with Supabase Auth.
New accounts are admins of their own todos. No user can access another user's list.

| Tool | Inputs | Member | Admin |
| --- | --- | --- | --- |
| `list_todos` | Optional `completed`, `limit` (1-100), `offset` | Read own | Read own |
| `add_todo` | `title` (1-500 characters) | Denied | Add own |
| `update_todo` | `id`, `title` and/or `completed` | Denied | Update own |
| `delete_todo` | `id` | Denied | Delete own |

## Install and sign in

From `plugins/rbac-todo` in this checkout:

```bash
codex plugin marketplace add ../..
codex plugin add rbac-todo@rbac-todo-dev
codex mcp login rbac-todo --oauth-client-registration dcr
codex
```

The login command opens a browser. Sign in with email and password, or select
**Create an account**, confirm your email, and continue. Approve the connection
and return to Codex. Ask: `Use rbac-todo to add Buy milk, then show my todos.`
If the connection request expires during email confirmation, run login again.
Start a new Codex session after installing or updating the plugin.

Codex stores the OAuth session and refreshes tokens. No API key, database
password, or exported access token is required. Disconnect with:

```bash
codex mcp logout rbac-todo
```

Claude Code can load the checkout with `claude --plugin-dir ./plugins/rbac-todo`
and use its MCP authentication flow. Both configurations contain only the HTTP
endpoint; the server advertises Supabase's OAuth authorization server.

- Sign-in page: https://rbac-todo-login.banachspace.chatgpt.site
- Project: `supabase-demo` (`tteazpolsuwfxqqqksoj`)
- MCP: `https://tteazpolsuwfxqqqksoj.supabase.co/functions/v1/rbac-todo/mcp`

## Security and ownership

Supabase Auth stores and hashes passwords. The web app uses only a public
publishable key. OAuth uses authorization codes with PKCE; the MCP client manages
its own session. The Edge Function validates the user's token with `getUser()`
and forwards it to Postgres using the anon key, never a service-role client.

An Auth insert trigger creates a `todo_members` admin row for new accounts.
RLS requires `todos.user_id = auth.uid()` on every operation. Both roles may read;
only admins may write. Users cannot edit memberships or change todo ownership.
An operator can demote a user to read-only access to their own list:

```sql
update public.todo_members set role = 'member' where user_id = 'USER_UUID';
```

Role changes take effect on the next operation, including with existing tokens.
Anonymous users and users without memberships have no access. Browser-origin MCP
calls are rejected; the browser only communicates with Supabase Auth.

The `(user_id, created_at DESC, id DESC)` index supports each user's ordered list.
The membership primary key indexes role lookups, and todo IDs have a primary key.
Queries include the owner filter explicitly as well as enforcing it through RLS.
Offset pagination is limited to 100 results per request.

The personal-todo migration preserves the existing demo list by assigning it to
the sole existing admin. It aborts when rows exist and ownership is ambiguous;
resolve those owners before applying it to a different project.

## Auth configuration

In Supabase Authentication, enable the OAuth server and dynamic client
registration. Set Site URL to the sign-in page above, authorization path to `/`,
and add that site's `/**` URL to allowed auth redirects. Keep email confirmation
enabled and configure a custom SMTP provider for public signup. Supabase's
built-in mail service only sends to authorized project team addresses.

**Deployment prerequisite:** this demo currently needs custom SMTP configured
before arbitrary new users can receive confirmation emails. Returning confirmed
users can sign in. Do not disable confirmation to work around missing SMTP.

The frontend is `web/`, a React app with shadcn components. The publishable key
and project URL in `web/app/page.tsx` are public project configuration. If moving
to another project, update those values and both MCP endpoint configurations.
Site hosting identity is in `web/.openai/hosting.json`.

## Develop and verify

From `plugins/rbac-todo`, with Deno 2, Python 3, Node 22+, and the Supabase CLI:

```bash
deno task --config supabase/functions/rbac-todo/deno.json check
python3 tests/test_mcp_config.py
cd web
npm ci
npm run lint
npm run build
npm run dev
```

In another terminal in `web/`, `npx playwright test --grep 'desktop and mobile'`
checks the local UI. Install Chromium once with `npx playwright install chromium`.
To test the live login, consent, PKCE exchange, MCP access, token refresh and
revocation with a temporary account, run:

```bash
AUTH_SITE_URL=https://rbac-todo-login.banachspace.chatgpt.site npx playwright test
```

The live browser test needs `SUPABASE_ACCESS_TOKEN`. Set `RBAC_TEST_CODEX=1`
to also exercise the native Codex login command with a temporary server entry.
Consent must run on the
configured Site URL because Supabase validates the request origin.
The database/MCP integration test also uses that management token to create and
remove temporary users. It checks two-user isolation, forged ownership, member
write denial, CRUD persistence, and immediate demotion:

```bash
deno task --config supabase/functions/rbac-todo/deno.json test
```

Deploy schema and Edge Function changes with:

```bash
supabase link --project-ref tteazpolsuwfxqqqksoj
supabase db push --dry-run
supabase db push
supabase functions deploy rbac-todo --project-ref tteazpolsuwfxqqqksoj
```

Linking needs `SUPABASE_ACCESS_TOKEN` and `SUPABASE_DB_PASSWORD`. The Edge Function
receives `SUPABASE_URL` and `SUPABASE_ANON_KEY` from Supabase automatically.
`verify_jwt = false` delegates token verification to the handler; retain its
explicit authentication check. Local Supabase development requires Docker.

## References

- [Supabase MCP with mcp-lite](https://supabase.com/docs/guides/functions/examples/mcp-server-mcp-lite)
- [Supabase OAuth MCP authentication](https://supabase.com/docs/guides/auth/oauth-server/mcp-authentication)
- [Supabase OAuth setup](https://supabase.com/docs/guides/auth/oauth-server/getting-started)
- [Supabase SMTP](https://supabase.com/docs/guides/auth/auth-smtp)
- [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase Postgres skill](https://github.com/supabase/agent-skills/tree/main/skills/supabase-postgres-best-practices)
