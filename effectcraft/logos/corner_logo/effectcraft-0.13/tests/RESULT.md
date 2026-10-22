# Corner Logo: test result (2026-10-21)

**Pass: 25 of 25 checks** (version 1.1.0: the Fade control).

Run: `python3 effectcraft/logos/corner_logo/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; no
GPU). It draws test logos (a solid wide 3:1, the same turned to 1:3, an empty picture), renders single transparent frames and
writes `tests/out/` (pictures, frames, a clip, `sheet.png`; not committed).

| Check | Result |
|---|---|
| A wide logo fits its 180 px box at 60 px from each corner, in both sizes (8 checks) | pass, exact to the pixel |
| A tall logo fits on its height (16x9, 9x16) | pass, exact |
| Size 300, Margin 20, Top Right | pass, exact |
| Nothing one frame before Start | pass |
| Half-way through the fade in: fainter (alpha 172 vs 230) and 6 px lower | pass |
| Opacity 90 → alpha 230; Opacity 50 → alpha 128 | pass |
| One frame before Duration 4: nearly gone (alpha 37) | pass |
| An empty picture draws nothing | pass |
| Fade, alpha at 0 s, 2 s and the last frame of a 4 s clip: Fade In and Out 0, 230, 37; Fade In 0, 230, 230; Steady 230, 230, 230; Fade Out 230, 230, 37 (4 checks) | pass |
| No jump at a cut: Fade In's last frame and Steady's first, Steady's last and Fade Out's first, are identical (2 checks) | pass, difference 0 |
| `"Corner": "Middle"` is refused by `tools/render.py`, naming the four | pass |
| Duration 3 renders a 3.00 s clip | pass |

Found on the way (EffectCraft 0.13): a Dropdown Menu Control is stored 0-based, and a values file sets it by that number only
(an item name is refused), while expressions read it 1-based as in After Effects. So the manifest has a `dropdown` control type
with its `options`, and `tools/render.py` turns the item name in a values file into the number.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 19/19 |
| 2026-10-21 | 0.13.0 | pass | 25/25 |
| 2026-10-21 | 0.13.0 | pass | 25/25 |
| 2026-10-22 | 0.13.0 | FAIL | 24/25 |
| 2026-10-22 | 0.13.0 | pass | 25/25 |
| 2026-10-22 | 0.14.0 | pass | 25/25 |
| 2026-10-22 | 0.13.0 | pass | 25/25 |
