#!/usr/bin/env python3
"""Map pictures for the map templates, and their fill: from a list of stops to rendered map cards.

  python3 tools/maps.py fetch                                     download the Natural Earth data once (about 52 MB, into data/)
  python3 tools/maps.py route-legs --stops stops.json --out DIR --variant 16x9 [--render]
  python3 tools/maps.py locator --stops stops.json --stop 0 --out DIR --variant 16x9 [--render]

stops.json is a list in travel order: [{"name": "Point Ritchie", "subtitle": "VIC", "lat": -38.40, "lon": 142.51}, …].
For each card the command writes the map picture (map_*.png), a values file for the template (*.values.json) and, for maps with
OpenStreetMap detail, the Overpass query used (*.overpass.txt). With --render it also renders each card through tools/render.py.

Map data: Natural Earth 1:10m (public domain), and on legs shorter than --osm-km, OpenStreetMap roads, towns and park outlines fetched
from an Overpass server (© OpenStreetMap contributors, ODbL); see PLAN.md, "MAP1".
"""
import argparse
import hashlib
import http.client
import json
import math
import pathlib
import subprocess
import sys
import time
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
NE_COMMIT = "789c9904087846cc3361302857aa2e76b0ae71ff"  # nvkelso/natural-earth-vector, latest change to geojson/ on 2026-10-21
NE_FILES = {  # file: SHA-256 at NE_COMMIT
    "ne_10m_land.geojson": "1ac90796408bc6ad6911d69448485d3c4dbf2190370080368a09976e1c9f7416",
    "ne_10m_lakes.geojson": "2d036f53dedec578001c5c30c2959ee7d4eebc1306900fa4367c49929ec8f2d9",
    "ne_10m_admin_0_countries.geojson": "239eec57ac17f100a11e2536cffc56752c318b50ae765b0918ff7aab4ce8f255",
    "ne_10m_admin_0_boundary_lines_land.geojson": "74d9c16229c095fde65943a9919e337682f044bcebccb120764f38edf3b70f4a",
    "ne_10m_admin_1_states_provinces_lines.geojson": "1a1f30ccaaf4cc9c4bde34266f0b8cbb955d3a4cf254b756912255f2ec7c75b6",
}
USER_AGENT = "craft-templates-maps/0.1 (+https://github.com/gkirkendall/pixies-craft-templates)"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(_args):
    folder = DATA / "naturalearth"
    folder.mkdir(parents=True, exist_ok=True)
    for name, expected in NE_FILES.items():
        path = folder / name
        if not path.is_file():
            url = f"https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{NE_COMMIT}/geojson/{name}"
            print(f"downloading {name}", flush=True)
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=120) as r, open(path.with_suffix(".part"), "wb") as f:
                while block := r.read(1 << 20):
                    f.write(block)
            path.with_suffix(".part").rename(path)
        digest = sha256(path)
        if expected and digest != expected:
            sys.exit(f"{name}: SHA-256 {digest} does not match the recorded {expected}; delete it and fetch again")
        print(f"{name}  {path.stat().st_size / 1e6:.1f} MB  sha256 {digest}")


# Starting look (PLAN.md: judged by eye, then options)
COLOURS = {"sea": "#b9d3e3", "land": "#f2ede4", "coast": "#8fa9b8", "state": "#b8ae9f", "country": "#9c9285",
           "park": "#d5e3c6", "road_casing": "#cdbea7", "road": "#ffffff", "town": "#8c8273"}
VARIANTS = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
SUPERSAMPLE = 2          # drawn at twice the size, then reduced, for smooth edges
EARTH_R = 6378137.0      # Web Mercator sphere radius (m)
MIN_SPAN_KM = 150        # a leg's map is at least this wide: the 1:10m coastline turns blocky closer in
LOCATOR_SCALE = 3        # the locator's map is drawn at 3x the frame, so its zoom stays sharp
OSM_CREDIT = "© OpenStreetMap"


def merc(lon, lat):
    lat = max(min(lat, 85.0), -85.0)
    return EARTH_R * math.radians(lon), EARTH_R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def haversine_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


class View:
    """A Web Mercator window: x0, y1 is the top-left corner in metres, m_per_px the scale, size the picture in pixels."""

    def __init__(self, cx, cy, m_per_px, size):
        self.m_per_px, self.size = m_per_px, size
        self.x0, self.y1 = cx - size[0] / 2 * m_per_px, cy + size[1] / 2 * m_per_px

    @classmethod
    def fit(cls, xs, ys, size, margin):
        """The smallest view holding every point with this fraction of the frame left free on each side."""
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        usable = (size[0] * (1 - 2 * margin), size[1] * (1 - 2 * margin))
        m = max((max(xs) - min(xs)) / usable[0], (max(ys) - min(ys)) / usable[1], 1e-9)
        return cls(cx, cy, m, size)

    def px(self, lon, lat):
        x, y = merc(lon, lat)
        return (x - self.x0) / self.m_per_px, (self.y1 - y) / self.m_per_px

    def lonlat_bounds(self):
        x1, y0 = self.x0 + self.size[0] * self.m_per_px, self.y1 - self.size[1] * self.m_per_px
        lon = lambda x: math.degrees(x / EARTH_R)
        lat = lambda y: math.degrees(2 * math.atan(math.exp(y / EARTH_R)) - math.pi / 2)
        return lon(self.x0), lat(y0), lon(x1), lat(self.y1)


_GEO = {}


def geo(name):
    if name not in _GEO:
        path = DATA / "naturalearth" / name
        if not path.is_file():
            sys.exit(f"{path} is missing: run `python3 tools/maps.py fetch` first")
        _GEO[name] = json.loads(path.read_text())["features"]
    return _GEO[name]


def rings(geometry):
    """Every ring of a (Multi)Polygon or (Multi)LineString as a list of [lon, lat] points."""
    if not geometry:  # a few Natural Earth features have no geometry
        return []
    t, c = geometry["type"], geometry["coordinates"]
    return {"Polygon": c, "MultiPolygon": [r for poly in c for r in poly], "LineString": [c],
            "MultiLineString": c}.get(t, [])


def ring_hits(ring, bounds):
    lo0, la0, lo1, la1 = bounds
    los, las = [p[0] for p in ring], [p[1] for p in ring]
    return max(los) >= lo0 and min(los) <= lo1 and max(las) >= la0 and min(las) <= la1


def draw_rings(draw, view, features, bounds, s, fill=None, outline=None, width=1, dash=None, close=True):
    for f in features:
        for ring in rings(f["geometry"]):
            if len(ring) < 2 or not ring_hits(ring, bounds):
                continue
            pts = [tuple(c * s for c in view.px(lon, lat)) for lon, lat in ring]
            if fill and close and len(pts) > 2:
                draw.polygon(pts, fill=fill)
            if outline:
                if dash:
                    dashed_line(draw, pts, outline, width * s, dash[0] * s, dash[1] * s)
                else:
                    draw.line(pts + ([pts[0]] if close else []), fill=outline, width=round(width * s), joint="curve")


def dashed_line(draw, pts, colour, width, on, off):
    carry, drawing = 0.0, True
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        pos = 0.0
        while pos < seg:
            step = min((on if drawing else off) - carry, seg - pos)
            if drawing:
                a, b = pos / seg, (pos + step) / seg
                draw.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)],
                          fill=colour, width=round(width))
            pos += step
            carry += step
            if carry >= (on if drawing else off) - 1e-9:
                carry, drawing = 0.0, not drawing


def overpass(view, url, out_txt):
    """Main roads, towns and protected areas in the view, from an Overpass server; answers are cached in data/osm/."""
    lo0, la0, lo1, la1 = view.lonlat_bounds()
    bbox = f"{la0:.5f},{lo0:.5f},{la1:.5f},{lo1:.5f}"
    span_km = (view.size[0] * view.m_per_px) * math.cos(math.radians((la0 + la1) / 2)) / 1000
    roads = "motorway|trunk|primary" if span_km < 120 else "motorway|trunk"  # a wide view of a city has too many primary roads
    # Roads come back without tags (out skel) to keep the answer small; parks and towns with theirs.
    query = (f"[out:json][timeout:120];way[highway~\"^({roads})$\"]({bbox});out skel geom;"
             f"node[place~\"^(city|town)$\"]({bbox});out body;"
             f"(way[boundary=national_park]({bbox});relation[boundary=national_park]({bbox});"
             f"way[leisure=nature_reserve]({bbox});relation[leisure=nature_reserve]({bbox}););out geom;")
    out_txt.write_text(f"# Overpass query used for {out_txt.stem} (data © OpenStreetMap contributors, ODbL 1.0)\n{query}\n")
    cache = DATA / "osm" / (hashlib.sha256(query.encode()).hexdigest()[:20] + ".json")
    if cache.is_file():
        return json.loads(cache.read_text())["elements"]
    cache.parent.mkdir(parents=True, exist_ok=True)
    tries = 5
    for attempt in range(tries):  # the policy: one query at a time; after a 429 or 406 (or an overloaded 502-504), wait at least 30 s
        request = urllib.request.Request(url, data=urllib.parse.urlencode({"data": query}).encode(), headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=180) as r:
                body = r.read()
            cache.write_bytes(body)
            return json.loads(body)["elements"]
        except urllib.error.HTTPError as e:
            if e.code not in (429, 406, 502, 503, 504) or attempt == tries - 1:
                raise
            print(f"Overpass answered {e.code}; waiting 60 s", flush=True)
            time.sleep(60)
        except (http.client.IncompleteRead, ConnectionError, TimeoutError) as e:  # a busy server can drop a long answer
            if attempt == tries - 1:
                raise
            print(f"Overpass answer cut short ({type(e).__name__}); waiting 60 s", flush=True)
            time.sleep(60)


def join_rings(parts):
    """Closed rings from the open way pieces of a park's outline (a large park relation stores its outer edge in many ways)."""
    key = lambda p: (round(p["lat"], 7), round(p["lon"], 7))
    parts = [list(g) for g in parts if len(g) > 1]
    done = [g for g in parts if key(g[0]) == key(g[-1])]
    open_ = [g for g in parts if key(g[0]) != key(g[-1])]
    while open_:
        ring = open_.pop()
        grown = True
        while grown and key(ring[0]) != key(ring[-1]):
            grown = False
            for i, g in enumerate(open_):
                if key(g[0]) == key(ring[-1]):
                    ring += g[1:]
                elif key(g[-1]) == key(ring[-1]):
                    ring += g[::-1][1:]
                elif key(g[-1]) == key(ring[0]):
                    ring = g[:-1] + ring
                elif key(g[0]) == key(ring[0]):
                    ring = g[::-1][:-1] + ring
                else:
                    continue
                open_.pop(i)
                grown = True
                break
        if key(ring[0]) == key(ring[-1]):
            done.append(ring)
    return done


def draw_osm(draw, view, elements, s):
    def line(geom):
        return [tuple(c * s for c in view.px(p["lon"], p["lat"])) for p in geom]
    for e in elements:  # parks first, under the roads
        if e.get("tags", {}).get("boundary") == "national_park" or e.get("tags", {}).get("leisure") == "nature_reserve":
            ways = [e["geometry"]] if e["type"] == "way" else [m["geometry"] for m in e.get("members", []) if m.get("role") == "outer" and "geometry" in m]
            for g in join_rings(ways):
                if len(g) > 3:
                    draw.polygon(line(g), fill=COLOURS["park"])
    roads = [line(e["geometry"]) for e in elements if e["type"] == "way" and not e.get("tags") and "geometry" in e]  # out skel
    for pts in roads:
        draw.line(pts, fill=COLOURS["road_casing"], width=round(4 * s), joint="curve")
    for pts in roads:
        draw.line(pts, fill=COLOURS["road"], width=round(2 * s), joint="curve")
    for e in elements:
        if e["type"] == "node" and e.get("tags", {}).get("place") in ("city", "town"):
            x, y = (c * s for c in view.px(e["lon"], e["lat"]))
            r = (5 if e["tags"]["place"] == "city" else 3.5) * s
            draw.ellipse([x - r, y - r, x + r, y + r], fill=COLOURS["town"])


def draw_map(view, osm=None):
    s = SUPERSAMPLE
    size = (view.size[0] * s, view.size[1] * s)
    img = Image.new("RGB", size, COLOURS["sea"])
    draw = ImageDraw.Draw(img)
    pad = 0.05 * max(view.lonlat_bounds()[2] - view.lonlat_bounds()[0], 1)
    lo0, la0, lo1, la1 = view.lonlat_bounds()
    bounds = (lo0 - pad, la0 - pad, lo1 + pad, la1 + pad)
    draw_rings(draw, view, geo("ne_10m_land.geojson"), bounds, s, fill=COLOURS["land"])
    if osm:
        draw_osm(draw, view, osm, s)
    draw_rings(draw, view, geo("ne_10m_lakes.geojson"), bounds, s, fill=COLOURS["sea"])
    draw_rings(draw, view, geo("ne_10m_land.geojson"), bounds, s, outline=COLOURS["coast"], width=1.5)
    draw_rings(draw, view, geo("ne_10m_admin_1_states_provinces_lines.geojson"), bounds, s, outline=COLOURS["state"],
               width=1.5, dash=(8, 6), close=False)
    draw_rings(draw, view, geo("ne_10m_admin_0_boundary_lines_land.geojson"), bounds, s, outline=COLOURS["country"],
               width=2.5, close=False)
    return img.resize(view.size, Image.LANCZOS)


def read_stops(path):
    stops = json.loads(pathlib.Path(path).read_text())
    for i, st in enumerate(stops):
        missing = [k for k in ("name", "lat", "lon") if st.get(k) in (None, "")]
        if missing:
            sys.exit(f"{path}: stop {i} has no {', '.join(missing)}")
    return stops


def leg_view(a, b, size):
    """Both stops inside the central part of the frame, at least MIN_SPAN_KM across."""
    (ax, ay), (bx, by) = merc(a["lon"], a["lat"]), merc(b["lon"], b["lat"])
    view = View.fit([ax, bx], [ay, by], size, margin=0.22)
    lat = math.radians((a["lat"] + b["lat"]) / 2)
    ground_km = view.m_per_px * size[0] * math.cos(lat) / 1000  # Mercator metres shrink by cos(latitude) on the ground
    if ground_km < MIN_SPAN_KM:
        view = View((ax + bx) / 2, (ay + by) / 2, view.m_per_px * MIN_SPAN_KM / ground_km, size)
    return view


def render_card(template, variant, values, out, a):
    cmd = [sys.executable, str(ROOT / "tools" / "render.py"), template, "--variant", variant, "--values", str(values), "--out", str(out)]
    if a.effectcraft_cli:
        cmd += ["--effectcraft-cli", a.effectcraft_cli]
    subprocess.run(cmd, check=True)


def route_legs(a):
    stops, size, out = read_stops(a.stops), VARIANTS[a.variant], pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for i, (s0, s1) in enumerate(zip(stops, stops[1:]), 1):
        km = haversine_km(s0, s1)
        stem = f"leg{i:02d}_{a.variant}"
        if km < a.min_leg_km:
            print(f"{stem}: {s0['name']} -> {s1['name']} is {km:.0f} km, under {a.min_leg_km} km: no route card")
            continue
        view = leg_view(s0, s1, size)
        osm = overpass(view, a.overpass_url, out / f"{stem}.overpass.txt") if km < a.osm_km else None
        picture = out / f"map_{stem}.png"
        draw_map(view, osm).save(picture)
        values = {"Map": picture.name, "From Position": [round(c, 1) for c in view.px(s0["lon"], s0["lat"])],
                  "To Position": [round(c, 1) for c in view.px(s1["lon"], s1["lat"])], "From Name": s0["name"],
                  "To Name": s1["name"], "Map Credit": OSM_CREDIT if osm else "", "Corner Inset": a.inset}
        (out / f"{stem}.values.json").write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n")
        print(f"{stem}: {s0['name']} -> {s1['name']}, {km:.0f} km{', with OSM detail' if osm else ''}")
        if a.render:
            render_card("effectcraft/maps/route_leg", a.variant, out / f"{stem}.values.json",
                        out / f"{stem}{'_inset' if a.inset else ''}.mov", a)


COAST_KM = 25  # a coastal stop can sit just offshore of Natural Earth's 1:10m coast; take the nearest country within this distance


def country_of(stop):
    """The Natural Earth country holding the stop (or the nearest one within COAST_KM), and the bounds of its main land (islands
    far offshore left out)."""
    best = None
    for f in geo("ne_10m_admin_0_countries.geojson"):
        g = f["geometry"]
        if not g:
            continue
        polys = [p[0] for p in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"])]
        for ring in polys:
            lons, lats = [q[0] for q in ring], [q[1] for q in ring]
            if not (min(lons) - 0.5 <= stop["lon"] <= max(lons) + 0.5 and min(lats) - 0.5 <= stop["lat"] <= max(lats) + 0.5):
                continue
            d = 0 if inside(stop["lon"], stop["lat"], ring) else min(haversine_km(stop, {"lat": lat, "lon": lon}) for lon, lat in ring)
            if best is None or d < best[0]:
                best = (d, f, polys, ring)
        if best and best[0] == 0:
            break
    if best is None or best[0] > COAST_KM:
        sys.exit(f"stop {stop['name']} ({stop['lat']}, {stop['lon']}) is not within {COAST_KM} km of any Natural Earth country")
    _, f, polys, ring = best
    area = lambda r: abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(r, r[1:] + r[:1]))) / 2
    big = max(area(r) for r in polys)
    kept = [r for r in polys if area(r) >= 0.01 * big or r is ring]
    return f["properties"].get("NAME", "?"), [p for r in kept for p in r]


def inside(x, y, ring):
    hit = False
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            hit = not hit
    return hit


def locator(a):
    stops, out = read_stops(a.stops), pathlib.Path(a.out)
    stop = stops[a.stop]
    out.mkdir(parents=True, exist_ok=True)
    size = tuple(c * LOCATOR_SCALE for c in VARIANTS[a.variant])
    country, points = country_of(stop)
    xs, ys = zip(*(merc(lon, lat) for lon, lat in points))
    view = View.fit(xs, ys, size, margin=0.08)
    stem = f"locator{a.stop:02d}_{a.variant}"
    picture = out / f"map_{stem}.png"
    draw_map(view).save(picture)
    values = {"Map": picture.name, "Place Position": [round(c, 1) for c in view.px(stop["lon"], stop["lat"])],
              "Zoom": LOCATOR_SCALE, "Place Name": stop["name"], "Subtitle": stop.get("subtitle", ""), "Map Credit": "",
              "Corner Inset": a.inset}
    (out / f"{stem}.values.json").write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n")
    print(f"{stem}: {stop['name']} in {country}")
    if a.render:
        render_card("effectcraft/maps/locator", a.variant, out / f"{stem}.values.json", out / f"{stem}{'_inset' if a.inset else ''}.mov", a)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch", help="download the Natural Earth data into data/naturalearth/")
    for name, helptext in (("route-legs", "a route card for each leg between consecutive stops"),
                           ("locator", "a locator card for one stop")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--stops", required=True, help="stops file (JSON list of name, subtitle, lat, lon)")
        p.add_argument("--out", required=True, help="folder for the pictures, values files and renders")
        p.add_argument("--variant", default="16x9", choices=sorted(VARIANTS))
        p.add_argument("--inset", action="store_true", help="the corner inset instead of the full-screen card")
        p.add_argument("--render", action="store_true", help="also render each card with tools/render.py")
        p.add_argument("--effectcraft-cli", help="path to effectcraft-cli (default: on the PATH)")
        if name == "route-legs":
            p.add_argument("--min-leg-km", type=float, default=25, help="no card for legs shorter than this")
            p.add_argument("--osm-km", type=float, default=200, help="OpenStreetMap detail on legs shorter than this")
            p.add_argument("--overpass-url", default="https://overpass-api.de/api/interpreter",
                           help="Overpass server; commercial use needs a paid or self-hosted one")
        else:
            p.add_argument("--stop", type=int, default=0, help="which stop (0 = the first)")
    a = ap.parse_args()
    {"fetch": fetch, "route-legs": route_legs, "locator": locator}[a.command](a)


if __name__ == "__main__":
    main()
