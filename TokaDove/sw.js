const CACHE='tokadove-v0.2';
const SHELL=['./','./tokadove.html','./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET') return;
  e.respondWith(
    fetch(e.request).then(r=>{
      const copy=r.clone();
      if(new URL(e.request.url).origin===location.origin){
        caches.open(CACHE).then(c=>c.put(e.request,copy)).catch(()=>{});
      }
      return r;
    }).catch(()=>caches.match(e.request))
  );
});