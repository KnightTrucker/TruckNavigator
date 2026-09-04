from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
FILES = {
    'index': ROOT / 'index.html',
    'planner': ROOT / 'planner.html',
    'navigator': ROOT / 'navigator.html',
    'sw': ROOT / 'sw.js',
}

for name, path in FILES.items():
    if not path.exists():
        raise SystemExit(f'ERRORE: manca {path.name} nella root del repository')

text = {k: p.read_text(encoding='utf-8') for k, p in FILES.items()}

# Strong base validation: this micro-fix is ONLY for the already-applied 0.70.50.
checks = [
    ('index 0.70.50', 'KnightTruckerNavy 0.70.50' in text['index']),
    ('planner 0.70.50', "window.KTN_APP_VERSION='0.0.70.50'" in text['planner']),
    ('navigator 0.70.50', 'window.KTN_NAV_BUILD="0.70.50"' in text['navigator']),
    ('sw 0.70.50', "const CACHE='ktn-007050-launcher-v3'" in text['sw']),
]
for label, ok in checks:
    if not ok:
        raise SystemExit(f'ERRORE: base inattesa ({label}). Nessun file modificato.')

# 1) Launcher must never request planner with the old 7049 cache-buster.
old = "location.href='./planner.html?mode='+encodeURIComponent(mode)+'&v=7049'"
new = "location.href='./planner.html?mode='+encodeURIComponent(mode)+'&v=7050'"
if text['index'].count(old) != 1:
    raise SystemExit('ERRORE: marker launcher v7049 non trovato in modo univoco. Nessun file modificato.')
text['index'] = text['index'].replace(old, new, 1)

# Force immediate service-worker script update for this coherence micro-fix.
old = "navigator.serviceWorker.register('./sw.js?v=7050',{scope:'./'})"
new = "navigator.serviceWorker.register('./sw.js?v=7050b',{scope:'./'})"
if text['index'].count(old) != 1:
    raise SystemExit('ERRORE: registrazione SW index 7050 non trovata. Nessun file modificato.')
text['index'] = text['index'].replace(old, new, 1)

# 2) Explicit navigator cache-buster in the iframe URL.
marker = "  if(window.__gattoExplorerMode){p.set('explorer','1');window.__gattoExplorerMode=false;}\n\n  try{localStorage.setItem('ktn34_active_navigation'"
replacement = "  if(window.__gattoExplorerMode){p.set('explorer','1');window.__gattoExplorerMode=false;}\n  p.set('v','7050');\n\n  try{localStorage.setItem('ktn34_active_navigation'"
if text['planner'].count(marker) != 1:
    raise SystemExit('ERRORE: marker URL navigator nel planner non trovato in modo univoco. Nessun file modificato.')
text['planner'] = text['planner'].replace(marker, replacement, 1)

old = "navigator.serviceWorker.register('./sw.js?v=7050',{scope:'./'})"
new = "navigator.serviceWorker.register('./sw.js?v=7050b',{scope:'./'})"
if text['planner'].count(old) != 1:
    raise SystemExit('ERRORE: registrazione SW planner 7050 non trovata. Nessun file modificato.')
text['planner'] = text['planner'].replace(old, new, 1)

# 3) If GPS already owns a watcher, NEVER bypass the 0.70.50 map-ready guard.
old = """    if(window.__ktnGpsOwnerActive && typeof watchId!=='undefined' && watchId!==null && watchId!==undefined){
      window.__KTN_GPS_START_REQUESTED__=false;
      var ld0=document.getElementById('loading');if(ld0)ld0.style.display='none';
      return watchId;
    }"""
new = """    if(window.__ktnGpsOwnerActive && typeof watchId!=='undefined' && watchId!==null && watchId!==undefined){
      window.__KTN_GPS_START_REQUESTED__=false;
      try{ktn07050ArmMapFallback();ktn07050RevealNavigation()}catch(e){}
      return watchId;
    }"""
if text['navigator'].count(old) != 1:
    raise SystemExit('ERRORE: ramo GPS-owner atteso non trovato in modo univoco. Nessun file modificato.')
text['navigator'] = text['navigator'].replace(old, new, 1)

# 4) New shell cache generation so installed PWAs refresh this exact set immediately.
old = "/* KnightTruckerNavy 0.70.50 — release-safe service worker */\nconst CACHE='ktn-007050-launcher-v3';"
new = "/* KnightTruckerNavy 0.70.50 — release-safe service worker · coherence fix */\nconst CACHE='ktn-007050-launcher-v4';"
if text['sw'].count(old) != 1:
    raise SystemExit('ERRORE: cache SW v3 non trovata. Nessun file modificato.')
text['sw'] = text['sw'].replace(old, new, 1)

# Post-patch sanity checks before writing anything.
assert '&v=7049' not in text['index']
assert '&v=7050' in text['index']
assert "p.set('v','7050')" in text['planner']
assert "sw.js?v=7050b" in text['index'] and "sw.js?v=7050b" in text['planner']
assert "ld0.style.display='none'" not in text['navigator']
assert "const CACHE='ktn-007050-launcher-v4'" in text['sw']

for k, path in FILES.items():
    path.write_text(text[k], encoding='utf-8', newline='\n')

print('KTN 0.70.50 COHERENCE FIX APPLICATO CORRETTAMENTE')
print('Modificati: index.html, planner.html, navigator.html, sw.js')
