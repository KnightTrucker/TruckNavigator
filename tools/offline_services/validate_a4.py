#!/usr/bin/env python3
import json,sys,unicodedata,re
from difflib import SequenceMatcher
db=json.load(open(sys.argv[1],encoding="utf-8"))
base=json.load(open(sys.argv[2],encoding="utf-8"))
def norm(s):
 s=unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()
 return re.sub(r"[^a-z0-9]+"," ",s).strip()
def core(s):
 return " ".join(t for t in norm(s).split() if t not in {"aire","de","du","des","d","la","le","les","l"})
def score(a,b):
 a,b=core(a),core(b)
 if not a or not b:return 0.0
 if a==b:return 1.0
 sa,sb=set(a.split()),set(b.split())
 tok=len(sa&sb)/max(1,len(sa|sb))
 return max(tok,SequenceMatcher(None,a,b).ratio())
rows=[x for x in db.get("areas",[]) if norm(x.get("name"))]
report={"route":base["route"],"generatedCount":db.get("count",len(rows)),"checks":[]};used=set()
for en,et,km in base["expected"]:
 best=None;bs=0
 for x in rows:
  if x.get("id") in used or (et and x.get("type")!=et):continue
  s=score(en,x.get("name"))
  if s>bs:bs,best=s,x
 found=bool(best and bs>=0.68)
 if found:used.add(best["id"])
 g=best.get("graph",{}) if found else {}
 report["checks"].append({"expected":en,"type":et,"km":km,"found":found,
  "match":best.get("name") if found else None,"osmId":best.get("id") if found else None,
  "score":round(bs,3) if best else 0.0,"graphStatus":g.get("status") if found else None,
  "roadRef":g.get("roadRef") if found else None,"roadWayId":g.get("roadWayId") if found else None,
  "entryWayIds":g.get("entryWayIds",[]) if found else []})
found=sum(c["found"] for c in report["checks"])
linked=sum(c["found"] and c["graphStatus"]=="carriageway_linked" for c in report["checks"])
a4linked=sum(c["found"] and c["graphStatus"]=="carriageway_linked" and norm(c.get("roadRef"))=="a4" for c in report["checks"])
report.update({"found":found,"total":len(report["checks"]),"coverage":round(found/max(1,len(report["checks"])),3),
 "graphLinked":linked,"a4GraphLinked":a4linked})
json.dump(report,open(sys.argv[3],"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("A4 names:",found,"/",len(report["checks"]),"graph linked:",linked,"A4-linked:",a4linked)
for c in report["checks"]:
 print(("OK" if c["found"] else "MISS"),c["expected"],"=>",c["match"],c["score"],c["graphStatus"],c["roadRef"])
if found<12:raise SystemExit("A4 extraction coverage regressed")
