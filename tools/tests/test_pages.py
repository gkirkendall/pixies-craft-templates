#!/usr/bin/env python3
"""Test the title and end pages of the demo reels (PLAN.md, DEMO2). Free: no app needed; reads the committed reels back with
tesseract (brew install tesseract).

  python3 tools/tests/test_pages.py

Every reel and video has both pages: the template reels, the showreel, the trip demo and the trip video kit's preview; a
9x16 reel (a Short) opens straight on the effect, with no title page, and still ends on the end page. Checks, on
Box Wipe's reel and the showreel: the title page (1.5 s in) names the template (or "Craft Templates"), the template
version from template.json and the EffectCraft versions it was tested with, and EffectCraft's links; the end page (1.5 s before
the end) has the credits, the links to the templates, ArtCraft and EffectCraft, the PixBack sponsor line and getpixback.com, and
the independent-project line. Every reel with a title page has one, and every reel ends on an end page.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import versions  # noqa: E402

BOX_WIPE = ROOT / "effectcraft" / "lower_thirds" / "box_wipe" / "effectcraft-0.13"
END = ["Credits", "Photos", "Music", "github.com/gkirkendall/pixies-craft-templates", "ArtCraft: getartcraft.com",
       "EffectCraft: getartcraft.com/apps/effectcraft", "Sponsored By PixBack - Photo and Video Backup to Google Photos",
       "getpixback.com", "not made or endorsed by the EffectCraft or ArtCraft teams"]
UNDER_PIXIE = ["See Pixie on YouTube", "youtube.com/@PixBack"]   # read in Pixie's column (left third) of a wide end page
COLUMN = (0, 0.6, 0.34, 1)


def read(video, at, tmp, box=None):
    """The text on one frame, as tesseract reads it (light on dark made dark on light, doubled), with whitespace joined; box
    (left, top, right, bottom as fractions of the frame) reads only that part, e.g. Pixie's column on a wide end page."""
    png = pathlib.Path(tmp) / "frame.png"
    seek = ["-sseof", str(at)] if at < 0 else ["-ss", str(at)]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *seek, "-i", str(video), "-frames:v", "1", str(png)], check=True)
    g = ImageOps.invert(Image.open(png).convert("L"))
    if box:
        g = g.crop(tuple(round(f * n) for f, n in zip(box, (g.width, g.height, g.width, g.height))))
    g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS)   # the end page's small text reads reliably only with a good filter
    g.save(png)
    try:
        out = subprocess.run(["tesseract", str(png), "-", "--psm", "6"], capture_output=True, text=True).stdout
    except FileNotFoundError:
        sys.exit("tesseract is needed: brew install tesseract (or your system's package)")
    return " ".join(out.replace("“", '"').replace("”", '"').replace("—", "-").split())


def main():
    results = []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail)

    folder = versions.Folder(BOX_WIPE)
    m = folder.manifest
    with tempfile.TemporaryDirectory() as tmp:
        title = read(BOX_WIPE / "previews" / "demo.mp4", 1.5, tmp)
        want = [m["name"], f"Template version {m['version']}", f"For EffectCraft {folder.range_text().replace(chr(0x2013), '-')} (tested)",   # tesseract reads the range's en-dash as a hyphen
                "getartcraft.com/apps/effectcraft", "github.com/storytold/effectcraft"]
        check("Box Wipe title page", all(w in title for w in want), f"read {title!r}; missing {[w for w in want if w not in title]}")
        end = read(BOX_WIPE / "previews" / "demo.mp4", -1.5, tmp)
        check("Box Wipe end page", all(w in end for w in END + ["Caveat Brush", "Montserrat"]),
              f"missing {[w for w in END + ['Caveat Brush', 'Montserrat'] if w not in end]}")
        for name, video in (("Box Wipe", BOX_WIPE / "previews" / "demo.mp4"), ("showreel", ROOT / "demo" / "showreel.mp4")):
            col = read(video, -1.5, tmp, COLUMN)
            check(f"{name}: See Pixie on YouTube under Pixie", all(w in col for w in UNDER_PIXIE), f"read {col!r}")
        title = read(ROOT / "demo" / "showreel.mp4", 1.5, tmp)
        check("showreel title page", "Pixie" in title and "Craft Templates" in title and "free motion templates" in title and "(tested)" in title, f"read {title!r}")
        end = read(ROOT / "demo" / "showreel.mp4", -1.5, tmp)
        check("showreel end page", all(w in end for w in END + ["Natural Earth"]), f"missing {[w for w in END if w not in end]}")
        for name, video, head in (("trip demo", ROOT / "demo" / "australia_trip" / "demo.mp4", "Australia Trip"),
                                  ("trip video kit preview", ROOT / "project_templates" / "trip_video" / "preview.mp4", "Trip Video")):
            title = read(video, 1.5, tmp)
            want = [head, "(tested)", "getartcraft.com/apps/effectcraft", "github.com/storytold/effectcraft"]
            check(f"{name} title page", all(w in title for w in want), f"read {title!r}; missing {[w for w in want if w not in title]}")
            end = read(video, -1.5, tmp)
            check(f"{name} ends on the same end page", all(w in end for w in END), f"missing {[w for w in END if w not in end]}")
    specs = sorted(ROOT.glob("effectcraft/*/*/*/previews/demo*.json")) + [ROOT / "demo" / "showreel.json", ROOT / "demo" / "showreel_9x16.json", ROOT / "demo" / "australia_trip" / "demo.json"]
    def pages_ok(spec):
        d = json.loads(spec.read_text())
        return d.get("end_page") and (d.get("title_page") or d.get("size") == "9x16")
    off = [s.relative_to(ROOT).as_posix() for s in specs if not pages_ok(s)]
    check("every reel has both pages (9x16: the end page)", not off, f"{len(specs)} reels" + (f"; without: {off}" if off else ""))
    clips = [n for n in ("showreel.json", "showreel_9x16.json")
             if any("clip" in seg for seg in json.loads((ROOT / "demo" / n).read_text())["segments"])]
    check("showreels are built from shots, not from finished videos", not clips, f"clip segments in {clips}" if clips else "no clip segments")
    print(f"\n{sum(results)} of {len(results)} checks pass")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
