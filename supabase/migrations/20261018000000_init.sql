-- Baseline: extensions and per-user profiles.
-- Feature tables (reels, jobs, slack_*) arrive with their phases; see the v1 design spec §8.

create extension if not exists vector with schema extensions;

create table public.profiles (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  timezone   text not null default 'UTC',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.profiles is 'One row per auth user; created by trigger on signup.';

-- Row-level security on every table, always. The API connects with a server role and
-- scopes queries itself; RLS is the backstop if anything ever talks to PostgREST directly.
alter table public.profiles enable row level security;

create policy "profiles: owner can read"
  on public.profiles for select
  to authenticated
  using ((select auth.uid()) = user_id);

create policy "profiles: owner can update"
  on public.profiles for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

create function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (user_id) values (new.id);
  return new;
end;
$$;

revoke execute on function public.handle_new_user() from public, anon, authenticated;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
