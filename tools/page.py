#!/usr/bin/env python3
"""Build the catalogue web page, index.html at the repository root, from each template's manifest, style sheet and demo reels
(PLAN.md, WEB1, WEB2).

  python3 tools/page.py           write index.html
  python3 tools/page.py --check   exit 1 if index.html is not what this script would write now

One plain HTML file with its CSS inline: no scripts, no outside fonts or requests; it uses the committed sheets and reels in place
(GitHub Pages serves the repository root, .nojekyll making it serve every file as it is). At the top, the title and the PixBack
sponsor line linking to getpixback.com and the "Download all templates (zip)" link to the latest release (PLAN.md, RELEASE1),
beside Pixie (brand/pixie.png; PLAN.md, BRAND1); then the showreel and the Australia trip demo; then a
heading per category and a row per template: its style sheet (previews/styles.jpg) and its demo reel(s), each labelled
underneath, then its description, its download links and fonts (from the release), sizes, tested versions and a link to its folder. Videos load nothing until played.
tools/catalog.py --check also fails when the page is out of date.
"""
import argparse
import html
import pathlib
import re
import sys

from PIL import Image

import catalog
import versions

ROOT = catalog.ROOT
PAGE = ROOT / "index.html"
NAME = "Pixie's Craft Templates"
REPO = "https://github.com/gkirkendall/pixies-craft-templates"
PIXIE = ROOT / "brand" / "pixie_web.png"
# The release files tools/release.py builds (PLAN.md, RELEASE1); "latest" always fetches the newest release
ASSETS = f"{REPO}/releases/latest/download/"
ZIP, FONTS_ZIP = "pixies-craft-templates.zip", "pixies-craft-templates-fonts.zip"
# How to install (PLAN.md, INSTALL1); the README's "How to install" says the same
INSTALL = [
    '<strong>Get EffectCraft</strong> 0.13 or later: <a href="https://getartcraft.com/apps/effectcraft">getartcraft.com/apps/effectcraft</a>.',
    f'<strong>Download:</strong> <a href="{ASSETS}{ZIP}">every template in one ZIP</a>, with their fonts and a README; or one '
    "template at a time with its download link below (16x9, 9x16).",
    "<strong>Install the fonts:</strong> in the ZIP's fonts folder, or each template's Fonts link below; double-click a font file to install it "
    "(on Linux, copy it to ~/.local/share/fonts). All are free (SIL Open Font License). EffectCraft swaps a missing font for its own.",
    "<strong>Use it:</strong> in EffectCraft, <em>File ▸ Import ▸ Essential Graphics Template…</em>, then change its text, colours, "
    "fonts and timing in the Essential Graphics panel.",
    f'<strong>From a script</strong> (for tools that make videos): <code>tools/render.py</code>; see <a href="{REPO}#using-a-template">'
    "Using a template</a> in the README.",
]


def font_folder(family):
    """A font family's folder in fonts/ ("Caveat Brush" -> fonts/caveat_brush)."""
    return ROOT / "fonts" / re.sub(r"[^a-z0-9]+", "_", family.lower()).strip("_")
SPONSOR = ("Sponsored By PixBack - Photo and Video Backup to Google Photos", "https://getpixback.com/")   # the end card's line
CATEGORIES = [("maps", "Maps"), ("lower_thirds", "Lower Thirds"), ("titles", "Titles"), ("logos", "Logos"), ("overlays", "Overlays"),
              ("utility", "Utility")]
CSS = """
:root { --bg: #f6f5f1; --card: #ffffff; --ink: #1d232b; --muted: #5c6670; --line: #dedbd3; --accent: #1f5f8b; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #15191e; --card: #1e242b; --ink: #e9edf1; --muted: #9aa6b2; --line: #2e3640; --accent: #7cb7e0; } }
:root[data-theme="dark"] { --bg: #15191e; --card: #1e242b; --ink: #e9edf1; --muted: #9aa6b2; --line: #2e3640; --accent: #7cb7e0; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 1280px; margin: 0 auto; padding: 32px 16px 48px; }
h1 { font-size: 2rem; margin: 0 0 4px; }
.sponsor { font-size: 1.05rem; margin: 0 0 12px; }
.download a { display: inline-block; background: var(--accent); color: var(--bg); text-decoration: none; font-weight: 600;
  padding: 8px 16px; border-radius: 8px; margin-bottom: 16px; }
.brand { display: flex; gap: 28px; align-items: center; }
.brand img { flex: none; width: 170px; height: auto; }
@media (max-width: 760px) { .brand { flex-direction: column; align-items: flex-start; gap: 12px; } .brand img { width: 130px; } }
h2 { font-size: 1.4rem; margin: 48px 0 16px; padding-bottom: 6px; border-bottom: 1px solid var(--line); }
h3 { font-size: 1.1rem; margin: 0 0 12px; }
p { margin: 0 0 8px; }
a { color: var(--accent); }
.lead { color: var(--muted); margin-bottom: 24px; }
.row { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 16px; margin-bottom: 20px; }
.media { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 16px; align-items: start; }
.media.top { grid-template-columns: 1fr 1fr; }
.reels { display: flex; flex-direction: column; gap: 16px; }
@media (max-width: 760px) { .media, .media.top { grid-template-columns: 1fr; } }
figure { margin: 0; }
figure img, figure video { display: block; width: 100%; height: auto; border-radius: 6px; background: #000; }
figure video.tall { max-height: 420px; width: auto; max-width: 100%; margin: 0 auto; }
.install li { margin-bottom: 6px; }
figcaption { text-align: center; color: var(--muted); font-size: 0.9rem; margin-top: 6px; }
.meta { color: var(--muted); font-size: 0.9rem; margin-top: 12px; }
footer { color: var(--muted); font-size: 0.85rem; margin-top: 48px; border-top: 1px solid var(--line); padding-top: 16px; }
"""


def rel(path):
    """A repository file as the page links it: relative to the root, where the page is."""
    return path.relative_to(ROOT).as_posix()


def video(path, label):
    poster = path.with_name("poster" + path.stem[4:] + ".jpg" if path.stem.startswith("demo") else f"{path.stem}_poster.jpg")
    tall = ' class="tall"' if path.stem.endswith("9x16") else ""
    return (f'<figure><video{tall} controls preload="none" poster="{rel(poster)}" src="{rel(path)}"></video>'
            f"<figcaption>{html.escape(label)}</figcaption></figure>")


def current(template):
    fs = versions.folders(ROOT / template)
    return ([f for f in fs if not f.frozen] or fs)[-1]


def templates():
    """Every template's id ("effectcraft/maps/route_leg"), in the order found."""
    manifests = {}
    for app in catalog.APPS:
        for path in sorted((ROOT / app).rglob("template.json")) if (ROOT / app).is_dir() else ():
            if "/tests/out/" not in path.as_posix():
                manifests.setdefault(path.parent.parent.relative_to(ROOT).as_posix(), None)
    return list(manifests)


def build():
    manifests = templates()
    pixie_w, pixie_h = Image.open(PIXIE).size
    out = ["<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">', f"<title>{html.escape(NAME, quote=False)}</title>",
           f"<style>{CSS}</style>", "</head>", "<body>", "<main>", '<header class="brand">',
           f'<img src="{rel(PIXIE)}" width="{pixie_w}" height="{pixie_h}" alt="Pixie, the PixBack chihuahua, in a peach dinosaur costume">',
           f"<div><h1>{html.escape(NAME, quote=False)}</h1>",
           f'<p class="sponsor"><a href="{SPONSOR[1]}">{html.escape(SPONSOR[0])}</a></p>',
           f'<p class="download"><a href="{ASSETS}{ZIP}">Download all templates (zip)</a></p>',
           '<p class="lead">Free motion templates for EffectCraft: maps, lower thirds, titles, logos and overlays. Each row shows all '
           "of a template's styles in one picture and a demo reel that names the feature on screen.</p></div>", "</header>",
           "<h2>The templates together</h2>", '<div class="media top">',
           video(ROOT / "demo" / "showreel.mp4", "Showreel: every template"),
           video(ROOT / "demo" / "australia_trip" / "demo.mp4", "Australia trip: the templates in one travel video"), "</div>",
           '<h2 id="install">How to install</h2>', '<ol class="install">'] + [f"<li>{step}</li>" for step in INSTALL] + ["</ol>"]
    by_category = {}
    for template in manifests:
        f = current(template)
        by_category.setdefault(f.manifest["category"], []).append(f)
    for key, heading in CATEGORIES + [(k, k.replace("_", " ").title()) for k in sorted(by_category) if k not in dict(CATEGORIES)]:
        if key not in by_category:
            continue
        out.append(f"<h2>{html.escape(heading)}</h2>")
        for f in sorted(by_category[key], key=lambda f: f.manifest["name"]):
            m, previews = f.manifest, f.path / "previews"
            name = html.escape(m["name"])
            out.append(f'<section class="row" id="{m["id"].split("/")[-1]}"><h3>{name}</h3><div class="media">')
            out.append(f'<figure><img loading="lazy" src="{rel(previews / "styles.jpg")}" alt="{name}: all styles">'
                       f"<figcaption>{name}: all styles</figcaption></figure>")
            out.append('<div class="reels">')
            for demo in sorted(previews.glob("demo*.mp4"), key=lambda d: d.stem.endswith("9x16")):
                out.append(video(demo, f"{m['name']}: demo reel" + (" (9x16)" if demo.stem.endswith("9x16") else "")))
            out.append("</div>")
            sizes = ", ".join(v["key"] for v in m["variants"])
            downloads = " · ".join(f'<a href="{ASSETS}{pathlib.Path(v["file"]).name}">{v["key"]}</a>' for v in m["variants"])
            fonts = " · ".join(f'<a href="{ASSETS}{FONTS_ZIP}">{html.escape(n)}</a>' for n in m.get("fonts", []))
            out.append(f'</div><p class="meta">{html.escape(m["description"])}<br>Download: {downloads}' + (f' · Fonts: {fonts}' if fonts else '') + f'<br>Sizes: {sizes} · Tested with EffectCraft '
                       f'{html.escape(catalog.tested_text(m["id"]))} · <a href="{REPO}/tree/main/{m["id"]}">Template folder</a></p></section>')
    out += ["<footer>",
            "<p>The templates are free (MIT or Apache 2.0); their fonts are under the SIL Open Font License.</p>",
            "<p>The videos and style sheets show travel photos © Gregory Kirkendall, all rights reserved, not under "
            "the templates' licence. Music: “Relaxing Flute Tune” by Kerri, Sound Effects Factory (Free License). Maps: "
            'Natural Earth; map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>.</p>',
            "<p>Pixie is PixBack's mascot: © Gregory Kirkendall, all rights reserved, not under the templates' licence.</p>",
            f'<p><a href="{REPO}">Source and templates on GitHub</a></p>', "</footer>", "</main>", "</body>", "</html>", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if index.html is out of date")
    a = ap.parse_args()
    page = build()
    if a.check:
        ok = PAGE.is_file() and PAGE.read_text() == page
        print("index.html is up to date" if ok else "index.html is out of date; run python3 tools/page.py")
        sys.exit(0 if ok else 1)
    PAGE.write_text(page)
    print(f"wrote {PAGE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
