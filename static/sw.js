// ウェブ版は公開を終了しました。
//
// 以前の Service Worker はアプリ本体をキャッシュしていたので、そのままだと
// 一度でも開いた人のブラウザが「消えたはずの画面」を出し続けてしまう。
// この版は自分自身を登録解除し、キャッシュを消すだけの中身にしてある。
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) await caches.delete(k);
    await self.registration.unregister();
    for (const c of await self.clients.matchAll()) c.navigate(c.url);
  })());
});
