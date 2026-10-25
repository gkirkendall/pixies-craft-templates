#!/usr/bin/env python3
"""Test for Box Wipe Lower Third. Free: no GPU; reads the text back with tesseract (brew install tesseract).

  python3 effectcraft/lower_thirds/box_wipe/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Renders single transparent frames. Checks, in both sizes, at rest: the title and subtitle read back (OCR, each band on its own)
exactly; the box's bottom-left corner is at Position (within 2 px); the text sits inside the box with room to spare; nothing is
drawn outside the box but the line along its top. In 16x9: empty at the first frame and the last; part-way in and part-way out
the box is narrower than at rest, and the text is gone before the box is shut; a long title (in Inter Bold, for OCR) wraps onto two lines and the box
stays within Max Width; with no subtitle the box is shorter; Position near each corner of the frame puts the box there; each font
control changes only its own line; Box Colour and Box Opacity colour the box; Duration sets the clip's length. Results go to
tests/out/ with a contact sheet.
"""
import argparse
import json
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE.parent
ROOT = next(p for p in TEMPLATE.parents if (p / "tools" / "render.py").is_file())
OUT = HERE / "out"
MANIFEST = json.loads((TEMPLATE / "template.json").read_text())
DEFAULTS = {c["name"]: c.get("default") for c in MANIFEST["controls"]}
FRAMES = {"16x9": ((1920, 1080), [110, 960], 1100), "9x16": ((1080, 1920), [70, 1540], 810)}
REST, DURATION = 2.0, DEFAULTS["Duration"]


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr or r.stdout}")
    return r


def ocr(im, box):
    """The white text inside box as tesseract reads it (one line): white made black on white, doubled in size."""
    g = im.crop(box).convert("RGBA")
    px = g.load()
    mask = Image.new("L", g.size, 255)
    mp = mask.load()
    for y in range(g.height):
        for x in range(g.width):
            r, gg, b, a = px[x, y]
            if a > 200 and min(r, gg, b) > 120 and b > 0.8 * r:   # white text, not the yellow line
                mp[x, y] = 255 - min(r, gg, b)
    mask = mask.resize((mask.width * 2, mask.height * 2))
    src = OUT / "ocr.png"
    mask.save(src)
    try:
        return " ".join(run(["tesseract", src, "-", "--psm", "7"]).stdout.split())
    except FileNotFoundError:
        sys.exit("tesseract is needed to read the text back: brew install tesseract (or your system's package)")


def box_of(im):
    """The box: its see-through pixels' extent, eroded first so the thin lines' soft edges don't count; None if there is none."""
    mask = im.getchannel("A").point(lambda v: 255 if 150 <= v <= 205 else 0).filter(ImageFilter.MinFilter(7))
    b = mask.getbbox()
    return (b[0] - 3, b[1] - 3, b[2] + 3, b[3] + 3) if b else None


def measure(im):
    """The box (its see-through pixels' extent), the underline's rows, and the white text's extent, in frame pixels."""
    px = im.load()
    box = box_of(im)
    yellow, white = [], []
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            r, g, b, al = px[x, y]
            if al > 240 and r > 220 and 180 < g < 230 and b < 140:
                yellow.append(y)
            elif al > 240 and min(r, g, b) > 200:
                white.append((x, y))
    under = (min(yellow), max(yellow)) if yellow else None
    text = (min(p[0] for p in white), min(p[1] for p in white), max(p[0] for p in white) + 1, max(p[1] for p in white) + 1) if white else None
    return box, under, text


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--effectcraft-cli", default="effectcraft-cli")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    results, sheet = [], []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail)

    def frame(variant, values, t, tag):
        vfile = OUT / f"{tag}.values.json"
        vfile.write_text(json.dumps(values))
        out = OUT / f"{tag}.png"
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", variant, "--values", vfile, "--out", out,
             "--frame", f"{t:.4f}", "--effectcraft-cli", a.effectcraft_cli])
        return Image.open(out).convert("RGBA")

    def thumb(tag):
        im = Image.open(OUT / f"{tag}.png").convert("RGBA")
        t = Image.new("RGBA", im.size, (120, 140, 150, 255))
        t.alpha_composite(im)
        t = t.convert("RGB")
        t.thumbnail((480, 480))
        sheet.append((tag, t))

    rest = {}
    for variant, ((W, H), P, _) in FRAMES.items():
        tag = f"{variant}_rest"
        im = frame(variant, {}, REST, tag)
        box, under, text = measure(im)
        rest[variant] = (box, under, text)
        title = ocr(im, (box[0], box[1], box[2], under[0] - 2))
        sub = ocr(im, (box[0], under[1] + 1, box[2], box[3]))
        check(f"{tag} text", title == DEFAULTS["Title"] and sub == DEFAULTS["Subtitle"], f"read {title!r} / {sub!r}")
        check(f"{tag} box at Position", abs(box[0] - P[0]) <= 2 and abs(box[3] - P[1]) <= 2,
              f"bottom-left ({box[0]}, {box[3]}) vs {P}")
        pad = 0.2 * (box[3] - box[1]) / 2
        check(f"{tag} text inside the box", text[0] - box[0] >= pad and box[2] - text[2] >= pad and text[1] - box[1] >= pad / 2
              and box[3] - text[3] >= pad / 2, f"box {box}, text {text}")
        drawn = im.getchannel("A").getbbox()
        check(f"{tag} nothing outside the box but the line", all(abs(drawn[i] - box[i]) <= 2 for i in (0, 2, 3))
              and box[1] - 16 <= drawn[1] < box[1], f"drawn {drawn}, box {box}")
        thumb(tag)

    box, under, text = rest["16x9"]
    ends = [frame("16x9", {}, t, f"end{n}").getchannel("A").getbbox() for n, t in ((0, 0), (1, DURATION - 1 / 24))]
    check("empty at the first and last frames", ends == [None, None], f"drawn at 0 s and {DURATION - 1 / 24:.2f} s: {ends}")
    win = box_of(frame("16x9", {}, 0.3, "wipe_in"))
    wout_im = frame("16x9", {}, DURATION - 0.35, "wipe_out")
    wout = box_of(wout_im)
    gone = measure(wout_im)[2] if wout else None
    check("the box wipes open and shut", win and wout and win[2] - win[0] < box[2] - box[0] - 50 and wout[2] - wout[0] < box[2] - box[0] - 50
          and abs(win[0] - box[0]) <= 2 and abs(wout[0] - box[0]) <= 2 and gone is None,
          f"box width at 0.3 s {win and win[2] - win[0]}, at {DURATION - 0.35:.2f} s {wout and wout[2] - wout[0]}, at rest {box[2] - box[0]}; "
          f"text while shutting: {gone}")
    thumb("wipe_in")

    long = "Twelve Apostles and the long road around Port Campbell"
    im = frame("16x9", {"Title": long, "Title Font": "Inter Bold"}, REST, "long")   # a plain font, for OCR to read both lines
    lbox, lunder, ltext = measure(im)
    white = im.crop((lbox[0], lbox[1], lbox[2], lunder[0])).convert("L").point(lambda v: 255 if v > 200 else 0)
    rows = [sum(white.crop((0, y, white.width, y + 1)).getdata()) for y in range(white.height)]
    third = white.height // 3
    mid = lbox[1] + min(range(third, 2 * third), key=lambda y: rows[y])   # the emptiest row between the lines (descenders above it)
    lines = [ocr(im, (lbox[0], lbox[1], lbox[2], mid)), ocr(im, (lbox[0], mid, lbox[2], lunder[0] - 2))]
    check("a long title wraps within Max Width", " ".join(lines) == long and lbox[2] - lbox[0] <= FRAMES["16x9"][2] + 2,
          f"read {lines}; box {lbox[2] - lbox[0]} px wide of {FRAMES['16x9'][2]}")
    thumb("long")
    nbox = measure(frame("16x9", {"Subtitle": ""}, REST, "no_sub"))[0]
    check("no subtitle: the box closes up", nbox[3] - nbox[1] < box[3] - box[1] - 30 and abs(nbox[3] - box[3]) <= 2,
          f"height {nbox[3] - nbox[1]} vs {box[3] - box[1]}")
    thumb("no_sub")

    W, H = FRAMES["16x9"][0]
    bw, bh = box[2] - box[0], box[3] - box[1]
    corners = []
    for name, P in (("top-left", [40, 40 + bh]), ("top-right", [W - 40 - bw, 40 + bh]), ("bottom-left", [40, H - 40]),
                    ("bottom-right", [W - 40 - bw, H - 40])):
        c = measure(frame("16x9", {"Position": P}, REST, f"corner_{name}"))[0]
        corners.append(abs(c[0] - P[0]) <= 2 and abs(c[3] - P[1]) <= 2 and c[2] <= W and c[1] >= 0)
    check("Position near each corner", all(corners), f"in place: {corners}")
    thumb("corner_top-right")

    for control, line in (("Title Font", 0), ("Subtitle Font", 1)):
        fim = frame("16x9", {control: "Montserrat Bold"}, REST, control.replace(" ", "_").lower())
        fbox, funder, _ = measure(fim)
        widths = []
        for b, u, img in ((box, under, Image.open(OUT / "16x9_rest.png").convert("RGBA")), (fbox, funder, fim)):
            bands = [(b[0], b[1], b[2], u[0]), (b[0], u[1] + 1, b[2], b[3])]
            inks = [img.crop(band).convert("L").point(lambda v: 255 if v > 200 else 0).getbbox() for band in bands]
            widths.append([i[2] - i[0] if i else 0 for i in inks])
        changed = [abs(x - y) > 10 for x, y in zip(*widths)]
        check(f"{control} changes only its line", changed == [line == 0, line == 1],
              f"title/subtitle ink widths {widths[0]} → {widths[1]}")
    thumb("title_font")

    cim = frame("16x9", {"Box Colour": "#ff0000", "Box Opacity": 40}, REST, "colour")
    px = cim.load()
    r, g, b, al = px[box[0] + 6, box[3] - 6]
    check("Box Colour and Box Opacity", r > 240 and g < 15 and b < 15 and abs(al - 102) <= 4, f"box corner pixel {(r, g, b, al)}")
    vfile = OUT / "duration.values.json"
    vfile.write_text(json.dumps({"Duration": 3}))
    clip = OUT / "duration.mov"
    run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", "16x9", "--values", vfile, "--out", clip,
         "--effectcraft-cli", a.effectcraft_cli])
    seconds = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip]).stdout.strip())
    check("Duration sets the clip length", abs(seconds - 3) <= 0.05, f"Duration 3 rendered {seconds:.2f} s")

    s = Image.new("RGB", (4 * 490 + 10, ((len(sheet) + 3) // 4) * 300 + 10), "white")
    for i, (tag, t) in enumerate(sheet):
        x, y = 10 + (i % 4) * 490, 10 + (i // 4) * 300
        s.paste(t, (x, y + 20))
        ImageDraw.Draw(s).text((x, y + 4), tag, fill=(0, 0, 0))
    s.save(OUT / "sheet.png")
    print(f"\n{sum(results)} of {len(results)} checks pass; sheet {OUT / 'sheet.png'}")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
