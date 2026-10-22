#!/usr/bin/env python3
"""Make a template's style sheet: one image of all its styles, each labelled underneath (PLAN.md, WEB1).

  python3 tools/sheet.py effectcraft/titles/animated_title/effectcraft-0.13/previews/styles.json --footage DIR

styles.json (beside the template's demo.json; "{root}" and "{work}" are filled in as in demo.json):
  footage     the subfolder of --footage DIR
  background  a footage key: overlay templates are shown over this photo (whole, through Fill the Frame) dimmed, so every cell
              reads alike; omit it for templates that fill the frame
  prepare     commands to run first, as in demo.json (e.g. maps.py drawing a map picture)
  columns     cells per row (default 3)
  cells       in order, each {"label": "Style: Bounce", "values": V, "time": S, "variant": "16x9"}; V as in demo.json (a dict, a
              values-file path, or {"file": path, "set": {...}}); time: the moment shown (default 2); variant: default "16x9";
              "background": KEY overrides the sheet's photo for this cell; a value "{footage}/KEY" is that photo's path
The sheet is written as styles.jpg beside styles.json, cells at the same height, labels in Inter. Its JPEG comment records the
template's version and a hash of styles.json, which tools/catalog.py --check compares, so a stale sheet is caught.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

import demo

ROOT = demo.ROOT
CELL_H, GAP, LABEL_H, PAD = 300, 20, 44, 24
INK, PAPER = (24, 30, 38), (244, 244, 241)


def stamp(styles_path):
    """The JPEG comment a current sheet carries: the template's version and a hash of its styles.json."""
    manifest = json.loads((styles_path.parent.parent / "template.json").read_text())
    digest = hashlib.sha256(styles_path.read_bytes()).hexdigest()[:12]
    return f"craft-templates sheet; template {manifest['version']}; styles {digest}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("spec", type=pathlib.Path, help="a previews/styles.json")
    ap.add_argument("--footage", type=pathlib.Path, required=True, help="folder holding the footage subfolder styles.json names")
    ap.add_argument("--keep-work", type=pathlib.Path, help="keep the working files in this folder (for checking)")
    ap.add_argument("--effectcraft-cli", default="effectcraft-cli")
    a = ap.parse_args()
    spec_path = a.spec.resolve()
    template = spec_path.parent.parent.parent   # <template>/<version folder>/previews/styles.json
    spec = json.loads(spec_path.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        work = a.keep_work.resolve() if a.keep_work else pathlib.Path(tmp)
        work.mkdir(parents=True, exist_ok=True)
        d = demo.Demo(spec_path, a, work)
        d.prepare()
        backgrounds, cells = {}, []
        for k, cell in enumerate(spec["cells"]):
            variant = cell.get("variant", "16x9")
            values = cell.get("values", {})
            if isinstance(values, dict):   # "{footage}/KEY": that photo from --footage
                values = {n: str(d.footage(v[len("{footage}/"):]).resolve()) if isinstance(v, str) and v.startswith("{footage}/") else v
                          for n, v in values.items()}
            vfile = d.values_file(values)
            out = work / f"cell{k:02d}.png"
            r = subprocess.run([sys.executable, ROOT / "tools" / "render.py", template, "--variant", variant, "--values", vfile,
                                "--out", out, "--frame", str(cell.get("time", 2)), "--effectcraft-cli", a.effectcraft_cli],
                               capture_output=True, text=True)
            if vfile.name.startswith("_demo") and vfile.parent != work:
                vfile.unlink()
            if r.returncode:
                sys.exit(f"cell {k} ({cell['label']}): {r.stderr or r.stdout}")
            img = Image.open(out).convert("RGBA")
            key = cell.get("background", spec.get("background"))
            if key:
                if (key, variant) not in backgrounds:
                    values = work / f"bg_{key}_{variant}.values.json"
                    values.write_text(json.dumps({"Media": str(d.footage(key).resolve()), "Duration": 3}))
                    png = work / f"bg_{key}_{variant}.png"
                    demo.run([sys.executable, ROOT / "tools" / "render.py", demo.FILL, "--variant", variant, "--values", values,
                              "--out", png, "--frame", "1", "--effectcraft-cli", a.effectcraft_cli])
                    backgrounds[(key, variant)] = ImageEnhance.Brightness(Image.open(png).convert("RGBA")).enhance(0.75)
                base = backgrounds[(key, variant)].copy()
                base.alpha_composite(img)
                img = base
            else:
                base = Image.new("RGBA", img.size, (0, 0, 0, 255))
                base.alpha_composite(img)
                img = base
            img = img.convert("RGB").resize((round(img.width * CELL_H / img.height), CELL_H), Image.LANCZOS)
            cells.append((cell["label"], img))

    font = ImageFont.truetype(str(ROOT / "fonts" / "inter" / "Inter[opsz,wght].ttf"), 22)
    font.set_variation_by_name("Medium")
    columns = spec.get("columns", 3)
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    # Each cell's slot is as wide as its picture or its label, whichever is wider (a 9x16 picture is narrow).
    slots = [(label, img, max(img.width, round(measure.textlength(label, font=font)) + 16)) for label, img in cells]
    rows = [slots[i:i + columns] for i in range(0, len(slots), columns)]
    width = max(sum(w for _, _, w in row) + GAP * (len(row) - 1) for row in rows) + 2 * PAD
    sheet = Image.new("RGB", (width, PAD * 2 + len(rows) * (CELL_H + LABEL_H) + (len(rows) - 1) * GAP), PAPER)
    draw = ImageDraw.Draw(sheet)
    y = PAD
    for row in rows:
        x = PAD
        for label, img, w in row:
            sheet.paste(img, (x + (w - img.width) // 2, y))
            tw = draw.textlength(label, font=font)
            draw.text((x + (w - tw) / 2, y + CELL_H + 10), label, font=font, fill=INK)
            x += w + GAP
        y += CELL_H + LABEL_H + GAP
    out = spec_path.with_name("styles.jpg")
    sheet.save(out, quality=85, optimize=True, comment=stamp(spec_path).encode())
    print(f"{out} ({sheet.width}x{sheet.height}, {len(cells)} styles)")


if __name__ == "__main__":
    main()
