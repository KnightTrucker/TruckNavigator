/* KnightTruckerNavy 0.70.40 SPLIT-ASSETS */
const CACHE='ktn-007040-split-assets-v1';
const PRECACHE=[
  "./",
  "./index.html",
  "./navigator.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./assets/audio/punta.mp3",
  "./assets/audio/schumacher.mp3",
  "./assets/audio/version-voice.m4a",
  "./assets/navigation/arrival-overlay.png",
  "./assets/navigation/camera-cop.png",
  "./assets/navigation/cat.png",
  "./assets/navigation/hgv-no-pass-off.png",
  "./assets/navigation/hgv-no-pass-on.png",
  "./assets/navigation/mascot.jpg",
  "./assets/navigation/stop-overlay.png",
  "./assets/ui/arrival.jpg",
  "./assets/ui/emblem.jpg",
  "./assets/ui/favicon.png",
  "./assets/ui/logo.png",
  "./assets/ui/truck-marker.jpg",
  "./assets/ui/version-crest.jpg"
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRECACHE)));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k =>
        k !== CACHE &&
        (k === 'ktn-0066-landscape-shell' || k.startsWith('ktn-007040-split-assets-'))
      ).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

async function networkFirst(request, fallbackUrl) {
  const cache=await caches.open(CACHE);
  try {
    const response=await fetch(request,{cache:'no-store'});
    if(response && response.ok) cache.put(request,response.clone()).catch(()=>{});
    return response;
  } catch(err) {
    return (await cache.match(request,{ignoreSearch:true})) ||
           (fallbackUrl ? await cache.match(fallbackUrl,{ignoreSearch:true}) : undefined) ||
           Response.error();
  }
}

self.addEventListener('fetch', event => {
  if(event.request.method!=='GET') return;
  const url=new URL(event.request.url);
  if(url.origin!==self.location.origin) return;

  const path=url.pathname;
  if(event.request.mode==='navigate' ||
     path.endsWith('/index.html') || path.endsWith('/navigator.html') ||
     path.endsWith('/manifest.json') || path.endsWith('.json') ||
     path.includes('/offline/')) {
    let fallback='./index.html';
    if(path.endsWith('/navigator.html')) fallback='./navigator.html';
    event.respondWith(networkFirst(event.request,fallback));
    return;
  }

  event.respondWith(
    caches.match(event.request,{ignoreSearch:true}).then(cached =>
      cached || fetch(event.request).then(response => {
        if(response && response.ok) {
          const copy=response.clone();
          caches.open(CACHE).then(cache=>cache.put(event.request,copy)).catch(()=>{});
        }
        return response;
      })
    )
  );
});
