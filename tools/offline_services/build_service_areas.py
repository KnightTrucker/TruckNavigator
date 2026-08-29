#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone
import osmium

KEEP = {
 "name","operator","brand","highway","ref","direction","destination","destination:ref",
 "access","hgv","toilets","shower","restaurant","fast_food","drinking_water",
 "opening_hours","fee","lit","wheelchair","internet_access"
}

def b(v):
    if v is None: return None
    v=str(v).lower()
    if v in ("yes","true","1","designated"): return True
    if v in ("no","false","0"): return False
    return None

class H(osmium.SimpleHandler):
    def __init__(self):
        super().__init__(); self.rows=[]
    def add(self, typ, oid, tags, lat, lon):
        hw=tags.get("highway")
        if hw not in ("services","rest_area"): return
        self.rows.append({
          "id":f"osm:{typ}/{oid}","osmType":typ,"osmId":oid,
          "name":tags.get("name") or tags.get("operator") or "",
          "type":hw,"lat":round(lat,7),"lon":round(lon,7),
          "roadRef":tags.get("ref") or None,
          "directionRaw":tags.get("direction") or tags.get("destination") or None,
          "hgv":tags.get("hgv","unknown"),"access":tags.get("access","unknown"),
          "facilities":{"toilets":b(tags.get("toilets")),"shower":b(tags.get("shower")),
             "restaurant":b(tags.get("restaurant")),"drinkingWater":b(tags.get("drinking_water"))},
          "graph":{"status":"unlinked","roadWayId":None,"entryWayId":None,"direction":None},
          "tags":{k:tags[k] for k in KEEP if k in tags}
        })
    def node(self,n):
        if n.tags.get("highway") in ("services","rest_area") and n.location.valid():
            self.add("node",n.id,n.tags,n.location.lat,n.location.lon)
    def way(self,w):
        if w.tags.get("highway") not in ("services","rest_area"): return
        pts=[]
        for n in w.nodes:
            try:
                if n.location.valid(): pts.append((n.location.lat,n.location.lon))
            except Exception: pass
        if pts:
            self.add("way",w.id,w.tags,sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts))

if len(sys.argv)<3: raise SystemExit("build_service_areas.py OUTPUT INPUT...")
outpath=sys.argv[1]; inputs=sys.argv[2:]
rows=[]
for f in inputs:
    h=H(); h.apply_file(f,locations=True); rows += h.rows
rows=list({r["id"]:r for r in rows}.values())
rows.sort(key=lambda r:(r["type"],r["name"],r["id"]))
obj={"schemaVersion":1,"country":"FR",
 "generatedAt":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
 "source":"OpenStreetMap / Geofabrik",
 "policy":{"acceptedHighway":["services","rest_area"],"genericParkingExcluded":True},
 "graphLinking":{"status":"pending","note":"No direction is guessed from proximity. Phase 2 will trace service roads and motorway_link to the motorway carriageway."},
 "count":len(rows),"areas":rows}
with open(outpath,"w",encoding="utf-8") as f: json.dump(obj,f,ensure_ascii=False,separators=(",",":"))
print("areas:",len(rows))
if not rows: raise SystemExit("ERROR: zero areas")
