import json, math
W, H = 1600, 1200
LAT0 = 40.92
LON0, LAT_TOP = 16.48, 41.42
LAT_SPAN = 1.0
K = H / LAT_SPAN                      # px per degree latitude
KX = K * math.cos(math.radians(LAT0))  # px per degree longitude
def xy(lon, lat):
    return ((lon - LON0) * KX + W/2, (LAT_TOP - lat) * K)

def rings(geom):
    if geom["type"] == "Polygon":
        return geom["coordinates"]
    if geom["type"] == "MultiPolygon":
        return [r for poly in geom["coordinates"] for r in poly]
    return []

def path(geom, simplify=1.2):
    out = []
    for ring in rings(geom):
        pts = [xy(*p[:2]) for p in ring]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) < -200 or min(xs) > W+200 or max(ys) < -200 or min(ys) > H+200:
            continue
        keep = [pts[0]]
        for p in pts[1:]:
            if abs(p[0]-keep[-1][0]) + abs(p[1]-keep[-1][1]) >= simplify:
                keep.append(p)
        out.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in keep) + "Z")
    return "".join(out)

regions = json.load(open("/tmp/geo/limits_IT_regions.geojson"))["features"]
land = "".join(path(f["geometry"]) for f in regions if f["properties"]["reg_name"] in ("Puglia","Basilicata","Campania","Calabria","Molise"))
regline = "".join(path(f["geometry"]) for f in regions if f["properties"]["reg_name"] in ("Puglia","Basilicata"))
muni = ""
for r in (16, 17):
    for f in json.load(open(f"/tmp/geo/limits_R_{r}_municipalities.geojson"))["features"]:
        muni += path(f["geometry"], simplify=1.6)

members = {"Giovinazzo":(16.669,41.186),"Palese":(16.762,41.155),"Bari":(16.871,41.117),"Torre a Mare":(17.006,41.054),
 "Valenzano":(16.885,41.044),"Capurso":(16.920,41.046),"Toritto":(16.680,40.997),"Casamassima":(16.920,40.956),
 "Cassano delle Murge":(16.767,40.891),"Acquaviva delle Fonti":(16.842,40.897),"Corato":(16.411,41.152),
 "Bisceglie":(16.502,41.241),"Matera":(16.604,40.666)}
groups = {"Bitonto":(16.691,41.108),"S. Paolo":(16.820,41.112),"Ceglie":(16.857,41.066),"Triggiano":(16.925,41.066),
 "Palo del Colle":(16.703,41.056),"Bitetto":(16.748,41.040),"Mola di Bari":(17.087,41.060)}
modugno = (16.782,41.084)
partners = {"Potenza":(15.805,40.640),"Massafra":(17.112,40.588)}
labels = {  # name: (dx, dy, anchor)
 "Bari":(12,-14,"start"),"Mola di Bari":(0,32,"middle"),"Corato":(0,-16,"middle"),
 "Bisceglie":(14,6,"start"),"Matera":(16,6,"start"),"Acquaviva delle Fonti":(14,22,"start"),
 "Giovinazzo":(-14,-8,"end"),"Casamassima":(16,6,"start"),"Toritto":(-14,12,"end"),
}
def lbl(name, x, y, size=24, weight=700, fill="#2a2d2f"):
    dx, dy, a = labels.get(name, (14, 6, "start"))
    return f'<text x="{x+dx:.1f}" y="{y+dy:.1f}" text-anchor="{a}" font-size="{size}" font-weight="{weight}" fill="{fill}" class="halo">{name}</text>'

g = []
for n, (lo, la) in members.items():
    x, y = xy(lo, la)
    g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#585e62"/>')
    if n in labels: g.append(lbl(n, x, y))
for n, (lo, la) in groups.items():
    x, y = xy(lo, la)
    g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="#fff" stroke="#e74759" stroke-width="3"/><circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#e74759"/>')
    if n in labels: g.append(lbl(n, x, y))
mx, my = xy(*modugno)
arcs = []
for n, (lo, la) in partners.items():
    x, y = xy(lo, la)
    cx_, cy_ = (mx + x)/2, (my + y)/2 - 120 if n == "Potenza" else (my + y)/2
    if n == "Massafra": cx_ += 160
    arcs.append(f'<path d="M{mx:.1f},{my:.1f} Q{cx_:.1f},{cy_:.1f} {x:.1f},{y:.1f}" fill="none" stroke="#e74759" stroke-width="4" stroke-linecap="round" stroke-dasharray=".1 12"/>')
    g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="26" fill="#e74759" opacity=".16"/><circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="#e74759" stroke="#fff" stroke-width="4"/>')
    g.append(f'<text x="{x:.1f}" y="{y-36:.1f}" text-anchor="middle" font-size="34" font-weight="800" fill="#1c1f21" class="halo">{n}</text>')
g.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="30" fill="#e74759" opacity=".16"/><circle cx="{mx:.1f}" cy="{my:.1f}" r="13" fill="#e74759" stroke="#fff" stroke-width="4"/>')
g.append(f'<text x="{mx-24:.1f}" y="{my-50:.1f}" text-anchor="end" font-size="38" font-weight="800" fill="#1c1f21" class="halo">Modugno</text>')

px, py = xy(16.30, 41.00); bx, by = xy(16.05, 40.42)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
@font-face{{font-family:M;src:url(file:///home/claude/fromtheheelofitaly/static/fonts/manrope-latin-700-normal.woff2);font-weight:700}}
@font-face{{font-family:M;src:url(file:///home/claude/fromtheheelofitaly/static/fonts/manrope-latin-800-normal.woff2);font-weight:800}}
@font-face{{font-family:M;src:url(file:///home/claude/fromtheheelofitaly/static/fonts/manrope-latin-500-normal.woff2);font-weight:500}}
text{{font-family:M,sans-serif}}
.halo{{paint-order:stroke;stroke:#f7f7f6;stroke-width:7px;stroke-linejoin:round}}
.sea{{font-size:22px;font-weight:500;fill:#8a949a;letter-spacing:6px;font-style:italic}}
.reg{{font-size:22px;font-weight:800;fill:#c5c9cb;letter-spacing:9px}}
</style>
<rect width="{W}" height="{H}" fill="#e2e6e9"/>
<path d="{land}" fill="#f7f7f6" stroke="#cfd3d6" stroke-width="1.5"/>
<path d="{muni}" fill="none" stroke="#e4e5e3" stroke-width="1.3"/>
<path d="{regline}" fill="none" stroke="#c9cdd0" stroke-width="2.2"/>
<text x="{W-60}" y="80" text-anchor="end" class="sea">ADRIATIC SEA</text>
<text x="{W-70}" y="{H-60}" text-anchor="end" class="sea">GULF OF TARANTO</text>
<text x="{px:.0f}" y="{py:.0f}" class="reg" text-anchor="middle">PUGLIA</text>
<text x="{xy(16.05,40.48)[0]:.0f}" y="{xy(16.05,40.48)[1]:.0f}" class="reg" text-anchor="middle">BASILICATA</text>
{"".join(arcs)}
{"".join(g)}
</svg>'''
open("/tmp/mapgen/map.svg","w").write(svg)
