/* QuizPick optional account / cloud sync.
 * Disabled until owner configures a Supabase project and applies strict RLS.
 * A nickname alone is not an account. Never publish secret/service-role keys.
 */
const HOST = '/quizpick-lite';
const root = document.getElementById('account-sync');
if (root) {
  const store = () => window.QuizPickChallengeStore;
  const status = (message, error=false) => {
    let target = root.querySelector('[data-sync-status]');
    if (!target) { target = document.createElement('p'); target.dataset.syncStatus = '';root.append(target); }
    target.textContent = message;
    target.className = error ? 'cloud-error' : 'cloud-note';
  };
  const element = (tag, content, className='') => {
    const node=document.createElement(tag);
    node.textContent=content;
    if(className)node.className=className;
    return node;
  };
  const VALID_KINDS = new Set(['fifty','hundred','gold']);
  const DATE = /^\d{4}-\d{2}-\d{2}$/;
  function validateLocal(value) {
    if (!value || value.version!==1 || typeof value.nickname!=='string' || !value.goals || typeof value.goals!=='object')
      throw new Error('로컬 기록을 읽을 수 없습니다.');
    const goals=[];
    const entries=[];
    for (const [kind, goal] of Object.entries(value.goals)) {
      if(!VALID_KINDS.has(kind)||!goal||typeof goal!=='object'||!DATE.test(goal.startDate))continue;
      const amount=Number(goal.goalWon||0);
      if(!Number.isInteger(amount)||amount<0||amount>100000000)throw new Error('목표 금액이 잘못되었습니다.');
      goals.push({kind,start_date:goal.startDate,goal_amount_won:amount});
      for (const [entry_date, n] of Object.entries(goal.entries||{})) {
        const amount_won=Number(n);
        if(!DATE.test(entry_date)||!Number.isInteger(amount_won)||amount_won<1||amount_won>1000000)
          throw new Error('기록 금액이 올바르지 않습니다.');
        entries.push({kind,entry_date,amount_won});
      }
    }
    if(entries.length>5000)throw new Error('기록이 너무 많습니다.');
    return {nickname:value.nickname.slice(0,16),goals,entries};
  }
  const setup = async () => {
    let conf;
    try {
      const r=await fetch(HOST+'/auth-config.json',{cache:'no-store'});
      if(!r.ok)throw new Error('설정 로드 불가');
      conf=await r.json();
    }catch(_){status('현재는 이 기기에만 저장됩니다. 계정 동기화는 준비 중입니다.');return;}
    if(!conf.enabled){status('현재 가입 없이 사용 가능합니다. 계정·기기간 동기화는 서버 연결 후 제공됩니다.');return;}
    const allowed=/^https:\/\/[a-z0-9-]+\.supabase\.co$/;
    if(!allowed.test(conf.projectUrl||'') || !/^sb_publishable_[A-Za-z0-9_-]+$/.test(conf.publishableKey||'')) {
      status('계정 연결 설정이 올바르지 않습니다. 현 기기 기록은 안전하게 유지됩니다.',true);
      return;
    }
    let createClient;
    try {
      ({createClient} = await import('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.118.0/+esm'));
    }catch(_) {status('로그인 라이브러리를 불러오지 못했습니다. 현재 기기 기록은 유지됩니다.',true);return;}
    const client=createClient(conf.projectUrl,conf.publishableKey,{
      auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true,flowType:'implicit'}
    });
    let current=null, enabledForUser=null, syncQueue=Promise.resolve(),busy=false;
    const wrapper=document.createElement('div');
    wrapper.className='cloud-panel';
    root.prepend(wrapper);
    function reset(text) {
      wrapper.replaceChildren();
      if(text)wrapper.append(element('p',text,'cloud-note'));
    }
    function button(text,click,extra='') {
      const b=element('button',text,'challenge-undo '+extra);
      b.type='button';b.addEventListener('click',click);
      return b;
    }
    async function readCloud(userId) {
      const [p,g,e]=await Promise.all([
        client.from('quizpick_profiles').select('nickname').eq('user_id',userId).maybeSingle(),
        client.from('quizpick_goals').select('kind,start_date,goal_amount_won').eq('user_id',userId),
        client.from('quizpick_entries').select('kind,entry_date,amount_won').eq('user_id',userId)
      ]);
      for(const v of [p,g,e])if(v.error)throw v.error;
      const goals={};
      for(const x of g.data||[])if(VALID_KINDS.has(x.kind)){
        goals[x.kind]={startDate:x.start_date,goalWon:x.goal_amount_won,entries:{}};
      }
      for(const x of e.data||[]){
        if(goals[x.kind])goals[x.kind].entries[x.entry_date]=x.amount_won;
      }
      return {version:1,nickname:p.data?.nickname||store()?.snapshot().nickname||'퀴즈픽 회원',goals};
    }
    async function uploadSnapshot(userId) {
      if(current?.id!==userId)throw new Error('로그인 계정이 변경되어 저장을 중지했습니다.');
      const source=store()?.snapshot();
      if(!source)throw new Error('로컬 챌린지 정보를 불러올 수 없습니다.');
      const parsed=validateLocal(source);
      if(parsed.nickname.trim().length<2)throw new Error('먼저 챌린지 닉네임을 설정해 주세요.');
      const profile=await client.from('quizpick_profiles').upsert({
        user_id:userId,nickname:parsed.nickname
      },{onConflict:'user_id'});
      if(profile.error)throw profile.error;
      if(parsed.goals.length){
        const goals=await client.from('quizpick_goals').upsert(
          parsed.goals.map(x=>({...x,user_id:userId})),{onConflict:'user_id,kind'});
        if(goals.error)throw goals.error;
      }
      // Local records override the same cloud date explicitly; other dates are preserved.
      for(let i=0;i<parsed.entries.length;i+=100){
        const entries=await client.from('quizpick_entries').upsert(
          parsed.entries.slice(i,i+100).map(x=>({...x,user_id:userId})),
          {onConflict:'user_id,kind,entry_date'});
        if(entries.error)throw entries.error;
      }
    }
    async function sync() {
      const userId=enabledForUser;
      if(!userId||!current||current.id!==userId)return;
      if(busy)return;
      busy=true;
      try {
        await uploadSnapshot(userId);
        const merged=await readCloud(userId);
        if(enabledForUser!==userId)return;
        enabledForUser=null; // don't recursively sync the import event
        store()?.replace(merged);
        enabledForUser=userId;
        status('클라우드에 동기화했습니다. 다른 기기에서도 같은 계정으로 로그인해 불러올 수 있습니다.');
      }catch(e){status('동기화 실패: '+(e.message||'다시 시도해 주세요.'),true);}
      finally{busy=false;}
    }
    function requestSync() {
      if(!enabledForUser)return;
      syncQueue=syncQueue.then(sync).catch(e=>status(String(e),true));
    }
    document.addEventListener('quizpick:local-change',requestSync);
    async function startSync() {
      if(!current)return;
      if(!window.confirm('이 기기의 현재 기록을 계정에 병합할까요? 같은 날짜·챌린지는 이 기기의 금액이 우선하고 다른 날짜는 보존합니다.'))return;
      const userId=current.id;
      try {
        status('현재 기록을 서버에 저장하는 중입니다.');
        await uploadSnapshot(userId);
        const merged=await readCloud(userId);
        if(current?.id!==userId)return;
        enabledForUser=null;
        store()?.replace(merged);
        enabledForUser=userId;
        status('계정 동기화가 켜졌습니다. 앞으로 체크 변경 시 저장됩니다.');
        renderSignedIn();
      }catch(e){status('동기화 시작 실패: '+(e.message||'저장되지 않았습니다.'),true);}
    }
    async function downloadCloud() {
      if(!current)return;
      if(!window.confirm('이 기기에 저장된 챌린지 기록을 계정에 있는 내용으로 교체할까요? 필요한 기록은 먼저 JSON 파일로 백업하세요.'))return;
      try{
        enabledForUser=null;
        const remote=await readCloud(current.id);
        store()?.replace(remote);
        status('계정 기록을 이 기기로 가져왔습니다. 이후 변경도 동기화하려면 동기화 켜기를 눌러 주세요.');
        renderSignedIn();
      }catch(e){status('계정 기록을 가져오지 못했습니다: '+(e.message||''),true);}
    }
    async function deleteCloud() {
      if(!current||!window.confirm('클라우드에 저장된 챌린지 기록과 닉네임을 모두 삭제할까요? 현재 브라우저 기록은 남습니다. 이 작업은 되돌릴 수 없습니다.'))return;
      enabledForUser=null;
      try {
        const goals=await client.from('quizpick_goals').delete().eq('user_id',current.id);
        if(goals.error)throw goals.error; // cascade deletes entries
        const p=await client.from('quizpick_profiles').delete().eq('user_id',current.id);
        if(p.error)throw p.error;
        renderSignedIn();status('클라우드 챌린지 기록을 삭제했습니다. 로그인 계정 자체는 유지됩니다.');
      }catch(e){status('삭제 실패: '+(e.message||''),true);}
    }
    async function signOut() {
      enabledForUser=null;
      const {error}=await client.auth.signOut();
      if(error)status('로그아웃 실패: '+error.message,true);
      else{current=null;renderSignedOut();status('로그아웃했습니다. 이 브라우저에 저장한 기록은 유지됩니다. 공용 기기라면 로컬 기록도 별도로 삭제하세요.');}
    }
    function renderSignedIn(){
      if(!current)return;
      reset();
      wrapper.append(element('strong','☁️ 계정 연결됨'));
      // Never submit PII through GA4; show email only inside account UI.
      wrapper.append(element('p',current.email||'로그인됨','cloud-note'));
      const ctr=document.createElement('div');ctr.className='cloud-actions';
      ctr.append(button(enabledForUser===current.id?'지금 동기화':'이 기기 기록 계정에 병합',
        ()=>enabledForUser===current.id?requestSync():startSync(),'challenge-start'));
      ctr.append(button('계정 기록 불러오기',downloadCloud));
      ctr.append(button('클라우드 기록 삭제',deleteCloud));
      ctr.append(button('로그아웃',signOut));
      wrapper.append(ctr);
      if(enabledForUser===current.id)status('자동 동기화 사용 중입니다.');
    }
    function renderSignedOut(){
      reset('이메일로 무료 가입·로그인할 수 있습니다. 기존 챌린지 기록은 동의 전까지 서버에 업로드하지 않습니다.');
      const form=document.createElement('form');form.className='cloud-form';
      const input=document.createElement('input');
      input.type='email';input.autocomplete='email';input.required=true;
      input.placeholder='이메일 주소';input.setAttribute('aria-label','계정 이메일');
      const send=element('button','이메일 로그인 링크 받기','challenge-start');
      send.type='submit';form.append(input,send);
      form.addEventListener('submit',async e=>{
        e.preventDefault();send.disabled=true;
        const email=input.value.trim();
        try{
          const {error}=await client.auth.signInWithOtp({
            email,options:{emailRedirectTo:location.origin+HOST+'/challenge/',shouldCreateUser:true}
          });
          if(error)throw error;
          status('이메일을 확인해 로그인 링크를 눌러 주세요. 같은 브라우저에서 열면 편리합니다.');
        }catch(e){status('이메일 발송 실패: '+(e.message||''),true);}
        finally{send.disabled=false;}
      });
      wrapper.append(form);
    }
    async function refresh() {
      try{
        const {data,error}=await client.auth.getUser();
        if(error && !/session/i.test(error.message||''))throw error;
        if(!data?.user){
          current=null;enabledForUser=null;renderSignedOut();return;
        }
        if(current?.id!==data.user.id)enabledForUser=null;
        current=data.user;
        renderSignedIn();
      }catch(e){status('계정 상태 확인 실패: '+(e.message||''),true);}
    }
    client.auth.onAuthStateChange(()=>{
      // Supabase docs warn against awaiting API calls inside this callback.
      setTimeout(refresh,0);
    });
    await refresh();
  };
  setup();
}
