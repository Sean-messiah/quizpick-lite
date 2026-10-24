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
  const health=(id,text,kind='neutral')=>{const el=$(id);if(el){el.textContent=text;el.dataset.state=kind;}};
  const formattedTime=iso=>{
    if(!iso)return '기록 없음';
    const d=new Date(iso);
    return Number.isNaN(+d)?'확인 불가':new Intl.DateTimeFormat('ko-KR',{
      timeZone:'Asia/Seoul',month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'
    }).format(d);
  };
  async function receiptFromWorker(reg) {
    if(!reg?.active || typeof MessageChannel==='undefined')return null;
    return new Promise(resolve=>{
      const channel=new MessageChannel();
      let complete=false;
      const done=v=>{if(complete)return;complete=true;channel.port1.close();resolve(v);};
      channel.port1.onmessage=e=>done(e.data?.at||null);
      reg.active.postMessage({type:'QUIZPICK_PUSH_LAST'},[channel.port2]);
      setTimeout(()=>done(null),1800);
    });
  }
  async function refreshDiagnostics() {
    if(!root)return;
    const capable=('serviceWorker' in navigator)&&('PushManager' in window)&&('Notification' in window);
    health('push-health-support',capable?'지원되는 브라우저':'지원 불가',capable?'ok':'bad');
    const permission=('Notification' in window)?Notification.permission:'unsupported';
    health('push-health-permission',permission==='granted'?'허용됨':permission==='denied'?'차단됨':permission==='default'?'허용 전':'지원 불가',
      permission==='granted'?'ok':permission==='denied'?'bad':'neutral');
    if(!capable){
      health('push-health-browser','푸시 사용 불가','bad');
      health('push-health-server','연결 확인 불가');
      return;
    }
    try{
      const reg=await getReg();
      const sub=await reg.pushManager.getSubscription();
      health('push-health-browser',sub?'브라우저 구독 존재':'구독 없음',sub?'ok':'neutral');
      const last=await receiptFromWorker(reg);
      health('push-health-received',last?'마지막 처리: '+formattedTime(last):'수신 기록 없음',last?'ok':'neutral');
      if(!sub){
        health('push-health-server','미등록');
        health('push-health-test','서버 테스트 기록 없음');
        return;
      }
      if(!config?.apiUrl){
        health('push-health-server','서버 연결 전');
        return;
      }
      const result=await post('status',sub.toJSON(),[]);
      health('push-health-server',result.registered?'서버 등록됨':'서버 미등록 · 재구독 필요',result.registered?'ok':'bad');
      health('push-health-test',result.lastTestAcceptedAt?
        '최근 발송 접수: '+formattedTime(result.lastTestAcceptedAt):'발송 접수 기록 없음',
        result.lastTestAcceptedAt?'ok':'neutral');
      if(result.registered && Array.isArray(result.topics)){
        // Server is authoritative for topic selections if this browser was previously registered.
        for(const checkbox of document.querySelectorAll('[name="push-topic"]')){
          checkbox.checked=result.topics.includes(checkbox.value);
        }
      }
    }catch(err){
      health('push-health-server','확인 실패 · '+String(err.message||'연결 오류').slice(0,54),'bad');
    }
  }
  if('serviceWorker' in navigator){
    navigator.serviceWorker.addEventListener('message',event=>{
      if(event.data?.type==='QUIZPICK_PUSH_RECEIVED'){
        health('push-health-received','마지막 처리: '+formattedTime(event.data.at),'ok');
        state('새 웹 푸시가 이 브라우저의 서비스워커까지 도착해 알림 표시 요청을 처리했어요.');
      }
    });
  }
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
      if($('push-check'))$('push-check').disabled=false;
      if($('push-local-test'))$('push-local-test').disabled=Notification.permission!=='granted';
      const existing=await registration.pushManager.getSubscription();
      if(existing && Notification.permission==='denied'){
        $('push-disable').disabled=false;
        $('push-test').disabled=true;
        state('기존 구독은 있지만 브라우저 알림이 차단돼 있어요. 주소창 왼쪽의 사이트 설정에서 알림을 허용해 주세요.');
      }else if(existing){
        $('push-disable').disabled=false;
        $('push-test').disabled=false;
        state('이 브라우저에 푸시 구독이 있습니다. 아래 테스트 알림 버튼으로 수신 상태를 확인해 보세요.');
      }else if(Notification.permission==='denied'){
        state('알림 권한이 차단되어 있습니다. 브라우저의 사이트 설정에서 알림을 허용해 주세요.');
      }else{
        state('받고 싶은 서비스를 고르고 수신 동의 후 알림 받기를 눌러주세요.');
      }
      await refreshDiagnostics();
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
        if($('push-local-test'))$('push-local-test').disabled=false;
        await refreshDiagnostics();
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
        await refreshDiagnostics();
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
        state('푸시 발송 서버가 메시지를 접수했어요. 아래 수신 기록과 PC·휴대폰 알림센터를 확인해 주세요.');
        await refreshDiagnostics();
      }catch(err){state('테스트 실패: '+String(err.message||err).slice(0,100));}
      finally{$('push-test').disabled=false;}
    });
    $('push-check')?.addEventListener('click',async()=>{
      const btn=$('push-check');btn.disabled=true;
      try{
        await refreshDiagnostics();
        state('진단 결과를 갱신했습니다. 서버 발송 접수와 실제 브라우저 수신은 서로 다릅니다.');
      }finally{btn.disabled=false;}
    });
    $('push-local-test')?.addEventListener('click',async()=>{
      const btn=$('push-local-test');btn.disabled=true;
      try{
        if(Notification.permission!=='granted')throw Error('먼저 알림 받기를 눌러 알림 권한을 허용해 주세요.');
        const reg=await getReg();
        await reg.showNotification('퀴즈픽 · 내 브라우저 표시 테스트 💗',{
          body:'이 알림은 서버를 거치지 않고 내 기기에서 직접 표시한 테스트예요.',
          icon:BASE+'assets/qp-icon-192.png',
          tag:'quizpick-local-check',
          data:{url:location.href}
        });
        state('브라우저에 알림 표시를 요청했습니다. 실제 화면 표시 여부는 Windows 또는 휴대폰 알림센터에서 확인해 주세요.');
      }catch(err){
        state('브라우저 테스트 실패: '+String(err.message||err).slice(0,100));
      }finally{btn.disabled=Notification.permission!=='granted';}
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