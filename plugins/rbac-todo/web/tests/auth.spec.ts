import { test, expect } from '@playwright/test';
import { spawn, execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { createHash, randomBytes, randomUUID } from 'node:crypto';
import { createClient } from '@supabase/supabase-js';

test('sign-in and signup work at desktop and mobile sizes', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByLabel('Email', { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  await page.getByRole('button', { name: 'Create an account' }).click();
  await expect(page.getByRole('heading', { name: 'A little less to remember' })).toBeVisible();
  await expect(page.getByLabel('Password', { exact: true })).toHaveAttribute('minlength', '8');
  await page.setViewportSize({ width: 375, height: 812 });
  await expect(page.getByRole('button', { name: 'Create account', exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: '/tmp/rbac-todo-signup-mobile.png' });
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.setViewportSize({ width: 1200, height: 900 });
  await page.screenshot({ path: '/tmp/rbac-todo-signin.png' });
});

test('browser login, PKCE consent, MCP access, refresh and revocation', async ({ page }) => {
  test.skip(!process.env.SUPABASE_ACCESS_TOKEN, 'Live test needs SUPABASE_ACCESS_TOKEN');
  const ref = 'tteazpolsuwfxqqqksoj';
  const base = `https://${ref}.supabase.co`;
  const resource = `${base}/functions/v1/rbac-todo/mcp`;
  const response = await fetch(`https://api.supabase.com/v1/projects/${ref}/api-keys`, {
    headers: { Authorization: `Bearer ${process.env.SUPABASE_ACCESS_TOKEN}` },
  });
  expect(response.ok).toBe(true);
  const keys: { name: string; api_key: string }[] = await response.json();
  const key = keys.find((item) => item.name === 'service_role')!.api_key;
  const admin = createClient(base, key, { auth: { persistSession: false, autoRefreshToken: false } });
  const email = `rbac-browser-${randomUUID()}@example.com`;
  const password = randomUUID();
  const { data: { user }, error } = await admin.auth.admin.createUser({ email, password, email_confirm: true });
  expect(error).toBeNull();
  let clientId = '';
  let callbackUrl: URL | undefined;
  const callback = createServer((request, reply) => {
    callbackUrl = new URL(request.url!, 'http://127.0.0.1');
    reply.writeHead(200, { 'Content-Type': 'text/html' });
    reply.end('<h1>Connected. Return to your client.</h1>');
  });
  await new Promise<void>((resolve) => callback.listen(0, '127.0.0.1', resolve));
  const address = callback.address();
  if (!address || typeof address === 'string') throw new Error('No callback address');
  const redirect = `http://127.0.0.1:${address.port}/callback`;
  try {
    const registered = await fetch(`${base}/auth/v1/oauth/clients/register`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_name: 'RBAC browser test', redirect_uris: [redirect], token_endpoint_auth_method: 'none', grant_types: ['authorization_code', 'refresh_token'], response_types: ['code'] }),
    });
    expect(registered.ok).toBe(true);
    const registration = await registered.json() as { client_id: string };
    clientId = registration.client_id;
    const verifier = Buffer.from(randomBytes(32)).toString('base64url');
    const state = randomUUID();
    const params = new URLSearchParams({ client_id: clientId, redirect_uri: redirect, response_type: 'code', scope: 'openid email profile offline_access', state, code_challenge: createHash('sha256').update(verifier).digest('base64url'), code_challenge_method: 'S256', resource });
    const authorize = await fetch(`${base}/auth/v1/oauth/authorize?${params}`, { redirect: 'manual' });
    expect(authorize.status).toBe(302);
    const location = new URL(authorize.headers.get('location')!);
    await page.goto(`/${location.search}`);
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Password', { exact: true }).fill('wrong-password');
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await expect(page.getByRole('alert')).toContainText('Invalid login credentials');
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Allow access' })).toBeVisible();
    await expect(page.getByText('RBAC browser test', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Allow access' }).click();
    await expect(page.getByRole('heading', { name: 'Connected. Return to your client.' })).toBeVisible();
    expect(callbackUrl?.searchParams.get('state')).toBe(state);
    const exchanged = await fetch(`${base}/auth/v1/oauth/token`, {
      method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ grant_type: 'authorization_code', client_id: clientId, redirect_uri: redirect, code: callbackUrl!.searchParams.get('code')!, code_verifier: verifier, resource }),
    });
    expect(exchanged.ok).toBe(true);
    const session = await exchanged.json() as { access_token: string; refresh_token: string };
    expect(Boolean(session.access_token && session.refresh_token)).toBe(true);
    const mcp = await fetch(resource, {
      method: 'POST', headers: { Authorization: `Bearer ${session.access_token}`, 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream' },
      body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'list_todos', arguments: {} } }),
    });
    expect(mcp.ok).toBe(true);
    const body = await mcp.text();
    expect(body).toContain('"text":"[]"');
    const refreshed = await fetch(`${base}/auth/v1/oauth/token`, {
      method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ grant_type: 'refresh_token', client_id: clientId, refresh_token: session.refresh_token }),
    });
    expect(refreshed.ok).toBe(true);
    const refreshedSession = await refreshed.json() as { access_token: string; refresh_token: string };
    expect(Boolean(refreshedSession.access_token)).toBe(true);
    if (process.env.RBAC_TEST_CODEX === '1') {
      const name = `rbac-todo-test-${randomUUID()}`;
      const config = ['-c', `mcp_servers.${name}.url="${resource}"`];
      const login = spawn('codex', [...config, 'mcp', 'login', name, '--oauth-client-registration', 'dcr'], { stdio: ['ignore', 'pipe', 'pipe'] });
      let output = '';
      let nativeClientId = '';
      const finished = new Promise<number | null>((resolve, reject) => {
        login.on('exit', resolve);
        login.on('error', reject);
      });
      login.stdout.on('data', (chunk) => { output += chunk.toString(); });
      login.stderr.on('data', (chunk) => { output += chunk.toString(); });
      try {
        await expect.poll(() => output.match(/https:\/\/[^\s]+oauth\/authorize\?[^\s]+/)?.[0], { timeout: 30000 }).toBeTruthy();
        const url = output.match(/https:\/\/[^\s]+oauth\/authorize\?[^\s]+/)![0];
        nativeClientId = new URL(url).searchParams.get('client_id')!;
        await page.goto(url);
        await expect(page.getByRole('button', { name: 'Allow access' })).toBeVisible();
        await page.getByRole('button', { name: 'Allow access' }).click();
        expect(await finished).toBe(0);
        expect(output).toContain('Successfully logged in');
      } finally {
        login.kill();
        execFileSync('codex', [...config, 'mcp', 'logout', name], { stdio: 'ignore' });
        if (nativeClientId) await admin.auth.admin.oauth.deleteClient(nativeClientId);
      }
    }

    const { error: revokeError } = await admin.auth.admin.signOut(refreshedSession.access_token, 'global');
    expect(revokeError).toBeNull();
    const revoked = await fetch(`${base}/auth/v1/oauth/token`, {
      method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ grant_type: 'refresh_token', client_id: clientId, refresh_token: refreshedSession.refresh_token }),
    });
    expect(revoked.ok).toBe(false);

  } finally {
    callback.close();
    if (clientId) await admin.auth.admin.oauth.deleteClient(clientId);
    if (user) expect((await admin.auth.admin.deleteUser(user.id)).error).toBeNull();
  }
});
