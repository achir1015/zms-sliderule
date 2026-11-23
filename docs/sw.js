/* 離線快取：程式檔先用網路（拿到最新版），沒網路才用快取；圖片與語音先用快取。
 * 改了 docs/ 的程式就把 CACHE 的版本號加 1。 */
const CACHE = "sliderule-v1";
const CORE = ["./", "./index.html", "./app/", "./app/index.html", "./app/style.css", "./app/rule.js", "./app/demo.js",
  "./app/data.js", "./app/app.js", "./manifest.webmanifest", "./img/icon-192.png", "./img/favicon-64.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  if (req.headers.has("range")) return;                     // 語音串流的分段請求交給瀏覽器
  const media = /\.(mp3|png|jpg|jpeg|svg)$/i.test(new URL(req.url).pathname);
  if (media) {
    e.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      if (res.ok && res.status === 200) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); }
      return res;
    })));
  } else {
    e.respondWith(fetch(req).then((res) => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true })));
  }
});
