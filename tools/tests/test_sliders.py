#!/usr/bin/env python3
"""Test the slider-range check of tools/catalog.py (PLAN.md, SLIDER1). Free: no app needed.

  python3 tools/tests/test_sliders.py

A Number control is drawn as a slider over 0-100 and EffectCraft's Essential Graphics panel clamps to it, so a default of 1651
(pixels) shows as 100. Checks, on a scratch template: a default of 86 passes; a default of 1651 fails, naming the control; an
example value of 1651 fails; a nested preview value of 140 fails; a negative value fails; a value for a control that isn't a
Number (a Point) is not checked.
"""
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import catalog  # noqa: E402


def problems(default, example=None, preview=None):
    with tempfile.TemporaryDirectory() as tmp:
        folder = pathlib.Path(tmp)
        (folder / "examples").mkdir()
        (folder / "previews").mkdir()
        manifest = {"controls": [{"name": "Max Width", "type": "number", "default": default},
                                 {"name": "Anchor", "type": "point", "default": [960, 540]}]}
        (folder / "examples" / "a.values.json").write_text(json.dumps(example or {"Anchor": [960, 540]}))
        (folder / "previews" / "demo.json").write_text(json.dumps(preview or {}))
        return catalog.check_sliders(manifest, folder, "scratch")


def main():
    results = []

    def check(name, ok, detail):
        results.append(ok)
        print(("PASS " if ok else "FAIL ") + name + ": " + detail)

    check("default 86 passes", problems(86) == [], "no problems")
    e = problems(1651)
    check("default 1651 fails, naming the control", len(e) == 1 and "Max Width" in e[0] and "1651" in e[0], "; ".join(e))
    e = problems(86, example={"Max Width": 1651})
    check("example value 1651 fails", len(e) == 1 and "examples/a.values.json" in e[0], "; ".join(e))
    e = problems(86, preview={"segments": [{"values": {"Max Width": 140}}]})
    check("nested preview value 140 fails", len(e) == 1 and "previews/demo.json" in e[0], "; ".join(e))
    e = problems(86, example={"Max Width": -15})
    check("negative value fails", len(e) == 1, "; ".join(e))
    check("a Point is not checked", problems(86, example={"Anchor": [960, 540]}) == [], "no problems")
    print(f"\n{sum(results)} of {len(results)} checks pass")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
