#!/usr/bin/env python3
"""The font check every template with text runs in its test (PLAN.md, FONT1): each font control takes any font, and changes only
the text it belongs to.

  from fontcheck import font_checks
  for name, ok, detail in font_checks(frame, {"Title Font": ["Title"], "Subtitle Font": ["Subtitle"]}):
      check(name, ok, detail)

frame(values, tag) renders one frame (at a time when all the text shows) and returns it as a PIL image. For each font control:
another font must change the frame; and with the control's own texts emptied, another font must change nothing, so it reaches no
other text. A control whose texts can't be emptied (the template's only text) gets the first half only (pass texts=[]).
"""
from PIL import ImageChops

OTHER = "Montserrat Bold"   # ships with this repository (fonts/montserrat/), unlike every template's default


def differs(a, b):
    """The box where two frames differ, or None. Every channel counts: an RGBA image's getbbox() alone sees only alpha, which
    never changes on an opaque frame (the maps)."""
    return ImageChops.difference(a.convert("RGBA"), b.convert("RGBA")).getbbox(alpha_only=False)


def font_checks(frame, controls, base=None):
    """(name, ok, detail) for each font control in controls ({control: [its text controls]}); base: values for every frame."""
    base = dict(base or {})
    tag = lambda *parts: "font_" + "_".join(p.replace(" ", "_").lower() for p in parts)
    default = frame(base, tag("default"))
    results = []
    for control, texts in controls.items():
        changed = differs(default, frame(dict(base, **{control: OTHER}), tag(control)))
        ok, detail = changed is not None, f"{OTHER} changes the frame in {changed}"
        if texts:
            empty = dict(base, **{t: "" for t in texts})
            leak = differs(frame(empty, tag(control, "empty")), frame(dict(empty, **{control: OTHER}), tag(control, "empty_other")))
            ok = ok and leak is None
            detail += f"; with {', '.join(texts)} empty it changes {leak or 'nothing'}"
        results.append((f"{control} takes any font", ok, detail))
    return results
