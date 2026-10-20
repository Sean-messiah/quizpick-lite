-- Daily quiz participation self-tracker. An app's actual payout is never asserted.
-- Keep old 50/100-won goal tables and records unchanged.
create table if not exists public.quizpick_daily_activities (
  user_id uuid not null references auth.users(id) on delete cascade,
  quiz_id text not null check (char_length(quiz_id) between 4 and 100),
  quiz_date date not null,
  app_slug text not null check (char_length(app_slug) between 1 and 60),
  app_name text not null check (char_length(app_name) between 1 and 100),
  quiz_title text not null check (char_length(quiz_title) between 1 and 200),
  is_done boolean not null default false,
  reward_amount integer not null default 0 check (reward_amount between 0 and 1000000),
  reward_unit text not null default '원' check (reward_unit in ('원','P','캐시','기타')),
  updated_at timestamptz not null default now(),
  primary key (user_id, quiz_id)
);
create index if not exists quizpick_daily_activities_user_date_idx
  on public.quizpick_daily_activities (user_id, quiz_date desc);
alter table public.quizpick_daily_activities enable row level security;
create policy "quizpick_daily_self_only" on public.quizpick_daily_activities
for all to authenticated
using (user_id=(select auth.uid()) and coalesce((auth.jwt()->>'is_anonymous')::boolean,false)=false)
with check (user_id=(select auth.uid()) and coalesce((auth.jwt()->>'is_anonymous')::boolean,false)=false);
revoke all on public.quizpick_daily_activities from anon;
grant select,insert,update,delete on public.quizpick_daily_activities to authenticated;
