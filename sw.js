/* KnightTruckerNavy 0.70.46 — launcher-safe service worker */
const CACHE='ktn-007046-launcher-v1';

self.addEventListener('install',event=>{
  self.skipWaiting();
});

self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    const keys=await caches.keys();

    await Promise.all(
      keys
        .filter(k=>k!==CACHE && k.startsWith('ktn-'))
        .map(k=>caches.delete(k))
    );

    await self.clients.claim();
  })());
});

async function netFirst(req){
  const cache=await caches.open(CACHE);
  const ctl=new AbortController();
  const timer=setTimeout(()=>ctl.abort(),4000);

  try{
    const r=await fetch(req,{
      cache:'no-store',
      signal:ctl.signal
    });

    if(r && r.ok){
      cache.put(req,r.clone()).catch(()=>{});
    }

    return r;

  }catch(e){

    const c=await cache.match(req,{
      ignoreSearch:true
    });

    return c || Response.error();

  }finally{
    clearTimeout(timer);
  }
}

self.addEventListener('fetch',event=>{
  const req=event.request;

  if(req.method!=='GET') return;

  const u=new URL(req.url);

  if(u.origin!==self.location.origin) return;

  if(
    req.headers.has('range') ||
    req.destination==='audio' ||
    req.destination==='video'
  ){
    return;
  }

  const p=u.pathname;

  if(
    req.mode==='navigate' ||
    p.endsWith('.html') ||
    p.endsWith('.json') ||
    p.includes('/offline/') ||
    p.includes('/road_safety/')
  ){
    event.respondWith(
      netFirst(req)
    );
    return;
  }

  event.respondWith(
    caches.match(
      req,
      {ignoreSearch:true}
    ).then(c=>{

      if(c) return c;

      return fetch(req).then(r=>{

        if(r && r.ok){
          caches.open(CACHE)
            .then(x=>x.put(req,r.clone()))
            .catch(()=>{});
        }

        return r;
      });
    })
  );
});
