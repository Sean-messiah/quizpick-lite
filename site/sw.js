'use strict';
const HOME = '/quizpick-lite/';
const DB = 'quizpick_push_diagnostics_v1';
function openDiagnostics() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB, 1);
    req.onupgradeneeded = () => {
      if(!req.result.objectStoreNames.contains('status')) req.result.createObjectStore('status');
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}
async function recordRemoteReceipt(time) {
  const db = await openDiagnostics();
  try {
    await new Promise((resolve,reject) => {
      const tx = db.transaction('status','readwrite');
      tx.objectStore('status').put(time,'lastRemoteReceipt');
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } finally { db.close(); }
}
async function readRemoteReceipt() {
  const db = await openDiagnostics();
  try {
    return await new Promise((resolve,reject) => {
      const tx = db.transaction('status','readonly');
      const req = tx.objectStore('status').get('lastRemoteReceipt');
      req.onsuccess = () => resolve(req.result||null);
      req.onerror = () => reject(req.error);
    });
  } finally { db.close(); }
}
self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (_) {}
  const title = typeof data.title === 'string' ? data.title.slice(0, 90) : '퀴즈픽 새 알림';
  const path = typeof data.url === 'string' ? data.url : HOME;
  const dest = new URL(path, self.location.origin);
  const url = dest.origin === self.location.origin && dest.pathname.startsWith(HOME) ? dest.href : self.location.origin + HOME;
  event.waitUntil((async () => {
    await self.registration.showNotification(title, {
      body: typeof data.body === 'string' ? data.body.slice(0, 180) : '새로운 정답을 확인하세요.',
      icon: HOME + 'assets/qp-icon-192.png',
      badge: HOME + 'assets/qp-icon-192.png',
      tag: typeof data.tag === 'string' ? data.tag.slice(0, 100) : 'quizpick',
      data: { url },
      renotify: false
    });
    const at = new Date().toISOString();
    // Store only the delivery handling time, never quiz answers or device keys.
    try { await recordRemoteReceipt(at); } catch (error) { console.warn('Push receipt not persisted'); }
    const windows = await self.clients.matchAll({type:'window',includeUncontrolled:true});
    for(const client of windows) client.postMessage({type:'QUIZPICK_PUSH_RECEIVED', at});
  })());
});
self.addEventListener('message', event => {
  if(event.data?.type!=='QUIZPICK_PUSH_LAST' || !event.ports?.[0]) return;
  event.waitUntil((async ()=>{
    let at=null;
    try { at=await readRemoteReceipt(); } catch (_) {}
    event.ports[0].postMessage({type:'QUIZPICK_PUSH_LAST',at});
  })());
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const dest = event.notification.data?.url || self.location.origin + HOME;
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type:'window', includeUncontrolled:true });
    const match = windows.find(x => x.url === dest);
    if (match) return match.focus();
    return self.clients.openWindow(dest);
  })());
});
