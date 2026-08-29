#!/usr/bin/env python3
import json,glob,hashlib,os,datetime
out={"schemaVersion":1,"generatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z"),"countries":{}}
for p in sorted(glob.glob("offline/service_areas/*.graph.json")):
 cc=os.path.basename(p).split(".")[0]; raw=open(p,"rb").read();d=json.loads(raw)
 out["countries"][cc]={"count":d["count"],"linked":d.get("graphLinking",{}).get("linked",0),"sha256":hashlib.sha256(raw).hexdigest(),"file":f"{cc}.graph.json"}
json.dump(out,open("offline/service_areas/manifest_europe.json","w"),ensure_ascii=False,indent=2)
print(json.dumps(out,indent=2))
