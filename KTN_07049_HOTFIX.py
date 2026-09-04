#!/usr/bin/env python3
# KnightTruckerNavy 0.70.49 — conservative hotfix patcher
# Targets the exact 0.70.49 / navigator 0.70.48 layout audited on 2026-09-04.
# Creates backups before writing and aborts without writes if an expected marker is missing.

from pathlib import Path
import shutil
import sys
import time

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
FILES = {
    "index": ROOT / "index.html",
    "planner": ROOT / "planner.html",
    "navigator": ROOT / "navigator.html",
    "sw": ROOT / "sw.js",
}

class PatchError(RuntimeError):
    pass

def need(path: Path):
    if not path.exists():
        raise PatchError(f"File mancante: {path.name}")
    return path.read_text(encoding="utf-8")

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise PatchError(f"{label}: atteso 1 blocco, trovati {n}")
    return text.replace(old, new, 1)

def replace_optional(text, old, new):
    return text.replace(old, new)

def replace_between(text, start, end, replacement, label):
    a = text.find(start)
    if a < 0:
        raise PatchError(f"{label}: marker iniziale non trovato")
    b = text.find(end, a + len(start))
    if b < 0:
        raise PatchError(f"{label}: marker finale non trovato")
    return text[:a] + replacement + text[b:]

def find_js_function_end(text, brace_pos):
    depth = 0
    i = brace_pos
    quote = None
    template = False
    line_comment = False
    block_comment = False
    esc = False

    while i < len(text):
        c = text[i]
        n = text[i+1] if i + 1 < len(text) else ""

        if line_comment:
            if c == "\n":
                line_comment = False
            i += 1
            continue

        if block_comment:
            if c == "*" and n == "/":
                block_comment = False
                i += 2
            else:
                i += 1
            continue

        if quote:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == quote:
                quote = None
            i += 1
            continue

        if template:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == "`":
                template = False
            i += 1
            continue

        if c == "/" and n == "/":
            line_comment = True
            i += 2
            continue
        if c == "/" and n == "*":
            block_comment = True
            i += 2
            continue
        if c in ("'", '"'):
            quote = c
            i += 1
            continue
        if c == "`":
            template = True
            i += 1
            continue

        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1

    raise PatchError("Funzione JS non chiusa")

def replace_js_function(text, name, new_source):
    marker = f"function {name}("
    start = text.find(marker)
    if start < 0:
        raise PatchError(f"Funzione {name} non trovata")
    if text.find(marker, start + 1) >= 0:
        raise PatchError(f"Funzione {name} duplicata: patch rifiutata")
    brace = text.find("{", start)
    if brace < 0:
        raise PatchError(f"Corpo funzione {name} non trovato")
    end = find_js_function_end(text, brace)
    return text[:start] + new_source.rstrip() + text[end:]

def replace_script(text, script_id, new_inner):
    marker = f'<script id="{script_id}">'
    a = text.find(marker)
    if a < 0:
        raise PatchError(f"Script {script_id} non trovato")
    if text.find(marker, a + 1) >= 0:
        raise PatchError(f"Script {script_id} duplicato: patch rifiutata")
    b = text.find("</script>", a)
    if b < 0:
        raise PatchError(f"Chiusura script {script_id} non trovata")
    return text[:a] + marker + "\n" + new_inner.strip() + "\n" + text[b:]

NEW_SW = r'''/* KnightTruckerNavy 0.70.49 — release-safe service worker */
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
'''

NEW_GPS_REQUEST = r'''function ktnRequestGpsStart(){
  window.__KTN_GPS_START_REQUESTED__=true;

  /* Already owned by NavigationRuntime: never restart the same watcher. */
  try{
    if(window.__ktnGpsOwnerActive && typeof watchId!=='undefined' && watchId!==null && watchId!==undefined){
      window.__KTN_GPS_START_REQUESTED__=false;
      var ld0=document.getElementById('loading');if(ld0)ld0.style.display='none';
      return watchId;
    }
  }catch(_e){}

  var g=window.KTN_NAV_RUNTIME&&window.KTN_NAV_RUNTIME.gps;
  if(g&&g.ready&&typeof g.start==='function'){
    window.__KTN_GPS_START_REQUESTED__=false;
    try{return g.start()}catch(e){
      var lm0=document.getElementById('loadingMsg');
      if(lm0)lm0.textContent='Errore avvio GPS: '+(e&&e.message?e.message:e);
      var sb0=document.getElementById('startBtn');
      if(sb0){sb0.style.display='block';sb0.textContent='RIPROVA GPS';}
      return null;
    }
  }

  var lm=document.getElementById('loadingMsg');
  if(lm)lm.textContent='Percorso pronto. Inizializzazione runtime GPS…';

  /* One watchdog only: it reports a broken runtime, it does NOT retry. */
  if(!window.__KTN_GPS_READY_WATCHDOG__){
    window.__KTN_GPS_READY_WATCHDOG__=setTimeout(function(){
      window.__KTN_GPS_READY_WATCHDOG__=null;
      if(!window.__KTN_GPS_START_REQUESTED__)return;
      var g2=window.KTN_NAV_RUNTIME&&window.KTN_NAV_RUNTIME.gps;
      if(g2&&g2.ready&&typeof g2.start==='function')return;
      var lm2=document.getElementById('loadingMsg');
      if(lm2)lm2.textContent='Runtime GPS non inizializzato. Ricarica il navigatore.';
      var sb2=document.getElementById('startBtn');
      if(sb2){sb2.style.display='block';sb2.textContent='RIPROVA GPS';}
    },8000);
  }
  return null;
}
'''

NEW_AUDIO_LOAD = r'''function ktn67LoadVoiceCfg(){
  try{
    var raw=localStorage.getItem('ktn67_voice_cfg');

    if(raw){
      var j=JSON.parse(raw||'{}');
      if(j&&typeof j==='object'){
        if(typeof j.voice==='string')ktn67VoiceCfg.voice=j.voice;
        if(typeof j.style==='string')ktn67VoiceCfg.style=j.style;
        if(isFinite(+j.rate))ktn67VoiceCfg.rate=Math.max(.65,Math.min(1.35,+j.rate));
        if(isFinite(+j.pitch))ktn67VoiceCfg.pitch=Math.max(.65,Math.min(1.45,+j.pitch));
        if(isFinite(+j.volume))ktn67VoiceCfg.volume=Math.max(.2,Math.min(1,+j.volume));
      }
      return;
    }

    /* One-time compatibility migration from the 0.70.17 audio settings. */
    var legacyStyle=localStorage.getItem('ktn27_voice_style_v2')||'';
    if(['professional','synthetic','trucker','cb','ironic'].indexOf(legacyStyle)>=0){
      ktn67VoiceCfg.style=legacyStyle;
    }

    var a=JSON.parse(localStorage.getItem('ktn27_audio_settings')||'null');
    if(a&&typeof a==='object'){
      var master=isFinite(+a.master)?Math.max(0,Math.min(1,+a.master)):1;
      var nav=isFinite(+a.nav)?Math.max(0,Math.min(1,+a.nav)):1;
      ktn67VoiceCfg.volume=Math.max(.2,Math.min(1,master*nav));
      if(a.muted===true)window.voiceOn=false;
    }

    localStorage.setItem('ktn67_voice_cfg',JSON.stringify(ktn67VoiceCfg));
  }catch(e){}
}
'''

NEW_SAVE_SESSION = r'''function saveNavSession(){
  if(Date.now()-sessionSaveTs<5000)return;
  if(!Array.isArray(routeCoords)||routeCoords.length<2||Number(totalMeters)<=300)return;
  sessionSaveTs=Date.now();

  /* Route geometry is already persisted by saveOfflineRoute() when it changes.
     The periodic session snapshot keeps only live progress/state. */
  try{
    localStorage.setItem('nav_session_v15',JSON.stringify({
      ts:Date.now(),
      cfg:cfg,
      lastPos:lastPos,
      snappedPos:snappedPos,
      lastRouteIndex:lastRouteIndex,
      nextStopIndex:nextStopIndex,
      totalMeters:totalMeters,
      actualTrack:actualTrack.slice(-200),
      geometryStore:'nav_offline_route_v13'
    }));
  }catch(e){}
}
'''

NEW_RESTORE_SESSION = r'''function restoreNavSession(){
  try{
    if(gattoExplorerMode||window.KTN_GATTO_EXPLORER)return false;
    if(Q.get('fresh')==='1')return false;

    var s=JSON.parse(localStorage.getItem('nav_session_v15')||'null');
    if(!s||Date.now()-s.ts>6*3600000)return false;

    var oldTo=s.cfg&&{lat:+s.cfg.toLat,lng:+s.cfg.toLng};
    var newTo={lat:+cfg.toLat,lng:+cfg.toLng};
    if(!oldTo||!isFinite(oldTo.lat)||!isFinite(oldTo.lng)||
       !isFinite(newTo.lat)||!isFinite(newTo.lng)||hav(oldTo,newTo)>250)return false;

    /* Backward compatible: old v15 sessions may still contain full geometry.
       New snapshots reuse the heavy route saved only when route geometry changes. */
    var rc=Array.isArray(s.routeCoords)&&s.routeCoords.length>=2?s.routeCoords:null;
    var st=Array.isArray(s.steps)?s.steps:null;
    var off=null;

    if(!rc){
      off=JSON.parse(localStorage.getItem('nav_offline_route_v13')||'null');
      if(!off||!Array.isArray(off.coords)||off.coords.length<2)return false;

      var offTo=off.cfg&&{lat:+off.cfg.toLat,lng:+off.cfg.toLng};
      if(!offTo||!isFinite(offTo.lat)||!isFinite(offTo.lng)||hav(offTo,newTo)>250)return false;

      rc=off.coords;
      st=Array.isArray(off.steps)?off.steps:[];
    }

    cfg=Object.assign(cfg,(off&&off.cfg)||{},s.cfg||{});
    routeCoords=rc;
    steps=st||[];
    lastRouteIndex=Math.max(0,Number(s.lastRouteIndex)||0);
    nextStopIndex=Math.max(0,Number(s.nextStopIndex)||0);
    actualTrack=Array.isArray(s.actualTrack)?s.actualTrack:[];

    cumDist=[0];
    for(var i=1;i<routeCoords.length;i++)cumDist[i]=cumDist[i-1]+hav(routeCoords[i-1],routeCoords[i]);
    totalMeters=cumDist[cumDist.length-1]||0;
    return totalMeters>300;
  }catch(e){
    return false;
  }
}
'''

NEW_HUD_OWNER = r'''(function(){
  'use strict';

  function el(id){ return document.getElementById(id); }
  function visible(node){
    if(!node) return false;
    var s=getComputedStyle(node);
    if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0) return false;
    var r=node.getBoundingClientRect();
    return r.width>0 && r.height>0;
  }
  function setImp(node,prop,val){
    if(!node)return;
    val=String(val);
    if(node.style.getPropertyValue(prop)===val &&
       node.style.getPropertyPriority(prop)==='important')return;
    node.style.setProperty(prop,val,'important');
  }

  function layout(){
    if(!document.body.classList.contains('pro-nav')) return;

    var vw=Math.max(document.documentElement.clientWidth||0,window.innerWidth||0);
    var turn=document.querySelector('.turnbox');
    var speed=document.querySelector('.pro-speedbox');
    var limit=el('proLimitVal');
    var sign=el('b10HgvNoPass');
    var cam=el('proCameraChip');
    var camAlert=el('proCameraAlert');
    var hgvAlert=el('b10HgvNoPassAlert');

    if(!speed || !turn) return;

    var turnR=turn.getBoundingClientRect();
    var isLandscape=window.innerWidth>window.innerHeight;
    var panelRight=isLandscape?Math.round(turnR.right):0;
    var top=isLandscape?Math.max(8,Math.round(turnR.top)):Math.round(turnR.bottom+8);

    var signSize=vw<=430?48:54;
    var edge=8;
    var gap=7;
    var reserve=signSize+gap+edge;

    setImp(speed,'top',top+'px');
    setImp(speed,'right',reserve+'px');
    setImp(speed,'left','auto');

    var speedR=speed.getBoundingClientRect();

    if(sign){
      var refR=(limit&&visible(limit))?limit.getBoundingClientRect():speedR;
      var sy=Math.round(refR.top+(refR.height-signSize)/2);
      setImp(sign,'top',sy+'px');
      setImp(sign,'left','auto');
      setImp(sign,'right',edge+'px');
      setImp(sign,'width',signSize+'px');
      setImp(sign,'height',signSize+'px');
      setImp(sign,'display','flex');
      setImp(sign,'visibility','visible');
      setImp(sign,'opacity','1');
    }

    speedR=speed.getBoundingClientRect();
    var signR=sign?sign.getBoundingClientRect():speedR;
    var clusterBottom=Math.max(speedR.bottom,signR.bottom);

    if(cam){
      setImp(cam,'top',Math.round(clusterBottom+8)+'px');
      setImp(cam,'right','10px');
      setImp(cam,'left','auto');
    }

    if(camAlert && camAlert.classList.contains('on')){
      var camR=cam.getBoundingClientRect();
      setImp(camAlert,'top',Math.round(camR.bottom+7)+'px');
      setImp(camAlert,'left',isLandscape?Math.round((panelRight+vw)/2)+'px':'50%');
      setImp(camAlert,'right','auto');
      setImp(camAlert,'transform','translateX(-50%)');
      setImp(camAlert,'max-width',isLandscape?'min(48vw,520px)':'min(88vw,520px)');
    }

    if(hgvAlert && hgvAlert.classList.contains('on')){
      var y=clusterBottom+8;
      if(cam && visible(cam)) y=Math.max(y,cam.getBoundingClientRect().bottom+7);
      if(camAlert && camAlert.classList.contains('on')) y=Math.max(y,camAlert.getBoundingClientRect().bottom+7);
      setImp(hgvAlert,'top',Math.round(y)+'px');
      setImp(hgvAlert,'left',isLandscape?Math.round((panelRight+vw)/2)+'px':'50%');
      setImp(hgvAlert,'right','auto');
      setImp(hgvAlert,'transform','translateX(-50%)');
    }
  }

  var scheduled=false;
  function requestLayout(){
    if(scheduled)return;
    scheduled=true;
    requestAnimationFrame(function(){
      scheduled=false;
      layout();
    });
  }

  function start(){ layout(); }

  /* Event-driven only. No global class/style MutationObserver:
     the old observer could retrigger itself after this owner wrote styles. */
  if(window.KTN_UI_LIFECYCLE)KTN_UI_LIFECYCLE.layout(requestLayout);
  [
    'ktn31camera',
    'ktn:services-state',
    'ktn:lane-state',
    'ktn:speed-limit',
    'ktn:road-events',
    'ktn39HgvNoPass'
  ].forEach(function(ev){
    window.addEventListener(ev,requestLayout,{passive:true});
  });

  document.addEventListener('visibilitychange',function(){
    if(!document.hidden)setTimeout(layout,80);
  });

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});
  else start();

  window.ktn71LayoutHud=layout;
})();'''

NEW_AVVISI_OWNER = r'''(function(){
'use strict';
function clean(){
  var a=document.getElementById('ktn17AlertBtn');
  if(a&&a.parentNode)a.parentNode.removeChild(a);
  [].slice.call(document.querySelectorAll('button')).forEach(function(b){
    if((b.textContent||'').trim().toUpperCase()==='AVVISI' && b.parentNode)b.parentNode.removeChild(b);
  });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',clean,{once:true});
else clean();
setTimeout(clean,300);
setTimeout(clean,1200);
if(window.KTN_UI_LIFECYCLE)KTN_UI_LIFECYCLE.dom(clean);
})();'''

def patch_all(originals):
    out = dict(originals)

    # index.html
    x = out["index"]
    x = replace_once(x, './manifest.json?v=7046', './manifest.json?v=7049', "index manifest cache-bust")
    x = replace_once(x, "./sw.js?v=7046", "./sw.js?v=7049", "index service worker version")
    out["index"] = x

    # planner.html
    p = out["planner"]
    p = replace_once(p, "./sw.js?v=7046", "./sw.js?v=7049", "planner service worker version")
    p = replace_optional(p, "manifest.json?v=007045", "manifest.json?v=007049")
    p = replace_optional(p, "manifest.json?v=7045", "manifest.json?v=7049")
    out["planner"] = p

    # navigator.html
    n = out["navigator"]

    n = replace_once(
        n,
        'window.KTN_NAV_BUILD="0.70.48";',
        'window.KTN_NAV_BUILD="0.70.49";',
        "navigator build"
    )

    n = replace_once(
        n,
        "if(window.KTN_ROADSIDE_ENGINE&&window.KTN_ROADSIDE_ENGINE.version==='0.70.24-cleanarch7')return;",
        "if(window.KTN_ROADSIDE_ENGINE&&window.KTN_ROADSIDE_ENGINE.version==='0.70.39-cleanarch12')return;",
        "RoadsideEngine guard"
    )

    n = replace_between(
        n,
        "var ktnGpsStartPending=false,ktnGpsStartTimer=null,ktnGpsStartSince=0;",
        "/* === v73 INTENTIONAL DEVIATION CONFIDENCE ===",
        NEW_GPS_REQUEST + "\n\n",
        "GPS request polling block"
    )

    n = replace_once(
        n,
        "setTimeout(function(){try{ktnRequestGpsStart()}catch(e){}},120);",
        "try{ktnRequestGpsStart()}catch(e){}",
        "route -> GPS handoff"
    )
    n = replace_once(
        n,
        "setTimeout(function(){try{ktnRequestGpsStart()}catch(e){}},100);",
        "try{ktnRequestGpsStart()}catch(e){}",
        "explorer -> GPS handoff"
    )

    n = replace_once(
        n,
        " if(e.code===3){setTimeout(function(){try{ktnRequestGpsStart()}catch(x){}},1500)}",
        " if(e.code===3){var sb=document.getElementById('startBtn');if(sb){sb.style.display='block';sb.textContent='RIPROVA GPS';}}",
        "GPS timeout auto-retry"
    )

    n = replace_once(
        n,
        "function runtimeStartGPS(){\n  var ld=document.getElementById('loading');if(ld)ld.style.display='none';",
        "function runtimeStartGPS(){\n  if(window.__KTN_GPS_READY_WATCHDOG__){clearTimeout(window.__KTN_GPS_READY_WATCHDOG__);window.__KTN_GPS_READY_WATCHDOG__=null;}\n  window.__KTN_GPS_START_REQUESTED__=false;\n  var sb0=document.getElementById('startBtn');if(sb0)sb0.style.display='none';\n  var ld=document.getElementById('loading');if(ld)ld.style.display='none';",
        "runtimeStartGPS cleanup"
    )

    handshake = r'''window.onGPS=runtimeOnGPS;

if(window.__KTN_GPS_START_REQUESTED__){
  window.__KTN_GPS_START_REQUESTED__=false;
  queueMicrotask(function(){
    try{runtimeStartGPS()}
    catch(e){
      var lm=document.getElementById('loadingMsg');
      if(lm)lm.textContent='Errore avvio GPS: '+(e&&e.message?e.message:e);
      var sb=document.getElementById('startBtn');
      if(sb){sb.style.display='block';sb.textContent='RIPROVA GPS';}
    }
  });
}

/* ownership is declared once by ktn00733ArchitectureManifest */'''
    n = replace_once(
        n,
        "window.onGPS=runtimeOnGPS;\n\n/* ownership is declared once by ktn00733ArchitectureManifest */",
        handshake,
        "runtime GPS one-shot handshake"
    )

    n = replace_once(
        n,
        "if(_routeValidForArrival && rem<45){",
        "if(_routeValidForArrival && rem<45 && speed<12){",
        "arrival latch speed"
    )
    n = replace_once(
        n,
        "if(validArrival && remain<45){",
        "if(validArrival && remain<45 && Math.max(0,Number(window.currentSpeedKmh)||0)<12){",
        "arrival HUD speed"
    )

    n = replace_once(
        n,
        """  setTimeout(function(){
    restoreSettings();
    bindActions();

    /* Mutation observer: menu is moved/rebuilt by old runtime layers. */
    try{
      new MutationObserver(function(){bindActions()}).observe(document.body,{childList:true,subtree:true});
    }catch(e){}
  },500);""",
        """  setTimeout(function(){
    restoreSettings();
    bindActions();
    if(window.KTN_UI_LIFECYCLE)KTN_UI_LIFECYCLE.dom(bindActions);
  },500);""",
        "menu global MutationObserver"
    )

    n = replace_js_function(n, "ktn67LoadVoiceCfg", NEW_AUDIO_LOAD)
    n = replace_js_function(n, "saveNavSession", NEW_SAVE_SESSION)
    n = replace_js_function(n, "restoreNavSession", NEW_RESTORE_SESSION)

    n = replace_script(n, "ktn71HudFinalOwner", NEW_HUD_OWNER)
    n = replace_script(n, "ktn014-remove-avvisi-owner", NEW_AVVISI_OWNER)

    out["navigator"] = n
    out["sw"] = NEW_SW.rstrip() + "\n"
    return out

def main():
    try:
        originals = {k: need(v) for k, v in FILES.items()}

        if "0.0.70.49" not in originals["planner"]:
            raise PatchError("planner.html non risulta 0.70.49")
        if 'window.KTN_NAV_BUILD="0.70.48";' not in originals["navigator"]:
            raise PatchError("navigator.html non risulta build 0.70.48 attesa")
        if "ktn-007046-launcher-v1" not in originals["sw"]:
            raise PatchError("sw.js non è la cache 0.70.46 attesa")

        patched = patch_all(originals)

        checks = [
            ("navigator", "ktnGpsStartTimer", False),
            ("navigator", "ktnGpsStartSince", False),
            ("navigator", 'window.KTN_NAV_BUILD="0.70.49";', True),
            ("navigator", "version==='0.70.39-cleanarch12'", True),
            ("navigator", "geometryStore:'nav_offline_route_v13'", True),
            ("navigator", "'ktn:road-events'", True),
            ("index", "./sw.js?v=7049", True),
            ("planner", "./sw.js?v=7049", True),
            ("sw", "ktn-007049-launcher-v2", True),
        ]
        for key, needle, should_exist in checks:
            found = needle in patched[key]
            if found != should_exist:
                raise PatchError(f"Controllo finale fallito: {key} / {needle}")

        stamp = time.strftime("%Y%m%d_%H%M%S")
        backups = []
        for key, path in FILES.items():
            bak = path.with_name(path.name + f".pre_hotfix_07049_{stamp}.bak")
            shutil.copy2(path, bak)
            backups.append(bak)

        try:
            for key, path in FILES.items():
                path.write_text(patched[key], encoding="utf-8", newline="\n")
        except Exception:
            for key, path in FILES.items():
                bak = backups[list(FILES.keys()).index(key)]
                if bak.exists():
                    shutil.copy2(bak, path)
            raise

        print("HOTFIX 0.70.49 APPLICATO CORRETTAMENTE")
        print(f"Cartella: {ROOT}")
        print("Modificati: index.html, planner.html, navigator.html, sw.js")
        print("Backup creati con suffisso .pre_hotfix_07049_*.bak")
        print("")
        print("Fix inclusi:")
        print("- cache/service worker 0.70.49 coerente, niente fallback HTML 0.70.46")
        print("- handshake GPS one-shot, rimosso polling 60 ms/15 s")
        print("- rimosso auto-retry GPS da 1.5 s")
        print("- RoadsideEngine guard corretto")
        print("- arrivo: 45 m + velocità < 12 km/h")
        print("- migrazione preferenze audio 0.70.17 -> ktn67")
        print("- HUD event-driven senza MutationObserver globale style/class")
        print("- rimozione AVVISI e menu senza observer globali dedicati")
        print("- session snapshot leggero; geometria rotta salvata solo quando cambia")

    except Exception as e:
        print("HOTFIX NON APPLICATO.")
        print("Errore:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
