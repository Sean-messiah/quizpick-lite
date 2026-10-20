'use strict';
/* QuizPick: published quiz checklist + personally observed reward amounts.
 * A user's check is not proof of participation or payment; conversion rates are NEVER assumed.
 */
(() => {
  const root=document.getElementById('daily-challenge');
  if (!root) return;
  const KEY='quizpick_daily_quizzes_v1', HOST='/quizpick-lite';
  const NICK_KEY='quizpick_public_nickname_v1';
  let nickname='';
  try { nickname=(localStorage.getItem(NICK_KEY)||'').slice(0,16); }catch(_){}
  let editingNickname=false;
  const UNITS=['원','P','캐시','기타'];
  const kst=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  const isDate=s=>typeof s==='string' && /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(Date.parse(s));
  const fmt=n=>(Number(n)||0).toLocaleString('ko-KR');
  const node=(tag,cls='',txt=null)=>{
    const el=document.createElement(tag);if(cls)el.className=cls;
    if(txt!==null)el.textContent=String(txt);return el;
  };
  const emit=event=>{if(typeof window.gtag==='function')window.gtag('event',event,{feature:'daily_quiz_check'})};
  function checkRecord(r) {
    if(!r||typeof r!=='object'||typeof r.quizId!=='string'||r.quizId.length>100||
       !/^[A-Za-z0-9_-]{4,100}$/.test(r.quizId)||!isDate(r.date)||
       typeof r.app!=='string'||!r.app||r.app.length>60||
       typeof r.title!=='string'||!r.title||r.title.length>200||
       !UNITS.includes(r.unit)||!Number.isInteger(r.amount)||r.amount<0||r.amount>1000000||
       typeof r.done!=='boolean')return false;
    return true;
  }
  function fromDisk(){
    try {
      const raw=JSON.parse(localStorage.getItem(KEY)||'{}');
      if(raw.version!==1||!raw.records||typeof raw.records!=='object')return {};
      const result={};for(const [id,r] of Object.entries(raw.records)){
        if(id===r?.quizId && checkRecord(r))result[id]=r;
      }
      return result;
    }catch(_){return {};}
  }
  let records=fromDisk(), feed=[], chosenDate=kst(), simulateCount=0,simulateAvg=5;
  function save() {
    try {
      localStorage.setItem(KEY,JSON.stringify({version:1,records}));
      document.dispatchEvent(new Event('quizpick:daily-change'));
      return true;
    } catch(_) {window.alert('기록을 저장할 수 없습니다. 브라우저 저장 공간을 확인해 주세요.');return false;}
  }
  const recordsList=()=>Object.values(records).filter(checkRecord);
  const active=r=>r.done===true;
  // Keep Toss and KakaoBank first, consistent with QuizPick's navigation priority.
  const selectedRows=()=>feed.filter(q=>q.date===chosenDate).sort((a,b)=>{
    const priority=x=>x.app==='toss'?0:x.app==='kakaobank'?1:2;
    return priority(a)-priority(b)||(b.time||'').localeCompare(a.time||'')||a.id.localeCompare(b.id);
  });
  function summary(day) {
    const all=recordsList().filter(r=>active(r)&&(!day||r.date===day));
    let earnedWon=0;const other={};
    for(const r of all){
      if(r.unit==='원')earnedWon+=r.amount;
      else if(r.amount>0){
        const key=r.app+'|'+r.unit;
        const group=other[key] || {app:r.appName||r.app,unit:r.unit,amount:0};
        group.amount+=r.amount;other[key]=group;
      }
    }
    return {count:all.length,won:earnedWon,other:Object.values(other)};
  }
  function streak() {
    const doneDates=new Set(recordsList().filter(active).map(r=>r.date));
    let d=new Date(kst()+'T12:00:00Z'), count=0;
    const today=kst();
    if(!doneDates.has(today))d.setUTCDate(d.getUTCDate()-1);
    for(let i=0;i<1000;i++){
      const date=d.toISOString().slice(0,10);
      if(!doneDates.has(date))break;
      count++;d.setUTCDate(d.getUTCDate()-1);
    }
    return count;
  }
  function update(id,patch) {
    const item=feed.find(q=>q.id===id);
    if(!item||item.date!==chosenDate)return;
    const old=records[id];
    const fresh={
      quizId:id,date:item.date,app:item.app,
      appName:item.appName,title:item.question.slice(0,200),
      done:old?.done||false,amount:old?.amount||0,unit:old?.unit||'원',
      updatedAt:new Date().toISOString(),
      ...patch
    };
    if(!checkRecord(fresh))return;
    records[id]=fresh;
    if(save()){
      // No nickname, amount, quiz answer or other personal values go to GA4.
      if(Object.prototype.hasOwnProperty.call(patch,'done') && patch.done!==!!old?.done) {
        emit(patch.done?'quiz_daily_check':'quiz_daily_uncheck');
      } else if(Object.prototype.hasOwnProperty.call(patch,'amount')) {
        emit('quiz_daily_reward_saved');
      } else {
        emit('quiz_daily_updated');
      }
      render();
    }
  }
  function stat(value,title,sub=''){
    const b=node('div','daily-stat');
    b.append(node('strong','',value),node('span','',title));
    if(sub)b.append(node('small','',sub));
    return b;
  }
  function render() {
    root.replaceChildren();
    const rows=selectedRows(),result=summary(chosenDate),doneIds=new Set(recordsList().filter(active).map(r=>r.quizId));
    const today=kst(),days=Array.from(new Set(feed.map(q=>q.date))).sort().reverse();
    const intro=node('div','daily-header');
    intro.append(node('h2','','오늘의 앱테크 체크리스트'));
    intro.append(node('p','daily-muted','퀴즈픽에 등록된 정답 기준입니다. 실제 참여 가능 여부와 보상 지급 여부를 뜻하지 않습니다.'));
    root.append(intro);
    // Optional nickname, never a signup gate. Save under a separate browser key.
    const profile=node('section','daily-nickname');
    if(editingNickname){
      const form=node('form','daily-nickname-form');
      const input=node('input');input.type='text';input.maxLength=16;
      input.value=nickname;input.placeholder='닉네임을 입력하세요 (선택)';
      input.setAttribute('aria-label','선택 닉네임');
      const saveName=node('button','challenge-start','저장');saveName.type='submit';
      const cancel=node('button','challenge-undo','취소');cancel.type='button';
      cancel.addEventListener('click',()=>{editingNickname=false;render();});
      form.addEventListener('submit',event=>{
        event.preventDefault();
        const name=input.value.trim();
        if(name.length===1){window.alert('닉네임을 입력하려면 두 글자 이상 사용해 주세요.');return;}
        try {
          if(name)localStorage.setItem(NICK_KEY,name);
          else localStorage.removeItem(NICK_KEY);
          nickname=name;editingNickname=false;render();
        }catch(_){window.alert('닉네임을 저장할 수 없습니다. 브라우저 설정을 확인해 주세요.');}
      });
      form.append(input,saveName,cancel);
      profile.append(node('span','daily-muted','이름은 입력하지 않아도 체크리스트를 이용할 수 있습니다.'),form);
    }else{
      profile.append(node('span','daily-muted',nickname?(nickname.endsWith('님')?nickname+'의 참여 기록':nickname+'님의 참여 기록')+' · 이 브라우저에만 저장':'닉네임 없이 바로 참여할 수 있어요.'));
      const edit=node('button','challenge-textbutton',nickname?'닉네임 변경·삭제':'닉네임 만들기 (선택)');
      edit.type='button';edit.addEventListener('click',()=>{editingNickname=true;render();});
      profile.append(edit);
    }
    root.append(profile);
    if(!feed.length) {
      root.append(node('p','notice','현재 공개된 퀴즈 목록을 불러오지 못했거나 등록된 퀴즈가 없습니다. 잠시 후 다시 확인해 주세요.'));return;
    }
    const daybar=node('div','daily-daybar');
    const lbl=node('label','', '확인할 날짜');
    const select=node('select');select.setAttribute('aria-label','퀴즈 날짜 선택');
    if(!days.includes(today)){
      const op=node('option','',today+' (등록 없음)');op.value=today;select.append(op);
    }
    for(const date of days){const op=node('option','',date===today?'오늘 '+date:date);op.value=date;select.append(op);}
    select.value=chosenDate;
    select.addEventListener('change',()=>{chosenDate=select.value;simulateCount=selectedRows().length;render();});
    lbl.append(select);daybar.append(lbl,node('span','daily-muted','한국시간 기준 · 최근 등록된 날짜'));
    root.append(daybar);
    const stats=node('div','daily-stats');
    stats.append(stat(result.count+' / '+rows.length,'직접 참여 체크'),
      stat(fmt(result.won)+'원','직접 기록한 원화', '다른 앱의 포인트와 별도'),
      stat('🔥 '+streak()+'일','연속 참여 기록'));
    root.append(stats);
    if(result.other.length){
      const pointBox=node('div','daily-point-summary');
      pointBox.append(node('strong','','💠 앱별로 별도 합산한 리워드'));
      for(const x of result.other)pointBox.append(node('span','',x.app+' · '+fmt(x.amount)+x.unit));
      root.append(pointBox);
    }
    const countBar=node('div','daily-count-bar');
    const filled=rows.length?Math.round(result.count/rows.length*100):0;
    const fill=node('div','daily-count-fill');fill.style.width=filled+'%';
    countBar.append(fill);countBar.setAttribute('role','progressbar');
    countBar.setAttribute('aria-label','오늘 참여 체크 진행률');
    countBar.setAttribute('aria-valuemin','0');countBar.setAttribute('aria-valuemax','100');countBar.setAttribute('aria-valuenow',String(filled));
    root.append(countBar);
    if(!rows.length){root.append(node('p','notice','이 날짜에는 퀴즈픽에 등록된 정답이 없습니다. 다른 날짜를 선택해 주세요.'));}
    const cards=node('div','daily-quiz-list');
    for(const q of rows){
      const v=records[q.id]||{done:false,unit:'원',amount:0};
      const card=node('article','daily-quiz-card'+(v.done?' is-complete':''));
      const checkLabel=node('label','daily-checkbox-label');
      const check=node('input');check.type='checkbox';check.checked=!!v.done;
      check.setAttribute('aria-label',q.appName+' '+q.question+' 참여 완료');
      check.addEventListener('change',()=>update(q.id,{done:check.checked,...(!check.checked?{amount:0}:{})}));
      const content=node('div','daily-card-main');
      content.append(node('strong','',q.appName));
      content.append(node('p','',q.question));
      content.append(node('small','',q.time?'확인된 시각 '+q.time:'등록된 참고 퀴즈'));
      checkLabel.append(check,content);card.append(checkLabel);
      const actions=node('div','daily-quiz-actions');
      const link=node('a','daily-answer-link','정답 확인 →');
      link.href=q.url;actions.append(link);
      if(v.done){
        const input=node('input');input.type='number';input.min='0';input.max='1000000';input.step='1';input.inputMode='numeric';
        input.value=String(v.amount);
        input.setAttribute('aria-label',q.appName+' 실제 받은 보상 수량');
        const unit=node('select');unit.setAttribute('aria-label',q.appName+' 보상 단위');
        const placeholder=node('option','','단위 선택');placeholder.value='';unit.append(placeholder);
        for(const u of UNITS){const option=node('option','',u);option.value=u;unit.append(option);}
        unit.value=v.amount>0?v.unit:'';
        const set=node('button','challenge-undo','기록 저장');set.type='button';
        set.addEventListener('click',()=>{
          const amount=Number(input.value);
          if(input.value.trim()===''||!Number.isInteger(amount)||amount<0||amount>1000000){
            window.alert('실제로 받은 보상 수량을 0 이상 1,000,000 이하의 정수로 입력해 주세요.');return;
          }
          if(amount>0&&!unit.value){
            window.alert('금액과 포인트를 혼동하지 않도록 받은 보상의 단위를 선택해 주세요.');return;
          }
          update(q.id,{done:true,amount,unit:unit.value||'원'});
        });
        actions.append(input,unit,set);
      }
      card.append(actions);cards.append(card);
    }
    root.append(cards);
    const note=node('p','daily-muted','체크는 직접 참여했다는 기록이며 실제 보상을 확인하지 않습니다. 받은 금액·포인트는 직접 입력하세요. 포인트, 캐시, 기타 단위는 원화로 자동 환산하지 않습니다.');
    root.append(note);
    const sim=node('section','daily-simulator');
    sim.append(node('h2','','🧮 오늘의 가정 수익 계산기'));
    sim.append(node('p','daily-muted','아래 평균 금액은 지급 보장액이 아닌 사용자가 조절하는 가정값입니다. 서로 다른 앱의 포인트는 실제 교환비율을 따져 별도로 계산해야 합니다.'));
    const fields=node('div','daily-sim-fields');
    const qtyLbl=node('label','','참여 가정 개수');
    const qty=node('input');qty.type='number';qty.min='0';qty.max=String(rows.length);qty.step='1';qty.value=String(Math.min(simulateCount,rows.length));
    qtyLbl.append(qty);
    const avgLbl=node('label','','한 퀴즈당 원화 환산액 가정 (원)');
    const avg=node('input');avg.type='number';avg.min='0';avg.max='1000000';avg.step='1';avg.value=String(simulateAvg);
    avgLbl.append(avg);fields.append(qtyLbl,avgLbl);sim.append(fields);
    const calc=node('div','daily-projection');sim.append(calc);
    const recalc=()=>{
      const count=Number(qty.value),average=Number(avg.value);
      if(!Number.isInteger(count)||count<0||count>rows.length||!Number.isInteger(average)||average<0||average>1000000){
        calc.textContent='참여 개수와 예상 평균 금액을 정확히 입력해 주세요.';return;
      }
      simulateCount=count;simulateAvg=average;
      const perDay=count*average;
      calc.textContent='하루 '+fmt(perDay)+'원 · 30일 '+fmt(perDay*30)+'원 · 100일 '+fmt(perDay*100)+'원 (동일 참여·환산액을 가정한 계산)';
    };
    qty.addEventListener('input',recalc);avg.addEventListener('input',recalc);recalc();root.append(sim);
    const tools=node('section','daily-history');
    const total=summary(null);const daysDone=new Set(recordsList().filter(active).map(r=>r.date)).size;
    tools.append(node('h2','','📅 내 누적 참여 기록'));
    tools.append(node('p','',daysDone+'일 참여 · '+fmt(total.won)+'원 직접 기록 · '+streak()+'일 연속'));
    if(daysDone>=7)tools.append(node('strong','daily-milestone','🌟 7일 참여 달성'));
    if(daysDone>=30)tools.append(node('strong','daily-milestone','🏅 30일 참여 달성'));
    if(daysDone>=100)tools.append(node('strong','daily-milestone','🏆 100일 참여 달성'));
    const exportBtn=node('button','challenge-undo','내 참여 기록 백업');exportBtn.type='button';
    exportBtn.addEventListener('click',()=>{
      const blob=new Blob([JSON.stringify({version:1,records},null,2)],{type:'application/json'});
      const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='quizpick-daily-'+kst()+'.json';a.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    tools.append(exportBtn);root.append(tools);
  }
  function mergeCloud(items) {
    if(!Array.isArray(items))throw new Error('클라우드 목록 형식 오류');
    const merged={...records};
    for(const r of items){
      if(!checkRecord(r))continue;
      const local=merged[r.quizId];
      if(!local||(r.updatedAt||'')>(local.updatedAt||''))merged[r.quizId]=r;
    }
    records=merged;
    if(save())render();
  }
  window.QuizPickDailyStore=Object.freeze({
    snapshot:()=>JSON.parse(JSON.stringify({version:1,records})),
    mergeCloud,
    count:()=>recordsList().length
  });
  (async()=>{
    try{
      const response=await fetch(HOST+'/challenge-feed.json',{cache:'no-store'});
      if(!response.ok)throw new Error('HTTP '+response.status);
      const json=await response.json();
      if(!Array.isArray(json.quizzes))throw new Error('퀴즈 목록 형식 오류');
      feed=json.quizzes.filter(q=>q&&typeof q.id==='string'&&/^[A-Za-z0-9_-]{4,100}$/.test(q.id)
        &&isDate(q.date)&&typeof q.app==='string'&&typeof q.appName==='string'
        &&typeof q.question==='string'&&typeof q.url==='string'
        &&/^\/quizpick-lite\/quiz\/[a-z0-9_-]+\/\d{4}-\d{2}-\d{2}\/[A-Za-z0-9_-]+\/$/.test(q.url));
      const days=Array.from(new Set(feed.map(q=>q.date))).sort();
      if(!days.includes(chosenDate)&&days.length)chosenDate=days[days.length-1];
      simulateCount=feed.filter(q=>q.date===chosenDate).length;
    }catch(e){root.replaceChildren();root.append(node('p','notice','퀴즈 목록을 불러오지 못했습니다. 새로고침 후 다시 시도해 주세요.'));return;}
    render();
  })();
})();
