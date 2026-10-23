#!/usr/bin/env python3
"""Make a demo reel from a demo.json (PLAN.md, DEMO1): footage with templates laid over it, map cards, a closing title, music.

  python3 tools/demo.py effectcraft/maps/route_leg/effectcraft-0.13/previews/demo.json --footage DIR [--music DIR] [--out FILE]
  python3 tools/demo.py demo/australia_trip/demo.json --footage DIR --music DIR
  python3 tools/demo.py --check FILE.mp4 [--max-seconds 15] [--max-mb 5]

The footage stays outside the repository: demo.json names it by key ("port_campbell"), and --footage DIR holds files named by key
(any extension; links are fine), in the subfolder demo.json names. So does the music: --music DIR holds the track demo.json names
(it is only ever mixed into the finished video, never copied). Without --music the demo is silent.

demo.json:
  size        "16x9" (1280x720 out) or "9x16" (720x1280)
  footage     the subfolder of --footage DIR
  music       the track's file name in --music DIR (looped with 2 s crossfades if the demo is longer; faded in and out)
  crossfade   seconds between segments (default 0.5)
  poster_at   seconds into the demo for poster.jpg (default 2)
  prepare     commands to run first, each a list: a tools/ script and its arguments ("{root}", "{work}" are filled in)
  segments    in order, each one of:
    {"card": TEMPLATE, "values": V, "seconds": S, "overlays": [...]}  a full-frame template on black (overlays as below)
    {"footage": KEY, "seconds": S, "overlays": [{"template": TEMPLATE, "values": V, "at": T}, ...]}
                    the footage shown whole through Fill the Frame, with transparent templates laid over it from T seconds
                    ("fill": {"Blur": 10, "Darken": 0} sets Fill the Frame's own controls, to show them; "fill": {"Media": "{root}/..."}
                    shows that picture instead of the footage one, e.g. the template's portrait example; "folder": "stock" looks the footage up in that
                    folder of --footage instead of the spec's own, e.g. for a video clip)
    {"title": ["line", ...], "seconds": S}                         a plain card drawn by script (Inter)
    {"clip": PATH, "start": T, "seconds": S}                         an excerpt of a finished video (its sound is dropped), e.g. a
                    template's demo, for the showreel
  V is a values dict, a values-file path, or {"file": path, "set": {...}} (a file with some values changed).
  title_page  "template" (a template's own reel: its name, version, the EffectCraft versions it was tested with and links, from
              template.json) or "collection" (the showreel: all the templates); 3 s before the first segment. Or an object for a
              reel of something else (the trip video kit's preview): {"name": "Trip Video", "line": "A ready-made EffectCraft project",
              "templates": ["effectcraft/maps/route_leg", ...]}, the templates it uses (for the tested versions and the credits)
  credit_photos  the end page's photo credit line (default: Pixie's own photos); e.g. "Photos: Pixabay (see CREDITS.md)"
  end_page    true: the credits (photos, music, maps, fonts), the links (templates, ArtCraft, EffectCraft), the sponsor and the
              independent-project line, 4 s after the last segment (PLAN.md, DEMO2). A clip of a reel with a title page starts after it.
  A card or footage segment may also have "caption": "Style: Bounce · By: Words", saying which feature is on screen: a small label
  (Inter on a dark pill) at the bottom left, or the top left with "caption_at": "top" (where a template sits bottom left), shown
  between the crossfades. "label": "Typewriter" puts the template's name in bold at the start of the same pill (the showreels).

The result is H.264 with no metadata (no creation time, no location), plus poster.jpg beside it. --check tests a finished demo:
it decodes to the end, is within the size and length limits, and carries no creation time or location.
"""
import argparse
import json
import math
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

import versions

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRAMES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
OUT_SIZES = {"16x9": (1280, 720), "9x16": (720, 1280)}
FPS = 24
FILL = "effectcraft/utility/fill_frame"
NAME = "Pixie's Craft Templates"
PIXIE = ROOT / "brand" / "pixie.png"
TITLE_SECONDS, END_SECONDS = 3, 4
EFFECTCRAFT_LINKS = "getartcraft.com/apps/effectcraft · github.com/storytold/effectcraft"
MUSIC_CREDITS = {"Relaxing Flute Tune-(SoundEffectsFactory.com)_.mp3": "\u201cRelaxing Flute Tune\u201d by Kerri, Sound Effects Factory"}
WHITE, LIGHT, LINK, DIM = (255, 255, 255), (200, 212, 224), (140, 196, 236), (130, 144, 158)
# Under Pixie on the end page (PLAN.md, END2): (text, px at 1080, Inter style, colour)
SHOWREEL_FONT = "font:raleway/static/Raleway-SemiBold.ttf"   # a style "font:<path in fonts/>" is a static font file, not an Inter style
UNDER_PIXIE = [("See Pixie on YouTube", 32, "SemiBold", WHITE), ("youtube.com/@PixBack", 30, "Medium", LINK)]


def run(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{(r.stderr or r.stdout)[-3000:]}")
    return r.stdout


def fill(text, work):
    return text.replace("{root}", str(ROOT)).replace("{work}", str(work))


class Demo:
    def __init__(self, spec_path, a, work):
        self.spec_path, self.a, self.work = spec_path, a, work
        self.spec = json.loads(spec_path.read_text())
        self.size = self.spec.get("size", "16x9")
        self.w, self.h = FRAMES[self.size]
        self.n = 0

    def values_file(self, v):
        """A values file for render.py: written beside the file it changes, so its relative media paths still resolve."""
        self.n += 1
        if isinstance(v, str):
            return pathlib.Path(fill(v, self.work))
        if "file" in v:
            base = pathlib.Path(fill(v["file"], self.work))
            merged = dict(json.loads(base.read_text()), **v.get("set", {}))
            out = base.parent / f"_demo{self.n:02d}.values.json"
        else:
            merged, out = v, self.work / f"_demo{self.n:02d}.values.json"
        out.write_text(json.dumps(merged, ensure_ascii=False))
        return out

    def render(self, template, values, out):
        vfile = self.values_file(values)
        run([sys.executable, ROOT / "tools" / "render.py", template, "--variant", self.size, "--values", vfile,
             "--out", out, "--effectcraft-cli", self.a.effectcraft_cli])
        if vfile.name.startswith("_demo") and vfile.parent != self.work:   # written beside a values file in the repository
            vfile.unlink()
        return out

    def check_fonts(self):
        """Every card's and overlay's fonts installed (render.py --check-fonts), before anything renders; else stop, naming them."""
        missing = []
        for i, seg in enumerate(self.spec["segments"]):
            jobs = ([(seg["card"], seg["values"])] if "card" in seg else []) + [(o["template"], o["values"]) for o in seg.get("overlays", [])]
            for template, values in jobs:
                vfile = self.values_file(values)
                r = subprocess.run([sys.executable, ROOT / "tools" / "render.py", template, "--values", vfile, "--check-fonts",
                                    "--effectcraft-cli", self.a.effectcraft_cli], capture_output=True, text=True)
                if vfile.name.startswith("_demo") and vfile.parent != self.work:
                    vfile.unlink()
                if r.returncode and not r.stderr.startswith("Fonts missing"):   # the check itself failed: say why
                    sys.exit(f"segment {i}, {template}: the font check failed:\n{(r.stderr or r.stdout).strip()}")
                if r.returncode:
                    missing.append(f"segment {i}, {template}:\n" + "\n".join(r.stderr.strip().splitlines()[1:]))
        if missing:
            sys.exit("Fonts missing, so nothing was rendered:\n" + "\n".join(missing))

    def footage(self, key, folder=None):
        folder = self.a.footage / (folder or self.spec["footage"])
        found = sorted(p for p in folder.glob(f"{key}.*"))
        if not found:
            sys.exit(f"no footage {key!r} in {folder}")
        return found[0]

    def segment(self, i, seg):
        """One segment as an H.264 clip at the frame size, exactly seg["seconds"] long."""
        out = self.work / f"seg{i:02d}.mp4"
        s = seg["seconds"]
        exact = ["-t", str(s), "-r", str(FPS), "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-an"]
        if "card" in seg or "footage" in seg:
            # The base (a card over black, or footage filling the frame), then the overlays on it in order.
            if "card" in seg:
                mov = self.render(seg["card"], seg["values"], self.work / f"card{i:02d}.mov")
                base = self.work / f"cardbase{i:02d}.mp4"
                run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=black:s={self.w}x{self.h}:r={FPS}:d={s}", "-i", mov,
                     "-filter_complex", "[1:v]tpad=stop_mode=clone:stop_duration=60[c];[0:v][c]overlay=eof_action=repeat", *exact,
                     base])
            else:
                values = self.work / f"fill{i:02d}.values.json"
                controls = dict(seg.get("fill", {}))
                media = controls.pop("Media", None)
                media = pathlib.Path(media.replace("{root}", str(ROOT))) if media else self.footage(seg["footage"], seg.get("folder"))
                values.write_text(json.dumps({"Media": str(media.resolve()), "Duration": s, **controls}))
                base = self.render(FILL, str(values), self.work / f"fill{i:02d}.mp4")
            inputs, chain, last = ["-i", base], [], "0:v"
            for k, o in enumerate(seg.get("overlays", [])):
                mov = self.render(o["template"], o["values"], self.work / f"over{i:02d}_{k}.mov")
                inputs += ["-itsoffset", str(o.get("at", 0)), "-i", mov]
                chain.append(f"[{last}][{k + 1}:v]overlay=eof_action=pass[o{k}]")
                last = f"o{k}"
            if seg.get("caption") or seg.get("label"):
                png = self.work / f"caption{i:02d}.png"
                caption(seg.get("caption"), (self.w, self.h), seg.get("caption_at", "bottom"), png, seg.get("label"))
                n = len(seg.get("overlays", [])) + 1
                inputs += ["-i", png]
                xf = self.spec.get("crossfade", 0.5)   # shown between the crossfades, so two captions never overlap
                chain.append(f"[{last}][{n}:v]overlay=enable='between(t,{xf},{s - xf})'[cap]")
                last = "cap"
            graph = ";".join(chain) if chain else "[0:v]null[o]"
            run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", f"[{last if chain else 'o'}]", *exact, out])
        elif "clip" in seg:
            src = pathlib.Path(fill(seg["clip"], self.work))
            start = seg.get("start", 0)
            made_from = src.with_suffix(".json")   # a reel with a title page: "start" counts from after it
            if made_from.is_file() and json.loads(made_from.read_text()).get("title_page"):
                start += TITLE_SECONDS   # the title page is still fading out until then
            run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", src, "-vf",
                 f"scale={self.w}:{self.h}:flags=lanczos,fps={FPS}", *exact, out])
        elif "page" in seg:
            png = self.work / f"page{i:02d}.png"
            page_card(seg["page"], (self.w, self.h), png, under=seg.get("under"))
            run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", png, *exact, out])
        elif "title" in seg:
            png = self.work / f"title{i:02d}.png"
            title_card(seg["title"], (self.w, self.h), png)
            run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", png, *exact, out])
        else:
            sys.exit(f"segment {i}: needs card, footage, clip or title")
        return out

    def prepare(self):
        for cmd in self.spec.get("prepare", []):
            run([sys.executable, ROOT / "tools" / cmd[0], *[fill(c, self.work) for c in cmd[1:]], "--effectcraft-cli", self.a.effectcraft_cli]
                if cmd[0] == "render.py" else [sys.executable, ROOT / "tools" / cmd[0], *[fill(c, self.work) for c in cmd[1:]]])

    def make(self, out):
        self.prepare()
        self.check_fonts()
        xf = self.spec.get("crossfade", 0.5)
        segs = list(self.spec["segments"])
        if self.spec.get("title_page"):
            segs.insert(0, {"page": self.title_page(), "seconds": TITLE_SECONDS})
        if self.spec.get("end_page"):
            segs.append({"page": self.end_page(), "under": UNDER_PIXIE, "seconds": END_SECONDS})
        clips = [self.segment(i, s) for i, s in enumerate(segs)]
        # Crossfade the segments in order: each join overlaps by xf seconds.
        inputs = sum((["-i", c] for c in clips), [])
        graph, last, t = [], "0:v", segs[0]["seconds"]
        for k in range(1, len(clips)):
            t -= xf
            graph.append(f"[{last}][{k}:v]xfade=transition=fade:duration={xf}:offset={t:.3f}[x{k}]")
            last, t = f"x{k}", t + segs[k]["seconds"]
        total = t
        ow, oh = OUT_SIZES[self.size]
        graph.append(f"[{last}]scale={ow}:{oh}:flags=lanczos,format=yuv420p[v]")
        music = self.music(total)
        if music:
            inputs += ["-i", music]
        cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(graph), "-map", "[v]"]
        if music:
            cmd += ["-map", f"{len(clips)}:a", "-c:a", "aac", "-b:a", "128k"]
        cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "24", "-r", str(FPS), "-t", f"{total:.3f}", "-map_metadata", "-1",
                "-map_chapters", "-1", "-fflags", "+bitexact", "-flags:v", "+bitexact", "-movflags", "+faststart", out]
        run(cmd)
        # demo.mp4 → poster.jpg, demo_9x16.mp4 → poster_9x16.jpg, anything else (showreel.mp4) → showreel_poster.jpg
        poster = out.with_name(f"poster{out.stem[4:]}.jpg" if out.stem.startswith("demo") else f"{out.stem}_poster.jpg")
        poster_at = self.spec.get("poster_at", 2) + (TITLE_SECONDS - xf if self.spec.get("title_page") else 0)
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(poster_at), "-i", out, "-frames:v", "1", "-q:v", "3",
             "-map_metadata", "-1", poster])
        return out, poster, total

    def templates(self):
        """The current version folders of the templates this reel shows (every template for the collection)."""
        if isinstance(self.spec.get("title_page"), dict):
            ids = set(self.spec["title_page"]["templates"])
        elif self.spec.get("title_page") == "collection":
            ids = {m.parent.parent.relative_to(ROOT).as_posix() for m in ROOT.glob("effectcraft/*/*/*/template.json")}
        elif self.spec.get("title_page") == "template":
            ids = {self.spec_path.parent.parent.parent.relative_to(ROOT).as_posix()}
        else:
            ids = {t for seg in self.spec["segments"] for t in [seg.get("card")] + [o["template"] for o in seg.get("overlays", [])] if t}
        out = []
        for i in sorted(ids):
            fs = versions.folders(ROOT / i)
            out.append(([f for f in fs if not f.frozen] or fs)[-1])
        return out

    def title_page(self):
        """The reel's title page: the template (or collection), its version, the EffectCraft versions tested and their links."""
        fs = self.templates()
        ranges = [f.tested_range() for f in fs if f.tested_range()]
        low, high = min((r[0] for r in ranges), key=versions.parse), max((r[1] for r in ranges), key=versions.parse)
        tested = f"For EffectCraft {low if low == high else f'{low}–{high}'} (tested)"
        if isinstance(self.spec["title_page"], dict):
            tp = self.spec["title_page"]
            head = [(NAME, 34, "SemiBold", LIGHT, 0), (tp["name"], 76, "Bold", WHITE, 18), (tp["line"], 36, "Medium", LIGHT, 30)]
        elif self.spec["title_page"] == "collection":
            head = [(NAME, 76, "Bold", WHITE, 0), (f"{len(fs)} free motion templates", 36, "Medium", LIGHT, 30)]
        else:
            m = fs[0].manifest
            head = [(NAME, 34, "SemiBold", LIGHT, 0), (m["name"], 76, "Bold", WHITE, 18),
                    (f"Template version {m['version']}", 36, "Medium", LIGHT, 30)]
        tail = [("Showreel", 144, SHOWREEL_FONT, WHITE, 40)] if self.spec["title_page"] == "collection" else []
        return head + [(tested, 34, "Regular", LIGHT, 14), (EFFECTCRAFT_LINKS, 30, "Regular", LINK, 34)] + tail

    def fonts_set(self):
        """Font families this reel's values pick ("Montserrat Bold" → Montserrat), found by their folder in fonts/."""
        found = set()
        for seg in self.spec["segments"]:
            for v in [seg.get("values")] + [o["values"] for o in seg.get("overlays", [])]:
                v = v.get("set", v) if isinstance(v, dict) else {}
                for name, value in v.items():
                    words = value.split() if name.endswith("Font") and isinstance(value, str) else []
                    for n in range(len(words), 0, -1):
                        family = " ".join(words[:n])
                        if (ROOT / "fonts" / re.sub(r"[^a-z0-9]+", "_", family.lower()).strip("_")).is_dir():
                            found.add(family)
                            break
        return found

    def end_page(self):
        """The credits, the links, the sponsor and the independent-project line (PLAN.md, DEMO2)."""
        fs = self.templates()
        lines = [("Credits", 60, "Bold", WHITE, 0), (self.spec.get("credit_photos", "Photos and Pixie \u00a9 Gregory Kirkendall"), 30, "Regular", LIGHT, 26)]
        track = self.spec.get("music")
        if track and self.a.music:
            if track not in MUSIC_CREDITS:
                sys.exit(f"no credit for the music {track!r}: add it to MUSIC_CREDITS in tools/demo.py")
            lines.append((f"Music: {MUSIC_CREDITS[track]}", 30, "Regular", LIGHT, 10))
        if any(f.manifest["category"] == "maps" for f in fs):
            lines.append(("Maps: Natural Earth; \u00a9 OpenStreetMap contributors", 30, "Regular", LIGHT, 10))
        fonts = sorted({font for f in fs for font in f.manifest.get("fonts", [])} | self.fonts_set()
                       | ({"Raleway"} if self.spec.get("title_page") == "collection" else set()))   # "Showreel" on the title page
        if fonts:
            lines.append((f"Font{'s' if len(fonts) > 1 else ''}: {', '.join(fonts)} (SIL Open Font License)", 30, "Regular", LIGHT, 10))
        lines += [("Templates: github.com/gkirkendall/pixies-craft-templates", 30, "Medium", LINK, 34),
                  ("ArtCraft: getartcraft.com", 30, "Medium", LINK, 10),
                  ("EffectCraft: getartcraft.com/apps/effectcraft", 30, "Medium", LINK, 10),
                  ("Sponsored By PixBack - Photo and Video Backup to Google Photos", 32, "SemiBold", WHITE, 34),
                  ("getpixback.com", 30, "Medium", LINK, 10),
                  ("An independent project, not made or endorsed by the EffectCraft or ArtCraft teams.", 22, "Regular", DIM, 40)]
        return lines

    def music(self, total):
        """The track looped with 2 s crossfades to the demo's length, faded in over 1 s and out over the last 2 s."""
        name = self.spec.get("music")
        if not name or not self.a.music:
            return None
        src = self.a.music / name
        if not src.is_file():
            sys.exit(f"music {src} not found")
        length = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]).strip())
        copies = max(1, math.ceil((total - 2) / (length - 2)))
        inputs = sum((["-i", src] for _ in range(copies)), [])
        graph, last = [], "0:a"
        for k in range(1, copies):
            graph.append(f"[{last}][{k}:a]acrossfade=d=2[m{k}]")
            last = f"m{k}"
        graph.append(f"[{last}]atrim=0:{total:.3f},afade=t=in:d=1,afade=t=out:st={max(0, total - 2):.3f}:d=2,volume=-2dB[a]")
        out = self.work / "music.m4a"
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(graph), "-map", "[a]", "-c:a", "aac", "-b:a", "192k", out])
        return out


def title_card(lines, size, out):
    """Plain centred lines on a dark background: the first in Inter Bold, the rest in Inter Regular."""
    w, h = size
    im = Image.new("RGB", size, (18, 26, 36))
    d = ImageDraw.Draw(im)
    font_file = ROOT / "fonts" / "inter" / "Inter[opsz,wght].ttf"
    unit = min(w, h) / 1080
    fonts = []
    for k, _ in enumerate(lines):
        f = ImageFont.truetype(str(font_file), round((64 if k == 0 else 34) * unit))
        f.set_variation_by_name("Bold" if k == 0 else "Regular")
        fonts.append(f)
    gaps = [round((44 if k == 1 else 18) * unit) for k in range(len(lines))]
    heights = [d.textbbox((0, 0), line, font=f)[3] for line, f in zip(lines, fonts)]
    y = (h - sum(heights) - sum(gaps[1:])) / 2
    for k, (line, f) in enumerate(zip(lines, fonts)):
        y += gaps[k] if k else 0
        tw = d.textlength(line, font=f)
        d.text(((w - tw) / 2, y), line, font=f, fill=(255, 255, 255) if k == 0 else (200, 212, 224))
        y += heights[k]
    im.save(out)


def page_card(lines, size, out, pixie=True, under=None):
    """A title or end page: centred lines on the dark background, each (text, px at 1080, Inter style, colour, gap above),
    (a style "font:raleway/static/Raleway-SemiBold.ttf" names a static font file in fonts/), wrapped at spaces to the text area's width, and scaled down together if they would not fit its height. With pixie, Pixie
    (brand/pixie.png; PLAN.md, BRAND1) stands at the left of a wide frame, the text centred to his right, or at the top of a tall
    frame, the text below. under: lines (text, px at 1080, Inter style, colour) centred under Pixie (the end page's YouTube line)."""
    w, h = size
    font_file = str(ROOT / "fonts" / "inter" / "Inter[opsz,wght].ttf")
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    margin = round(0.07 * w)
    im = Image.new("RGB", size, (18, 26, 36))
    left, top, right, bottom = margin, margin, w - margin, h - margin
    unit = min(w, h) / 1080
    caption = []   # the lines under Pixie: (text, font, colour, height)
    for text, px, style, colour in (under or []) if pixie else []:
        f = ImageFont.truetype(font_file, round(px * unit))
        f.set_variation_by_name(style)
        caption.append((text, f, colour, d.textbbox((0, 0), "Hg", font=f)[3] + round(6 * unit)))
    cap_h = sum(c[3] for c in caption) + (round(18 * unit) if caption else 0)
    cap_w = max((d.textlength(t, font=f) for t, f, _, _ in caption), default=0)

    def draw_caption(cx, y):
        y += round(18 * unit)
        for text, f, colour, lh in caption:
            ImageDraw.Draw(im).text((cx - d.textlength(text, font=f) / 2, y), text, font=f, fill=colour)
            y += lh

    if pixie:
        art = Image.open(PIXIE).convert("RGBA")
        if w > h:
            ph = round((0.56 if caption else 0.66) * h)
            art = art.resize((round(art.width * ph / art.height), ph), Image.LANCZOS)
            column = max(art.width, round(cap_w))
            x, y = round(0.05 * w), (h - ph - cap_h) // 2
            im.paste(art, (x + (column - art.width) // 2, y), art)
            if caption:
                draw_caption(x + column / 2, y + ph)
            left = x + column + round(0.04 * w)
        else:   # Pixie, the lines under him and the text are centred together, below the first margin
            ph, gap = round(0.24 * h), round(0.03 * h)
            art = art.resize((round(art.width * ph / art.height), ph), Image.LANCZOS)
            top += ph + cap_h + gap
    width = right - left

    def lay(scale):
        rows = []
        for text, px, style, colour, gap in lines:
            if style.startswith("font:"):
                file = ROOT / "fonts" / style[5:]
                if not file.is_file():   # Pillow would quietly use an installed font of the same file name instead
                    sys.exit(f"font file {file} not found")
                f = ImageFont.truetype(str(file), max(8, round(px * scale)))
            else:
                f = ImageFont.truetype(font_file, max(8, round(px * scale)))
                f.set_variation_by_name(style)
            # Too wide: break after " - " or " · " first, so a phrase stays whole; else at spaces.
            mark = next((m for m in (" - ", " · ") if m in text), None)
            if mark and d.textlength(text, font=f) > width:
                head, tail = text.split(mark, 1)
                words = [head + mark.rstrip(), "\n" + tail]
                words = words[:1] + tail.split(" ")
                words[1] = "\n" + words[1]
            else:
                words = text.split(" ")
            line = ""
            first = True
            for word in words:
                forced = word.startswith("\n")
                word = word.lstrip("\n")
                trial = f"{line} {word}".strip()
                if line and (forced or d.textlength(trial, font=f) > width):
                    rows.append((line, f, colour, round(gap * scale) if first else round(6 * scale)))
                    line, first = word, False
                else:
                    line = trial
            rows.append((line, f, colour, round(gap * scale) if first else round(6 * scale)))
        height = sum(d.textbbox((0, 0), "Hg", font=f)[3] + g for _, f, _, g in rows)
        return rows, height

    scale = min(w, h) / 1080
    rows, height = lay(scale)
    while height > bottom - top:
        scale *= 0.95
        rows, height = lay(scale)
    draw = ImageDraw.Draw(im)
    y = top + (bottom - top - height) / 2
    if pixie and w <= h:
        y = (h - (ph + cap_h + gap + height)) / 2 + ph + cap_h + gap
        im.paste(art, ((w - art.width) // 2, round(y - gap - cap_h - ph)), art)
        if caption:
            draw_caption(w / 2, y - gap - cap_h)
    for text, f, colour, gap in rows:
        y += gap
        draw.text((left + (width - draw.textlength(text, font=f)) / 2, y), text, font=f, fill=colour)
        y += draw.textbbox((0, 0), "Hg", font=f)[3]
    im.save(out)


def caption(text, size, at, out, label=None):
    """A transparent frame with text in a small dark pill: at the bottom left, or the top left (at="top").
    label: a name in bold white at the start of the pill, then a thin rule, then the caption (the showreels name each template)."""
    w, h = size
    unit = min(w, h) / 1080
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    font_file = str(ROOT / "fonts" / "inter" / "Inter[opsz,wght].ttf")
    f = ImageFont.truetype(font_file, round(30 * unit))
    f.set_variation_by_name("SemiBold")
    fb = ImageFont.truetype(font_file, round(30 * unit))
    fb.set_variation_by_name("Bold")
    parts = ([(label, fb, 255)] if label else []) + ([(text, f, 255 if not label else 225)] if text else [])
    boxes = [d.textbbox((0, 0), t, font=ft) for t, ft, _ in parts]
    px, py, margin, gap = round(22 * unit), round(12 * unit), round(36 * unit), round(18 * unit)
    top = min(b[1] for b in boxes)
    th = max(b[3] for b in boxes) - top
    tw = sum(b[2] - b[0] for b in boxes) + (2 * gap + round(2 * unit) if len(parts) > 1 else 0)
    bw, bh = tw + 2 * px, th + 2 * py
    x, y = margin, (margin if at == "top" else h - margin - bh)
    d.rounded_rectangle((x, y, x + bw, y + bh), radius=bh // 2, fill=(0, 0, 0, 150))
    cx = x + px
    for k, ((t, ft, a), b) in enumerate(zip(parts, boxes)):
        if k:
            d.rectangle((cx + gap, y + py, cx + gap + round(2 * unit), y + py + th), fill=(255, 255, 255, 120))
            cx += 2 * gap + round(2 * unit)
        d.text((cx - b[0], y + py - top), t, font=ft, fill=(255, 255, 255, a))
        cx += b[2] - b[0]
    im.save(out)


def check(path, max_seconds, max_mb):
    """Plays to the end, within limits, no creation time or location."""
    problems = []
    info = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path]))
    seconds = float(info["format"]["duration"])
    mb = path.stat().st_size / 1e6
    if seconds > max_seconds:
        problems.append(f"{seconds:.1f} s is over {max_seconds} s")
    if mb > max_mb:
        problems.append(f"{mb:.1f} MB is over {max_mb} MB")
    tags = json.dumps([info["format"].get("tags", {})] + [s.get("tags", {}) for s in info["streams"]]).lower()
    for word in ("creation_time", "location", "com.apple.quicktime", "date"):
        if word in tags:
            problems.append(f"metadata has {word}")
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], capture_output=True, text=True)
    if r.returncode or r.stderr.strip():
        problems.append(f"does not decode cleanly: {r.stderr.strip()[:200]}")
    print(f"{path}: {seconds:.1f} s, {mb:.2f} MB" + ("; " + "; ".join(problems) if problems else "; ok"))
    return not problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("spec", nargs="?", type=pathlib.Path, help="a demo.json")
    ap.add_argument("--footage", type=pathlib.Path, help="folder holding the footage subfolder demo.json names")
    ap.add_argument("--music", type=pathlib.Path, help="folder holding the track demo.json names (omit for a silent demo)")
    ap.add_argument("--out", type=pathlib.Path, help="default: demo.mp4 beside demo.json (demo_9x16.mp4 for a 9x16 demo)")
    ap.add_argument("--keep-work", type=pathlib.Path, help="keep the working files in this folder (for checking)")
    ap.add_argument("--check", type=pathlib.Path, help="check a finished demo instead of making one")
    ap.add_argument("--max-seconds", type=float, default=25)
    ap.add_argument("--max-mb", type=float, default=5)
    ap.add_argument("--effectcraft-cli", default="effectcraft-cli")
    a = ap.parse_args()
    if a.check:
        sys.exit(0 if check(a.check, a.max_seconds, a.max_mb) else 1)
    if not a.spec or not a.footage:
        ap.error("give a demo.json and --footage")
    spec_path = a.spec.resolve()
    size = json.loads(spec_path.read_text())["size"]
    out = (a.out or spec_path.with_name("demo.mp4" if size == "16x9" else "demo_9x16.mp4")).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        work = a.keep_work.resolve() if a.keep_work else pathlib.Path(tmp)
        work.mkdir(parents=True, exist_ok=True)
        out, poster, total = Demo(spec_path, a, work).make(out)
    print(f"{out} ({total:.1f} s), poster {poster}")


if __name__ == "__main__":
    main()
