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
  if (!value) return;
  const answer = value.textContent.trim();
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
  const cards = Array.from(document.querySelectorAll('.app-list .appcard'));
  const empty = document.getElementById('search-empty');
  const count = document.getElementById('search-count');
  const filter = () => {
    const q = search.value.trim().toLocaleLowerCase('ko-KR');
    let matches = 0;
    for (const card of cards) {
      card.hidden = !card.textContent.toLocaleLowerCase('ko-KR').includes(q);
      if (!card.hidden) matches += 1;
    }
    if (empty) empty.hidden = matches !== 0;
    if (count) count.textContent = matches + '개 앱 표시';
  };
  search.addEventListener('input', filter);
  filter();
}

// 즐겨찾기는 이 브라우저에만 저장되며 회원 계정이나 서버에 전송하지 않습니다.
const SAVED_KEY = 'quizpick_saved_v1';
function readSaved() {
  try {
    const value = JSON.parse(localStorage.getItem(SAVED_KEY) || '[]');
    return Array.isArray(value) ? value.filter(x => x && typeof x.url === 'string') : [];
  } catch (_) { return []; }
}
function writeSaved(items) {
  try { localStorage.setItem(SAVED_KEY, JSON.stringify(items.slice(0, 100))); return true; }
  catch (_) { toast('이 브라우저에서는 즐겨찾기를 저장할 수 없습니다.'); return false; }
}
function safeQuizPath(value) {
  return typeof value === 'string' && /^\/quizpick-lite\/quiz\/[a-z0-9_-]+\/\d{4}-\d{2}-\d{2}\/[a-z0-9_-]+\/$/.test(value);
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
  const title = btn.dataset.title || '저장한 퀴즈';
  if (!safeQuizPath(url)) return;
  let items = readSaved();
  const selected = items.some(x => x.url === url);
  items = selected ? items.filter(x => x.url !== url) : [{ url, title }, ...items];
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
  const items = readSaved().filter(x => safeQuizPath(x.url));
  const empty = document.getElementById('saved-empty');
  if (empty) empty.hidden = items.length > 0;
  for (const item of items) {
    const row = document.createElement('div');
    row.className = 'saved-item';
    const info = document.createElement('div');
    const title = document.createElement('strong');
    title.textContent = String(item.title || '저장한 퀴즈');
    const note = document.createElement('small');
    note.textContent = '정답 상세 페이지로 이동';
    info.append(title, note);
    const actions = document.createElement('div');
    const anchor = document.createElement('a');
    anchor.href = item.url;
    anchor.textContent = '열기 →';
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
renderSaved();
