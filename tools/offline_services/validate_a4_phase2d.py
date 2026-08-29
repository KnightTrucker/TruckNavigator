#!/usr/bin/env python3
import json,sys,re,unicodedata
from difflib import SequenceMatcher

db=json.load(open(sys.argv[1],encoding="utf-8"))
base=json.load(open(sys.argv[2],encoding="utf-8"))

ALIASES={
 "Aire de Tardenois Sud":["tardenois","ardres et tardenois","tardenois sud"],
 "Aire de Longeville-lès-Saint-Avold Sud":["longeville sud","longeville les saint avold sud"],
 "Aire de La Fontenelle":["fontenelle","la fontenelle"]
}

def norm(s):
 s=unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().upper()
 return re.sub(r"[^A-Z0-9]+","",s)

def words(s):
 s=unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()
 return re.sub(r"[^a-z0-9]+"," ",s).strip()

def core(s):
 stop={"aire","de","du","des","d","la","le","les","l"}
 return " ".join(x for x in words(s).split() if x not in stop)

def score(a,b):
 a,b=core(a),core(b)
 if not a or not b:return 0.0
 if a==b:return 1.0
 sa,sb=set(a.split()),set(b.split())
 return max(len(sa&sb)/max(1,len(sa|sb)),SequenceMatcher(None,a,b).ratio())

def namescore(expected,candidate):
 vals=[expected]+ALIASES.get(expected,[])
 return max(score(x,candidate) for x in vals)

rows=[x for x in db.get("areas",[]) if words(x.get("name"))]
checks=[];used=set()
for expected,typ,km in base["expected"]:
 best=None;bs=0.0
 for x in rows:
  if x.get("id") in used or (typ and x.get("type")!=typ):continue
  s=namescore(expected,x.get("name"))
  if s>bs:bs,best=s,x
 found=bool(best and bs>=0.68)
 if found:used.add(best["id"])
 g=best.get("graph",{}) if found else {}
 ref=norm(g.get("roadRef")) if found else ""
 is_a4=(ref=="A4")
 # A named A4 validation item is certified only if topology reaches A4.
 certified=bool(found and g.get("status")=="carriageway_linked" and is_a4 and g.get("entryWayIds"))
 checks.append({
  "expected":expected,"type":typ,"km":km,"found":found,
  "match":best.get("name") if found else None,"osmId":best.get("id") if found else None,
  "score":round(bs,3) if best else 0.0,
  "graphStatus":g.get("status") if found else None,
  "roadRefRaw":g.get("roadRef") if found else None,
  "roadRefNormalized":ref or None,
  "roadWayId":g.get("roadWayId") if found else None,
  "entryWayIds":list(dict.fromkeys(g.get("entryWayIds",[]))) if found else [],
  "certifiedA4":certified
 })

report={"route":base["route"],"generatedCount":db.get("count",len(rows)),"checks":checks}
report["found"]=sum(x["found"] for x in checks)
report["total"]=len(checks)
report["coverage"]=round(report["found"]/max(1,report["total"]),3)
report["graphLinked"]=sum(x["graphStatus"]=="carriageway_linked" for x in checks)
report["a4GraphLinked"]=sum(x["roadRefNormalized"]=="A4" and x["graphStatus"]=="carriageway_linked" for x in checks)
report["certifiedA4"]=sum(x["certifiedA4"] for x in checks)
report["wrongMotorway"]=[x["expected"] for x in checks if x["found"] and x["graphStatus"]=="carriageway_linked" and x["roadRefNormalized"]!="A4"]
json.dump(report,open(sys.argv[3],"w",encoding="utf-8"),ensure_ascii=False,indent=2)

print("A4 names",report["found"],"/",report["total"])
print("A4 topology",report["a4GraphLinked"],"/",report["total"])
print("A4 certified",report["certifiedA4"],"/",report["total"])
print("Wrong motorway:",report["wrongMotorway"])
for x in checks:
 print(("CERT" if x["certifiedA4"] else "CHECK"),x["expected"],"=>",x["match"],x["roadRefRaw"],x["roadWayId"])

if report["found"]<13: raise SystemExit("Name matching regressed")
if report["a4GraphLinked"]<11: raise SystemExit("A4 topology coverage too low")
