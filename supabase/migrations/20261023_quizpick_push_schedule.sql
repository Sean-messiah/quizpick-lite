-- Requires pg_cron and pg_net extensions, and a Vault secret named quizpick_dispatch_token.
-- Scheduled in Supabase separately after secret configuration.
create extension if not exists pg_cron with schema pg_catalog;
create extension if not exists pg_net with schema extensions;
select cron.schedule('quizpick-reviewed-push-15m','*/15 * * * *',
$cron$ select net.http_post(
 url:='https://ngozrhjczaattarydgnr.supabase.co/functions/v1/quizpick-push?action=dispatch',
 headers:=jsonb_build_object('Content-Type','application/json','x-quizpick-dispatch',
 (select decrypted_secret from vault.decrypted_secrets where name='quizpick_dispatch_token' limit 1)),
 body:='{}'::jsonb,timeout_milliseconds:=15000
) $cron$);
