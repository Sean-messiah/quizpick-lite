'use strict';
/* QuizPick daily savings self-tracker.
   No cash is paid or transferred. No signup or cross-device sync.
   v1 data format supports later server migration. */
(() => {
  const root = document.getElementById('challenge-app');
  if (!root) return;
  const KEY = 'quizpick_challenge_v1';
  const PLANS = {
    fifty: { title: '하루 50원 만들기', daily: 50, targetDays: 100, icon: '🌱', accent: 'pink' },
    hundred: { title: '하루 100원 만들기', daily: 100, targetDays: 100, icon: '💗', accent: 'rose' },
    gold: { title: '금 0.1돈 모으기', daily: 0, targetDays: 100, icon: '✨', accent: 'gold' }
  };
  const won = n => Math.max(0, Math.round(Number(n)||0)).toLocaleString('ko-KR') + '원';
  const dateKST = (d = new Date()) => new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(d);
  const dateToUtc = s => {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || '');
    return m ? Date.UTC(+m[1], +m[2] - 1, +m[3]) : NaN;
  };
  const addDays = (s, n) => dateKST(new Date(dateToUtc(s)+n*86400000+12*3600000));
  const validDate = s => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s)
    && Number.isFinite(dateToUtc(s));
  function blank() { return {version:1,nickname:'',goals:{}}; }
  function load() {
    try {
      const obj = JSON.parse(localStorage.getItem(KEY) || '{}');
      if (!obj || obj.version !== 1 || typeof obj.goals !== 'object' || !obj.goals) return blank();
      return {version:1,nickname:typeof obj.nickname==='string'?obj.nickname.slice(0,20):'',goals:obj.goals};
    } catch (_) { return blank(); }
  }
  let data = load();
  const persist = () => {
    try {
      localStorage.setItem(KEY, JSON.stringify(data));
      document.dispatchEvent(new Event('quizpick:local-change'));
      return true;
    }
    catch (_) { window.alert('기기에 기록을 저장할 수 없습니다. 브라우저 저장공간을 확인해 주세요.'); return false; }
  };
  const el = (tag, klass, text) => {
    const node = document.createElement(tag);
    if (klass) node.className = klass;
    if (text !== undefined) node.textContent = String(text);
    return node;
  };
  const send = name => {
    if (typeof window.gtag === 'function') window.gtag('event', name, {challenge_feature:'self_tracker'});
  };
  const heading = (h, t) => { const n=el('h3','',h); const p=el('p','challenge-muted',t); const f=el('div');f.append(n,p);return f; };
  function card(slug) {
    const cfg = PLANS[slug], goal = data.goals[slug], today = dateKST();
    const box = el('article','challenge-card challenge-'+cfg.accent);
    box.append(el('div','challenge-symbol',cfg.icon),el('h3','',cfg.title));
    if (!goal) {
      box.append(el('p','challenge-muted',slug==='gold'
        ? '금 0.1돈 = 0.375g. 필요한 금액을 직접 목표로 설정하고 매일 모은 금액을 기록해요.'
        : '100일간 하루 '+won(cfg.daily)+'씩 모으면 '+won(cfg.daily*100)+'이 됩니다.'));
      const start = el('button','challenge-start','도전 시작');
      start.type='button';start.addEventListener('click',()=> {
        data.goals[slug] = {startDate:today,entries:{},goalWon:slug==='gold'?0:cfg.daily*100};
        if (persist()) { send('challenge_started'); render(); }
      });
      box.append(start);return box;
    }
    const entries=goal.entries && typeof goal.entries==='object'?goal.entries:{};
    const daysDone=Object.keys(entries).filter(k=>validDate(k)&&Number(entries[k])>0).length;
    const saved=Object.values(entries).reduce((sum,v)=>sum+(Number.isFinite(+v)&&+v>0?+v:0),0);
    const totalDays = Number.isFinite(dateToUtc(goal.startDate))
      ? Math.min(100,Math.max(1,Math.floor((dateToUtc(today)-dateToUtc(goal.startDate))/86400000)+1)) : 1;
    const target=slug==='gold'?(+goal.goalWon||0):cfg.daily*100;
    const percent=target>0?Math.min(100,Math.round(saved/target*100)):0;
    let streak=0;
    let cursor=Number(entries[today])>0?today:addDays(today,-1);
    for(let i=0;i<100&&Number(entries[cursor])>0;i++){
      streak++;cursor=addDays(cursor,-1);
    }
    const meta=el('div','challenge-meta');
    meta.append(el('span','',daysDone+'일 체크'),el('span','',won(saved)+' 기록'));
    if(streak>0) meta.append(el('span','','🔥 연속 '+streak+'일'));
    if(daysDone>=100) meta.append(el('span','','🏆 100일 완주'));
    else if(daysDone>=30) meta.append(el('span','','🏅 30일 달성'));
    else if(daysDone>=7) meta.append(el('span','','🌟 7일 달성'));
    box.append(meta);
    const progress=el('div','challenge-progress');
    progress.setAttribute('role','progressbar');progress.setAttribute('aria-valuemin','0');
    progress.setAttribute('aria-valuemax','100');progress.setAttribute('aria-valuenow',String(percent));
    progress.setAttribute('aria-label',cfg.title+' 목표 달성률');
    const fill=el('span');fill.style.width=percent+'%';progress.append(fill);box.append(progress);
    box.append(el('p','challenge-muted',target
      ? '100일 목표 '+won(target)+' · '+percent+'% 달성 · 남은 금액 '+won(Math.max(0,target-saved))
      : '금 0.1돈 구매 목표 예산을 아래에 입력해 주세요.'));
    if (slug==='gold') {
      const label=el('label','challenge-input-label','금 0.1돈(0.375g) 구매 목표 예산');
      const input=el('input');
      input.type='number';input.inputMode='numeric';input.min='1';input.max='100000000';
      input.step='1';input.placeholder='직접 예산 입력 (원)';
      input.value=goal.goalWon>0?goal.goalWon:'';
      input.addEventListener('change',()=> {
        const n=Math.floor(+input.value);
        if (!Number.isFinite(n)||n<1||n>100000000) { window.alert('1원 이상 1억원 이하의 목표 금액을 입력해 주세요.');return; }
        goal.goalWon=n;if(persist()){send('challenge_budget_set');render();}
      });
      label.append(input);box.append(label);
    }
    const dateLabel=el('p','challenge-muted','오늘 '+today+' · 시작 '+goal.startDate+' · '+totalDays+'/100일차');
    box.append(dateLabel);
    const label=el('label','challenge-input-label','오늘 실제로 모은 금액 (직접 기록, 원)');
    const amount=el('input');
    amount.type='number';amount.min='0';amount.max='1000000';amount.step='1';amount.inputMode='numeric';
    amount.value=Object.hasOwn(entries,today)?entries[today]:(cfg.daily||'');
    amount.placeholder='오늘 모은 금액';
    label.append(amount);box.append(label);
    const controls=el('div','challenge-actions');
    const update=el('button','challenge-start',Object.hasOwn(entries,today)?'오늘 기록 수정':'오늘 기록 체크');
    update.type='button';
    update.addEventListener('click',()=>{
      const n=Number(amount.value);
      if (!Number.isFinite(n)||!Number.isInteger(n)||n<1||n>1000000) {
        window.alert('실제로 모은 금액을 1원부터 1,000,000원까지 입력해 주세요.');return;
      }
      goal.entries={...entries,[today]:n};
      if (persist()) { send('challenge_daily_check');render(); }
    });
    controls.append(update);
    if(Object.hasOwn(entries,today)) {
      const undo=el('button','challenge-undo','오늘 체크 취소');
      undo.type='button';undo.addEventListener('click',()=>{
        const next={...entries};delete next[today];goal.entries=next;
        if(persist()){send('challenge_undo');render();}
      });
      controls.append(undo);
    }
    box.append(controls);
    const week=el('div','challenge-week');
    for(let i=6;i>=0;i--){
      const day=addDays(today,-i);
      const cell=el('div','challenge-day '+(Number(entries[day])>0?'done':''),day.slice(5));
      cell.append(el('strong','',Number(entries[day])>0?'✓':'·'));
      cell.title=day+(entries[day]?' · '+won(entries[day]):' · 미기록');
      week.append(cell);
    }
    box.append(week);
    return box;
  }
  function render() {
    root.replaceChildren();
    const intro=el('div','challenge-intro');
    if (!data.nickname) {
      intro.append(heading('닉네임으로 가볍게 시작하기',
        '가입 없이 이 브라우저에만 기록됩니다. 다른 기기와 자동 연동되지는 않아요.'));
      const form=el('form','challenge-profile');
      const inp=el('input');inp.type='text';inp.maxLength=16;inp.placeholder='닉네임 (예: 매일 100원)';inp.required=true;
      inp.setAttribute('aria-label','챌린지 닉네임');
      const btn=el('button','challenge-start','시작하기');btn.type='submit';
      form.append(inp,btn);
      form.addEventListener('submit',event=>{
        event.preventDefault();const name=inp.value.trim();
        if(name.length<2){window.alert('닉네임을 두 글자 이상 입력해 주세요.');return;}
        data.nickname=name;if(persist()){send('challenge_profile_created');render();}
      });intro.append(form);
      root.append(intro);return;
    }
    intro.append(heading(data.nickname+'님의 100일 챌린지',
      '퀴즈픽은 실제 돈이나 금을 지급하지 않습니다. 내가 다른 앱에서 모은 금액을 직접 적는 기록장입니다.'));
    const top=el('div','challenge-top');
    top.append(el('span','challenge-neutral','대한민국 표준시(KST) 기준 하루 한 번 기록'));
    const reset=el('button','challenge-textbutton','내 기록 관리');
    reset.type='button';reset.addEventListener('click',()=>{
      document.getElementById('challenge-manage').hidden=
        !document.getElementById('challenge-manage').hidden;
    });
    top.append(reset);intro.append(top);root.append(intro);
    const cards=el('div','challenge-grid');
    Object.keys(PLANS).forEach(slug=>cards.append(card(slug)));
    root.append(cards);
    const manage=el('section','challenge-manage');manage.id='challenge-manage';manage.hidden=true;
    manage.append(heading('내 데이터 관리','기기에만 저장됩니다. 로그인과 서버 동기화는 아직 제공하지 않습니다.'));
    const exportBtn=el('button','challenge-undo','내 기록 JSON 백업');
    exportBtn.type='button';exportBtn.addEventListener('click',()=>{
      const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
      const url=URL.createObjectURL(blob);const a=document.createElement('a');
      a.href=url;a.download='quizpick-challenges-'+dateKST()+'.json';a.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    const deleteBtn=el('button','challenge-undo','내 모든 기록 삭제');
    deleteBtn.type='button';deleteBtn.addEventListener('click',()=>{
      if(!window.confirm('이 브라우저의 챌린지 닉네임과 모든 체크 기록을 삭제할까요? 복구할 수 없습니다.'))return;
      data=blank();if(persist()){send('challenge_data_deleted');render();}
    });
    const upload=el('input');
    upload.type='file';upload.accept='application/json,.json';upload.className='challenge-restore';
    upload.setAttribute('aria-label','챌린지 백업 파일 불러오기');
    upload.addEventListener('change',async ()=>{
      const file=upload.files?.[0];
      if(!file)return;
      try {
        if(file.size>100000) throw new Error('백업 파일 크기가 너무 큽니다.');
        const json=JSON.parse(await file.text());
        if(json.version!==1||typeof json.nickname!=='string'||!json.goals||typeof json.goals!=='object')
          throw new Error('퀴즈픽 챌린지 v1 백업 파일이 아닙니다.');
        const goals={};
        for(const [id,goal] of Object.entries(json.goals)){
          if(!Object.hasOwn(PLANS,id)||!goal||typeof goal!=='object')continue;
          if(!validDate(goal.startDate)||!goal.entries||typeof goal.entries!=='object')
            throw new Error('챌린지 기록 날짜를 확인할 수 없습니다.');
          const entries={};
          for(const [day,value] of Object.entries(goal.entries)){
            const amount=Number(value);
            if(!validDate(day)||!Number.isInteger(amount)||amount<1||amount>1000000)
              throw new Error('챌린지 기록 형식이 올바르지 않습니다.');
            entries[day]=amount;
          }
          const budget=Number(goal.goalWon)||0;
          if(!Number.isInteger(budget)||budget<0||budget>100000000)
            throw new Error('목표 금액 형식이 올바르지 않습니다.');
          goals[id]={startDate:goal.startDate,goalWon:budget,entries};
        }
        if(!window.confirm('현재 이 기기의 체크 기록을 백업 파일 내용으로 교체할까요?'))return;
        data={version:1,nickname:json.nickname.slice(0,16),goals};
        if(persist()){send('challenge_restore');render();}
      }catch(error){window.alert('복원 실패: '+error.message);}
      finally{upload.value='';}
    });
    const restoreLabel=el('label','challenge-restore-label','JSON 백업 파일로 복원');
    restoreLabel.append(upload);
    manage.append(exportBtn,restoreLabel,deleteBtn);root.append(manage);
  }
  // Explicit, local-first bridge to optional cloud auth. No storage sent automatically.
  window.QuizPickChallengeStore = Object.freeze({
    snapshot: () => JSON.parse(JSON.stringify(data)),
    replace: incoming => {
      if (!incoming || incoming.version !== 1 ||
          typeof incoming.nickname !== 'string' || !incoming.goals ||
          typeof incoming.goals !== 'object') throw new Error('기록 형식이 올바르지 않습니다.');
      data = JSON.parse(JSON.stringify(incoming));
      if (persist()) render();
    }
  });
  render();
})();
