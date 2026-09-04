/* KnightTruckerNavy 0.70.49 — release-safe service worker */
const CACHE='ktn-007049-launcher-v2';
const SHELL=['./index.html','./planner.html','./navigator.html','./manifest.json'];

function canonicalRequest(reqOrUrl){
  const u=new URL(typeof reqOrUrl==='string'?reqOrUrl:reqOrUrl.url,self.registration.scope);
  return new Request(u.origin+u.pathname,{credentials:'same-origin'});
}

self.addEventListener('install',event=>{
  event.waitUntil((async()=>{
    const cache=await caches.open(CACHE);
    await Promise.allSettled(SHELL.map(async path=>{
      try{
        const r=await fetch(path,{cache:'no-store'});
        if(r&&r.ok)await cache.put(canonicalRequest(new URL(path,self.registration.scope).href),r.clone());
      }catch(_e){}
    }));
    await self.skipWaiting();
  })());
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

async function htmlNetFirst(req){
  const cache=await caches.open(CACHE);
  const canonical=canonicalRequest(req);
  const ctl=new AbortController();
  const timer=setTimeout(()=>ctl.abort(),8000);
  try{
    const r=await fetch(req,{cache:'no-store',signal:ctl.signal});
    if(r&&r.ok)cache.put(canonical,r.clone()).catch(()=>{});
    return r;
  }catch(_e){
    return (await cache.match(canonical)) || Response.error();
  }finally{
    clearTimeout(timer);
  }
}

async function dataNetFirst(req){
  const cache=await caches.open(CACHE);
  const ctl=new AbortController();
  const timer=setTimeout(()=>ctl.abort(),6000);
  try{
    const r=await fetch(req,{cache:'no-store',signal:ctl.signal});
    if(r&&r.ok)cache.put(req,r.clone()).catch(()=>{});
    return r;
  }catch(_e){
    return (await cache.match(req,{ignoreSearch:true})) || Response.error();
  }finally{
    clearTimeout(timer);
  }
}

self.addEventListener('fetch',event=>{
  const req=event.request;
  if(req.method!=='GET')return;

  const u=new URL(req.url);
  if(u.origin!==self.location.origin)return;

  if(req.headers.has('range')||req.destination==='audio'||req.destination==='video')return;

  const p=u.pathname;
  if(req.mode==='navigate'||p.endsWith('.html')){
    event.respondWith(htmlNetFirst(req));
    return;
  }

  if(p.endsWith('.json')||p.includes('/offline/')||p.includes('/road_safety/')){
    event.respondWith(dataNetFirst(req));
    return;
  }

  event.respondWith(
    caches.match(req).then(c=>{
      if(c)return c;
      return fetch(req).then(r=>{
        if(r&&r.ok)caches.open(CACHE).then(x=>x.put(req,r.clone())).catch(()=>{});
        return r;
      });
    })
  );
});
