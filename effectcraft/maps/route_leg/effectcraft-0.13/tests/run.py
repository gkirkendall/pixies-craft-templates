#!/usr/bin/env python3
"""MAP1 test for Route Leg (craft-templates PLAN.md, MAP1 "Test"). Free: no GPU, no paid service.

  python3 effectcraft/maps/route_leg/effectcraft-0.13/tests/run.py --effectcraft-cli PATH [--clip CLIP.mp4]

Draws the example legs with tools/maps.py, renders them with tools/render.py, and checks:
- each pin, found in the last frame by its colour, re-projects to its stop's GPS position within 1 % of the frame;
- the line reaches both pins;
- "© OpenStreetMap" is drawn on exactly the maps made with OpenStreetMap data;
- the corner card is transparent outside its frame;
- the short-leg rule skips a leg below --min-leg-km.
The corner card is also laid over the start of a clip (ffmpeg): --clip, or a test pattern. Results go to tests/out/ and a contact sheet
tests/out/sheet.png. Names are checked by eye on the sheet.
"""
import argparse
import json
import math
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE.parent
ROOT = next(p for p in TEMPLATE.parents if (p / "tools" / "render.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from fontcheck import font_checks  # noqa: E402
import maps  # noqa: E402

OUT = HERE / "out"
STOPS = TEMPLATE / "examples" / "australia.stops.json"
PIN, LINE = (255, 0, 255), (0, 200, 0)   # test colours found nowhere on the maps
END = 4.5                                 # a time after everything has appeared


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr or r.stdout}")
    return r.stdout


def blobs(img, colour, tol=40):
    """Centres of the separate patches of one colour (flood fill on a coarse mask)."""
    w, h = img.size
    px = img.load()
    hit = {(x, y) for y in range(0, h, 2) for x in range(0, w, 2) if sum(abs(a - b) for a, b in zip(px[x, y][:3], colour)) < tol}
    out = []
    while hit:
        stack, part = [hit.pop()], []
        while stack:
            x, y = stack.pop()
            part.append((x, y))
            for n in ((x + 2, y), (x - 2, y), (x, y + 2), (x, y - 2)):
                if n in hit:
                    hit.remove(n)
                    stack.append(n)
        if len(part) > 8:
            out.append((sum(p[0] for p in part) / len(part), sum(p[1] for p in part) / len(part), len(part)))
    return out


def to_lonlat(view, x, y):
    mx, my = view.x0 + x * view.m_per_px, view.y1 - y * view.m_per_px
    return math.degrees(mx / maps.EARTH_R), math.degrees(2 * math.atan(math.exp(my / maps.EARTH_R)) - math.pi / 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--effectcraft-cli", default="effectcraft-cli")
    ap.add_argument("--clip", type=pathlib.Path, help="a 1024x576 clip to lay the corner card over (default: a test pattern)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    stops = maps.read_stops(STOPS)
    results, sheet = [], []

    def check(name, ok, detail):
        results.append((name, ok, detail))
        print(("PASS " if ok else "FAIL ") + name + ": " + detail)

    for variant in ("16x9", "9x16"):
        run([sys.executable, ROOT / "tools" / "maps.py", "route-legs", "--stops", STOPS, "--out", OUT / "maps", "--variant", variant])
    # The short-leg rule: leg 1 (Port Campbell to Point Ritchie, 43 km) is drawn at the default 25 km and skipped at 50 km.
    short = run([sys.executable, ROOT / "tools" / "maps.py", "route-legs", "--stops", STOPS, "--out", OUT / "short",
                 "--variant", "16x9", "--min-leg-km", "50"])
    check("short-leg rule", (OUT / "maps" / "leg01_16x9.values.json").exists() and not (OUT / "short" / "leg01_16x9.values.json").exists(),
          "43 km leg drawn at --min-leg-km 25, skipped at 50" + (f" ({short.strip().splitlines()[0]})" if short.strip() else ""))

    cases = [("leg02", "16x9", False), ("leg02", "9x16", False), ("leg05", "16x9", False), ("leg01", "16x9", False), ("leg02", "16x9", True)]
    for leg, variant, inset in cases:
        n = int(leg[3:])
        values = json.loads((OUT / "maps" / f"{leg}_{variant}.values.json").read_text())
        values.update({"Pin Colour": "#ff00ff", "Line Colour": "#00c800", "Corner Inset": inset})
        tag = f"{leg}_{variant}" + ("_inset" if inset else "")
        vfile = OUT / "maps" / f"{tag}.test.values.json"
        vfile.write_text(json.dumps(values, ensure_ascii=False))
        frame = OUT / f"{tag}.png"
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", variant, "--values", vfile, "--out", frame,
             "--frame", END, "--effectcraft-cli", a.effectcraft_cli])
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", variant, "--values", vfile,
             "--out", OUT / f"{tag}.mov", "--effectcraft-cli", a.effectcraft_cli])
        img = Image.open(frame).convert("RGBA")
        w, h = img.size
        size = maps.VARIANTS[variant]
        view = maps.leg_view(stops[n - 1], stops[n], size)
        k, ox, oy = (0.36, w - 48 - w * 0.36, 48) if inset else (1, 0, 0)

        # Pins: the two largest magenta patches, mapped back to map pixels and then to GPS.
        pins = sorted(blobs(img, PIN), key=lambda b: -b[2])[:2]
        errs = []
        for stop in (stops[n - 1], stops[n]):
            ex, ey = view.px(stop["lon"], stop["lat"])
            best = min(pins, key=lambda b: math.hypot((b[0] - ox) / k - ex, (b[1] - oy) / k - ey)) if pins else None
            if best is None:
                errs.append((float("inf"), float("inf")))
                continue
            lon, lat = to_lonlat(view, (best[0] - ox) / k, (best[1] - oy) / k)
            km = maps.haversine_km({"lat": lat, "lon": lon}, stop)
            km_per_frame = view.m_per_px * max(size) * math.cos(math.radians(stop["lat"])) / 1000
            errs.append((km / km_per_frame * 100, km))
        check(f"{tag} pins on GPS", len(pins) == 2 and max(e[0] for e in errs) <= 1.0,
              "pin to GPS " + ", ".join(f"{p:.2f} % of the frame ({km:.2f} km)" for p, km in errs))

        # The line reaches each pin: line-coloured pixels within 30 px (scaled) of each pin centre.
        line = blobs(img, LINE)
        px = img.load()
        near = []
        for bx, by, _ in pins:
            r = 30 * (0.6 if inset else 1)
            near.append(any(sum(abs(c - d) for c, d in zip(px[x, y][:3], LINE)) < 60
                            for x in range(int(bx - r), int(bx + r)) for y in range(int(by - r), int(by + r))
                            if 0 <= x < w and 0 <= y < h and math.hypot(x - bx, y - by) <= r))
        check(f"{tag} line meets pins", bool(line) and len(near) == 2 and all(near), f"{len(line)} line patch(es); near pins {near}")

        # The OSM credit: drawn exactly when the map has OpenStreetMap data (maps.py writes the query beside such maps).
        osm = (OUT / "maps" / f"{leg}_{variant}.overpass.txt").exists()
        no_credit = dict(values, **{"Map Credit": ""})
        (OUT / "maps" / f"{tag}.nocredit.json").write_text(json.dumps(no_credit, ensure_ascii=False))
        bare = OUT / f"{tag}_nocredit.png"
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", variant, "--values",
             OUT / "maps" / f"{tag}.nocredit.json", "--out", bare, "--frame", END, "--effectcraft-cli", a.effectcraft_cli])
        from PIL import ImageChops
        corner = (int(ox + w * k * 0.6), int(oy + h * k * 0.9), int(ox + w * k), int(oy + h * k))
        drawn = ImageChops.difference(img.convert("RGB").crop(corner), Image.open(bare).convert("RGB").crop(corner)).getbbox() is not None
        check(f"{tag} OSM credit", drawn == osm and (values["Map Credit"] == maps.OSM_CREDIT) == osm,
              f"OSM data {osm}, credit text {values['Map Credit']!r}, drawn {drawn}")

        if inset:
            alpha = img.getchannel("A")
            card = (int(ox - 8), int(oy - 8), int(ox + w * k + 8), int(oy + h * k + 8))
            outside = Image.new("L", img.size, 255)
            ImageDraw.Draw(outside).rectangle(card, fill=0)
            leak = ImageChops.multiply(alpha, outside).getbbox()
            inner = alpha.crop((card[0] + 12, card[1] + 12, card[2] - 12, card[3] - 12)).getextrema()
            check(f"{tag} transparent outside the card", leak is None and inner[0] == 255,
                  f"alpha outside: {'none' if leak is None else leak}; inside min {inner[0]}")
            clip = a.clip
            if clip is None:   # no clip given: a 1024x576 moving test pattern, so the check always runs
                clip = OUT / "test_clip.mp4"
                run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1024x576:r=24:d=6", "-pix_fmt", "yuv420p", clip])
            clip_out = OUT / "inset_over_clip.mp4"
            run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-i", OUT / f"{tag}.mov", "-filter_complex",
                 "[1:v]scale=iw*1024/1920:-1[o];[0:v][o]overlay=0:0:shortest=1", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                 "-crf", "18", "-c:a", "copy", clip_out])
            check("corner card over a clip", clip_out.exists(), str(clip_out.relative_to(ROOT)))
        sheet.append((tag, img))

    # Each font control takes any font and reaches only its own text (tools/fontcheck.py), the credit filled so it shows.
    def still(values, tag):
        vfile = OUT / "maps" / f"{tag}.json"   # beside the map picture the values name
        vfile.write_text(json.dumps(values, ensure_ascii=False))
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", "16x9", "--values", vfile, "--out", OUT / f"{tag}.png",
             "--frame", END, "--effectcraft-cli", a.effectcraft_cli])
        return Image.open(OUT / f"{tag}.png")
    base = dict(json.loads((OUT / "maps" / "leg02_16x9.values.json").read_text()), **{"Map Credit": maps.OSM_CREDIT})
    for name, ok, detail in font_checks(still, {"Name Font": ["From Name", "To Name"], "Credit Font": ["Map Credit"]}, base):
        check(name, ok, detail)

    # Contact sheet: each last frame over a dark background, for the names and the look.
    tiles = []
    for tag, img in sheet:
        bg = Image.new("RGBA", img.size, (60, 70, 60, 255))
        bg.alpha_composite(img)
        t = bg.convert("RGB")
        t.thumbnail((640, 640))
        tiles.append((tag, t))
    W = sum(t.width for _, t in tiles) + 10 * (len(tiles) + 1)
    H = max(t.height for _, t in tiles) + 40
    s = Image.new("RGB", (W, H), (255, 255, 255))
    x = 10
    for tag, t in tiles:
        s.paste(t, (x, 30))
        ImageDraw.Draw(s).text((x, 8), tag, fill=(0, 0, 0))
        x += t.width + 10
    s.save(OUT / "sheet.png")
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks pass; sheet {OUT / 'sheet.png'}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
