#!/usr/bin/env python3
import json,sys,osmium
from datetime import datetime,timezone
COUNTRY=sys.argv[1]; OUT=sys.argv[2]; INPUTS=sys.argv[3:]
def b(v):
    if v is None:return None
    v=str(v).lower()
    if v in ("yes","true","1","designated"):return True
    if v in ("no","false","0"):return False
    return None
KEEP={"name","operator","brand","highway","ref","direction","destination","destination:ref",
"access","hgv","toilets","shower","restaurant","fast_food","drinking_water","opening_hours",
"fee","lit","wheelchair","internet_access","fuel","compressed_air","charging_station"}
class H(osmium.SimpleHandler):
 def __init__(s):super().__init__();s.rows=[]
 def add(s,t,i,tags,lat,lon):
  h=tags.get("highway")
  if h not in ("services","rest_area"):return
  s.rows.append({"id":f"osm:{t}/{i}","osmType":t,"osmId":i,
   "name":tags.get("name") or tags.get("operator") or "","type":h,
   "lat":round(lat,7),"lon":round(lon,7),"roadRef":tags.get("ref") or None,
   "directionRaw":tags.get("direction") or tags.get("destination") or None,
   "hgv":tags.get("hgv","unknown"),"access":tags.get("access","unknown"),
   "facilities":{"toilets":b(tags.get("toilets")),"shower":b(tags.get("shower")),
   "restaurant":b(tags.get("restaurant")),"drinkingWater":b(tags.get("drinking_water"))},
   "graph":{"status":"unlinked","roadWayId":None,"entryWayIds":[],"direction":None},
   "tags":{k:tags[k] for k in KEEP if k in tags}})
 def node(s,n):
  if n.tags.get("highway") in ("services","rest_area") and n.location.valid():
   s.add("node",n.id,n.tags,n.location.lat,n.location.lon)
 def way(s,w):
  if w.tags.get("highway") not in ("services","rest_area"):return
  p=[]
  for n in w.nodes:
   try:
    if n.location.valid():p.append((n.location.lat,n.location.lon))
   except:pass
  if p:s.add("way",w.id,w.tags,sum(x[0] for x in p)/len(p),sum(x[1] for x in p)/len(p))
rows=[]
for f in INPUTS:
 h=H();h.apply_file(f,locations=True);rows+=h.rows
rows=list({x["id"]:x for x in rows}.values());rows.sort(key=lambda x:(x["type"],x["name"],x["id"]))
db={"schemaVersion":5,"country":COUNTRY,"generatedAt":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
"source":"OpenStreetMap / Geofabrik","policy":{"acceptedHighway":["services","rest_area"],"genericParkingExcluded":True},
"count":len(rows),"areas":rows}
json.dump(db,open(OUT,"w",encoding="utf8"),ensure_ascii=False,separators=(",",":"))
print(COUNTRY,"areas",len(rows))
if not rows:raise SystemExit("zero areas")
