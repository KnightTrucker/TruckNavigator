#!/usr/bin/env python3
import json,sys,math,collections,re,unicodedata
import osmium

ALLOWED={"service","motorway_link","motorway"}
MAX_HOPS=160
RADII=(220.0,350.0,500.0)
MAX_SEEDS=16

def hav(a,b,c,d):
    R=6371000.0
    p1=math.radians(a); p2=math.radians(c)
    q=math.sin(math.radians(c-a)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2
    return 2*R*math.asin(min(1,math.sqrt(q)))

def norm(s):
    s=unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+"," ",s).strip()

def oneway(tags,hw):
    v=(tags.get("oneway") or "").lower()
    if v in ("yes","1","true"): return 1
    if v=="-1": return -1
    if v in ("no","0","false"): return 0
    return 1 if hw=="motorway" else 0

class Roads(osmium.SimpleHandler):
    def __init__(self):
        super().__init__(); self.ways={}; self.nodeways=collections.defaultdict(set)
        self.coords={}; self.service_nodes=set()
    def node(self,n):
        if n.location.valid(): self.coords[n.id]=(n.location.lat,n.location.lon)
    def way(self,w):
        hw=w.tags.get("highway")
        if hw not in ALLOWED:return
        ns=[n.ref for n in w.nodes]
        if len(ns)<2:return
        self.ways[w.id]={"id":w.id,"nodes":ns,"highway":hw,"ref":w.tags.get("ref"),
          "name":w.tags.get("name"),"oneway":oneway(w.tags,hw),
          "destination":w.tags.get("destination"),"destination_ref":w.tags.get("destination:ref")}
        for n in ns:
            self.nodeways[n].add(w.id)
            if hw=="service":self.service_nodes.add(n)

def seeds(area,roads,radius):
    lat,lon=area.get("lat"),area.get("lon")
    if lat is None or lon is None:return []
    z=[]
    for n in roads.service_nodes:
        c=roads.coords.get(n)
        if not c:continue
        d=hav(lat,lon,c[0],c[1])
        if d<=radius:z.append((d,n))
    z.sort()
    return z[:MAX_SEEDS]

def trace(seed_rows,roads):
    q=collections.deque((n,0,[],d) for d,n in seed_rows)
    seen=set(n for _,n in seed_rows); hits=[]
    while q:
        n,h,path,sd=q.popleft()
        if h>MAX_HOPS:continue
        for wid in roads.nodeways.get(n,()):
            w=roads.ways[wid]; p2=path+[wid]
            if w["highway"]=="motorway":
                links=[x for x in p2 if roads.ways.get(x,{}).get("highway")=="motorway_link"]
                hits.append((0 if links else 1,h,sd,w,p2)); continue
            if w["highway"] not in ("service","motorway_link"):continue
            ns=w["nodes"]
            for i,x in enumerate(ns):
                if x!=n:continue
                nxt=[]
                if w["oneway"]==1:
                    if i+1<len(ns):nxt=[ns[i+1]]
                elif w["oneway"]==-1:
                    if i:nxt=[ns[i-1]]
                else:
                    if i:nxt.append(ns[i-1])
                    if i+1<len(ns):nxt.append(ns[i+1])
                for m in nxt:
                    if m not in seen:
                        seen.add(m);q.append((m,h+1,p2,sd))
    return sorted(hits,key=lambda x:(x[0],x[1],x[2]))

if len(sys.argv)<4:raise SystemExit("build_service_graph.py AREAS_JSON OUTPUT_JSON INPUT_PBF...")
src,out,*pbfs=sys.argv[1:]
db=json.load(open(src,encoding="utf-8"))
roads=Roads()
for p in pbfs:
    r=Roads();r.apply_file(p,locations=True)
    roads.ways.update(r.ways);roads.coords.update(r.coords);roads.service_nodes.update(r.service_nodes)
    for n,ws in r.nodeways.items():roads.nodeways[n].update(ws)

linked=seeded=withlink=0
for a in db["areas"]:
    chosen=[];radius=None
    for rad in RADII:
        sr=seeds(a,roads,rad)
        if sr:seeded+=1 if radius is None else 0
        hits=trace(sr,roads) if sr else []
        if hits:
            chosen=hits;radius=rad;break
    g={"status":"unlinked","roadWayId":None,"roadRef":None,"entryWayIds":[],
       "direction":None,"confidence":0.0,"source":"osm_topology_seeded_2c","seedRadiusM":radius}
    if chosen:
        _,h,sd,w,path=chosen[0]
        links=[x for x in path if roads.ways.get(x,{}).get("highway")=="motorway_link"]
        if links:withlink+=1
        g.update({"status":"carriageway_linked","roadWayId":f"osm:way/{w['id']}",
          "roadRef":w.get("ref"),"entryWayIds":[f"osm:way/{x}" for x in links],
          "direction":"way_forward" if w["oneway"]==1 else None,
          "confidence":0.97 if links and radius==220.0 else 0.92 if links else 0.75,
          "hops":h,"seedDistanceM":round(sd,1)})
        linked+=1
    a["graph"]=g
    if g["roadRef"]:a["roadRef"]=g["roadRef"]

db["schemaVersion"]=4
db["graphLinking"]={"status":"phase2c","linked":linked,"total":len(db["areas"]),
 "areasWithMotorwayLinkPath":withlink,"seedRadiiM":list(RADII),
 "note":"Progressive internal-service-road seeding; motorway association remains exact topology. No carriageway side is guessed from coordinates."}
json.dump(db,open(out,"w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"))
print("phase2c linked:",linked,"/",len(db["areas"]),"motorway_link:",withlink)
if linked<150:raise SystemExit("ERROR: phase2c regression: linked count below 150")
