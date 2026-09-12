# rbac-todo

A shared to-do list persisted in Supabase Postgres. One Supabase Edge Function
serves four MCP tools using `mcp-lite` over stateless Streamable HTTP.

| Tool | Inputs | Member | Admin |
| --- | --- | --- | --- |
| `list_todos` | Optional `completed`, `limit` (1-100), `offset` | Read | Read |
| `add_todo` | `title` (1-500 characters) | Denied | Add |
| `update_todo` | `id`, `title` and/or `completed` | Denied | Update |
| `delete_todo` | `id` | Denied | Delete |

## Connect

Project: `supabase-demo` (`tteazpolsuwfxqqqksoj`). Endpoint:

```text
https://tteazpolsuwfxqqqksoj.supabase.co/functions/v1/rbac-todo/mcp
```

Create users in Supabase Dashboard > Authentication > Users. Assign each user's
UUID a role using the SQL Editor:

```sql
insert into public.todo_members (user_id, role)
values ('USER_UUID', 'admin') -- use 'member' for read-only access
on conflict (user_id) do update set role = excluded.role;
```

Only the trusted project operator or service role can assign roles. The MCP
cannot manage memberships. There are no default users or passwords.

Sign in through Supabase Auth and export that user's session `access_token` as
`RBAC_TODO_ACCESS_TOKEN` before launching your MCP client. This is a user JWT,
not a Supabase management token, API key, or database password. To obtain a token
without saving a password in shell history (Python 3, no dependencies), run from
`plugins/rbac-todo`:

```bash
export SUPABASE_ANON_KEY='your-project-anon-key'
export RBAC_TODO_ACCESS_TOKEN="$(python3 scripts/login.py)"
```

The anon key is available in Supabase Dashboard > Project Settings > API Keys.
The script prompts for your email and password through the terminal and outputs
only the access token. Tokens expire; sign in again and restart the client when
needed. This demo uses bearer tokens, without an OAuth discovery/login flow.

For this checkout, launch Claude Code with:

```bash
claude --plugin-dir ./plugins/rbac-todo
```

After this plugin is published to the repo marketplace, install with
`claude plugin install rbac-todo@walkerhughes` and restart Claude Code.
The plugin includes both Claude and Codex manifests and `.mcp.json`.
Other clients can use the endpoint with an `Authorization: Bearer <user JWT>`
header. Browser origins are rejected; use a native MCP client.

## Security

`todo_members` contains one `admin` or `member` role per Auth user. Users can
only read their own membership and cannot change roles, even via the REST API.
Unassigned users and anonymous callers have no access to to-dos.

RLS on `todos` allows both roles to select and only admins to insert, update or
delete. The function validates the token with `auth.getUser()` and forwards it
to every database query using the anon key. It never uses a service-role client.
Roles are read from the database, so demotion takes effect on the next operation
even with an existing JWT. User-editable metadata does not grant access.

`verify_jwt = false` disables the legacy gateway check, while the function
performs authentication itself. Do not remove the handler's auth check.

## Develop and deploy

Run from `plugins/rbac-todo`. Requires Deno 2 and Supabase CLI. If needed, use
`npm exec --yes --package=deno -- deno ...` and `npx supabase ...`.

```bash
deno task --config supabase/functions/rbac-todo/deno.json check
supabase link --project-ref tteazpolsuwfxqqqksoj
supabase db push --dry-run
supabase db push
supabase functions deploy rbac-todo --project-ref tteazpolsuwfxqqqksoj
```

`supabase link` uses `SUPABASE_ACCESS_TOKEN` and `SUPABASE_DB_PASSWORD`.
The project name is not its reference ID. Supabase provisions `SUPABASE_URL`
and `SUPABASE_ANON_KEY` automatically inside the Edge Function.
For a local stack, run `supabase start`, `supabase migration up --local`, and
`supabase functions serve rbac-todo`; Docker is required.

The live integration test creates temporary admin, member and unassigned Auth
users, calls the deployed MCP, verifies persistence through REST, attacks the
RLS policies directly, tests role demotion, and removes its own users and rows:

```bash
export SUPABASE_PROJECT_REF=tteazpolsuwfxqqqksoj
deno task --config supabase/functions/rbac-todo/deno.json test
```

The test requires `SUPABASE_ACCESS_TOKEN` to retrieve project credentials for
temporary user setup and cleanup. Credentials are never printed or stored.

## References

- [Supabase: building an MCP server with mcp-lite](https://supabase.com/docs/guides/functions/examples/mcp-server-mcp-lite)
- [Supabase: row level security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase: Edge Function authentication](https://supabase.com/docs/guides/functions/auth)
- [Supabase Postgres best practices skill](https://github.com/supabase/agent-skills/tree/main/skills/supabase-postgres-best-practices)
