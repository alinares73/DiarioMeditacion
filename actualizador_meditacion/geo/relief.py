import numpy as np, io
from PIL import Image
from scipy import ndimage as ndi
dem=np.load('/home/claude/geo/dem.npy');att=np.load('/home/claude/geo/att.npy')
X0,X1,Y0,Y1,RES=-100,900,-60,1050,1.0
W,H=int((X1-X0)*RES),int((Y1-Y0)*RES)
xs=X0+(np.arange(W)+.5)/RES;ys=Y0+(np.arange(H)+.5)/RES
XX,YY=np.meshgrid(xs,ys);LON=XX/(0.848*400)+34.25;LAT=33.72-YY/400
r=(34-LAT)*120-.5;c=(LON-34)*120-.5
h=ndi.map_coordinates(dem,[r,c],order=3,mode='nearest')
sea=ndi.map_coordinates((att==1).astype(np.float32)[::2,::2],[(34-LAT)*600-.5,(LON-34)*600-.5],order=1,mode='nearest')>0.5
sea|=LON<34
h=np.where(sea,np.minimum(h,0)*0,h)
hs=ndi.gaussian_filter(h,1.0)
cell=(1/RES)*111000/400
gy,gx=np.gradient(hs,cell);ex=2.2
nx,ny,nz=-gx*ex,gy*ex,np.ones_like(hs);nrm=np.sqrt(nx**2+ny**2+nz**2)
az,alt=np.radians(315),np.radians(42)
lx,ly,lz=np.cos(alt)*np.sin(az),np.cos(alt)*np.cos(az),np.sin(alt)
dsh=(nx*lx+ny*ly+nz*lz)/nrm-np.sin(alt)
A=np.zeros((H,W,4))
def over(rgb,a):
    a=np.clip(a,0,1)[...,None];A[...,:3]=np.array(rgb)*a+A[...,:3]*(1-a);A[...,3:]=a+A[...,3:]*(1-a)
hi=np.clip(h/1100,0,1)
over((0.55,0.42,0.25),0.05+0.22*hi**1.1)
over((0.30,0.50,0.30),0.10*np.clip(1-h/300,0,1)*(h>-50))
over((0.35,0.30,0.22),0.22*np.clip(-h/350,0,1))
over((0,0,0),np.clip(-dsh*1.1,0,.5))
over((1,1,1),np.clip(dsh*1.0,0,.3))
A[sea]=0
rgb=np.where(A[...,3:]>0,A[...,:3]/np.maximum(A[...,3:],1e-6),0)
img=Image.fromarray(np.dstack([rgb*255,A[...,3:]*255]).clip(0,255).astype(np.uint8),'RGBA')
img.save('/home/claude/geo/relieve.png')
b=io.BytesIO();img.save(b,'WEBP',quality=62,method=6);open('/home/claude/geo/relieve.webp','wb').write(b.getvalue())
print(len(b.getvalue())//1024,'KB')
