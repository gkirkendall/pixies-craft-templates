#!/usr/bin/env python3
"""Test for Fill the Frame. Free: no GPU.

  python3 effectcraft/utility/fill_frame/effectcraft-0.13/tests/run.py --effectcraft-cli PATH

Draws three test pictures (4:3 and portrait 3:4 for 16x9, 16:9 for 9x16; a bright gradient with a grid and a 1 % red border) and
renders each through the template, then a clip and a looped clip. Checks: the whole picture (or clip frame) is shown, centred and fitted (the frame's fitted rectangle matches the
picture scaled to it, its red border included); no black bars (every row and column outside the picture is lit); Darken darkens
the copy behind; and the clip is as long as Duration. Results go to tests/out/ with a contact sheet.
"""
import argparse
import json
import shutil
import pathlib
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageStat

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE.parent
ROOT = next(p for p in TEMPLATE.parents if (p / "tools" / "render.py").is_file())
OUT = HERE / "out"
FRAMES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
CASES = [("4x3", (1600, 1200), "16x9"), ("3x4", (900, 1200), "16x9"), ("16x9", (1920, 1080), "9x16")]


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stderr or r.stdout}")
    return r.stdout


def picture(size):
    w, h = size
    im = Image.new("RGB", size)
    d = ImageDraw.Draw(im)
    for x in range(w):   # bright everywhere, so a dark area in the render can only be a bar
        d.line([(x, 0), (x, h)], fill=(80 + int(150 * x / w), 200 - int(100 * x / w), 120))
    for i in range(1, 8):
        d.line([(w * i // 8, 0), (w * i // 8, h)], fill=(250, 250, 250), width=max(w, h) // 200)
        d.line([(0, h * i // 8), (w, h * i // 8)], fill=(250, 250, 250), width=max(w, h) // 200)
    border = max(w, h) // 100
    d.rectangle((0, 0, w - 1, h - 1), outline=(230, 20, 20), width=border)
    return im


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--effectcraft-cli", default="effectcraft-cli")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    results, sheet = [], []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail)

    def render(variant, values, out, frame=1):
        vfile = OUT / f"{out.stem}.values.json"
        vfile.write_text(json.dumps(values))
        run([sys.executable, ROOT / "tools" / "render.py", TEMPLATE, "--variant", variant, "--values", vfile, "--out", out,
             "--effectcraft-cli", a.effectcraft_cli] + (["--frame", frame] if frame is not None else []))
        return Image.open(out).convert("RGB") if frame is not None else None

    for case, size, variant in CASES:
        src = picture(size)
        src.save(OUT / f"picture_{case}.png")
        tag = f"{case}_in_{variant}"
        img = render(variant, {"Media": f"picture_{case}.png"}, OUT / f"{tag}.png")
        W, H = FRAMES[variant]
        f = min(W / size[0], H / size[1])
        pw, ph = round(size[0] * f), round(size[1] * f)
        box = ((W - pw) // 2, (H - ph) // 2, (W - pw) // 2 + pw, (H - ph) // 2 + ph)
        shown = img.crop(box)
        expected = src.resize((pw, ph), Image.LANCZOS)
        diff = ImageStat.Stat(ImageChops.difference(shown, expected)).mean
        # The red border must be in the render at each edge of the fitted rectangle: nothing of the picture is cut off.
        b = max(2, round(max(size) // 100 * f) // 2)
        edges = [shown.crop(e) for e in ((0, 0, pw, b), (0, ph - b, pw, ph), (0, 0, b, ph), (pw - b, 0, pw, ph))]
        red = all(s[0] > 180 and s[1] < 80 for s in (ImageStat.Stat(e).mean for e in edges))
        check(f"{tag} whole picture shown", max(diff) < 8 and red,
              f"fitted {box}, mean difference from the picture {max(diff):.1f} (of 255); red border at all four edges: {red}")
        # No black bars: outside the picture, every row and column has light in it.
        outside = Image.new("L", (W, H), 255)
        ImageDraw.Draw(outside).rectangle((box[0], box[1], box[2] - 1, box[3] - 1), fill=0)
        grey = img.convert("L")
        dark = []
        for x in range(W):
            col = [grey.getpixel((x, y)) for y in range(0, H, 4) if outside.getpixel((x, y))]
            if col and max(col) < 16:
                dark.append(("column", x))
        for y in range(H):
            row = [grey.getpixel((x, y)) for x in range(0, W, 4) if outside.getpixel((x, y))]
            if row and max(row) < 16:
                dark.append(("row", y))
        lit = ImageStat.Stat(grey, outside).mean[0]
        check(f"{tag} no black bars", not dark, f"dark rows/columns outside the picture: {len(dark)}; mean brightness there {lit:.0f}")
        sheet.append((tag, img))

    # Darken: 0 leaves the copy behind as bright as the picture; 80 takes it well down.
    W, H = FRAMES["16x9"]
    side = (0, 0, 200, H)   # the left margin, outside a 4:3 picture
    light = ImageStat.Stat(render("16x9", {"Media": "picture_4x3.png", "Darken": 0}, OUT / "darken0.png").crop(side).convert("L")).mean[0]
    darker = ImageStat.Stat(render("16x9", {"Media": "picture_4x3.png", "Darken": 80}, OUT / "darken80.png").crop(side).convert("L")).mean[0]
    check("Darken darkens the copy behind", darker < light * 0.5, f"left margin brightness {light:.0f} at Darken 0, {darker:.0f} at 80")

    # A numbered photo beside other numbered photos (as a phone names them): EffectCraft would read the folder as an image
    # sequence and show colour bars, unless render.py hands the file over on its own. Rendered at 1 s, where a sequence has no frame.
    numbered = OUT / "numbered"
    numbered.mkdir(exist_ok=True)
    for n in (1, 2, 3):
        shutil.copyfile(OUT / "picture_4x3.png", numbered / f"IMG_000{n}.png")
    img = render("16x9", {"Media": "numbered/IMG_0002.png"}, OUT / "numbered_photo.png")
    diff = max(ImageStat.Stat(ImageChops.difference(img.crop((240, 0, 1680, 1080)), picture((1600, 1200)).resize((1440, 1080), Image.LANCZOS))).mean)
    check("a numbered photo among numbered photos", diff < 8, f"mean difference from the picture {diff:.1f} (of 255)")

    # Duration: the clip is as long as the control says.
    clip = OUT / "duration2.mp4"
    render("16x9", {"Media": "picture_4x3.png", "Duration": 2}, clip, frame=None)
    seconds = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip]).strip())
    check("Duration sets the clip length", abs(seconds - 2) <= 0.1, f"Duration 2 rendered {seconds:.2f} s")

    # A clip as Media: that 16:9 clip into 9x16 shows its frame at the same time, whole.
    still = OUT / "duration2_at1s.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", clip, "-frames:v", "1", still])
    img = render("9x16", {"Media": clip.name}, OUT / "clip_in_9x16.png")
    W, H = FRAMES["9x16"]
    ph = round(1080 * W / 1920)
    shown = img.crop((0, (H - ph) // 2, W, (H - ph) // 2 + ph))
    diff = max(ImageStat.Stat(ImageChops.difference(shown, Image.open(still).convert("RGB").resize((W, ph), Image.LANCZOS))).mean)
    check("a clip as Media", diff < 8, f"mean difference from the clip's frame at 1 s {diff:.1f} (of 255)")

    # Loop: a 2 s moving test pattern (ffmpeg testsrc2), Duration 5, plays again from the start at 2 s and 4 s.
    moving = OUT / "moving2.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1280x720:r=24:d=2", "-pix_fmt", "yuv420p", moving])
    looped = OUT / "looped5.mp4"
    render("16x9", {"Media": moving.name, "Duration": 5}, looped, frame=None)
    seconds = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", looped]).strip())
    # Which of the clip's 48 frames each rendered frame shows (closest match, in the fitted area): expect (t mod 2) × 24.
    frames = OUT / "moving2"
    frames.mkdir(exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", moving, frames / "%02d.png"])
    source = [Image.open(f).convert("RGB").resize((320, 180)) for f in sorted(frames.glob("*.png"))]
    shown = []
    for when in (0.5, 1.5, 2.5, 4.5):
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(when), "-i", looped, "-frames:v", "1", OUT / f"looped_{when}.png"])
        img = Image.open(OUT / f"looped_{when}.png").convert("RGB").resize((320, 180))
        shown.append(min(range(len(source)), key=lambda i: max(ImageStat.Stat(ImageChops.difference(img, source[i])).mean)))
    expected = [round((when % 2) * 24) for when in (0.5, 1.5, 2.5, 4.5)]
    check("a short clip loops up to Duration", abs(seconds - 5) <= 0.1 and all(abs(s - e) <= 1 for s, e in zip(shown, expected)),
          f"{seconds:.2f} s; at 0.5, 1.5, 2.5, 4.5 s it shows clip frames {shown} (expected {expected}, ±1)")

    tiles = []
    for tag, img in sheet:
        t = img.copy()
        t.thumbnail((480, 480))
        tiles.append((tag, t))
    s = Image.new("RGB", (sum(t.width for _, t in tiles) + 10 * (len(tiles) + 1), max(t.height for _, t in tiles) + 40), "white")
    x = 10
    for tag, t in tiles:
        s.paste(t, (x, 30))
        ImageDraw.Draw(s).text((x, 8), tag, fill=(0, 0, 0))
        x += t.width + 10
    s.save(OUT / "sheet.png")
    print(f"\n{sum(results)} of {len(results)} checks pass; sheet {OUT / 'sheet.png'}")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
