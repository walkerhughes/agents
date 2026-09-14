create table public.todo_members (
  user_id uuid primary key references auth.users(id) on delete cascade,
  role text not null check (role in ('admin', 'member'))
);

alter table public.todo_members enable row level security;
revoke all on public.todo_members from anon, authenticated;
grant select on public.todo_members to authenticated;
grant all on public.todo_members to service_role;

create policy "Read own membership" on public.todo_members
  for select to authenticated
  using (user_id = (select auth.uid()));

create table public.todos (
  id uuid primary key default gen_random_uuid(),
  title text not null check (char_length(btrim(title)) between 1 and 500),
  completed boolean not null default false,
  created_at timestamptz not null default now()
);

create index todos_created_at_id_idx on public.todos (created_at desc, id desc);
alter table public.todos enable row level security;
revoke all on public.todos from anon, authenticated;
grant select, insert, delete on public.todos to authenticated;
grant update (title, completed) on public.todos to authenticated;
grant all on public.todos to service_role;

create policy "Members read todos" on public.todos
  for select to authenticated
  using ((select role from public.todo_members where user_id = (select auth.uid()))
    in ('admin', 'member'));

create policy "Admins insert todos" on public.todos
  for insert to authenticated
  with check ((select role from public.todo_members where user_id = (select auth.uid())) = 'admin');

create policy "Admins update todos" on public.todos
  for update to authenticated
  using ((select role from public.todo_members where user_id = (select auth.uid())) = 'admin')
  with check ((select role from public.todo_members where user_id = (select auth.uid())) = 'admin');

create policy "Admins delete todos" on public.todos
  for delete to authenticated
  using ((select role from public.todo_members where user_id = (select auth.uid())) = 'admin');
