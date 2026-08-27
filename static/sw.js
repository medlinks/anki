/* 予備試験 暗記カード — Service Worker
   HTML は network-first（オンラインなら必ず最新版）、
   アイコン等は cache-first。オフラインでも起動できる。 */
const VERSION = '__VERSION__';
const CACHE = 'yb-' + VERSION;
const ASSETS = ['./', './index.html', './manifest.webmanifest',
                './icon-192.png', './icon-512.png', './icon-180.png', './icon-512-maskable.png',
                './kijunchi.html'];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    await Promise.all(ASSETS.map(u => c.add(u).catch(() => {})));
    // ここでは skipWaiting しない。学習中に勝手にリロードされるのを防ぎ、
    // 画面上の「今すぐ更新」を押したときだけ新バージョンに切り替える。
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  // ページ遷移だけを network-first に。
  // （accept ヘッダで判定していた頃は manifest.webmanifest まで HTML 扱いになり、
  //   オフライン時に index.html が返って「Manifest: Syntax error」を起こしていた）
  const isHTML = req.mode === 'navigate' || req.destination === 'document';
  if (isHTML) {
    e.respondWith((async () => {
      try {
        const fresh = await fetch(req);
        const c = await caches.open(CACHE);
        // 要求された URL そのものをキャッシュする。
        // （以前は常に './index.html' に上書きしていたため、別冊ページを開くと
        //   index.html のキャッシュが別冊の中身で潰れ、オフライン時に壊れていた）
        c.put(req, fresh.clone());
        return fresh;
      } catch (err) {
        return (await caches.match(req)) ||
               (await caches.match('./index.html')) ||
               (await caches.match('./')) ||
               new Response('オフラインです', {status: 503, headers: {'content-type': 'text/plain; charset=utf-8'}});
      }
    })());
    return;
  }
  e.respondWith((async () => {
    const hit = await caches.match(req);
    if (hit) return hit;
    try {
      const res = await fetch(req);
      if (res.ok && new URL(req.url).origin === location.origin) {
        const c = await caches.open(CACHE);
        c.put(req, res.clone());
      }
      return res;
    } catch (err) {
      return new Response('', {status: 504});
    }
  })());
});

self.addEventListener('message', e => { if (e.data === 'skipWaiting') self.skipWaiting(); });
