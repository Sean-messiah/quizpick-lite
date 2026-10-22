'use strict';
const HOME = '/quizpick-lite/';
self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (_) {}
  const title = typeof data.title === 'string' ? data.title.slice(0, 90) : '퀴즈픽 새 알림';
  const path = typeof data.url === 'string' ? data.url : HOME;
  const dest = new URL(path, self.location.origin);
  const url = dest.origin === self.location.origin && dest.pathname.startsWith(HOME) ? dest.href : self.location.origin + HOME;
  event.waitUntil(self.registration.showNotification(title, {
    body: typeof data.body === 'string' ? data.body.slice(0, 180) : '새로운 정답을 확인하세요.',
    icon: HOME + 'assets/qp-icon.svg',
    badge: HOME + 'assets/qp-icon.svg',
    tag: typeof data.tag === 'string' ? data.tag.slice(0, 100) : 'quizpick',
    data: { url },
    renotify: false
  }));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const dest = event.notification.data?.url || self.location.origin + HOME;
  event.waitUntil((async () => {
    const windows = await clients.matchAll({ type:'window', includeUncontrolled:true });
    const match = windows.find(x => x.url === dest);
    if (match) return match.focus();
    return clients.openWindow(dest);
  })());
});