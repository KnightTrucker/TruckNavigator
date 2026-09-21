/* ToraNavy 0.17.77 TUNNEL ROAD-NAME HANDOFF */
/* ToraNavy 0.17.50 MICROSCOPIO SAFE FINAL */
const CACHE='ktn-v01777-tunnel-roadname-handoff';
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
  './toranavy_maneuver_exit.webp',
  './toranavy_maneuver_exit_left.webp',
  './toranavy_maneuver_exit_right.webp',
  './toranavy_maneuver_fork_left.webp',
  './toranavy_maneuver_fork_right.webp',
  './toranavy_maneuver_keep_left.webp',
  './toranavy_maneuver_keep_right.webp',
  './toranavy_maneuver_merge_left.webp',
  './toranavy_maneuver_merge_right.webp',
  './toranavy_maneuver_next_exit.webp',
  './toranavy_maneuver_sharp_left.webp',
  './toranavy_maneuver_sharp_right.webp',
  './toranavy_maneuver_slight_left.webp',
  './toranavy_maneuver_slight_right.webp',
  './toranavy_maneuver_straight.webp',
  './toranavy_maneuver_turn_left.webp',
  './toranavy_maneuver_turn_right.webp',
  './toranavy_maneuver_uturn_left.webp',
  './toranavy_maneuver_uturn_right.webp',
  './rallenta.webp'];

self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(c=>c.addAll(LOCAL)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate',event=>{
  event.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))
      .then(()=>self.clients.claim())
  );
});

self.addEventListener('fetch',event=>{
  const req=event.request;
  if(req.method!=='GET')return;
  const url=new URL(req.url);
  if(url.origin!==self.location.origin)return;

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
