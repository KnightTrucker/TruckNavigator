#!/usr/bin/env python3
import json, sys, math, collections
import osmium

ALLOWED = {"service","motorway_link","motorway"}
MAX_HOPS = 80

def oneway(tags, hw):
    v=(tags.get("oneway") or "").lower()
    if v in ("yes","1","true"): return 1
    if v=="-1": return -1
    if v in ("no","0","false"): return 0
    return 1 if hw=="motorway" else 0

class Roads(osmium.SimpleHandler):
    def __init__(self):
        super().__init__(); self.ways={}; self.nodeways=collections.defaultdict(set)
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
        for n in ns: self.nodeways[n].add(w.id)

def connected_area_nodes(area, roads):
    # Phase 2A: exact OSM topology for area ways. Node POIs cannot be certified
    # unless the POI node itself participates in the road graph.
    if area.get("osmType")=="way":
        wid=area.get("osmId")
        # area polygon isn't in road graph; get its nodes in second handler below
        return area_nodes.get(wid,[])
    oid=area.get("osmId")
    return [oid] if oid in roads.nodeways else []

class AreaNodes(osmium.SimpleHandler):
    def __init__(self, ids):
        super().__init__(); self.ids=set(ids); self.nodes={}
    def way(self,w):
        if w.id in self.ids: self.nodes[w.id]=[n.ref for n in w.nodes]

def trace(start_nodes, roads):
    q=collections.deque()
    seen_nodes=set(start_nodes); seen_ways=set()
    for n in start_nodes: q.append((n,0,[]))
    candidates=[]
    while q:
        n,hops,path=q.popleft()
        if hops>MAX_HOPS: continue
        for wid in roads.nodeways.get(n,()):
            if wid in seen_ways: continue
            w=roads.ways[wid]; seen_ways.add(wid)
            p2=path+[wid]
            if w["highway"]=="motorway":
                candidates.append((hops,w,p2,n)); continue
            if w["highway"] not in ("service","motorway_link"): continue
            ns=w["nodes"]
            try: i=ns.index(n)
            except ValueError: continue
            nxt=[]
            if w["oneway"]==1:
                if i+1<len(ns): nxt=[ns[i+1]]
            elif w["oneway"]==-1:
                if i>0: nxt=[ns[i-1]]
            else:
                if i>0: nxt.append(ns[i-1])
                if i+1<len(ns): nxt.append(ns[i+1])
            for m in nxt:
                if m not in seen_nodes:
                    seen_nodes.add(m); q.append((m,hops+1,p2))
    return sorted(candidates,key=lambda x:x[0])

if len(sys.argv)<4:
    raise SystemExit("build_service_graph.py AREAS_JSON OUTPUT_JSON INPUT_PBF...")

src,out,*pbfs=sys.argv[1:]
db=json.load(open(src,encoding="utf-8"))
target_way_ids=[a["osmId"] for a in db["areas"] if a.get("osmType")=="way"]

global area_nodes
area_nodes={}
roads=Roads()
for pbf in pbfs:
    an=AreaNodes(target_way_ids); an.apply_file(pbf,locations=False); area_nodes.update(an.nodes)
    r=Roads(); r.apply_file(pbf,locations=False)
    roads.ways.update(r.ways)
    for n,ws in r.nodeways.items(): roads.nodeways[n].update(ws)

linked=0
for a in db["areas"]:
    starts=connected_area_nodes(a,roads)
    hits=trace(starts,roads) if starts else []
    g={"status":"unlinked","roadWayId":None,"roadRef":None,"entryWayIds":[],
       "direction":None,"confidence":0.0,"source":"osm_topology"}
    if hits:
        hop,w,path,node=hits[0]
        links=[x for x in path if roads.ways.get(x,{}).get("highway")=="motorway_link"]
        # Direction is deliberately not guessed from coordinates. A carriageway is
        # identified by the exact motorway way reached through directed topology.
        g.update({"status":"carriageway_linked","roadWayId":f"osm:way/{w['id']}",
                  "roadRef":w.get("ref"),"entryWayIds":[f"osm:way/{x}" for x in links],
                  "direction":"way_forward" if w["oneway"]==1 else None,
                  "confidence":0.95 if links else 0.75})
        linked+=1
    a["graph"]=g
    if g["roadRef"]: a["roadRef"]=g["roadRef"]

db["schemaVersion"]=2
db["graphLinking"]={"status":"phase2a","linked":linked,"total":len(db["areas"]),
 "note":"Exact OSM node topology only; no coordinate-side direction guessing. Direction labels such as Paris/Strasbourg require route-orientation validation."}
json.dump(db,open(out,"w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"))
print("graph linked:",linked,"/",len(db["areas"]))
