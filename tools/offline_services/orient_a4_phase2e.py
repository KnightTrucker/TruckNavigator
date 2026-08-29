#!/usr/bin/env python3
import osmium,json,sys,re,unicodedata,math,collections

def norm(s):
 s=unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().upper()
 return re.sub(r"[^A-Z0-9]+","",s)

class A4(osmium.SimpleHandler):
 def __init__(self):
  super().__init__(); self.coords={}; self.ways={}; self.nodeways=collections.defaultdict(set)
 def node(self,n):
  if n.location.valid(): self.coords[n.id]=(n.location.lat,n.location.lon)
 def way(self,w):
  if w.tags.get("highway")!="motorway" or norm(w.tags.get("ref"))!="A4": return
  ns=[x.ref for x in w.nodes]
  if len(ns)<2:return
  one=(w.tags.get("oneway") or "yes").lower()
  self.ways[w.id]={"id":w.id,"nodes":ns,"oneway":one}
  for n in ns:self.nodeways[n].add(w.id)

def bearing(a,b):
 y=math.sin(math.radians(b[1]-a[1]))*math.cos(math.radians(b[0]))
 x=math.cos(math.radians(a[0]))*math.sin(math.radians(b[0]))-math.sin(math.radians(a[0]))*math.cos(math.radians(b[0]))*math.cos(math.radians(b[1]-a[1]))
 return (math.degrees(math.atan2(y,x))+360)%360

def way_direction(w,g):
 ns=w["nodes"]
 pts=[g.coords.get(n) for n in ns]
 pts=[p for p in pts if p]
 if len(pts)<2:return None,None
 # OSM motorway ways normally point in travel direction. Handle explicit -1.
 a,b=pts[0],pts[-1]
 if w["oneway"]=="-1":a,b=b,a
 br=bearing(a,b)
 # A4 corridor Paris->Strasbourg is broadly eastbound; use only as semantic
 # anchor after topology has already certified the exact A4 carriageway.
 direction="Paris->Strasbourg" if 45<=br<=135 else "Strasbourg->Paris" if 225<=br<=315 else "ambiguous"
 return direction,round(br,1)

report=json.load(open(sys.argv[1],encoding="utf-8"))
g=A4()
for p in sys.argv[3:]:g.apply_file(p,locations=True)

out=[]
for c in report["checks"]:
 wid=c.get("roadWayId")
 if not c.get("certifiedA4") or not wid:
  out.append({**c,"semanticDirection":None,"bearingDeg":None,"directionCertified":False});continue
 try:i=int(wid.rsplit("/",1)[1])
 except:i=-1
 w=g.ways.get(i)
 d,b=way_direction(w,g) if w else (None,None)
 out.append({**c,"semanticDirection":d,"bearingDeg":b,"directionCertified":d in ("Paris->Strasbourg","Strasbourg->Paris")})

summary={
 "schemaVersion":1,"route":"A4","method":"certified A4 topology + OSM oneway geometry orientation",
 "checks":out,
 "certifiedA4":sum(x.get("certifiedA4",False) for x in out),
 "directionCertified":sum(x["directionCertified"] for x in out),
 "parisToStrasbourg":sum(x["semanticDirection"]=="Paris->Strasbourg" for x in out),
 "strasbourgToParis":sum(x["semanticDirection"]=="Strasbourg->Paris" for x in out),
 "ambiguous":sum(x.get("certifiedA4") and not x["directionCertified"] for x in out),
 "note":"Direction is assigned only after exact topology certifies A4. No area-side/proximity direction guess is used."
}
json.dump(summary,open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("A4 certified:",summary["certifiedA4"])
print("Direction certified:",summary["directionCertified"])
print("Paris->Strasbourg:",summary["parisToStrasbourg"])
print("Strasbourg->Paris:",summary["strasbourgToParis"])
print("Ambiguous:",summary["ambiguous"])
for x in out:
 if x.get("certifiedA4"): print(x["expected"],x["roadWayId"],x["bearingDeg"],x["semanticDirection"])
if summary["directionCertified"] < 10: raise SystemExit("Direction certification coverage too low")
