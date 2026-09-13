// Live integration check. Creates temporary Auth users and removes its own data.
import { strict as assert } from "node:assert";

const projectRef = Deno.env.get("SUPABASE_PROJECT_REF") ??
  "tteazpolsuwfxqqqksoj";
const url = `https://${projectRef}.supabase.co`;
const endpoint = `${url}/functions/v1/rbac-todo/mcp`;
const accessToken = Deno.env.get("SUPABASE_ACCESS_TOKEN");
assert(accessToken, "Set SUPABASE_ACCESS_TOKEN for test user provisioning");

const keyResponse = await fetch(
  `https://api.supabase.com/v1/projects/${projectRef}/api-keys`,
  { headers: { Authorization: `Bearer ${accessToken}` } },
);
assert.equal(keyResponse.status, 200, "Get project API keys");
const keys = await keyResponse.json();
const anon = keys.find((key: { name: string }) => key.name === "anon")?.api_key;
const service = keys.find((key: { name: string }) =>
  key.name === "service_role"
)?.api_key;
assert(
  anon && service,
  "Project requires legacy anon and service_role keys for this test",
);

async function api(
  path: string,
  token: string,
  method = "GET",
  body?: unknown,
) {
  const response = await fetch(`${url}${path}`, {
    method,
    headers: {
      apikey: token === service ? service : anon,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      Prefer: "return=representation",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(30000),
  });
  const text = await response.text();
  return { status: response.status, data: text ? JSON.parse(text) : null };
}

let rpcId = 0;
async function rpc(token: string, method: string, params: unknown) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
      "MCP-Protocol-Version": "2025-06-18",
    },
    body: JSON.stringify({ jsonrpc: "2.0", id: ++rpcId, method, params }),
    signal: AbortSignal.timeout(30000),
  });
  const text = await response.text();
  assert.equal(response.status, 200, `MCP ${method}: ${text}`);
  const json =
    response.headers.get("content-type")?.includes("text/event-stream")
      ? JSON.parse(
        text.split("\n").find((line) => line.startsWith("data: "))!.slice(6),
      )
      : JSON.parse(text);
  return json;
}

async function call(token: string, name: string, args: unknown, fails = false) {
  const response = await rpc(token, "tools/call", { name, arguments: args });
  if (fails) {
    assert(response.error || response.result?.isError, `${name} must fail`);
    return;
  }
  assert(
    !response.error && !response.result?.isError,
    JSON.stringify(response),
  );
  return JSON.parse(response.result.content[0].text);
}

const users: string[] = [];
const tokens: Record<string, string> = {};
const marker = `rbac-todo-e2e-${crypto.randomUUID()}`;
try {
  for (const role of ["admin", "other", "member", "outsider"]) {
    const email = `${marker}-${role}@example.com`;
    const password = crypto.randomUUID();
    const created = await api("/auth/v1/admin/users", service, "POST", {
      email,
      password,
      email_confirm: true,
      user_metadata: { role: "admin" },
    });
    assert.equal(created.status, 200);
    const userId = created.data.id;
    users.push(userId);
    const membership = await api(
      `/rest/v1/todo_members?user_id=eq.${userId}`,
      service,
    );
    assert.equal(
      membership.data[0].role,
      "admin",
      "New users automatically own an admin membership",
    );
    if (role === "member") {
      assert.equal(
        (await api(
          `/rest/v1/todo_members?user_id=eq.${userId}`,
          service,
          "PATCH",
          { role },
        )).status,
        200,
      );
      assert.equal(
        (await api("/rest/v1/todos", service, "POST", {
          title: marker,
          user_id: userId,
        })).status,
        201,
      );
    }
    if (role === "outsider") {
      assert.equal(
        (await api(
          `/rest/v1/todo_members?user_id=eq.${userId}`,
          service,
          "DELETE",
        )).status,
        200,
      );
    }
    const login = await api(
      "/auth/v1/token?grant_type=password",
      anon,
      "POST",
      { email, password },
    );
    assert.equal(login.status, 200);
    tokens[role] = login.data.access_token;
  }
  for (
    const [token, expected] of [["", 401], ["invalid", 401], [
      tokens.outsider,
      403,
    ]] as const
  ) {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    await response.text();
    assert.equal(response.status, expected);
    if (!token) {
      assert(
        response.headers.get("www-authenticate")?.includes(
          "resource_metadata=",
        ),
      );
    }
  }
  const metadata = await fetch(
    `${url}/functions/v1/rbac-todo/.well-known/oauth-protected-resource`,
  );
  const advertised = await metadata.json();
  assert.equal(advertised.resource, endpoint);
  assert(advertised.scopes_supported.includes("offline_access"));
  const init = await rpc(tokens.admin, "initialize", {
    protocolVersion: "2025-06-18",
    capabilities: {},
    clientInfo: { name: "e2e", version: "1" },
  });
  assert.equal(init.result.serverInfo.name, "rbac-todo");
  const tools = await rpc(tokens.admin, "tools/list", {});
  assert.equal(tools.result.tools.length, 4);
  const browser = await fetch(endpoint, {
    headers: {
      Origin: "https://evil.example",
      Authorization: `Bearer ${tokens.admin}`,
    },
  });
  await browser.text();
  assert.equal(browser.status, 403);
  console.log(
    "PASS: signup role, authentication, OAuth discovery and MCP discovery",
  );

  const todo = await call(tokens.admin, "add_todo", { title: marker });
  const own = await api(`/rest/v1/todos?id=eq.${todo.id}`, tokens.admin);
  assert.equal(own.data[0].user_id, users[0]);
  for (const role of ["other", "member", "outsider"]) {
    const hidden = await api(`/rest/v1/todos?id=eq.${todo.id}`, tokens[role]);
    assert.deepEqual(hidden.data, []);
    for (const method of ["PATCH", "DELETE"]) {
      const denied = await api(
        `/rest/v1/todos?id=eq.${todo.id}`,
        tokens[role],
        method,
        method === "PATCH" ? { completed: true } : undefined,
      );
      assert.equal(denied.status, 200);
      assert.deepEqual(denied.data, []);
    }
    const forged = await api("/rest/v1/todos", tokens[role], "POST", {
      title: marker,
      user_id: users[0],
    });
    assert.equal(forged.status, 403);
    const promoted = await api(
      `/rest/v1/todo_members?user_id=eq.${users[2]}`,
      tokens[role],
      "PATCH",
      { role: "admin" },
    );
    assert.equal(promoted.status, 403);
  }
  const transferred = await api(
    `/rest/v1/todos?id=eq.${todo.id}`,
    tokens.admin,
    "PATCH",
    { user_id: users[1] },
  );
  assert.equal(transferred.status, 403, "Owners cannot transfer records");
  assert.equal((await api("/rest/v1/todos", anon)).status, 401);
  assert.deepEqual(await call(tokens.other, "list_todos", {}), []);
  const memberTodos = await call(tokens.member, "list_todos", {});
  assert.equal(memberTodos.length, 1);
  assert.notEqual(memberTodos[0].id, todo.id);
  await call(tokens.member, "add_todo", { title: marker }, true);
  await call(tokens.member, "update_todo", {
    id: memberTodos[0].id,
    completed: true,
  }, true);
  await call(tokens.member, "delete_todo", { id: memberTodos[0].id }, true);
  await call(
    tokens.other,
    "update_todo",
    { id: todo.id, completed: true },
    true,
  );
  await call(tokens.other, "delete_todo", { id: todo.id }, true);
  await call(tokens.admin, "add_todo", { title: "  " }, true);
  await call(tokens.admin, "update_todo", { id: todo.id }, true);
  await call(tokens.admin, "delete_todo", { id: "invalid" }, true);
  console.log(
    "PASS: two-user isolation, own-row member reads, member write denial and forged ownership",
  );

  await call(tokens.admin, "update_todo", { id: todo.id, completed: true });
  assert.equal(
    (await api(`/rest/v1/todos?id=eq.${todo.id}`, tokens.admin)).data[0]
      .completed,
    true,
  );
  assert.deepEqual(
    await call(tokens.admin, "list_todos", { completed: false }),
    [],
  );
  assert.equal(
    (await call(tokens.admin, "list_todos", { completed: true, limit: 1 }))
      .length,
    1,
  );
  assert.equal(
    (await api(
      `/rest/v1/todo_members?user_id=eq.${users[0]}`,
      service,
      "PATCH",
      { role: "member" },
    )).status,
    200,
  );
  await call(tokens.admin, "delete_todo", { id: todo.id }, true);
  assert.equal(
    (await api(
      `/rest/v1/todo_members?user_id=eq.${users[0]}`,
      service,
      "PATCH",
      { role: "admin" },
    )).status,
    200,
  );
  await call(tokens.admin, "delete_todo", { id: todo.id });
  assert.deepEqual(
    (await api(`/rest/v1/todos?id=eq.${todo.id}`, tokens.admin)).data,
    [],
  );
  console.log(
    "PASS: own-row CRUD persistence, filtering and immediate role demotion",
  );
} finally {
  for (const user of users) {
    const removed = await api(
      `/auth/v1/admin/users/${user}`,
      service,
      "DELETE",
    );
    assert.equal(
      removed.status,
      200,
      "Remove test user and cascade-delete owned data",
    );
  }
  console.log("Temporary users and their todos removed");
}
