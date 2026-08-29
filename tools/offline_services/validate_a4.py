#!/usr/bin/env python3
import json,sys,unicodedata,re
db=json.load(open(sys.argv[1],encoding="utf-8")); base=json.load(open(sys.argv[2],encoding="utf-8"))
def norm(s):
 s=unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()
 return re.sub(r"[^a-z0-9]+"," ",s).strip()
names=[(norm(x.get("name")),x) for x in db["areas"]]
report={"route":base["route"],"generatedCount":db["count"],"checks":[]}
for name,typ,km in base["expected"]:
 n=norm(name); hit=next((x for nn,x in names if n in nn or nn in n),None)
 report["checks"].append({"expected":name,"type":typ,"km":km,"found":bool(hit),
  "match":hit.get("name") if hit else None,"osmId":hit.get("id") if hit else None})
found=sum(x["found"] for x in report["checks"]); report["found"]=found; report["total"]=len(report["checks"])
report["coverage"]=round(found/max(1,len(report["checks"])),3)
json.dump(report,open(sys.argv[3],"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(f"A4 validation: {found}/{len(report['checks'])} ({report['coverage']:.0%})")
# Phase 1 is extraction validation, not directional certification.
if found < max(5, len(report["checks"])//2): raise SystemExit("A4 extraction coverage too low")
