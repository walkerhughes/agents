alter table public.todos add column user_id uuid references auth.users(id) on delete cascade;

-- The old demo had no ownership. Refuse to guess if multiple admins exist.
do $$
begin
  if exists (select 1 from public.todos) then
    if (select count(*) from public.todo_members where role = 'admin') <> 1 then
      raise exception 'Assign an explicit owner to existing todos before migrating';
    end if;
    update public.todos set user_id = (select user_id from public.todo_members where role = 'admin');
  end if;
end;
$$;

alter table public.todos alter column user_id set default auth.uid();
alter table public.todos alter column user_id set not null;
drop index public.todos_created_at_id_idx;
create index todos_user_created_id_idx on public.todos (user_id, created_at desc, id desc);

create function public.create_todo_membership()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.todo_members (user_id, role) values (new.id, 'admin');
  return new;
end;
$$;
revoke all on function public.create_todo_membership() from public, anon, authenticated;
create trigger create_todo_membership after insert on auth.users
  for each row execute function public.create_todo_membership();
insert into public.todo_members (user_id, role)
  select id, 'admin' from auth.users on conflict (user_id) do nothing;

drop policy "Members read todos" on public.todos;
drop policy "Admins insert todos" on public.todos;
drop policy "Admins update todos" on public.todos;
drop policy "Admins delete todos" on public.todos;

create policy "Owners read todos" on public.todos for select to authenticated
  using (user_id = (select auth.uid()) and
    (select role from public.todo_members where user_id = (select auth.uid())) in ('admin', 'member'));
create policy "Owners insert todos" on public.todos for insert to authenticated
  with check (user_id = (select auth.uid()) and
    (select role from public.todo_members where user_id = (select auth.uid())) = 'admin');
create policy "Owners update todos" on public.todos for update to authenticated
  using (user_id = (select auth.uid()) and
    (select role from public.todo_members where user_id = (select auth.uid())) = 'admin')
  with check (user_id = (select auth.uid()) and
    (select role from public.todo_members where user_id = (select auth.uid())) = 'admin');
create policy "Owners delete todos" on public.todos for delete to authenticated
  using (user_id = (select auth.uid()) and
    (select role from public.todo_members where user_id = (select auth.uid())) = 'admin');
