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
  search.addEventListener('input', () => {
    const q = search.value.trim().toLocaleLowerCase('ko-KR');
    for (const card of cards) {
      card.hidden = !card.textContent.toLocaleLowerCase('ko-KR').includes(q);
    }
  });
}