"""Italy seen in perspective from the south, Puglia raised and highlighted.
Boundaries: openpolis/geojson-italy limits_IT_regions.geojson"""
import json, math, sys
src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/geo/limits_IT_regions.geojson"
regs = json.load(open(src))["features"]
LAT0 = 41.9; KX = math.cos(math.radians(LAT0))
LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = 6.5, 18.7, 36.5, 47.2
W, H = 900, 560
# ground coordinates: x in km-ish units centred, depth from south (near) to north (far)
def ground(lon, lat):
    gx = (lon - 12.6) * KX          # ~ -5..5
    gy = (lat - LAT_MIN)            # 0 (south) .. 10.7 (north)
    return gx, gy
def rings(g):
    rs = g["coordinates"] if g["type"] == "Polygon" else [r for p in g["coordinates"] for r in p]
    return [r for r in rs if min(c[1] for c in r) > 36.6 and min(c[0] for c in r) > 12.2 or min(c[1] for c in r) > 37.2]
CAMH, Z0 = 9.0, 12.0                # camera height, distance of the south edge
def raw(lon, lat):
    gx, gy = ground(lon, lat)
    z = Z0 + gy
    return (gx / z, CAMH / z)
# fit the projected country into the view box with margins
_pts = [raw(*c[:2]) for f in regs for r in rings(f["geometry"]) for c in r]
_xs = [a for a, b in _pts]; _ys = [b for a, b in _pts]
MX, MT, MB = 30, 80, 60
_sc = min((W - 2*MX) / (max(_xs) - min(_xs)), (H - MT - MB) / (max(_ys) - min(_ys)))
_ox = (W - _sc * (max(_xs) + min(_xs))) / 2
_oy = MT - _sc * min(_ys)
def proj(lon, lat):
    a, b = raw(lon, lat)
    return (_ox + _sc * a, _oy + _sc * b)
def path(g, dy=0.0, tol=1.0, min_area=8):
    out = []
    for r in rings(g):
        pts = [proj(*p[:2]) for p in r]
        keep = [pts[0]]
        for q in pts[1:]:
            if abs(q[0]-keep[-1][0]) + abs(q[1]-keep[-1][1]) >= tol: keep.append(q)
        if len(keep) < 4: continue
        a = 0.5*abs(sum(keep[i][0]*keep[i-1][1]-keep[i-1][0]*keep[i][1] for i in range(len(keep))))
        if a < min_area: continue
        out.append("M" + " L".join(f"{x:.1f},{y+dy:.1f}" for x, y in keep) + "Z")
    return "".join(out)
others = [f for f in regs if f["properties"]["reg_name"] != "Puglia"]
pug = next(f for f in regs if f["properties"]["reg_name"] == "Puglia")
land_top = "".join(path(f["geometry"]) for f in others)
land_all = land_top + path(pug["geometry"])
SLAB, LIFT = 9, 16
slab = "".join(f'<path d="{land_all}" transform="translate(0,{i})"/>' for i in range(SLAB, 0, -1))
pug_top = path(pug["geometry"], dy=-LIFT)
pug_sides = "".join(f'<path d="{path(pug["geometry"], dy=-i)}"/>' for i in range(0, LIFT, 1))
lx, ly = proj(17.2, 41.55)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Map of Italy seen from the south, with the region of Puglia raised and highlighted">
<defs>
  <radialGradient id="sh" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#000" stop-opacity=".16"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
  <linearGradient id="top" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f4f2ee"/><stop offset="1" stop-color="#e6e2dc"/></linearGradient>
  <linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f06272"/><stop offset="1" stop-color="#d9364a"/></linearGradient>
  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6"/></filter>
</defs>
<ellipse cx="{W/2+10}" cy="{H-48}" rx="{W*0.30}" ry="34" fill="url(#sh)"/>
<g fill="#cfc9c0">{slab}</g>
<path d="{land_top}" fill="url(#top)" stroke="#ffffff" stroke-width="1.4" stroke-linejoin="round"/>
<path d="{path(pug["geometry"])}" fill="#000" opacity=".18" filter="url(#glow)" transform="translate(6,8)"/>
<g fill="#a3142a">{pug_sides}</g>
<path d="{pug_top}" fill="url(#pg)" stroke="#ffffff" stroke-width="2.4" stroke-linejoin="round"/>
<text x="{lx:.0f}" y="{ly-LIFT-40:.0f}" text-anchor="middle" font-family="Manrope, sans-serif" font-weight="800" font-size="30" letter-spacing="1" fill="#b0181b">Puglia</text>
</svg>'''
print(svg)
