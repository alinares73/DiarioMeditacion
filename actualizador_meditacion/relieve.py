"""Relieve sombreado aproximado de Palestina para el mapa del Atlas (modelo de alturas hecho a mano)."""
import numpy as np, base64, io
from PIL import Image
X0, X1, Y0, Y1, RES = -100, 900, -60, 1050, 1.0
W, H = int((X1 - X0) * RES), int((Y1 - Y0) * RES)
xs = X0 + (np.arange(W) + .5) / RES; ys = Y0 + (np.arange(H) + .5) / RES
XX, YY = np.meshgrid(xs, ys)
LON = XX / (0.848 * 400) + 34.25; LAT = 33.72 - YY / 400
KX = 0.848  # grados de longitud -> distancia comparable a latitud

def g(lat, lon, h, slat, slon=None):
    slon = slon or slat
    return h * np.exp(-(((LAT - lat) / slat) ** 2 + ((LON - lon) * KX / slon) ** 2))

def ridge(pts, h, w):
    """Cresta a lo largo de una polilínea [(lat,lon,h_rel)], anchura w (grados)."""
    out = np.zeros_like(LAT)
    for (a1, o1, h1), (a2, o2, h2) in zip(pts, pts[1:]):
        px, py = (LON - o1) * KX, LAT - a1; dx, dy = (o2 - o1) * KX, a2 - a1
        L2 = dx * dx + dy * dy; t = np.clip((px * dx + py * dy) / L2, 0, 1)
        d2 = (px - t * dx) ** 2 + (py - t * dy) ** 2
        out = np.maximum(out, h * (h1 + (h2 - h1) * t) * np.exp(-d2 / w ** 2))
    return out

def dist_line(pts):
    d = np.full(LAT.shape, 9.0)
    for (a1, o1), (a2, o2) in zip(pts, pts[1:]):
        px, py = (LON - o1) * KX, LAT - a1; dx, dy = (o2 - o1) * KX, a2 - a1
        t = np.clip((px * dx + py * dy) / (dx * dx + dy * dy), 0, 1)
        d = np.minimum(d, np.sqrt((px - t * dx) ** 2 + (py - t * dy) ** 2))
    return d

rng0 = np.random.default_rng(3)
def smooth_noise(sc, seed):
    r = np.random.default_rng(seed); n = r.standard_normal((H // sc + 4, W // sc + 4)).astype(np.float32)
    return np.array(Image.fromarray(n, 'F').resize(((W // sc + 4) * sc, (H // sc + 4) * sc), Image.BICUBIC))[:H, :W]
LAT0, LON0 = LAT.copy(), LON.copy()
LAT = LAT0 + 0.028 * smooth_noise(110, 11) + 0.012 * smooth_noise(45, 12)
LON = LON0 + 0.028 * smooth_noise(110, 13) + 0.012 * smooth_noise(45, 14)
h = np.zeros_like(LAT)
# meseta oriental (Transjordania) que sube hacia el este
east = np.clip((LON - 35.62) / 0.25, 0, 1)
h += east * (700 + 250 * np.clip((LAT - 31.2) / 2.5, 0, 1))
# espina central: Hebrón – Jerusalén – Betel – Garizim – Gelboé
h = np.maximum(h, ridge([(31.25, 35.05, .75), (31.53, 35.10, 1.0), (31.78, 35.22, .8), (31.93, 35.23, .9), (32.20, 35.27, .85), (32.35, 35.25, .55), (32.47, 35.40, .5)], 1000, .13))
h = np.maximum(h, ridge([(32.73, 35.00, 1), (32.62, 35.10, .9), (32.53, 35.18, .7)], 520, .045))   # Carmelo
h = np.maximum(h, ridge([(32.70, 35.15, .8), (32.70, 35.30, 1), (32.72, 35.45, .8)], 520, .06))    # colinas de Nazaret
h = np.maximum(h, ridge([(32.86, 35.20, .9), (32.82, 35.38, 1), (32.85, 35.48, .8)], 560, .07))    # Baja Galilea
h = np.maximum(h, ridge([(32.95, 35.20, .6), (33.00, 35.41, 1), (33.10, 35.45, .85), (33.30, 35.45, .9), (33.60, 35.55, 1)], 1150, .12))  # Alta Galilea y Líbano
h += g(32.687, 35.390, 380, .02)            # Tabor
h += g(33.416, 35.857, 2400, .10, .13)      # Hermón
h += g(31.77, 35.73, 150, .05)              # Nebo
h = np.maximum(h, ridge([(32.10, 35.72, .9), (32.35, 35.75, 1), (32.55, 35.85, .7)], 1150, .14))  # Galaad
h = np.maximum(h, g(32.65, 36.70, 1600, .25, .2))  # Yébel Druso
# llanura de Esdrelón (baja)
h = np.maximum(h - g(32.60, 35.28, 420, .08, .13) - g(32.62, 35.12, 250, .05, .06), 40 * (h > 40) + np.minimum(h, 40) * (h <= 40))
# fosa del Jordán (bajo el nivel del mar)
LAT, LON = LAT0, LON0
jor = [(33.25, 35.65), (33.07, 35.615), (32.89, 35.60), (32.80, 35.59), (32.705, 35.575), (32.40, 35.555), (32.05, 35.53), (31.77, 35.535), (31.50, 35.48), (31.20, 35.43)]
d = dist_line(jor)
depth = 250 + 200 * np.clip((32.6 - LAT) / 1.0, 0, 1) + 150 * np.clip((31.8 - LAT) / .3, 0, 1)
h = h * (1 - np.exp(-(d / .09) ** 2)) - depth * np.exp(-(d / .065) ** 2)
# costa: llanura baja
h *= np.clip((LON - (34.45 + (LAT - 31.2) * 0.25)) / 0.18, 0.05, 1)
# textura: colinas pequeñas
rng = np.random.default_rng(7)
noise = np.zeros_like(h)
from scipy.ndimage import gaussian_filter
for sc, amp in ((70, 1.0), (32, .5), (14, .25)):
    n = rng.standard_normal((H // sc + 4, W // sc + 4)).astype(np.float32)
    n = np.array(Image.fromarray(n, 'F').resize(((W // sc + 4) * sc, (H // sc + 4) * sc), Image.BICUBIC))[:H, :W]
    noise += amp * n
h += noise * (10 + 0.09 * np.clip(h, 0, None))

# sombreado (luz del noroeste)
from scipy.ndimage import gaussian_filter
hs = gaussian_filter(h, 1.2)
cell = (1 / RES) * 111000 / 400  # metros por píxel
gy, gx = np.gradient(hs, cell)
ex = 2.6
nx, ny, nz = -gx * ex, gy * ex, np.ones_like(hs)   # y de la imagen hacia abajo = sur
norm = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
az, alt = np.radians(315), np.radians(42)
lx, ly, lz = np.cos(alt) * np.sin(az), np.cos(alt) * np.cos(az), np.sin(alt)
shade = (nx * lx + ny * ly + nz * lz) / norm
flat = np.sin(alt)
dsh = shade - flat
# capas: tinte hipsométrico + sombras + luces
A = np.zeros((H, W, 4))
def over(rgb, a):
    a = np.clip(a, 0, 1)[..., None]
    A[..., :3] = np.array(rgb) * a + A[..., :3] * (1 - a); A[..., 3:] = a + A[..., 3:] * (1 - a)
hi = np.clip(h / 1100, 0, 1)
over((0.55, 0.42, 0.25), 0.05 + 0.20 * hi ** 1.2)                 # tierras altas: ocre
over((0.30, 0.50, 0.30), 0.10 * np.clip(1 - h / 300, 0, 1) * (h > -50))  # llanuras: verde suave
over((0.35, 0.30, 0.22), 0.20 * np.clip(-h / 300, 0, 1))          # fosa del Jordán: más oscura
over((0, 0, 0), np.clip(-dsh * 1.1, 0, .45))
over((1, 1, 1), np.clip(dsh * 1.0, 0, .30))
rgb = np.where(A[..., 3:] > 0, A[..., :3] / np.maximum(A[..., 3:], 1e-6), 0)
img = Image.fromarray(np.dstack([rgb * 255, A[..., 3:] * 255]).clip(0, 255).astype(np.uint8), 'RGBA')
img.save('/home/claude/v/relieve.png')
b = io.BytesIO(); img.save(b, 'WEBP', quality=60, method=6)
open('/home/claude/v/relieve.webp', 'wb').write(b.getvalue())
print(W, H, len(b.getvalue()) // 1024, 'KB', 'h min/max', int(h.min()), int(h.max()))
