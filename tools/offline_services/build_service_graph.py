#!/usr/bin/env python3
import json,sys,math,collections,osmium
ALLOWED={"service","motorway_link","motorway"}; MAX_HOPS=160; RADII=(220.,350.,500.); MAX_SEEDS=16; CELL=.005
def hav(a,b,c,d):
 R=6371000.;p1=math.radians(a);p2=math.radians(c);q=math.sin(math.radians(c-a)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2
 return 2*R*math.asin(min(1,math.sqrt(q)))
def ow(t,h):
 v=(t.get("oneway") or "").lower()
 if v in ("yes","1","true"):return 1
 if v=="-1":return -1
 if v in ("no","0","false"):return 0
 return 1 if h=="motorway" else 0
class R(osmium.SimpleHandler):
 def __init__(s):super().__init__();s.w={};s.nw=collections.defaultdict(set);s.c={};s.sn=set()
 def node(s,n):
  if n.location.valid():s.c[n.id]=(n.location.lat,n.location.lon)
 def way(s,w):
  h=w.tags.get("highway")
  if h not in ALLOWED:return
  ns=[n.ref for n in w.nodes]
  if len(ns)<2:return
  s.w[w.id]={"id":w.id,"nodes":ns,"highway":h,"ref":w.tags.get("ref"),"oneway":ow(w.tags,h)}
  for n in ns:s.nw[n].add(w.id);s.sn.add(n) if h=="service" else None
def cell(a,b):return math.floor(a/CELL),math.floor(b/CELL)
def index(r):
 x=collections.defaultdict(list)
 for n in r.sn:
  if n in r.c:x[cell(*r.c[n])].append(n)
 return x
def candidates(a,r,ix):
 lat,lon=a.get("lat"),a.get("lon")
 if lat is None or lon is None:return []
 md=RADII[-1];dy=md/111000.;dx=md/(111000.*max(.25,math.cos(math.radians(lat))))
 p=cell(lat-dy,lon-dx);q=cell(lat+dy,lon+dx);z=[]
 for i in range(p[0],q[0]+1):
  for j in range(p[1],q[1]+1):
   for n in ix.get((i,j),()):
    c=r.c[n];d=hav(lat,lon,*c)
    if d<=md:z.append((d,n))
 return sorted(z)
def trace(seeds,r):
 q=collections.deque((n,0,[],d) for d,n in seeds);best={n:0 for d,n in seeds};hits=[]
 while q:
  n,h,path,sd=q.popleft()
  if h>MAX_HOPS:continue
  for wid in r.nw.get(n,()):
   w=r.w[wid];p=path+[wid]
   if w["highway"]=="motorway":
    links=[x for x in p if r.w.get(x,{}).get("highway")=="motorway_link"];hits.append((0 if links else 1,h,sd,w,p));continue
   if w["highway"] not in ("service","motorway_link"):continue
   for i,x in enumerate(w["nodes"]):
    if x!=n:continue
    ns=w["nodes"]; nxt=[]
    if w["oneway"]==1:
     if i+1<len(ns):nxt=[ns[i+1]]
    elif w["oneway"]==-1:
     if i:nxt=[ns[i-1]]
    else:
     if i:nxt.append(ns[i-1])
     if i+1<len(ns):nxt.append(ns[i+1])
    for m in nxt:
     nh=h+1
     if nh<best.get(m,10**9):best[m]=nh;q.append((m,nh,p,sd))
 return sorted(hits,key=lambda x:(x[0],x[1],x[2]))
src,out,*pbfs=sys.argv[1:];db=json.load(open(src,encoding="utf-8"));r=R()
for p in pbfs:
 x=R();x.apply_file(p,locations=True);r.w.update(x.w);r.c.update(x.c);r.sn.update(x.sn)
 for n,ws in x.nw.items():r.nw[n].update(ws)
ix=index(r);linked=withlink=seeded=0
for k,a in enumerate(db["areas"],1):
 rows=candidates(a,r,ix);seeded+=bool(rows);chosen=[];rad=None
 for rr in RADII:
  ss=[x for x in rows if x[0]<=rr][:MAX_SEEDS]
  if ss:
   hh=trace(ss,r)
   if hh:chosen=hh;rad=rr;break
 g={"status":"unlinked","roadWayId":None,"roadRef":None,"entryWayIds":[],"direction":None,"confidence":0.,"source":"osm_topology_seeded_2c_fast","seedRadiusM":rad}
 if chosen:
  _,h,sd,w,path=chosen[0];links=[x for x in path if r.w.get(x,{}).get("highway")=="motorway_link"];withlink+=bool(links)
  g.update({"status":"carriageway_linked","roadWayId":f"osm:way/{w['id']}","roadRef":w.get("ref"),"entryWayIds":[f"osm:way/{x}" for x in links],"direction":"way_forward" if w["oneway"]==1 else None,"confidence":.97 if links and rad==220 else .92 if links else .75,"hops":h,"seedDistanceM":round(sd,1)});linked+=1
 a["graph"]=g
 if g["roadRef"]:a["roadRef"]=g["roadRef"]
 if k%50==0:print("processed",k,"linked",linked,flush=True)
db["schemaVersion"]=4;db["graphLinking"]={"status":"phase2c-fast","linked":linked,"total":len(db["areas"]),"areasWithServiceRoadSeed":seeded,"areasWithMotorwayLinkPath":withlink,"seedRadiiM":list(RADII),"spatialIndexCellDegrees":CELL}
json.dump(db,open(out,"w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"));print("phase2c-fast",linked,len(db["areas"]),withlink)
if linked<150:raise SystemExit("phase2c regression")
