#!/usr/bin/env python3
from pathlib import Path
import shutil, time, sys

FILES = ['index.html','planner.html','navigator.html','sw.js']

def die(msg):
    print('\nERRORE:', msg)
    sys.exit(1)

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        die(f'{label}: atteso 1 marker, trovati {n}')
    return text.replace(old, new, 1)

def replace_at_least_once(text, old, new, label):
    n = text.count(old)
    if n < 1:
        die(f'{label}: marker non trovato')
    return text.replace(old, new)

root = Path.cwd()
for f in FILES:
    if not (root/f).exists():
        die(f'manca {f} nella root del repository')

src = {f:(root/f).read_text(encoding='utf-8') for f in FILES}

# Strong preflight: this hotfix must run only on the successful 0.70.49 hotfix state.
if 'window.KTN_NAV_BUILD="0.70.49";' not in src['navigator.html']:
    die('navigator.html non e la build 0.70.49 attesa')
if "const CACHE='ktn-007049-launcher-v2';" not in src['sw.js']:
    die('sw.js non e la release-safe 0.70.49 attesa')
if './sw.js?v=7049' not in src['index.html']:
    die('index.html non richiama sw.js?v=7049')
if './sw.js?v=7049' not in src['planner.html']:
    die('planner.html non richiama sw.js?v=7049')

out = dict(src)

# --- index.html ---
i = out['index.html']
i = replace_once(i, '<title>KnightTruckerNavy 0.70.49</title>', '<title>KnightTruckerNavy 0.70.50</title>', 'index title')
i = replace_once(i, './manifest.json?v=7049', './manifest.json?v=7050', 'index manifest cache bust')
i = replace_once(i, '<div class="ver">VERSIONE 0.70.49</div>', '<div class="ver">VERSIONE 0.70.50</div>', 'index visible version')
i = replace_once(i, './sw.js?v=7049', './sw.js?v=7050', 'index sw cache bust')
out['index.html'] = i

# --- planner.html ---
p = out['planner.html']
p = replace_once(p, "window.KTN_APP_VERSION='0.0.70.49';", "window.KTN_APP_VERSION='0.0.70.50';", 'planner app version')
p = replace_once(p, "window.KTN_STARTUP_VERSION='0.0.70.49';", "window.KTN_STARTUP_VERSION='0.0.70.50';", 'planner startup version')
p = replace_once(p, './manifest.json?v=007049', './manifest.json?v=007050', 'planner manifest cache bust')
p = replace_once(p, './sw.js?v=7049', './sw.js?v=7050', 'planner sw cache bust')
# Keep descriptive title in sync if exact current title is present.
p = p.replace('KnightTruckerNavy - 0.0.70.49 GPS RESTORE FIX', 'KnightTruckerNavy - 0.0.70.50 MAP START FIX')
out['planner.html'] = p

# --- navigator.html ---
n = out['navigator.html']
n = replace_once(n, 'window.KTN_NAV_BUILD="0.70.49";', 'window.KTN_NAV_BUILD="0.70.50";', 'navigator build')

STARTUP_GUARD = r'''/* === 0.70.50 MAP STARTUP GUARD ===
   Do not reveal a black cockpit. Navigation becomes visible only when
   either MapLibre is really ready or the already-rendered Leaflet map is
   explicitly promoted as fallback. One timeout, no polling loop. */
function ktn07050HasRoute(){
  try{return Array.isArray(routeCoords)&&routeCoords.length>=2&&Number(totalMeters)>0}catch(e){return false}
}
function ktn07050IsExplorer(){
  try{return !!(window.KTN_GATTO_EXPLORER||gattoExplorerMode)}catch(e){return !!window.KTN_GATTO_EXPLORER}
}
function ktn07050MapVisibleReady(){
  return !!(window.PRO_MAP_READY||document.body.classList.contains('pro-map-fallback'));
}
function ktn07050FmtSec(sec){
  sec=Math.max(0,Number(sec)||0);var m=Math.round(sec/60),h=Math.floor(m/60);m%=60;
  return h>0?(h+':'+String(m).padStart(2,'0')):(m+' min');
}
function ktn07050RouteReadyUI(){
  if(!ktn07050HasRoute())return;
  try{
    if(!lastPos){
      var e=document.getElementById('turnInstruction');if(e)e.textContent='Percorso pronto · attesa GPS…';
      e=document.getElementById('turnRoad');if(e)e.textContent=String((cfg&&cfg.toName)||'Arrivo').split(',')[0];
      e=document.getElementById('remaining');if(e)e.textContent=fmtKm(totalMeters);
      var sec=Math.max(0,Number(window.ktn51PlannedDurationSec)||0);
      e=document.getElementById('ktn51TimeRemaining');if(e)e.textContent=sec?ktn07050FmtSec(sec):'--:--';
      e=document.getElementById('ktn51ArrivalTime');if(e&&sec)e.textContent=new Date(Date.now()+sec*1000).toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'});
    }
  }catch(e){}
}
function ktn07050RevealNavigation(){
  var contentReady=ktn07050IsExplorer()||ktn07050HasRoute();
  if(!contentReady||!ktn07050MapVisibleReady())return false;
  try{ktn07050RouteReadyUI()}catch(e){}
  var ld=document.getElementById('loading');if(ld)ld.style.display='none';
  return true;
}
function ktn07050PromoteLeafletFallback(reason){
  if(window.PRO_MAP_READY){
    try{if(typeof window.proMapUpdateRoute==='function')window.proMapUpdateRoute()}catch(e){}
    ktn07050RevealNavigation();
    return;
  }
  document.body.classList.add('pro-map-fallback');
  try{
    if(typeof MAP!=='undefined'&&MAP){
      MAP.invalidateSize(true);
      if(typeof routeLayer!=='undefined'&&routeLayer&&routeLayer.getBounds){var b=routeLayer.getBounds();if(b&&b.isValid&&b.isValid())MAP.fitBounds(b.pad(.08));}
    }
  }catch(e){}
  try{console.warn('KTN 0.70.50 Leaflet fallback:',reason||'MapLibre not ready')}catch(e){}
  ktn07050RevealNavigation();
}
function ktn07050ArmMapFallback(){
  if(window.__KTN_07050_MAP_TIMER__)clearTimeout(window.__KTN_07050_MAP_TIMER__);
  if(window.PRO_MAP_READY){ktn07050RevealNavigation();return;}
  window.__KTN_07050_MAP_TIMER__=setTimeout(function(){
    window.__KTN_07050_MAP_TIMER__=null;
    if(!window.PRO_MAP_READY)ktn07050PromoteLeafletFallback('startup timeout');
    else ktn07050RevealNavigation();
  },1600);
}
window.ktn07050OnMapReady=function(){
  if(window.__KTN_07050_MAP_TIMER__){clearTimeout(window.__KTN_07050_MAP_TIMER__);window.__KTN_07050_MAP_TIMER__=null;}
  try{if(typeof window.proMapUpdateRoute==='function')window.proMapUpdateRoute()}catch(e){}
  try{if(typeof proCameraFetchRoute==='function'&&ktn07050HasRoute())proCameraFetchRoute()}catch(e){}
  ktn07050RevealNavigation();
};

'''

n = replace_once(n, 'function ktnRequestGpsStart(){', STARTUP_GUARD + 'function ktnRequestGpsStart(){', 'insert 0.70.50 startup guard')

# Route is already calculated here. Prime the HUD and arm one map fallback timeout.
old_apply = "updateStopUI();\n proMapUpdateRoute();setTimeout(proCameraFetchRoute,500);"
new_apply = "updateStopUI();\n proMapUpdateRoute();setTimeout(proCameraFetchRoute,500);\n try{ktn07050RouteReadyUI();ktn07050ArmMapFallback();ktn07050RevealNavigation()}catch(e){}"
n = replace_once(n, old_apply, new_apply, 'applyRoute map-ready handoff')

# Do not hide the loading screen merely because watchPosition has started.
old_runtime = "var sb0=document.getElementById('startBtn');if(sb0)sb0.style.display='none';\n  var ld=document.getElementById('loading');if(ld)ld.style.display='none';\n  if(!navigator.geolocation)"
new_runtime = "var sb0=document.getElementById('startBtn');if(sb0)sb0.style.display='none';\n  try{ktn07050ArmMapFallback();ktn07050RevealNavigation()}catch(e){}\n  if(!navigator.geolocation)"
n = replace_once(n, old_runtime, new_runtime, 'runtime reveal only when map ready')

# When the professional map really reaches its load event, release startup immediately.
old_ready = "E.ready=true;window.PRO_MAP_READY=true;\n      hybrid();ensureRoute();ensureMarker();gestures();setMode('GUIDA');"
new_ready = "E.ready=true;window.PRO_MAP_READY=true;\n      hybrid();ensureRoute();ensureMarker();gestures();setMode('GUIDA');\n      try{if(typeof window.ktn07050OnMapReady==='function')queueMicrotask(window.ktn07050OnMapReady)}catch(_e){}"
n = replace_once(n, old_ready, new_ready, 'MapLibre ready handoff')

out['navigator.html'] = n

# --- sw.js ---
s = out['sw.js']
s = replace_once(s, '/* KnightTruckerNavy 0.70.49 — release-safe service worker */', '/* KnightTruckerNavy 0.70.50 — release-safe service worker */', 'sw header')
s = replace_once(s, "const CACHE='ktn-007049-launcher-v2';", "const CACHE='ktn-007050-launcher-v3';", 'sw cache')
out['sw.js'] = s

# Sanity checks before any write.
checks = [
    ('navigator build', 'window.KTN_NAV_BUILD="0.70.50";' in out['navigator.html']),
    ('startup guard', 'function ktn07050ArmMapFallback()' in out['navigator.html']),
    ('runtime no early hide', "var ld=document.getElementById('loading');if(ld)ld.style.display='none';\n  if(!navigator.geolocation)" not in out['navigator.html']),
    ('map ready hook', 'window.ktn07050OnMapReady' in out['navigator.html']),
    ('index sw 7050', './sw.js?v=7050' in out['index.html']),
    ('planner sw 7050', './sw.js?v=7050' in out['planner.html']),
    ('sw cache 7050', "const CACHE='ktn-007050-launcher-v3';" in out['sw.js']),
]
for label, ok in checks:
    if not ok: die('sanity check fallito: '+label)

stamp=time.strftime('%Y%m%d_%H%M%S')
for f in FILES:
    shutil.copy2(root/f, root/(f+'.pre_hotfix_07050_'+stamp+'.bak'))
for f in FILES:
    (root/f).write_text(out[f], encoding='utf-8', newline='\n')

print('\nHOTFIX 0.70.50 APPLICATO CORRETTAMENTE')
print('- schermata nera: non viene piu mostrata prima della mappa pronta')
print('- fallback Leaflet automatico dopo 1.6 s se MapLibre non e pronta')
print('- nessun polling: un solo timeout startup')
print('- percorso/tempo/ETA visibili gia durante attesa primo fix GPS')
print('- cache PWA aggiornata a 0.70.50')
