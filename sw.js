/* KnightTruckerNavy 0.70.41 HOTFIX — non-blocking service worker */
const CACHE='ktn-007041-hotfix-v1';
const CORE=[
  './',
  './index.html',
  './navigator.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
];

async function safePrecache(){
  const cache=await caches.open(CACHE);
  await Promise.allSettled(CORE.map(async url=>{
    try{
      const r=await fetch(url,{cache:'reload'});
      if(r&&r.ok) await cache.put(url,r.clone());
    }catch(_){ /* un singolo file non deve bloccare l'installazione */ }
  }));
}

self.addEventListener('install',event=>{
  self.skipWaiting();
  event.waitUntil(safePrecache());
});

self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(keys.filter(k=>
      k!==CACHE && (
        k==='ktn-0066-landscape-shell' ||
        k.startsWith('ktn-007040-split-assets-') ||
        k.startsWith('ktn-007041-hotfix-')
      )
    ).map(k=>caches.delete(k)));
    await self.clients.claim();
  })());
});

async function fetchWithTimeout(request,ms){
  const ctl=new AbortController();
  const t=setTimeout(()=>ctl.abort(),ms);
  try{return await fetch(request,{cache:'no-store',signal:ctl.signal})}
  finally{clearTimeout(t)}
}

async function networkFirst(request,fallbackUrl){
  const cache=await caches.open(CACHE);
  try{
    const response=await fetchWithTimeout(request,4500);
    if(response&&response.ok){
      cache.put(request,response.clone()).catch(()=>{});
      return response;
    }
    throw new Error('HTTP non valido');
  }catch(_){
    return (await cache.match(request,{ignoreSearch:true})) ||
           (fallbackUrl ? await cache.match(fallbackUrl,{ignoreSearch:true}) : undefined) ||
           Response.error();
  }
}

self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  const url=new URL(event.request.url);

  /* CDN e servizi esterni: lascia fare direttamente al browser. */
  if(url.origin!==self.location.origin)return;

  const path=url.pathname;
  if(event.request.mode==='navigate' ||
     path.endsWith('/index.html') || path.endsWith('/navigator.html') ||
     path.endsWith('/manifest.json') || path.endsWith('.json') ||
     path.includes('/offline/')){
    const fallback=path.endsWith('/navigator.html')?'./navigator.html':'./index.html';
    event.respondWith(networkFirst(event.request,fallback));
    return;
  }

  /* Asset locali: cache on demand; niente precache da 4.5 MB che blocca installazione. */
  event.respondWith(caches.match(event.request,{ignoreSearch:true}).then(cached=>{
    if(cached)return cached;
    return fetch(event.request).then(response=>{
      if(response&&response.ok){
        const copy=response.clone();
        caches.open(CACHE).then(c=>c.put(event.request,copy)).catch(()=>{});
      }
      return response;
    });
  }));
});
