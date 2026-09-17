const APP_PREFIX='toradove-';
const CACHE='toradove-pwa-v0.4.9';
const SHELL=[
  './',
  './index.html',
  './toradove.webmanifest',
  './tora_crest.png',
  './powered_by_az.png',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install',e=>{
  e.waitUntil(
    caches.open(CACHE)
      .then(c=>c.addAll(SHELL))
      .then(()=>self.skipWaiting())
  );
});

self.addEventListener('activate',e=>{
  e.waitUntil(
    caches.keys()
      .then(keys=>Promise.all(
        keys
          .filter(k=>k.startsWith(APP_PREFIX) && k!==CACHE)
          .map(k=>caches.delete(k))
      ))
      .then(()=>self.clients.claim())
  );
});

self.addEventListener('fetch',e=>{
  const r=e.request;
  if(r.method!=='GET')return;

  const u=new URL(r.url);

  /* Non toccare richieste di altre origini. */
  if(u.origin!==self.location.origin)return;

  /* Navigazioni: network-first, fallback SOLO sull'index ToraDove. */
  if(r.mode==='navigate'){
    e.respondWith(
      fetch(r).then(resp=>{
        const copy=resp.clone();
        caches.open(CACHE).then(c=>c.put('./index.html',copy)).catch(()=>{});
        return resp;
      }).catch(()=>caches.match('./index.html'))
    );
    return;
  }

  e.respondWith(
    caches.match(r).then(hit=>hit||fetch(r))
  );
});
