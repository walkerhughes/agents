import { createClient } from "@supabase/supabase-js";
import { McpServer, StreamableHttpTransport } from "mcp-lite";
import { z } from "zod";

const title = z.string().trim().min(1).max(500);
const id = z.string().uuid();

function result(
  data: unknown,
  error: { code?: string; message: string } | null,
) {
  if (error) {
    const message = error.code === "42501"
      ? "Only admins can write to the to-do list."
      : error.code === "PGRST116"
      ? "To-do not found or you do not have permission to change it."
      : "Database request failed. Try again.";
    return {
      isError: true,
      content: [{ type: "text" as const, text: message }],
    };
  }
  return { content: [{ type: "text" as const, text: JSON.stringify(data) }] };
}

Deno.serve(async (request) => {
  const pathname = new URL(request.url).pathname;
  if (!/^\/(?:functions\/v1\/)?rbac-todo\/mcp\/?$/.test(pathname)) {
    return new Response("Not found", { status: 404 });
  }
  // Native MCP clients send no Origin. Reject browser origins by default.
  if (request.headers.has("origin")) {
    return new Response("Browser origins are not allowed", { status: 403 });
  }
  const authorization = request.headers.get("authorization") ?? "";
  if (!/^Bearer \S+$/i.test(authorization)) {
    return new Response("A Supabase Auth access token is required", {
      status: 401,
      headers: { "WWW-Authenticate": "Bearer" },
    });
  }

  // Each request gets its own user-scoped client. Never use the service role here.
  const db = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!,
    {
      global: { headers: { Authorization: authorization } },
      auth: { persistSession: false, autoRefreshToken: false },
    },
  );
  const { data: { user }, error: authError } = await db.auth.getUser(
    authorization.slice(7),
  );
  if (authError || !user) {
    return new Response("Invalid or expired access token", {
      status: 401,
      headers: { "WWW-Authenticate": 'Bearer error="invalid_token"' },
    });
  }
  const { data: membership, error } = await db.from("todo_members")
    .select("role").eq("user_id", user.id).maybeSingle();
  if (error) return new Response("Membership lookup failed", { status: 503 });
  if (!membership) return new Response("Membership required", { status: 403 });

  const mcp = new McpServer({
    name: "rbac-todo",
    version: "1.0.0",
    schemaAdapter: (schema) => z.toJSONSchema(schema as z.ZodType),
  });
  mcp.tool("list_todos", {
    description:
      "Read the shared to-do list, newest first. Available to members and admins. Use offset to fetch the next page.",
    inputSchema: z.object({
      completed: z.boolean().optional(),
      limit: z.number().int().min(1).max(100).default(50),
      offset: z.number().int().min(0).max(1000000).default(0),
    }),
    handler: async ({ completed, limit, offset }) => {
      let query = db.from("todos").select("id,title,completed,created_at")
        .order("created_at", { ascending: false })
        .order("id", { ascending: false }).range(offset, offset + limit - 1);
      if (completed !== undefined) query = query.eq("completed", completed);
      const { data, error } = await query;
      return result(data, error);
    },
  });
  mcp.tool("add_todo", {
    description: "Add a to-do to the shared list. Admin only.",
    inputSchema: z.object({ title }),
    handler: async ({ title }) => {
      const { data, error } = await db.from("todos").insert({ title }).select()
        .single();
      return result(data, error);
    },
  });
  mcp.tool("update_todo", {
    description:
      "Rename a to-do or mark it complete/incomplete by ID. Admin only.",
    inputSchema: z.object({
      id,
      title: title.optional(),
      completed: z.boolean().optional(),
    }).refine(
      (args) => args.title !== undefined || args.completed !== undefined,
      {
        message: "Provide title or completed",
      },
    ),
    handler: async ({ id, ...changes }) => {
      const { data, error } = await db.from("todos").update(changes).eq(
        "id",
        id,
      )
        .select().single();
      return result(data, error);
    },
  });
  mcp.tool("delete_todo", {
    description: "Permanently delete a to-do by ID. Admin only.",
    inputSchema: z.object({ id }),
    handler: async ({ id }) => {
      const { data, error } = await db.from("todos").delete().eq("id", id)
        .select("id").single();
      return result(data, error);
    },
  });

  return new StreamableHttpTransport().bind(mcp)(request);
});
