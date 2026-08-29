#!/usr/bin/env python3
import osmium,json,sys,re,unicodedata,math,collections

def norm(s):
    s=unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+","",s)

class A4(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.coords={}
        self.ways={}
        self.node_to_ways=collections.defaultdict(set)
    def node(self,n):
        if n.location.valid():
            self.coords[n.id]=(n.location.lat,n.location.lon)
    def way(self,w):
        if w.tags.get("highway")!="motorway" or norm(w.tags.get("ref"))!="A4":
            return
        ns=[x.ref for x in w.nodes]
        if len(ns)<2:return
        ow=(w.tags.get("oneway") or "yes").lower()
        # Store nodes in actual travel order.
        if ow=="-1": ns=list(reversed(ns))
        self.ways[w.id]={"id":w.id,"nodes":ns}
        for n in ns:self.node_to_ways[n].add(w.id)

def hav(a,b):
    R=6371000
    p1,p2=map(math.radians,[a[0],b[0]])
    dp=math.radians(b[0]-a[0]); dl=math.radians(b[1]-a[1])
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

def end_progress(w,g):
    pts=[g.coords.get(n) for n in w["nodes"]]
    pts=[p for p in pts if p]
    if len(pts)<2:return None
    # Longitude progression is evaluated across a continuous directed corridor,
    # not as "which side of the motorway is the service area".
    return pts[-1][1]-pts[0][1]

def neighbors_forward(wid,g):
    w=g.ways[wid]; end=w["nodes"][-1]
    out=[]
    for x in g.node_to_ways.get(end,()):
        if x==wid:continue
        wx=g.ways[x]
        if wx["nodes"] and wx["nodes"][0]==end:out.append(x)
    return out

def neighbors_backward(wid,g):
    w=g.ways[wid]; start=w["nodes"][0]
    out=[]
    for x in g.node_to_ways.get(start,()):
        if x==wid:continue
        wx=g.ways[x]
        if wx["nodes"] and wx["nodes"][-1]==start:out.append(x)
    return out

def corridor(wid,g,max_ways=80):
    # Walk the directed A4 carriageway around the certified linked way.
    seen={wid}; q=collections.deque([(wid,0)])
    while q:
        cur,d=q.popleft()
        if d>=max_ways:continue
        for nxt in neighbors_forward(cur,g)+neighbors_backward(cur,g):
            if nxt not in seen:
                seen.add(nxt); q.append((nxt,d+1))
    return seen

def classify(wid,g):
    if wid not in g.ways:return None,0,0
    ids=corridor(wid,g)
    progress=0.0; length=0.0
    for i in ids:
        w=g.ways[i]
        pts=[g.coords.get(n) for n in w["nodes"]]
        pts=[p for p in pts if p]
        if len(pts)<2:continue
        seglen=sum(hav(a,b) for a,b in zip(pts,pts[1:]))
        progress+=(pts[-1][1]-pts[0][1])*seglen
        length+=seglen
    if length==0:return None,len(ids),0
    avg=progress/length
    # A4 Paris->Strasbourg progresses globally east; reverse carriageway west.
    # Tiny values remain unresolved rather than forced.
    if avg>1e-6:d="Paris->Strasbourg"
    elif avg<-1e-6:d="Strasbourg->Paris"
    else:d="ambiguous"
    return d,len(ids),avg

report=json.load(open(sys.argv[1],encoding="utf-8"))
g=A4()
for p in sys.argv[3:]:
    g.apply_file(p,locations=True)

checks=[]
for c in report["checks"]:
    wid=c.get("roadWayId")
    if not c.get("certifiedA4") or not wid:
        checks.append({**c,"semanticDirection":None,"directionCertified":False})
        continue
    try:i=int(wid.rsplit("/",1)[1])
    except:i=-1
    d,n,prog=classify(i,g)
    checks.append({**c,"semanticDirection":d,"directionCertified":d in ("Paris->Strasbourg","Strasbourg->Paris"),
                   "orientationCorridorWays":n,"orientationProgress":prog})

summary={
 "schemaVersion":2,
 "route":"A4",
 "method":"certified A4 topology + directed oneway carriageway continuity",
 "checks":checks,
 "certifiedA4":sum(x.get("certifiedA4",False) for x in checks),
 "directionCertified":sum(x.get("directionCertified",False) for x in checks),
 "parisToStrasbourg":sum(x.get("semanticDirection")=="Paris->Strasbourg" for x in checks),
 "strasbourgToParis":sum(x.get("semanticDirection")=="Strasbourg->Paris" for x in checks),
 "ambiguous":sum(x.get("certifiedA4") and not x.get("directionCertified") for x in checks),
 "note":"Individual local bearing is not used. Direction is derived from continuity of the already-certified directed A4 carriageway."
}
json.dump(summary,open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in summary.items() if k!="checks"},ensure_ascii=False,indent=2))
for x in checks:
    if x.get("certifiedA4"):
        print(x["expected"],"=>",x["semanticDirection"],"corridorWays",x.get("orientationCorridorWays"))
# Validation: this baseline is explicitly the SANEF Strasbourg-bound sample.
wrong=[x["expected"] for x in checks if x.get("certifiedA4") and x.get("semanticDirection")=="Strasbourg->Paris"]
if wrong:
    raise SystemExit("Opposite-direction certified sample(s): "+", ".join(wrong))
