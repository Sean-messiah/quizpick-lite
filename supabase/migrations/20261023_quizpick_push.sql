-- QuizPick consent-only Web Push. IMPORTANT: deploy with private Vault keys separately; never commit secrets.
create table if not exists public.quizpick_push_subscriptions (
 id uuid primary key default gen_random_uuid(),
 endpoint text not null check (char_length(endpoint) between 35 and 2048),
 endpoint_hash text not null unique check (char_length(endpoint_hash)=64),
 device_hash text not null check (char_length(device_hash)=64),
 p256dh text not null check (char_length(p256dh) between 32 and 255),
 auth text not null check (char_length(auth) between 10 and 100),
 topics text[] not null default array['toss','kakaobank']::text[],
 cadence text not null default 'instant' check(cadence='instant'),
 active boolean not null default true,
 consent_at timestamptz not null default now(),
 consent_version text not null default '2026-10-v1',
 last_test_at timestamptz,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create index if not exists quizpick_push_active_idx on public.quizpick_push_subscriptions(active,created_at) where active;
create table if not exists public.quizpick_push_delivery (
 subscription_id uuid not null references public.quizpick_push_subscriptions(id) on delete cascade,
 quiz_id text not null check(char_length(quiz_id) between 2 and 100),
 status text not null default 'claimed' check(status in ('claimed','sent')),
 created_at timestamptz not null default now(),
 sent_at timestamptz,
 primary key(subscription_id,quiz_id)
);
create index if not exists quizpick_push_delivery_created_idx on public.quizpick_push_delivery(created_at);
alter table public.quizpick_push_subscriptions enable row level security;
alter table public.quizpick_push_delivery enable row level security;
revoke all on public.quizpick_push_subscriptions,public.quizpick_push_delivery from anon,authenticated;
grant all on public.quizpick_push_subscriptions,public.quizpick_push_delivery to service_role;
create or replace function public.quizpick_push_runtime_secret()
returns table(public_key text,private_key text,dispatch_token text)
language sql security definer set search_path=''
as $f$
select (select decrypted_secret from vault.decrypted_secrets where name='quizpick_vapid_public_key' order by created_at desc limit 1),
       (select decrypted_secret from vault.decrypted_secrets where name='quizpick_vapid_private_key' order by created_at desc limit 1),
       (select decrypted_secret from vault.decrypted_secrets where name='quizpick_dispatch_token' order by created_at desc limit 1)
$f$;
revoke all on function public.quizpick_push_runtime_secret() from public,anon,authenticated;
grant execute on function public.quizpick_push_runtime_secret() to service_role;
