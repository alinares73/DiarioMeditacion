import numpy as np, json, heapq
from skimage import measure
from scipy import ndimage as ndi
R=1200;LON0,LAT1=34,34
att=np.load('/home/claude/geo/att.npy');dem=np.load('/home/claude/geo/dem.npy')
H,W=att.shape
def ll(c):  # (fila,col) -> [lat,lon]
    return [round(LAT1-(c[0]+.5)/R,4),round(LON0+(c[1]+.5)/R,4)]
def simp(c,tol): return measure.approximate_polygon(c,tol)
out={}
# costa: contorno del mar (suavizado ligero)
sea=ndi.gaussian_filter((att==1).astype(np.float32),1.5)
cs=measure.find_contours(sea,0.5)
cs=sorted(cs,key=len,reverse=True)
coast=simp(cs[0],1.5)
out['coast']=[ll(p) for p in coast]
print('costa',len(cs[0]),'->',len(coast),out['coast'][0],out['coast'][-1])
# lagos
lab,n=ndi.label(att==3)
def lake_at(lat,lon):
    return lab[int((LAT1-lat)*R),int((lon-LON0)*R)]
gal=lab==lake_at(32.82,35.59)
# mar Muerto antiguo: lago actual + todo lo que hoy está por debajo de -395 m en la cuenca
demz=ndi.zoom(dem,R/120,order=1)[:H,:W]
ds=lab==lake_at(31.55,35.50)
box=np.zeros_like(ds);y0=int((LAT1-31.86)*R);x0=int((35.30-LON0)*R);x1=int((35.66-LON0)*R);box[y0:,x0:x1]=True
anc=(ds|((demz<-395)&box))
l2,_=ndi.label(anc);anc=l2==l2[int((LAT1-31.55)*R),int((35.50-LON0)*R)]
for nm,m,tol in (('galilee',gal,1.2),('dead',anc,2.0)):
    m=ndi.gaussian_filter(m.astype(np.float32),2)
    c=max(measure.find_contours(m,0.5),key=len);c=simp(c,tol)
    out[nm]=[ll(p) for p in c];print(nm,len(c))
# ríos: Jordán de Natural Earth + afluentes trazados sobre el relieve real (descenso por la máxima pendiente)
d=json.load(open('/tmp/rivers.geojson'));jor=[]
for f in d['features']:
    if f['properties'].get('name')=='Jordan':
        g=f['geometry'];cs2=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
        for c in cs2:
            if any(34<x<37 and 31<y<34 for x,y in c): jor.append([[round(y,4),round(x,4)] for x,y in c])
out['jordan']=jor
# relleno de depresiones (priority flood) sobre el DEM de 30"
Z=dem.copy();h,w=Z.shape;done=np.zeros_like(Z,bool);pq=[]
sea30=ndi.zoom((att==1).astype(np.float32),120/R,order=1)>0.5
lakes30=ndi.zoom((gal|ds).astype(np.float32),120/R,order=1)>0.3
seed=sea30|lakes30
jl=np.zeros_like(seed)
for c in [c for c in jor if c[0][0]<32.75]:
    for (a1,o1),(a2,o2) in zip(c,c[1:]):
        for t in np.linspace(0,1,20):
            la=a1+(a2-a1)*t;lo=o1+(o2-o1)*t;yy=int((34-la)*120);xx=int((lo-34)*120)
            if 0<=yy<360 and 0<=xx<360: jl[yy,xx]=True
seed=seed|jl
for y in range(h):
    for x in range(w):
        if seed[y,x] or y in (0,h-1) or x in (0,w-1):
            heapq.heappush(pq,(Z[y,x],y,x));done[y,x]=True
while pq:
    z,y,x=heapq.heappop(pq)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            yy,xx=y+dy,x+dx
            if 0<=yy<h and 0<=xx<w and not done[yy,xx]:
                done[yy,xx]=True;Z[yy,xx]=max(Z[yy,xx],z+0.01);heapq.heappush(pq,(Z[yy,xx],yy,xx))
def trace(lat,lon,maxn=400):
    y=int((34-lat)*120);x=int((lon-34)*120);pts=[]
    for _ in range(maxn):
        pts.append([round(34-(y+.5)/120,4),round(34+(x+.5)/120,4)])
        if seed[y,x]: break
        best=None
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                if dy==dx==0: continue
                yy,xx=y+dy,x+dx
                if 0<=yy<h and 0<=xx<w:
                    s=(Z[y,x]-Z[yy,xx])/(1.414 if dy and dx else 1)
                    if best is None or s>best[0]: best=(s,yy,xx)
        if best[0]<=0: print('  parada',Z[y,x]); break
        y,x=best[1],best[2]
    return pts
SRC={'jordan_alto':(33.245,35.692),'yarmuk':(32.62,36.25),'jaboc':(31.98,35.98),'kison':(32.47,35.32),'arnon':(31.30,35.98),'querit':(31.82,35.26),'cedron':(31.79,35.235),'zarqa_main':(31.66,35.75)}
out['rivers']={k:trace(*v) for k,v in SRC.items()}
for k,v in out['rivers'].items(): print(k,len(v),v[0],v[-1])
json.dump(out,open('/home/claude/geo/geo.json','w'))
np.save('/home/claude/geo/demfill.npy',Z)
