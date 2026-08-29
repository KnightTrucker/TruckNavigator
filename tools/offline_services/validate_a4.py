#!/usr/bin/env python3
import json,sys,unicodedata,re
from difflib import SequenceMatcher

db=json.load(open(sys.argv[1],encoding="utf-8"))
base=json.load(open(sys.argv[2],encoding="utf-8"))

def norm(s):
    s=unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+"," ",s).strip()

def core(s):
    return " ".join(t for t in norm(s).split() if t not in {"aire","de","du","des","d","la","le","les"})

def score(a,b):
    a,b=core(a),core(b)
    if not a or not b: return 0.0
    if a==b: return 1.0
    if a in b or b in a: return min(len(a),len(b))/max(len(a),len(b))
    sa,sb=set(a.split()),set(b.split())
    return max(len(sa&sb)/max(1,len(sa|sb)),SequenceMatcher(None,a,b).ratio())

rows=[x for x in db.get("areas",[]) if norm(x.get("name"))]
report={"route":base["route"],"generatedCount":db.get("count",len(db.get("areas",[]))),"checks":[]}
used=set()

for expected_name,expected_type,km in base["expected"]:
    best=None; best_score=0.0
    for x in rows:
        if x.get("id") in used or (expected_type and x.get("type")!=expected_type): continue
        s=score(expected_name,x.get("name"))
        if s>best_score: best_score,best=s,x
    found=bool(best and best_score>=0.72)
    if found: used.add(best["id"])
    report["checks"].append({
        "expected":expected_name,"type":expected_type,"km":km,"found":found,
        "match":best.get("name") if found else None,
        "osmId":best.get("id") if found else None,
        "score":round(best_score,3) if best else 0.0
    })

found=sum(x["found"] for x in report["checks"])
report["found"]=found
report["total"]=len(report["checks"])
report["coverage"]=round(found/max(1,len(report["checks"])),3)
json.dump(report,open(sys.argv[3],"w",encoding="utf-8"),ensure_ascii=False,indent=2)

print(f"A4 validation: {found}/{len(report['checks'])} ({report['coverage']:.0%})")
for c in report["checks"]:
    print(("OK " if c["found"] else "MISS"),c["expected"],"=>",c["match"],"score",c["score"])

if found < max(5,len(report["checks"])//2):
    raise SystemExit("A4 extraction coverage too low")
