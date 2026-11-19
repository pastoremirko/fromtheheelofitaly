import json, math
W, H = 1600, 1200
LON0 = 15.65
KX = W / 3.6
LAT0 = 40.93
K = KX / math.cos(math.radians(LAT0))
LAT_TOP = LAT0 + (H / 2) / K
def xy(lon, lat): return ((lon - LON0) * KX + W/2, (LAT_TOP - lat) * K)

def rings(geom):
    if geom["type"] == "Polygon": return geom["coordinates"]
    if geom["type"] == "MultiPolygon": return [r for poly in geom["coordinates"] for r in poly]
    return []
def path(geom, simplify=1.2):
    out = []
    for ring in rings(geom):
        pts = [xy(*p[:2]) for p in ring]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) < -200 or min(xs) > W+200 or max(ys) < -200 or min(ys) > H+200: continue
        keep = [pts[0]]
        for p in pts[1:]:
            if abs(p[0]-keep[-1][0]) + abs(p[1]-keep[-1][1]) >= simplify: keep.append(p)
        if len(keep) > 2: out.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in keep) + "Z")
    return "".join(out)

regions = json.load(open("/tmp/geo/limits_IT_regions.geojson"))["features"]
land = "".join(path(f["geometry"]) for f in regions if f["properties"]["reg_name"] in ("Puglia","Basilicata","Campania","Calabria","Molise","Lazio","Abruzzo"))
regline = "".join(path(f["geometry"]) for f in regions if f["properties"]["reg_name"] in ("Puglia","Basilicata","Campania","Molise","Calabria"))
muni = ""
for r in (15, 16, 17):
    for f in json.load(open(f"/tmp/geo/limits_R_{r}_municipalities.geojson"))["features"]:
        muni += path(f["geometry"], simplify=2.2)

modugno = (16.782, 41.084)
targets = {"Giugliano": (14.196, 40.928, "middle", -40), "Potenza": (15.805, 40.640, "middle", -40), "Massafra": (17.112, 40.588, "middle", -40)}
mx, my = xy(*modugno)
arcs, marks = [], []
for n, (lo, la, anc, dy) in targets.items():
    x, y = xy(lo, la)
    if n == "Giugliano": c = ((mx + x)/2, min(my, y) - 230)
    elif n == "Potenza": c = ((mx + x)/2 - 40, (my + y)/2 - 110)
    else: c = ((mx + x)/2 + 130, (my + y)/2)
    arcs.append(f'<path d="M{mx:.1f},{my:.1f} Q{c[0]:.1f},{c[1]:.1f} {x:.1f},{y:.1f}" fill="none" stroke="#e74759" stroke-width="4.5" stroke-linecap="round" stroke-dasharray=".1 13"/>')
    marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="40" fill="#f4b41a" opacity=".22"/>'
                 f'<circle cx="{x:.1f}" cy="{y:.1f}" r="21" fill="#f4b41a" stroke="#fff" stroke-width="5"/>'
                 f'<text x="{x:.1f}" y="{y+dy-8:.1f}" text-anchor="{anc}" font-size="38" font-weight="800" fill="#1c1f21" class="halo">{n}</text>')
marks.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="32" fill="#e74759" opacity=".18"/><circle cx="{mx:.1f}" cy="{my:.1f}" r="15" fill="#e74759" stroke="#fff" stroke-width="5"/>'
             f'<text x="{mx:.1f}" y="{my-40:.1f}" text-anchor="middle" font-size="40" font-weight="800" fill="#1c1f21" class="halo">Modugno</text>')
def t(lon, lat, s, cls): x, y = xy(lon, lat); return f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="middle" class="{cls}">{s}</text>'
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
@font-face{{font-family:M;src:url(file:///home/claude/fromtheheelofitaly/static/fonts/manrope-latin-500-normal.woff2);font-weight:500}}
@font-face{{font-family:M;src:url(file:///home/claude/fromtheheelofitaly/static/fonts/manrope-latin-800-normal.woff2);font-weight:800}}
text{{font-family:M,sans-serif}}
.halo{{paint-order:stroke;stroke:#f7f7f6;stroke-width:8px;stroke-linejoin:round}}
.sea{{font-size:22px;font-weight:500;fill:#8a949a;letter-spacing:6px;font-style:italic}}
.reg{{font-size:22px;font-weight:800;fill:#c3c7c9;letter-spacing:9px}}
</style>
<rect width="{W}" height="{H}" fill="#e2e6e9"/>
<path d="{land}" fill="#f7f7f6" stroke="#cfd3d6" stroke-width="1.5"/>
<path d="{muni}" fill="none" stroke="#e7e8e6" stroke-width="1.1"/>
<path d="{regline}" fill="none" stroke="#c9cdd0" stroke-width="2.2"/>
{t(17.05, 41.75, "ADRIATIC SEA", "sea")}
{t(14.45, 40.25, "TYRRHENIAN SEA", "sea")}
{t(16.88, 40.08, "GULF OF TARANTO", "sea")}
{t(14.85, 41.22, "CAMPANIA", "reg")}
{t(16.05, 40.30, "BASILICATA", "reg")}
{t(16.20, 41.30, "PUGLIA", "reg")}
{"".join(arcs)}{"".join(marks)}
</svg>'''
open("/tmp/mapgen/map2.svg", "w").write(svg)
