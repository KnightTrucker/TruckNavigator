/* ToraNavy 0.16.96 GUIDANCE-MODEL · ROOT PWA SCOPE FIX */
const CACHE='ktn-v01696-guidance-model-pwa-scopefix1';
const LOCAL=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png',
  './toranavy_startup.webp',
  './toranavy_logo.webp',
  './toranavy_stemma_sfondo.webp',
  './toranavy_arrivo_shell.webp',
  './toranavy_stemma_versione.webp',
  './toranavy_mascotte.webp',
  './toranavy_autovelox_poliziotto.webp',
  './toranavy_arrivo_navigatore.webp',
  './toranavy_sosta_tappa.webp',
  './rallenta.webp'];

self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(c=>c.addAll(LOCAL)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate',event=>{
  event.waitUntil(
    caches.keys().then(keys=>Promise.all(
      keys
        .filter(k=>k.startsWith('ktn-') && k!==CACHE)
        .map(k=>caches.delete(k))
    )).then(()=>self.clients.claim())
  );
});

self.addEventListener('fetch',event=>{
  const req=event.request;
  if(req.method!=='GET')return;
  const url=new URL(req.url);
  if(url.origin!==self.location.origin)return;

  /* ToraDove è una PWA separata in sottocartella.
     Il service worker root di ToraNavy NON deve intercettarla. */
  const path=url.pathname.toLowerCase();
  if(path.startsWith('/toradove/'))return;

  if(req.mode==='navigate' || url.pathname.endsWith('/index.html')){
    event.respondWith(
      fetch(req).then(resp=>{
        const copy=resp.clone();
        caches.open(CACHE).then(c=>c.put('./index.html',copy));
        return resp;
      }).catch(()=>caches.match('./index.html'))
    );
    return;
  }

  event.respondWith(
    caches.match(req).then(hit=>hit || fetch(req).then(resp=>{
      const copy=resp.clone();
      caches.open(CACHE).then(c=>c.put(req,copy));
      return resp;
    }))
  );
});
