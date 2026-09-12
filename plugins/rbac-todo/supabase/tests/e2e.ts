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
let todoId: string | undefined;
const marker = `rbac-todo-e2e-${crypto.randomUUID()}`;
try {
  const tokens: Record<string, string> = {};
  for (const role of ["admin", "member", "outsider"]) {
    const email = `${marker}-${role}@example.com`;
    const password = crypto.randomUUID();
    const created = await api("/auth/v1/admin/users", service, "POST", {
      email,
      password,
      email_confirm: true,
      // User-editable metadata must never grant privileges.
      user_metadata: { role: "admin" },
    });
    assert.equal(created.status, 200, `Create ${role}`);
    users.push(created.data.id);
    if (role !== "outsider") {
      const assigned = await api("/rest/v1/todo_members", service, "POST", {
        user_id: created.data.id,
        role,
      });
      assert.equal(assigned.status, 201, `Assign ${role}`);
    }
    const login = await api(
      "/auth/v1/token?grant_type=password",
      anon,
      "POST",
      {
        email,
        password,
      },
    );
    assert.equal(login.status, 200, `Sign in ${role}`);
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
    assert.equal(response.status, expected, "Reject unauthorized client");
  }
  const browser = await fetch(endpoint, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${tokens.admin}`,
      Origin: "https://evil.example",
    },
  });
  await browser.text();
  assert.equal(browser.status, 403, "Reject unexpected browser origin");
  for (const role of ["admin", "member"]) {
    const init = await rpc(tokens[role], "initialize", {
      protocolVersion: "2025-06-18",
      capabilities: {},
      clientInfo: { name: "e2e", version: "1" },
    });
    assert.equal(init.result.serverInfo.name, "rbac-todo");
    const list = await rpc(tokens[role], "tools/list", {});
    assert.deepEqual(
      list.result.tools.map((tool: { name: string }) => tool.name).sort(),
      ["add_todo", "delete_todo", "list_todos", "update_todo"],
    );
  }
  console.log("PASS: authentication and MCP discovery");

  const added = await call(tokens.admin, "add_todo", { title: marker });
  todoId = added.id;
  assert.equal(added.completed, false);
  const stored = await api(`/rest/v1/todos?id=eq.${todoId}`, tokens.member);
  assert.equal(stored.data[0].title, marker, "MCP write persisted in Postgres");
  const listed = await call(tokens.member, "list_todos", { limit: 100 });
  assert(listed.some((todo: { id: string }) => todo.id === todoId));
  for (const token of [tokens.member, tokens.outsider]) {
    const inserted = await api("/rest/v1/todos", token, "POST", {
      title: marker,
    });
    assert.equal(inserted.status, 403, "RLS denies direct insert");
    for (const method of ["PATCH", "DELETE"]) {
      const denied = await api(
        `/rest/v1/todos?id=eq.${todoId}`,
        token,
        method,
        method === "PATCH" ? { completed: true } : undefined,
      );
      assert.equal(denied.status, 200);
      assert.deepEqual(denied.data, [], `RLS filters direct ${method}`);
    }
    const promoted = await api(
      `/rest/v1/todo_members?user_id=eq.${users[1]}`,
      token,
      "PATCH",
      { role: "admin" },
    );
    assert.equal(promoted.status, 403, "No self-promotion");
    const enrollment = await api("/rest/v1/todo_members", token, "POST", {
      user_id: users[2],
      role: "admin",
    });
    assert.equal(enrollment.status, 403, "No self-enrollment");
  }
  const hidden = await api(`/rest/v1/todos?id=eq.${todoId}`, tokens.outsider);
  assert.deepEqual(hidden.data, [], "Unassigned user cannot read");
  const anonymous = await api("/rest/v1/todos", anon);
  assert.equal(anonymous.status, 401, "Anonymous REST denied");
  await call(tokens.member, "add_todo", { title: marker }, true);
  await call(
    tokens.member,
    "update_todo",
    { id: todoId, completed: true },
    true,
  );
  await call(tokens.member, "delete_todo", { id: todoId }, true);
  await call(tokens.admin, "add_todo", { title: "   " }, true);
  await call(tokens.admin, "update_todo", { id: todoId }, true);
  await call(tokens.admin, "delete_todo", { id: "invalid" }, true);
  console.log(
    "PASS: RLS, member write denial, metadata spoofing and input validation",
  );

  const updated = await call(tokens.admin, "update_todo", {
    id: todoId,
    completed: true,
    title: `${marker}-updated`,
  });
  assert.equal(updated.completed, true);
  const persisted = await api(`/rest/v1/todos?id=eq.${todoId}`, tokens.member);
  assert.equal(persisted.data[0].title, `${marker}-updated`);
  const filtered = await call(tokens.member, "list_todos", {
    completed: false,
  });
  assert(!filtered.some((todo: { id: string }) => todo.id === todoId));

  const demoted = await api(
    `/rest/v1/todo_members?user_id=eq.${users[0]}`,
    service,
    "PATCH",
    { role: "member" },
  );
  assert.equal(demoted.status, 200);
  await call(
    tokens.admin,
    "update_todo",
    { id: todoId, completed: false },
    true,
  );
  const restored = await api(
    `/rest/v1/todo_members?user_id=eq.${users[0]}`,
    service,
    "PATCH",
    { role: "admin" },
  );
  assert.equal(restored.status, 200);
  await call(tokens.admin, "delete_todo", { id: todoId });
  const deleted = await api(`/rest/v1/todos?id=eq.${todoId}`, tokens.member);
  assert.deepEqual(deleted.data, []);
  await call(
    tokens.admin,
    "update_todo",
    { id: todoId, completed: true },
    true,
  );
  console.log(
    "PASS: admin CRUD, persistence, filtering and immediate role demotion",
  );
} finally {
  // Scope cleanup to this run, including writes that unexpectedly bypassed RLS.
  const removed = await api(
    `/rest/v1/todos?title=like.${marker}*`,
    service,
    "DELETE",
  );
  assert.equal(removed.status, 200, "Clean up test todos");
  for (const user of users) {
    const removed = await api(
      `/auth/v1/admin/users/${user}`,
      service,
      "DELETE",
    );
    assert.equal(removed.status, 200, "Clean up test user");
  }
  console.log("Temporary users and test todos removed");
}
