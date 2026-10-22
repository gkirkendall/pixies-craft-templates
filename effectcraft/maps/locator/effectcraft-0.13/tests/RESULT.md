# Locator: MAP1 test result (2026-10-21)

**Pass: 10 of 10 checks** (version 2.0.0: Name Font, Subtitle Font and Credit Font).

Run: `python3 effectcraft/maps/locator/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; about 20 s, no GPU). It draws the
locator map for the first example stop, Port Campbell National Park, renders the template full frame (16x9, 9x16) and as the 16x9
corner card, and writes `tests/out/` (frames, ProRes 4444 clips, `sheet.png`; not committed).

| Check | 16x9 card | 16x9 | 9x16 |
|---|---|---|---|
| Pin on the map's GPS position (pin to a marker painted into the map picture at the GPS point; limit 1 %) | 0.15 % of the card | 0.46 % of the frame | 0.47 % of the frame |
| No credit on a Natural Earth map (and the control draws one when filled) | pass | pass | pass |
| Transparent outside the card, solid inside | pass | n/a | n/a |
| Names exactly as supplied (by eye on `sheet.png`) | pass | pass | pass |

The pin check paints a ring into a copy of the map picture at the stop's GPS position (with the same Web Mercator view maps.py uses)
and finds it in the rendered frame after the zoom, so it tests the map picture, Place Position, the zoom and the inset together.

Fixed on the way: the zoomed map spilled past the corner card (now clipped by a Card Mask track matte); long names ran past the card
(now shrink to fit); and the test's first credit comparison read only the alpha channel (Pillow's `getbbox` on RGBA), so it now
compares RGB.

Still for Pixie: open `templates/locator_16x9.ectemplate` in the EffectCraft app and check its named controls.

**Fonts** (`tools/fontcheck.py`): Name Font, Subtitle Font and Credit Font each take any font: Montserrat Bold changes the frame, and with that control's own text emptied it changes nothing, so it reaches no other text.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 7/7 |
| 2026-10-21 | 0.13.0 | pass | 10/10 |
| 2026-10-22 | 0.13.0 | FAIL | 0/0 |
| 2026-10-22 | 0.13.0 | FAIL | 0/0 |
| 2026-10-22 | 0.13.0 | pass | 10/10 |
| 2026-10-22 | 0.14.0 | pass | 10/10 |
