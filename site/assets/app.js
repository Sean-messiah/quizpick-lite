'use strict';
function ga(name, app) {
  if (typeof window.gtag === 'function') {
    window.gtag('event', name, { quiz_app: app || 'other' });
  }
}
function toast(message) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(window.__quizToast);
  window.__quizToast = setTimeout(() => el.classList.remove('show'), 2200);
}
document.addEventListener('click', (event) => {
  const target = event.target.closest('[data-event]');
  if (target) ga(target.dataset.event, target.dataset.app);
});
document.addEventListener('click', async (event) => {
  const target = event.target.closest('[data-copy-answer]');
  if (!target) return;
  const value = document.getElementById('answer-value');
  const answer = (target.dataset.copyText || value?.textContent || '').trim();
  if (!answer) return;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(answer);
    } else {
      const area = document.createElement('textarea');
      area.value = answer;
      area.style.position = 'fixed';
      area.style.left = '-9999px';
      document.body.append(area);
      area.select();
      try {
        if (!document.execCommand('copy')) throw new Error('clipboard unavailable');
      } finally {
        area.remove();
      }
    }
    ga('answer_copy', target.dataset.app);
    toast('정답을 복사했어요. 원본 앱의 회차를 확인해 주세요!');
  } catch (error) {
    toast('복사할 수 없습니다. 정답을 길게 눌러 복사해 주세요.');
  }
});

const search = document.getElementById('app-search');
if (search) {
  const activeCards = Array.from(document.querySelectorAll('.app-list .appcard'));
  const candidateCards = Array.from(document.querySelectorAll('.app-list .directory-card'));
  const cards = [...activeCards, ...candidateCards];
  const details = document.getElementById('candidate-details');
  const empty = document.getElementById('search-empty');
  const count = document.getElementById('search-count');
  const filter = () => {
    const q = search.value.trim().toLocaleLowerCase('ko-KR');
    let matches = 0, candidateMatches = 0;
    for (const card of cards) {
      card.hidden = !card.textContent.toLocaleLowerCase('ko-KR').includes(q);
      if (!card.hidden) {
        matches += 1;
        if (card.classList.contains('directory-card')) candidateMatches += 1;
      }
    }
    if (details && q && candidateMatches) details.open = true;
    if (details && !q) details.open = false;
    if (empty) empty.hidden = matches !== 0;
    if (count) count.textContent = q
      ? matches + '개 검색 결과 · 확인 대기 항목은 현재 참여 가능하다는 뜻이 아닙니다'
      : '정답 자료 있는 앱 ' + activeCards.length + '개 · 확인 대기 후보 ' + candidateCards.length + '개';
  };
  search.addEventListener('input', filter);
  filter();
}

const SAVED_KEY = 'quizpick_saved_v1';
const QUIZ_ROUTE = /^\/quizpick-lite\/quiz\/([a-z0-9_-]+)\/(\d{4}-\d{2}-\d{2})\/([a-z0-9_-]+)\/$/;
let publishedQuizPaths = new Set();
function safeQuizPath(value) {
  return typeof value === 'string' && QUIZ_ROUTE.test(value);
}
function readSaved() {
  try {
    const value = JSON.parse(localStorage.getItem(SAVED_KEY) || '[]');
    return Array.isArray(value) ? value.filter(x => x && safeQuizPath(x.url)).slice(0, 100) : [];
  } catch (_) { return []; }
}
function writeSaved(items) {
  try {
    localStorage.setItem(SAVED_KEY, JSON.stringify(items.slice(0, 100)));
    return true;
  } catch (_) {
    toast('이 브라우저에서는 즐겨찾기를 저장할 수 없습니다.');
    return false;
  }
}
function daysFromToday(dateStr) {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Seoul', year: 'numeric', month: '2-digit', day: '2-digit'
  }).formatToParts(new Date());
  const fields = Object.fromEntries(parts.map(p => [p.type, p.value]));
  const todayUtc = Date.UTC(+fields.year, +fields.month - 1, +fields.day);
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateStr || '');
  if (!match) return Infinity;
  const rowUtc = Date.UTC(+match[1], +match[2] - 1, +match[3]);
  return Math.floor((todayUtc - rowUtc) / 86400000);
}
function canOpenSaved(url) {
  const match = QUIZ_ROUTE.exec(url || '');
  if (!match) return false;
  const age = daysFromToday(match[2]);
  return age >= 0 && age <= 6 && publishedQuizPaths.has(url);
}
function appHub(url) {
  const m = QUIZ_ROUTE.exec(url || '');
  if (!m) return '/quizpick-lite/apps/';
  if (m[1] === 'toss' || m[1] === 'kakaobank')
    return '/quizpick-lite/' + m[1] + '/';
  return '/quizpick-lite/apps/' + m[1] + '/';
}
function syncSaveButtons() {
  const items = readSaved();
  document.querySelectorAll('[data-save-quiz]').forEach(btn => {
    const selected = items.some(x => x.url === btn.dataset.url);
    btn.setAttribute('aria-pressed', String(selected));
    btn.textContent = selected ? '♥ 저장됨 · 해제하기' : '♡ 즐겨찾기에 저장';
  });
}
document.addEventListener('click', event => {
  const btn = event.target.closest('[data-save-quiz]');
  if (!btn) return;
  const url = btn.dataset.url || '';
  if (!safeQuizPath(url)) return;
  const title = (btn.dataset.title || '저장한 퀴즈').slice(0, 120);
  let items = readSaved();
  const selected = items.some(x => x.url === url);
  const entry = {
    url, title,
    answer: (btn.dataset.answer || '').slice(0, 240),
    question: (btn.dataset.question || '').slice(0, 180)
  };
  items = selected ? items.filter(x => x.url !== url) : [entry, ...items];
  if (writeSaved(items)) {
    syncSaveButtons();
    toast(selected ? '즐겨찾기에서 삭제했어요.' : '즐겨찾기에 저장했어요.');
    ga(selected ? 'quiz_unsave' : 'quiz_save', btn.dataset.app);
  }
});
function renderSaved() {
  const root = document.getElementById('saved-list');
  if (!root) return;
  root.replaceChildren();
  const items = readSaved();
  const empty = document.getElementById('saved-empty');
  if (empty) empty.hidden = items.length > 0;
  for (const item of items) {
    const row = document.createElement('div');
    row.className = 'saved-item';
    const info = document.createElement('div');
    const title = document.createElement('strong');
    title.textContent = String(item.title || '저장한 퀴즈');
    const note = document.createElement('small');
    const available = canOpenSaved(item.url);
    note.textContent = available
      ? '최근 회차 · 원본 앱에서 리워드 여부 확인'
      : '지난 회차 · 정답 스냅샷 보관 / 현재 보상 미확인';
    info.append(title, note);
    if (!available && item.answer) {
      const question = document.createElement('small');
      question.textContent = String(item.question || '저장된 정답');
      const answer = document.createElement('div');
      answer.className = 'saved-snapshot';
      answer.textContent = '당시 참고 정답: ' + String(item.answer);
      info.append(question, answer);
    }
    if (!available && !item.answer) {
      const note2 = document.createElement('small');
      note2.textContent = '과거에 저장된 주소입니다. 이전 정답은 저장되지 않았습니다.';
      info.append(note2);
    }
    const actions = document.createElement('div');
    actions.className = 'saved-actions';
    const anchor = document.createElement('a');
    anchor.href = available ? item.url : appHub(item.url);
    anchor.textContent = available ? '정답 보기 →' : '앱 목록 →';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'remove-saved';
    button.textContent = '삭제';
    button.setAttribute('aria-label', title.textContent + ' 즐겨찾기 삭제');
    button.addEventListener('click', () => {
      if (writeSaved(readSaved().filter(x => x.url !== item.url))) {
        renderSaved();
        toast('삭제했어요.');
      }
    });
    actions.append(anchor, button);
    row.append(info, actions);
    root.append(row);
  }
}
syncSaveButtons();
(async () => {
  try {
    const response = await fetch('/quizpick-lite/active-quizzes.json', { cache: 'no-store' });
    if (response.ok) {
      const json = await response.json();
      if (Array.isArray(json.paths)) {
        publishedQuizPaths = new Set(json.paths.filter(safeQuizPath));
      }
    }
  } catch (_) {
    // Without a verified published manifest, prefer archived summaries over 404 links.
  }
  renderSaved();
})();
