#!/usr/bin/env python3
import json, sys, math, collections
import osmium

# Phase 2B
# 1) Keep strict service/rest_area candidates from FR.json.
# 2) Build a road graph from service, motorway_link and motorway ways.
# 3) For each area, find nearby service-road seed nodes/ways using geometry only
#    to enter the local internal road network.
# 4) From that seed onward, require exact OSM topology to reach motorway_link
#    and then motorway. Direction is never inferred from "left/right of road".

ALLOWED = {"service","motorway_link","motorway"}
MAX_HOPS = 120
SEED_RADIUS_M = 220.0
MAX_SEEDS = 10

def hav(a,b,c,d):
    R=6371000.0
    p1=math.radians(a); p2=math.radians(c)
    dp=math.radians(c-a); dl=math.radians(d-b)
    q=math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(min(1,math.sqrt(q)))

def oneway(tags, hw):
    v=(tags.get("oneway") or "").lower()
    if v in ("yes","1","true"): return 1
    if v=="-1": return -1
    if v in ("no","0","false"): return 0
    return 1 if hw=="motorway" else 0

class Roads(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.ways={}
        self.nodeways=collections.defaultdict(set)
        self.coords={}
        self.service_nodes=set()
    def node(self,n):
        if n.location.valid():
            self.coords[n.id]=(n.location.lat,n.location.lon)
    def way(self,w):
        hw=w.tags.get("highway")
        if hw not in ALLOWED: return
        ns=[n.ref for n in w.nodes]
        if len(ns)<2: return
        d={"id":w.id,"nodes":ns,"highway":hw,"ref":w.tags.get("ref"),
           "name":w.tags.get("name"),"oneway":oneway(w.tags,hw),
           "destination":w.tags.get("destination"),
           "destination_ref":w.tags.get("destination:ref")}
        self.ways[w.id]=d
        for n in ns:
            self.nodeways[n].add(w.id)
            if hw=="service": self.service_nodes.add(n)

def trace(start_nodes, roads):
    q=collections.deque()
    seen=set()
    for n in start_nodes:
        q.append((n,0,[]))
        seen.add((n,0))
    candidates=[]
    while q:
        n,hops,path=q.popleft()
        if hops>MAX_HOPS: continue
        for wid in roads.nodeways.get(n,()):
            w=roads.ways[wid]
            p2=path+[wid]
            if w["highway"]=="motorway":
                candidates.append((hops,w,p2,n))
                continue
            if w["highway"] not in ("service","motorway_link"):
                continue
            ns=w["nodes"]
            try:
                idxs=[i for i,x in enumerate(ns) if x==n]
            except Exception:
                idxs=[]
            for i in idxs:
                nxt=[]
                if w["oneway"]==1:
                    if i+1<len(ns): nxt.append(ns[i+1])
                elif w["oneway"]==-1:
                    if i>0: nxt.append(ns[i-1])
                else:
                    if i>0: nxt.append(ns[i-1])
                    if i+1<len(ns): nxt.append(ns[i+1])
                for m in nxt:
                    state=(m,hops+1)
                    if state not in seen:
                        seen.add(state); q.append((m,hops+1,p2))
    return sorted(candidates,key=lambda x:x[0])

def seed_nodes(area, roads):
    lat,lon=area.get("lat"),area.get("lon")
    if lat is None or lon is None: return []
    rows=[]
    for n in roads.service_nodes:
        c=roads.coords.get(n)
        if not c: continue
        d=hav(lat,lon,c[0],c[1])
        if d<=SEED_RADIUS_M:
            rows.append((d,n))
    rows.sort()
    return [n for _,n in rows[:MAX_SEEDS]]

if len(sys.argv)<4:
    raise SystemExit("build_service_graph.py AREAS_JSON OUTPUT_JSON INPUT_PBF...")

src,out,*pbfs=sys.argv[1:]
db=json.load(open(src,encoding="utf-8"))

roads=Roads()
for pbf in pbfs:
    r=Roads(); r.apply_file(pbf,locations=True)
    roads.ways.update(r.ways)
    roads.coords.update(r.coords)
    roads.service_nodes.update(r.service_nodes)
    for n,ws in r.nodeways.items(): roads.nodeways[n].update(ws)

linked=0; with_seed=0; with_link=0
for a in db["areas"]:
    seeds=seed_nodes(a,roads)
    if seeds: with_seed+=1
    hits=trace(seeds,roads) if seeds else []
    g={"status":"unlinked","roadWayId":None,"roadRef":None,"entryWayIds":[],
       "direction":None,"confidence":0.0,"source":"osm_topology_seeded",
       "seedRadiusM":SEED_RADIUS_M,"seedCount":len(seeds)}
    if hits:
        hop,w,path,node=hits[0]
        links=[x for x in path if roads.ways.get(x,{}).get("highway")=="motorway_link"]
        if links: with_link+=1
        g.update({"status":"carriageway_linked",
                  "roadWayId":f"osm:way/{w['id']}",
                  "roadRef":w.get("ref"),
                  "entryWayIds":[f"osm:way/{x}" for x in links],
                  "direction":"way_forward" if w["oneway"]==1 else None,
                  "confidence":0.95 if links else 0.80,
                  "hops":hop})
        linked+=1
    a["graph"]=g
    if g["roadRef"]: a["roadRef"]=g["roadRef"]

db["schemaVersion"]=3
db["graphLinking"]={
    "status":"phase2b",
    "linked":linked,
    "total":len(db["areas"]),
    "areasWithServiceRoadSeed":with_seed,
    "areasWithMotorwayLinkPath":with_link,
    "seedRadiusM":SEED_RADIUS_M,
    "note":"Nearby geometry is used only to seed the area's internal service-road network. The actual motorway association must then be reached through exact OSM service/motorway_link/motorway topology. No left/right carriageway guess is used."
}
json.dump(db,open(out,"w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"))
print("phase2b linked:",linked,"/",len(db["areas"]),
      "seeded:",with_seed,"motorway_link paths:",with_link)
if linked < 20:
    raise SystemExit("ERROR: graph linking unexpectedly low")
