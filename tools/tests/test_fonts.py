#!/usr/bin/env python3
"""Test the font check of tools/render.py (PLAN.md, FONT2). Free: no app needed.

  python3 tools/tests/test_fonts.py

A stand-in effectcraft-cli reports version 0.13.0, lists a chosen set of fonts, and leaves a marker file if it is asked to render.
Checks, on the real Box Wipe Lower Third (Caveat Brush by default): with every font installed it renders; a misspelt font in the
values file stops it before rendering, suggesting the installed name; a default font that isn't installed stops it, naming this
repository's font file; a {font, style} value is accepted; --check-fonts reports and renders nothing; a template with no font
controls needs none.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "effectcraft" / "lower_thirds" / "box_wipe"
ALL = {"Caveat Brush": ["Regular"], "Montserrat": ["Regular", "Bold"], "Inter": ["Regular", "Bold"]}


def stand_in(tmp, fonts):
    """A stand-in effectcraft-cli with these fonts; it touches <tmp>/rendered when asked to render."""
    tmp = pathlib.Path(tmp)
    (tmp / "fonts.json").write_text(json.dumps({"families": [{"family": f, "origin": "system", "styles": s} for f, s in fonts.items()]}))
    cli = tmp / "effectcraft-cli"
    cli.write_text(f'#!/bin/sh\ncase "$1" in\n  exec) cat "{tmp}/fonts.json" ;;\n  render|render-frame) touch "{tmp}/rendered" ;;\n'
                   "  *) echo 'effectcraft-cli 0.13.0' ;;\nesac\n")
    cli.chmod(0o755)
    (tmp / "rendered").unlink(missing_ok=True)
    return cli


def render(tmp, cli, values, *extra, template=TEMPLATE):
    vfile = pathlib.Path(tmp) / "values.json"
    vfile.write_text(json.dumps(values))
    r = subprocess.run([sys.executable, ROOT / "tools" / "render.py", template, "--variant", "16x9", "--values", vfile,
                        "--out", pathlib.Path(tmp) / "out.png", "--frame", "2", "--effectcraft-cli", cli, *extra],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr, (pathlib.Path(tmp) / "rendered").exists()


def main():
    results = []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail.strip().replace("\n", " | "))

    with tempfile.TemporaryDirectory() as tmp:
        code, out, rendered = render(tmp, stand_in(tmp, ALL), {})
        check("all installed: renders", code == 0 and rendered, out or "rendered")
        code, out, rendered = render(tmp, stand_in(tmp, ALL), {"Title Font": "Montserat Bold"})
        check("misspelt value font stops it", code != 0 and not rendered and 'did you mean "Montserrat Bold"' in out
              and "nothing was rendered" in out, out)
        no_caveat = {f: s for f, s in ALL.items() if f != "Caveat Brush"}
        code, out, rendered = render(tmp, stand_in(tmp, no_caveat), {})
        check("missing default font stops it", code != 0 and not rendered and "fonts/caveat_brush/CaveatBrush-Regular.ttf" in out
              and "Title Font" in out and "Subtitle Font" in out, out)
        code, out, rendered = render(tmp, stand_in(tmp, no_caveat), {"Title Font": {"font": "Montserrat", "style": "Bold"},
                                                                     "Subtitle Font": "Inter Regular"})
        check("{font, style} and replaced defaults accepted", code == 0 and rendered, out or "rendered")
        code, out, rendered = render(tmp, stand_in(tmp, no_caveat), {}, "--check-fonts")
        check("--check-fonts reports and renders nothing", code != 0 and not rendered and "Fonts missing" in out, out)
        code, out, rendered = render(tmp, stand_in(tmp, {}), {}, "--check-fonts", template=ROOT / "effectcraft" / "overlays" / "glint")
        check("no font controls: nothing needed", code == 0 and not rendered and "uses no fonts" in out, out)
    print(f"\n{sum(results)} of {len(results)} checks pass")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
