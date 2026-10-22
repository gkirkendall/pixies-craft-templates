# Animated Title: test result (2026-10-21)

**Pass: 35 of 35 checks.**

Run: `python3 effectcraft/titles/animated_title/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; no
GPU; tesseract reads the text back). It renders single transparent frames with the shadow off and writes `tests/out/` (frames,
`sheet.png`; not committed).

| Check | Result |
|---|---|
| Each of the eight Styles at rest, 16x9 and 9x16: text read back without its stars, centred on Position | exact; centred to the pixel |
| Part-way in (0.35 s after Start), each Style but Spread In: the first third of the text has more ink drawn than the last; part-way out, less (7 checks) | pass (in: 0.02–0.03 vs 0.000; out: 0.000 vs 0.006–0.015) |
| Spread In part-way in is wider than at rest | 1146 px vs 887 |
| By Words / By Lines (Stagger 0.25): the first word or line further in than the last | words 0.98 vs 0.00 of their ink at rest; lines 0.98 vs 0.70 |
| Highlight Colour on the starred word only | 11 367 highlight pixels in "centre", none elsewhere, no white in "centre" |
| Nothing one frame before Start; Fade Steady full at the first and last frames; Fade In, Steady and Fade Out clips meet without a jump | pass (difference 0) |
| A 58-letter title fits Max Width and is at rest by 2 s | 1652 of 1651; 930 of 929 |
| Size 60 is half the width of Size 120; Font Montserrat Bold changes the width; Duration 3 renders 3.00 s | pass |

Found on the way (EffectCraft 0.13): an expression on a text selector's Based On or on a layer's Anchor Point Grouping is ignored
(both are menus that take a value only), so the template has one title layer per By item; with grouping by character, a word set
to scale or turn did so letter by letter about each letter's own centre. A long text at the default Stagger took longer to come
in than the clip allowed and began to leave before it had arrived, so the Stagger is now shortened to fit a third of Duration.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 35/35 |
| 2026-10-21 | 0.13.0 | pass | 35/35 |
