import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.57.0";
import webpush from "npm:web-push@3.6.7";

const ALLOWED_ORIGIN = "https://sean-messiah.github.io";
const APPS = new Set(["toss","kakaobank","cashwalk","okquiz","shinhanpay","shinhanbank","kbpay","kbstar","cashdoc","bitbunny","hpoint","kbank","monimo"]);
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "";
const SERVICE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const client = createClient(SUPABASE_URL, SERVICE, { auth:{persistSession:false,autoRefreshToken:false} });
const enc = new TextEncoder();
function response(body:unknown,status=200,origin=ALLOWED_ORIGIN){
  return new Response(JSON.stringify(body),{status,headers:{
    "content-type":"application/json; charset=utf-8","cache-control":"no-store",
    "access-control-allow-origin":origin,"access-control-allow-methods":"GET,POST,OPTIONS",
    "access-control-allow-headers":"content-type","vary":"Origin"
  }});
}
async function hash(value:string) {
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256",enc.encode(value)));
  return [...digest].map(x=>x.toString(16).padStart(2,"0")).join("");
}
async function secrets(){
  const {data,error}=await client.rpc("quizpick_push_runtime_secret");
  if(error || !Array.isArray(data) || !data[0]?.public_key || !data[0]?.private_key || !data[0]?.dispatch_token) throw new Error("push secrets unavailable");
  return data[0] as {public_key:string,private_key:string,dispatch_token:string};
}
function endpointOkay(endpoint:unknown) {
  if(typeof endpoint!=="string" || endpoint.length>2048 || endpoint.length<35)return false;
  try {
    const u=new URL(endpoint);
    const h=u.hostname.toLowerCase();
    return u.protocol==="https:" && !u.username && !u.password && u.port==="" &&
      (h==="fcm.googleapis.com" || h==="updates.push.services.mozilla.com" ||
       h.endsWith(".push.apple.com") || h==="web.push.apple.com" ||
       h.endsWith(".notify.windows.com") || h==="wns2-db5p.notify.windows.com");
  } catch {return false;}
}
function validToken(value:unknown){return typeof value==="string" && /^[a-f0-9]{64}$/.test(value);}
function cleanTopics(raw:unknown):string[]{
  if(!Array.isArray(raw))return [];
  return [...new Set(raw.filter((v):v is string=>typeof v==="string"&&APPS.has(v)))].slice(0,13);
}
function verifiedSubscription(v:any){
  return v && endpointOkay(v.endpoint) && v.keys && typeof v.keys==="object" &&
   typeof v.keys.p256dh==="string" && /^[a-zA-Z0-9_-]{32,255}$/.test(v.keys.p256dh) &&
   typeof v.keys.auth==="string" && /^[a-zA-Z0-9_-]{10,100}$/.test(v.keys.auth);
}
function dateIsTodayOrYesterday(date:string){
  const now=new Date();
  const kst=new Date(now.getTime()+9*3600000).toISOString().slice(0,10);
  const yest=new Date(now.getTime()+9*3600000-86400000).toISOString().slice(0,10);
  return date===kst||date===yest;
}
async function send(sub:any, payload:Record<string,string>, keys:any) {
  // Browser PushSubscription.toJSON() nests keys; DB rows store them flat.
  // Support both shapes instead of sending undefined keys for browser tests.
  const encryptionKeys = sub.keys && typeof sub.keys === "object"
    ? { p256dh:sub.keys.p256dh, auth:sub.keys.auth }
    : { p256dh:sub.p256dh, auth:sub.auth };
  if (!encryptionKeys.p256dh || !encryptionKeys.auth) {
    throw new Error("Missing browser push encryption keys");
  }
  return await webpush.sendNotification(
    {endpoint:sub.endpoint,keys:encryptionKeys},
    JSON.stringify(payload),
    {vapidDetails:{subject:ALLOWED_ORIGIN,publicKey:keys.public_key,privateKey:keys.private_key},
     TTL:14400,urgency:"normal",contentEncoding:"aes128gcm",timeout:10000}
  );
}
async function dispatch(keys:any){
  // Publication gate: only manually reviewed, timestamped entries; never push scraped/unconfirmed answers.
  const url=ALLOWED_ORIGIN+"/quizpick-lite/manual-quizzes.json";
  const feed=await fetch(url,{headers:{"accept":"application/json"},signal:AbortSignal.timeout(12000)});
  if(!feed.ok)throw new Error("approved feed fetch failed");
  const data=await feed.json();
  const rows=Array.isArray(data?.quizzes)?data.quizzes:[];
  const approved=rows.filter((r:any)=>r?.reviewed===true &&
      typeof r?.id==="string" && /^[a-zA-Z0-9_-]{4,100}$/.test(r.id) &&
      APPS.has(r.app) && dateIsTodayOrYesterday(String(r.date||"")) &&
      typeof r.answer==="string" && r.answer.trim().length>0 &&
      typeof r.reviewed_at_kst==="string" && !Number.isNaN(Date.parse(r.reviewed_at_kst)) &&
      Date.now()-Date.parse(r.reviewed_at_kst)>=0 &&
      Date.now()-Date.parse(r.reviewed_at_kst)<24*3600000
  ).slice(0,20);
  if(!approved.length)return {sent:0,failed:0,approved:0,notes:"No freshly reviewed quiz entries"};
  const {data:subs,error}=await client.from("quizpick_push_subscriptions")
    .select("id,endpoint,p256dh,auth,topics,consent_at")
    .eq("active",true).eq("cadence","instant").order("created_at",{ascending:true}).limit(200);
  if(error)throw error;
  let sent=0,failed=0;
  for(const sub of subs||[]){
    for(const item of approved){
      const at=Date.parse(item.reviewed_at_kst);
      if(!sub.topics?.includes(item.app) || Date.parse(sub.consent_at)>at) continue;
      // Insert claim is atomic. Unique key suppresses already-sent and concurrent duplicate alerts.
      const claim=await client.from("quizpick_push_delivery").insert({subscription_id:sub.id,quiz_id:item.id,status:"claimed"});
      if(claim.error)continue;
      try{
        const path="/quizpick-lite/quiz/"+encodeURIComponent(item.app)+"/"+encodeURIComponent(item.date)+"/"+encodeURIComponent(item.id)+"/";
        await send(sub,{title:"퀴즈픽 · "+item.app+" 정답 알림",body:"참고 정답: "+String(item.answer).trim().slice(0,180)+" · 원본 앱에서 회차 재확인",url:ALLOWED_ORIGIN+path,tag:"quizpick-"+item.id},keys);
        await client.from("quizpick_push_delivery").update({status:"sent",sent_at:new Date().toISOString()}).eq("subscription_id",sub.id).eq("quiz_id",item.id);
        sent++;
      }catch(err){
        failed++;
        if([404,410].includes(Number((err as any)?.statusCode)))await client.from("quizpick_push_subscriptions").delete().eq("id",sub.id);
        else await client.from("quizpick_push_delivery").delete().eq("subscription_id",sub.id).eq("quiz_id",item.id);
      }
    }
  }
  return {sent,failed,approved:approved.length};
}
Deno.serve(async req=>{
  if(req.method==="OPTIONS"){
    if(req.headers.get("origin")!==ALLOWED_ORIGIN)return response({error:"origin not allowed"},403);
    return response({ok:true});
  }
  const u=new URL(req.url);
  const isDispatch=req.method==="POST"&&u.searchParams.get("action")==="dispatch";
  // Require same-origin browser requests; Cron requests must present a dedicated secret.
  if(!isDispatch && req.headers.get("origin")!==ALLOWED_ORIGIN &&
     !(req.method==="GET" && !req.headers.has("origin")))return response({error:"origin not allowed"},403);
  try{
    const keys=await secrets();
    if(req.method==="GET")return response({enabled:true,publicKey:keys.public_key,topics:[...APPS]});
    if(req.method!=="POST")return response({error:"method"},405);
    if(isDispatch){
      const incoming=req.headers.get("x-quizpick-dispatch")||"";
      if(!incoming || await hash(incoming)!==await hash(keys.dispatch_token))return response({error:"not authorized"},403);
      return response(await dispatch(keys));
    }
    if(Number(req.headers.get("content-length")||"0")>8192)return response({error:"too large"},413);
    const data=await req.json();
    const action=data?.action;
    if(!validToken(data?.deviceToken))return response({error:"bad device key"},400);
    const device_hash=await hash(data.deviceToken);
    if(!verifiedSubscription(data?.subscription))return response({error:"bad push subscription"},400);
    const sub=data.subscription;
    const endpoint_hash=await hash(sub.endpoint);
    const {data:existing,error:readError}=await client.from("quizpick_push_subscriptions")
      .select("id,device_hash,last_test_at,created_at,topics,active").eq("endpoint_hash",endpoint_hash).maybeSingle();
    if(readError)throw readError;
    if(existing && existing.device_hash!==device_hash)return response({error:"subscription belongs to another browser token"},409);
    if(action==="status"){
      return response({
        ok:true,registered:!!existing?.active,
        topics:existing?.active ? (existing.topics||[]) : [],
        lastTestAcceptedAt:existing?.active ? (existing.last_test_at||null) : null
      });
    }
    if(action==="subscribe"){
      const topics=cleanTopics(data.topics);
      if(!topics.length)return response({error:"Choose at least one service"},400);
      const row={endpoint:sub.endpoint,endpoint_hash,device_hash,p256dh:sub.keys.p256dh,auth:sub.keys.auth,
        topics,cadence:"instant",active:true,consent_at:new Date().toISOString(),consent_version:"2026-10-v1",updated_at:new Date().toISOString()};
      // Anonymous registrations are consent-driven. One row per unique push endpoint.
      if(!existing){
        const {error}=await client.from("quizpick_push_subscriptions").insert(row);if(error)throw error;
      }else{
        const {error}=await client.from("quizpick_push_subscriptions").update(row).eq("id",existing.id);if(error)throw error;
      }
      return response({ok:true,subscribed:true,topics});
    }
    if(action==="unsubscribe"){
      if(existing){
        const {error}=await client.from("quizpick_push_subscriptions").delete().eq("id",existing.id);
        if(error)throw error;
      }
      return response({ok:true,subscribed:false});
    }
    if(action==="test"){
      if(!existing?.active)return response({error:"subscribe first"},409);
      // Attempts recorded before the bug fix were all failed sends. Do not
      // apply cooldown to those failed attempts.
      const fixedAt = Date.parse("2026-10-23T17:30:00Z");
      const priorTestAt = existing.last_test_at ? Date.parse(existing.last_test_at) : 0;
      if(priorTestAt>=fixedAt && Date.now()-priorTestAt<15*60*1000)
        return response({error:"테스트 알림은 성공 후 15분 간격으로 보낼 수 있습니다."},429);
      // Throttle only successful sends. A failed send must not lock the
      // user out for 15 minutes while troubleshooting.
      await send(sub,{title:"퀴즈픽 알림 테스트 💗",body:"정상 연결됐어요. 검수된 새 정답이 등록되면 알려드릴게요.",url:ALLOWED_ORIGIN+"/quizpick-lite/alerts/",tag:"quizpick-test"},keys);
      const {error}=await client.from("quizpick_push_subscriptions").update({last_test_at:new Date().toISOString()}).eq("id",existing.id);
      if(error)console.error("test throttle update failed");
      return response({ok:true,delivery:"sent"});
    }
    return response({error:"invalid action"},400);
  }catch(err){
    console.error("push error",String((err as Error)?.message||err).slice(0,180));
    return response({error:"알림 서버 요청을 처리하지 못했습니다."},503);
  }
});