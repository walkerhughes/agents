"use client";

import Link from "next/link";
import { useEffect, useState, type SubmitEvent } from "react";
import { createClient, type OAuthAuthorizationDetails, type Session, type SupabaseClient } from "@supabase/supabase-js";
import { ArrowRight, Check, CheckCheck, LoaderCircle, LockKeyhole } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function Home() {
  const [client, setClient] = useState<SupabaseClient | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [authorizationId, setAuthorizationId] = useState("");
  const [details, setDetails] = useState<OAuthAuthorizationDetails | null>(null);
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const db = createClient("https://tteazpolsuwfxqqqksoj.supabase.co", "sb_publishable_PvaOE2UNJbUnBb9bEa_VNg_c_Tt9QVz", {
      auth: { flowType: "pkce", detectSessionInUrl: true },
    });
    const { data: { subscription } } = db.auth.onAuthStateChange((_event, current) => {
      setSession(current);
      setReady(true);
    });
    void db.auth.getSession().then(({ data, error }) => {
      setClient(db);
      setAuthorizationId(new URLSearchParams(window.location.search).get("authorization_id") ?? "");
      setSession(data.session);
      if (error) setError(error.message);
      setReady(true);
    });
    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!client || !session || !authorizationId) return;
    let active = true;
    void client.auth.oauth.getAuthorizationDetails(authorizationId).then(({ data, error }) => {
      if (!active) return;
      if (error) setError("This connection request has expired or is invalid. Run the login command again.");
      else if ("redirect_url" in data) window.location.assign(data.redirect_url);
      else setDetails(data);
    });
    return () => { active = false; };
  }, [client, session, authorizationId]);

  function redirectTo() {
    const url = new URL("/", window.location.origin);
    if (authorizationId) url.searchParams.set("authorization_id", authorizationId);
    return url.toString();
  }

  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!client) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const { data, error } = mode === "signin"
        ? await client.auth.signInWithPassword({ email, password })
        : await client.auth.signUp({ email, password, options: { emailRedirectTo: redirectTo() } });
      if (error) throw error;
      setPassword("");
      if (!data.session) setNotice("Check your email to confirm your account, then return here to sign in.");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not sign in. Please try again.");
    } finally { setBusy(false); }
  }

  async function consent(approve: boolean) {
    if (!client || !details) return;
    setBusy(true); setError("");
    try {
      const { data, error } = approve
        ? await client.auth.oauth.approveAuthorization(details.authorization_id, { skipBrowserRedirect: true })
        : await client.auth.oauth.denyAuthorization(details.authorization_id, { skipBrowserRedirect: true });
      if (error) throw error;
      window.location.assign(data.redirect_url);
    } catch {
      setError("Could not complete the connection. Run the login command again.");
      setBusy(false);
    }
  }

  async function signOut() {
    if (!client) return;
    setBusy(true);
    const { error } = await client.auth.signOut({ scope: "local" });
    if (error) setError(error.message);
    else { setDetails(null); setNotice(""); setError(""); }
    setBusy(false);
  }

  const heading = session ? (authorizationId ? "Connect your to-dos" : "You're signed in") : mode === "signin" ? "Welcome back" : "A little less to remember";
  return (
    <main className="auth-shell">
      <Link className="brand" href="/" aria-label="RBAC To-do home"><span className="brand-icon"><CheckCheck size={20} /></span>rbac-todo</Link>
      <section className="auth-panel" aria-labelledby="heading">
        <Card className="auth-card">
          <CardHeader className="space-y-3 p-0">
            <span className="eyebrow">YOUR LIST. YOUR SPACE.</span>
            <h1 id="heading">{heading}</h1>
            <p className="description">{session ? "Your to-dos stay private to your account." : mode === "signin" ? "Sign in to pick up where you left off." : "Create an account for your personal to-do list."}</p>
          </CardHeader>
          <CardContent className="p-0 pt-7">
            {!ready ? <output className="muted flex items-center gap-2"><LoaderCircle className="animate-spin" size={16} />Getting things ready...</output> : session ? (
              <div className="space-y-5">
                <div className="account"><span className="account-icon"><Check size={18} /></span><span>{session.user.email}</span></div>
                {details ? <>
                  <p className="description"><strong>{details.client.name || "Your MCP client"}</strong> wants permission to connect to your to-do list.</p>
                  <div className="permissions"><p>Access requested</p><ul><li>View your personal to-dos</li><li>Manage your to-dos when your role allows it</li></ul><p className="muted mt-3">Account permissions: {details.scope}</p></div>
                  <Button className="primary-button" disabled={busy} onClick={() => consent(true)}>{busy ? <LoaderCircle className="animate-spin" /> : <>Allow access <ArrowRight /></>}</Button>
                  <Button className="w-full" variant="ghost" disabled={busy} onClick={() => consent(false)}>Cancel</Button>
                </> : authorizationId ? <output className="description">{error ? "Start a new login from your MCP client to continue." : "Loading connection request..."}</output> : <div className="success-box"><CheckCheck size={24} /><p>You can return to your MCP client and run its login command to connect this account.</p></div>}
                <Button className="w-full muted" variant="ghost" disabled={busy} onClick={signOut}>Use a different account</Button>
              </div>
            ) : (
              <form onSubmit={submit} className="space-y-5">
                <div className="space-y-2"><Label htmlFor="email">Email</Label><Input id="email" type="email" autoComplete="email" placeholder="you@example.com" required value={email} onChange={(e) => setEmail(e.target.value)} disabled={busy} className="auth-input" /></div>
                <div className="space-y-2"><Label htmlFor="password">Password</Label><Input id="password" type="password" autoComplete={mode === "signup" ? "new-password" : "current-password"} minLength={mode === "signup" ? 8 : undefined} maxLength={256} required value={password} onChange={(e) => setPassword(e.target.value)} disabled={busy} className="auth-input" />{mode === "signup" && <p className="muted text-sm">At least 8 characters.</p>}</div>
                <Button type="submit" className="primary-button" disabled={busy}>{busy ? <><LoaderCircle className="animate-spin" />Please wait</> : <>{mode === "signin" ? "Sign in" : "Create account"}<ArrowRight /></>}</Button>
                <p className="switch-mode">{mode === "signin" ? "New here?" : "Already have an account?"} <button type="button" disabled={busy} onClick={() => { setMode(mode === "signin" ? "signup" : "signin"); setError(""); setNotice(""); }}>{mode === "signin" ? "Create an account" : "Sign in"}</button></p>
              </form>
            )}
            {notice && <output className="notice">{notice}</output>}
            {error && <p role="alert" className="error">{error}</p>}
          </CardContent>
        </Card>
        <p className="privacy"><LockKeyhole size={14} /> Only you can access your personal to-dos.</p>
      </section>
      <footer>One less thing on your mind.</footer>
    </main>
  );
}
