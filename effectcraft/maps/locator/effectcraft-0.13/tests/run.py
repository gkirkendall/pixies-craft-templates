#!/usr/bin/env python3
"""MAP1 test for Locator (craft-templates PLAN.md, MAP1 "Test"). Free: no GPU, no paid service.

  python3 effectcraft/maps/locator/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Draws the Port Campbell locator map with tools/maps.py, then paints a marker into a copy of the map picture at the stop's GPS
position. After the zoom, the template's pin must sit on that marker within 1 % of the frame: this checks the whole chain (map
picture, Place Position, zoom and inset) against the map itself, not against the numbers that placed the pin. Also checks that the
corner card is transparent outside its frame and that no map credit is drawn (Natural Earth needs none). Results go to tests/out/,
with a contact sheet tests/out/sheet.png; names are checked by eye there.
"""
import argparse
import json
import math
import pathlib
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE.parent
ROOT = next(p for p in TEMPLATE.parents if (p / "tools" / "render.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
from fontcheck import font_checks  # noqa: E402
import maps  # noqa: E402

OUT = HERE / "out"
STOPS = TEMPLATE / "examples" / "australia.stops.json"
MARK, PIN = (255, 0, 255), (0, 200, 0)
END = 4.5


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr or r.stdout}")
    return r.stdout


def centre(img, colour, tol=60):
    px = img.load()
    pts = [(x, y) for y in range(img.height) for x in range(img.width) if sum(abs(a - b) for a, b in zip(px[x, y][:3], colour)) < tol]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), len(pts)) if pts else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--effectcraft-cli", default="effectcraft-cli")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    stop = maps.read_stops(STOPS)[0]
    results, sheet = [], []

    def check(name, ok, detail):
        results.append((name, ok, detail))
        print(("PASS " if ok else "FAIL ") + name + ": " + detail)

    for variant, inset in (("16x9", True), ("16x9", False), ("9x16", False)):
        run([sys.executable, ROOT / "tools" / "maps.py", "locator", "--stops", STOPS, "--stop", "0", "--out", OUT / "maps", "--variant", variant])
        values = json.loads((OUT / "maps" / f"locator00_{variant}.values.json").read_text())
        # The marker: a ring painted into the map picture at the stop's GPS position, with the view maps.py used.
        size = tuple(c * maps.LOCATOR_SCALE for c in maps.VARIANTS[variant])
        _, points = maps.country_of(stop)
        xs, ys = zip(*(maps.merc(lon, lat) for lon, lat in points))
        view = maps.View.fit(xs, ys, size, margin=0.08)
        gx, gy = view.px(stop["lon"], stop["lat"])
        original = values["Map"]
        marked = Image.open(OUT / "maps" / original).convert("RGB")
        ImageDraw.Draw(marked).ellipse((gx - 40, gy - 40, gx + 40, gy + 40), outline=MARK, width=10)
        marked.save(OUT / "maps" / f"marked_{variant}.png")
        tag = f"locator_{variant}" + ("_inset" if inset else "")
        values.update({"Map": f"marked_{variant}.png", "Pin Colour": "#00c800", "Corner Inset": inset})
        vfile = OUT / "maps" / f"{tag}.test.values.json"
        vfile.write_text(json.dumps(values, ensure_ascii=False))
        frame = OUT / f"{tag}.png"
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", variant, "--values", vfile, "--out", frame,
             "--frame", END, "--effectcraft-cli", a.effectcraft_cli])
        plain = dict(values, Map=original)
        (OUT / "maps" / f"{tag}.plain.json").write_text(json.dumps(plain, ensure_ascii=False))
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", variant, "--values", OUT / "maps" / f"{tag}.plain.json",
             "--out", OUT / f"{tag}.mov", "--effectcraft-cli", a.effectcraft_cli])
        img = Image.open(frame).convert("RGBA")
        w, h = img.size
        k = 0.36 if inset else 1
        # The ring's centre is where the map shows the stop; the ring is wider than the pin, so it stays visible around it.
        ring, pin = centre(img, MARK), centre(img, PIN)
        if ring and pin:
            err = math.hypot(ring[0] - pin[0], ring[1] - pin[1]) / (max(w, h) * k) * 100
            check(f"{tag} pin on the map's GPS position", err <= 1.0, f"pin to marker {err:.2f} % of the {'card' if inset else 'frame'}")
        else:
            check(f"{tag} pin on the map's GPS position", False, f"marker found {bool(ring)}, pin found {bool(pin)}")
        ox, oy = (w - 48 - w * k, 48) if inset else (0, 0)
        corner = (int(ox + w * k * 0.6), int(oy + h * k * 0.9), int(ox + w * k), int(oy + h * k))
        credited = dict(plain, **{"Map Credit": maps.OSM_CREDIT})
        (OUT / "maps" / f"{tag}.credit.json").write_text(json.dumps(credited, ensure_ascii=False))
        with_credit, without = OUT / f"{tag}_credit.png", OUT / f"{tag}_plain.png"
        for vf, out in ((OUT / "maps" / f"{tag}.credit.json", with_credit), (OUT / "maps" / f"{tag}.plain.json", without)):
            run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", variant, "--values", vf, "--out", out,
                 "--frame", END, "--effectcraft-cli", a.effectcraft_cli])
        # No credit by default; and the control does draw one when filled (so "none drawn" is a real result).
        drawn = ImageChops.difference(Image.open(with_credit).convert("RGB").crop(corner), Image.open(without).convert("RGB").crop(corner)).getbbox()
        check(f"{tag} no credit on a Natural Earth map", values["Map Credit"] == "" and drawn is not None,
              f"credit text {values['Map Credit']!r}; the control draws text when filled: {drawn is not None}")
        if inset:
            alpha = img.getchannel("A")
            card = (int(ox - 8), int(oy - 8), int(ox + w * k + 8), int(oy + h * k + 8))
            outside = Image.new("L", img.size, 255)
            ImageDraw.Draw(outside).rectangle(card, fill=0)
            leak = ImageChops.multiply(alpha, outside).getbbox()
            inner = alpha.crop((card[0] + 12, card[1] + 12, card[2] - 12, card[3] - 12)).getextrema()
            check(f"{tag} transparent outside the card", leak is None and inner[0] == 255,
                  f"alpha outside: {'none' if leak is None else leak}; inside min {inner[0]}")
        sheet.append((tag, Image.open(without).convert("RGBA")))

    # Each font control takes any font and reaches only its own text (tools/fontcheck.py), the credit filled so it shows.
    def still(values, tag):
        vfile = OUT / "maps" / f"{tag}.json"   # beside the map picture the values name
        vfile.write_text(json.dumps(values, ensure_ascii=False))
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", "16x9", "--values", vfile, "--out", OUT / f"{tag}.png",
             "--frame", END, "--effectcraft-cli", a.effectcraft_cli])
        return Image.open(OUT / f"{tag}.png")
    base = dict(json.loads((OUT / "maps" / "locator00_16x9.values.json").read_text()), **{"Map Credit": maps.OSM_CREDIT})
    for name, ok, detail in font_checks(still, {"Name Font": ["Place Name"], "Subtitle Font": ["Subtitle"], "Credit Font": ["Map Credit"]}, base):
        check(name, ok, detail)

    tiles = []
    for tag, img in sheet:
        bg = Image.new("RGBA", img.size, (60, 70, 60, 255))
        bg.alpha_composite(img)
        t = bg.convert("RGB")
        t.thumbnail((640, 640))
        tiles.append((tag, t))
    s = Image.new("RGB", (sum(t.width for _, t in tiles) + 10 * (len(tiles) + 1), max(t.height for _, t in tiles) + 40), (255, 255, 255))
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
