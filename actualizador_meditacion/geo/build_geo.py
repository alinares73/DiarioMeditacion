"""Geografía real para el mapa del Atlas: costa y lagos (ASTER Water Bodies, 1") y relieve (SRTM30+, 30")."""
import numpy as np, tifffile, json, os
from PIL import Image
from skimage import measure
R=1200  # px por grado (3")
LON0,LON1,LAT0,LAT1=34,37,31,34
W=(LON1-LON0)*R;H=(LAT1-LAT0)*R
att=np.ones((H,W),np.uint8)  # por defecto mar (teselas inexistentes = mar)
for la in (31,32,33):
    for lo in (34,35,36):
        f='/tmp/wb/ASTWBDV001_N%02dE%03d_att.tif'%(la,lo)
        if not os.path.exists(f): continue
        a=tifffile.imread(f)[:3600,:3600][::3,::3]
        y0=(LAT1-la-1)*R; x0=(lo-LON0)*R
        att[y0:y0+R,x0:x0+R]=a
np.save('/home/claude/geo/att.npy',att)
print(np.unique(att,return_counts=True))
# --- DEM SRTM30+ (24 bits con signo: r + g*256 + b*65536)
im=np.array(Image.open('/tmp/n30e030.png').convert('RGB')).astype(np.int64)
v=im[...,0]+im[...,1]*256+im[...,2]*65536; v=np.where(v>=2**23,v-2**24,v)
dem=v[(40-LAT1)*120:(40-LAT0)*120,(LON0-30)*120:(LON1-30)*120].astype(np.float32)  # 360x360
np.save('/home/claude/geo/dem.npy',dem)
print('dem',dem.shape,dem.min(),dem.max())
