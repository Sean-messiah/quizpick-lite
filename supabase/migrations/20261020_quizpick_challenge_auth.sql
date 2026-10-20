-- QuizPick 100-day challenge. Apply to a verified project using Supabase Migrations.
-- Never place secret/service_role API keys in the GitHub Pages frontend.
-- All data are user-entered self-tracker records, not verified reward balances.
begin;

create table if not exists public.quizpick_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  nickname text not null check (char_length(trim(nickname)) between 2 and 16),
  created_at timestamptz not null default now()
);

create table if not exists public.quizpick_goals (
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null check (kind in ('fifty','hundred','gold')),
  start_date date not null,
  goal_amount_won integer not null default 0 check (goal_amount_won between 0 and 100000000),
  created_at timestamptz not null default now(),
  primary key (user_id, kind)
);

create table if not exists public.quizpick_entries (
  user_id uuid not null references auth.users(id) on delete cascade,
  kind text not null,
  entry_date date not null,
  amount_won integer not null check (amount_won between 1 and 1000000),
  updated_at timestamptz not null default now(),
  primary key (user_id, kind, entry_date),
  constraint quizpick_entries_goal_fk
    foreign key (user_id,kind)
    references public.quizpick_goals(user_id,kind)
    on delete cascade
);

create index if not exists quizpick_entries_user_day_idx
  on public.quizpick_entries (user_id, entry_date desc);

alter table public.quizpick_profiles enable row level security;
alter table public.quizpick_goals enable row level security;
alter table public.quizpick_entries enable row level security;

-- No public access. Real authenticated users only, restricted to their own rows.
-- The is_anonymous JWT flag blocks anonymous sign-in accounts if enabled later.
create policy "profiles_owner_all"
  on public.quizpick_profiles for all to authenticated
  using (user_id=(select auth.uid()) and coalesce((auth.jwt()->>'is_anonymous')::boolean,false)=false)
  with check (user_id=(select auth.uid()) and coalesce((auth.jwt()->>'is_anonymous')::boolean,false)=false);

create policy "goals_owner_all"
  on public.quizpick_goals for all to authenticated
  using (user_id=(select auth.uid()) and coalesce((auth.jwt()->>'is_anonymous')::boolean,false)=false)
  with check (user_id=(select auth.uid()) and coalesce((auth.jwt()->>'is_anonymous')::boolean,false)=false);

create policy "entries_owner_all"
  on public.quizpick_entries for all to authenticated
  using (user_id=(select auth.uid()) and coalesce((auth.jwt()->>'is_anonymous')::boolean,false)=false)
  with check (user_id=(select auth.uid()) and coalesce((auth.jwt()->>'is_anonymous')::boolean,false)=false);

revoke all on public.quizpick_profiles, public.quizpick_goals, public.quizpick_entries from anon;
grant usage on schema public to authenticated;
grant select,insert,update,delete on public.quizpick_profiles, public.quizpick_goals, public.quizpick_entries to authenticated;

commit;
