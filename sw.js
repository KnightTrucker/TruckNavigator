/* KnightTruckerNavy 0.70.45 STABLE — resilient service worker */
const CACHE='ktn-007045-stable-v1';
const CORE=['./','./index.html','./navigator.html','./manifest.json','./icon-192.png','./icon-512.png'];

async function safePrecache(){
  const cache=await caches.open(CACHE);
  await Promise.allSettled(CORE.map(async url=>{
    try{const r=await fetch(url,{cache:'reload'});if(r&&r.ok)await cache.put(url,r.clone())}catch(_e){}
  }));
}
self.addEventListener('install',event=>{self.skipWaiting();event.waitUntil(safePrecache())});
self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(keys.filter(k=>k!==CACHE&&(k==='ktn-0066-landscape-shell'||k.startsWith('ktn-00704')||k.startsWith('ktn-007040')||k.startsWith('ktn-007041')||k.startsWith('ktn-007042')||k.startsWith('ktn-007043')||k.startsWith('ktn-007044'))).map(k=>caches.delete(k)));
    await self.clients.claim();
  })());
});
async function fetchTimed(request,ms){
  const ctl=new AbortController(),t=setTimeout(()=>ctl.abort(),ms);
  try{return await fetch(request,{cache:'no-store',signal:ctl.signal})}finally{clearTimeout(t)}
}
async function networkFirst(request,fallback){
  const cache=await caches.open(CACHE);
  try{
    const r=await fetchTimed(request,5000);
    if(!r||!r.ok)throw new Error('network');
    cache.put(request,r.clone()).catch(()=>{});return r;
  }catch(_e){
    const c=await cache.match(request,{ignoreSearch:true});if(c)return c;
    if(fallback){const f=await cache.match(fallback,{ignoreSearch:true});if(f)return f}
    return Response.error();
  }
}
self.addEventListener('fetch',event=>{
  const req=event.request;if(req.method!=='GET')return;
  const url=new URL(req.url);if(url.origin!==self.location.origin)return;
  if(req.headers.has('range')||req.destination==='audio'||req.destination==='video')return;
  const p=url.pathname;
  if(req.mode==='navigate'||p.endsWith('/index.html')||p.endsWith('/navigator.html')){
    event.respondWith(networkFirst(req,p.endsWith('/navigator.html')?'./navigator.html':'./index.html'));return;
  }
  if(p.endsWith('.json')||p.includes('/offline/')||p.includes('/road_safety/')){
    event.respondWith(networkFirst(req,null));return;
  }
  event.respondWith(caches.match(req,{ignoreSearch:true}).then(c=>c||fetch(req).then(r=>{if(r&&r.ok){const cp=r.clone();caches.open(CACHE).then(x=>x.put(req,cp)).catch(()=>{})}return r})));
});
