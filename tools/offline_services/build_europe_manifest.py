#!/usr/bin/env python3
import hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
EXPECTED=("IT","FR","DE","CH","AT","BE","LU")
BASE=Path(sys.argv[1]) if len(sys.argv)>1 else Path("offline/service_areas")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
cs={}
for cc in EXPECTED:
 p=BASE/f"{cc}.json";d=json.loads(p.read_text(encoding="utf-8"));a=d.get("areas")
 if d.get("country")!=cc or not isinstance(a,list) or not a or d.get("count")!=len(a):raise SystemExit(f"invalid {cc}")
 cs[cc]={"file":f"{cc}.json","count":len(a),"sha256":sha(p),"schemaVersion":d.get("schemaVersion"),"generatedAt":d.get("generatedAt")}
o={"schemaVersion":3,"generatedAt":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"graphRequired":False,"countries":cs,"totalAreas":sum(x["count"] for x in cs.values()),"scope":"IT,FR,DE,CH,AT,BE,LU"}
(BASE/"manifest.json").write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(o,indent=2))
