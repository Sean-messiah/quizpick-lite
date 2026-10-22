'use strict';
(() => {
  const BASE = '/quizpick-lite/';
  const KEY='quizpick_push_device_v1';
  const PREF='quizpick_push_pref_v1';
  const names={toss:'토스',kakaobank:'카카오뱅크',cashwalk:'캐시워크',okquiz:'오퀴즈',shinhanpay:'신한 SOL페이',shinhanbank:'신한 SOL뱅크',kbpay:'KB Pay',kbstar:'KB스타뱅킹',cashdoc:'캐시닥',bitbunny:'비트버니',hpoint:'H.Point',kbank:'케이뱅크',monimo:'모니모'};
  const root=document.getElementById('push-settings');
  const $=id=>document.getElementById(id);
  let config=null, apiKey=null, registration=null;
  const state=text=>{if($('push-status'))$('push-status').textContent=text;};
  const token=()=>{
    try{
      let t=localStorage.getItem(KEY);
      if(t && /^[a-f0-9]{64}$/.test(t)) return t;
      const bytes=crypto.getRandomValues(new Uint8Array(32));
      t=[...bytes].map(x=>x.toString(16).padStart(2,'0')).join('');
      localStorage.setItem(KEY,t);return t;
    }catch(_){return null;}
  };
  function selected(){return [...document.querySelectorAll('[name="push-topic"]:checked')].map(x=>x.value);}
  function bytes(v){
    const padded=v+'='.repeat((4-v.length%4)%4);
    const raw=atob(padded.replace(/-/g,'+').replace(/_/g,'/'));
    return Uint8Array.from(raw,c=>c.charCodeAt(0));
  }
  async function post(action,subscription,topics){
    if(!config?.apiUrl)throw Error('알림 서버가 연결되지 않았습니다.');
    const deviceToken=token();
    if(!deviceToken)throw Error('브라우저 저장공간을 사용할 수 없습니다.');
    const resp=await fetch(config.apiUrl,{method:'POST',mode:'cors',cache:'no-store',
      headers:{'content-type':'application/json'},body:JSON.stringify({action,subscription,deviceToken,topics})});
    const result=await resp.json().catch(()=>({}));
    if(!resp.ok)throw Error(result?.error||'서버 응답 오류');
    return result;
  }
  async function getReg(){
    if(registration)return registration;
    registration=await navigator.serviceWorker.register(BASE+'sw.js',{scope:BASE,updateViaCache:'none'});
    await navigator.serviceWorker.ready;
    return registration;
  }
  function persistPrefs(topics){
    try{localStorage.setItem(PREF,JSON.stringify(topics));}catch(_){}
  }
  function oldPrefs(){
    try{const x=JSON.parse(localStorage.getItem(PREF)||'null');return Array.isArray(x)?x:['toss','kakaobank'];}
    catch(_){return ['toss','kakaobank'];}
  }
  async function init(){
    if(!('serviceWorker' in navigator)) {
      if(root)state('현재 브라우저에서는 웹 푸시가 지원되지 않습니다. Chrome 또는 지원 브라우저를 이용해 주세요.');
      return;
    }
    // PWA service worker is registered without ever requesting notification permission.
    try{await getReg();}catch(_){if(root)state('앱 알림 서비스를 등록할 수 없습니다. 새로고침해 주세요.');return;}
    if(!root)return;
    if(!('Notification' in window)||!('PushManager' in window)){
      state('이 브라우저에서는 백그라운드 알림을 지원하지 않습니다.');return;
    }
    if(/iPad|iPhone|iPod/.test(navigator.userAgent) && !window.navigator.standalone && !window.matchMedia('(display-mode: standalone)').matches){
      state('아이폰에서는 Safari 공유 → 홈 화면에 추가한 다음 설치한 퀴즈픽에서 알림을 켜주세요.');
    }
    try{
      const resp=await fetch(BASE+'push-config.json',{cache:'no-store'});config=await resp.json();
      if(!config.enabled)throw Error('현재 알림 기능은 준비 중입니다.');
      const meta=await fetch(config.apiUrl,{mode:'cors',cache:'no-store'});
      const conf=await meta.json();if(!meta.ok||!conf.enabled||!conf.publicKey)throw Error('서버를 연결하지 못했습니다.');
      apiKey=conf.publicKey;
      const saved=oldPrefs();
      const list=$('push-topics');list.replaceChildren();
      for(const name of conf.topics||[]){
        if(!Object.prototype.hasOwnProperty.call(names,name))continue;
        const label=document.createElement('label');label.className='push-topic';
        const box=document.createElement('input');box.type='checkbox';box.name='push-topic';box.value=name;box.checked=saved.includes(name);
        const span=document.createElement('span');span.textContent=names[name];
        label.append(box,span);list.append(label);
      }
      $('push-enable').disabled=false;
      const existing=await registration.pushManager.getSubscription();
      if(existing){
        $('push-disable').disabled=false;
        $('push-test').disabled=false;
        state('이 브라우저에 푸시 구독이 있습니다. 수신 서비스를 변경하거나 해지할 수 있어요.');
      }else if(Notification.permission==='denied'){
        state('알림 권한이 차단되어 있습니다. 브라우저의 사이트 설정에서 알림을 허용해 주세요.');
      }else{
        state('받고 싶은 서비스를 고르고 수신 동의 후 알림 받기를 눌러주세요.');
      }
    }catch(err){
      state('알림 서비스를 연결할 수 없습니다. '+String(err.message||'').slice(0,80));
    }
  }
  if(root){
    $('push-enable').addEventListener('click',async ()=>{
      if(!apiKey)return;
      if(!$('push-consent').checked){state('알림 수신에 동의한 후 신청해 주세요.');return;}
      const topics=selected();if(!topics.length){state('알림 받을 앱을 하나 이상 선택해 주세요.');return;}
      $('push-enable').disabled=true;
      try{
        // Must request permission from the direct button click (never on page load).
        const permission=Notification.permission==='granted'?'granted':await Notification.requestPermission();
        if(permission!=='granted')throw Error('브라우저 알림 권한이 허용되지 않았습니다.');
        const reg=await getReg();
        let sub=await reg.pushManager.getSubscription();
        if(!sub)sub=await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:bytes(apiKey)});
        await post('subscribe',sub.toJSON(),topics);
        persistPrefs(topics);
        $('push-disable').disabled=false;$('push-test').disabled=false;
        $('push-consent').checked=false;
        state('구독 완료! 검수된 새 정답이 올라오면 선택한 앱의 알림을 보내드려요. 💗');
        if(window.gtag)gtag('event','push_subscribe',{topics_count:topics.length});
      }catch(err){state('구독하지 못했습니다: '+String(err.message||err).slice(0,100));}
      finally{$('push-enable').disabled=false;}
    });
    $('push-disable').addEventListener('click',async ()=>{
      $('push-disable').disabled=true;
      try{
        const sub=await (await getReg()).pushManager.getSubscription();
        if(sub){
          await post('unsubscribe',sub.toJSON(),[]);
          await sub.unsubscribe();
        }
        $('push-test').disabled=true;
        state('알림 구독을 해지했습니다. 서버의 수신 대상에서도 제외했어요.');
        if(window.gtag)gtag('event','push_unsubscribe');
      }catch(err){state('해지 확인 실패: '+String(err.message||err).slice(0,90));}
      finally{$('push-disable').disabled=false;}
    });
    $('push-test').addEventListener('click',async ()=>{
      $('push-test').disabled=true;
      try{
        const sub=await (await getReg()).pushManager.getSubscription();
        if(!sub)throw Error('먼저 알림을 구독해 주세요.');
        await post('test',sub.toJSON(),selected());
        state('서버에서 테스트 알림을 발송했습니다. 휴대폰 알림창을 확인해 주세요.');
      }catch(err){state('테스트 실패: '+String(err.message||err).slice(0,100));}
      finally{$('push-test').disabled=false;}
    });
  }
  let installEvent=null;
  window.addEventListener('beforeinstallprompt',event=>{
    event.preventDefault();installEvent=event;
    const btn=$('push-install');if(btn)btn.hidden=false;
  });
  $('push-install')?.addEventListener('click',async()=>{
    if(!installEvent)return;await installEvent.prompt();installEvent=null;
    $('push-install').hidden=true;
  });
  init();
})();