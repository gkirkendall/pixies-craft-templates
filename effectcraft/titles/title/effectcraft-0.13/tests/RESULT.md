# Title: test result (2026-10-21)

**Pass: 41 of 41 checks.**

Run: `python3 effectcraft/titles/title/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; no GPU;
tesseract reads the text back). It renders single transparent frames with the shadow off and writes `tests/out/` (frames,
`sheet.png`; not committed).

| Case (16x9 and 9x16) | Result |
|---|---|
| Each of the six Places: text read back (label in capitals, then title) | exact |
| Each of the six Places: two bands of text, Margin from the named edges or centred | pass, exact to the pixel (16x9: 96 px, 9x16: 80 px) |
| No label, Bottom Right | pass: one band, still Margin from the bottom and right |
| A 59-character title | pass: shrunk to Max Width (1652 of 1651; 932 of 929, the ink a few pixels beyond the glyph box) |

Also: nothing one frame before Start; half-way through the fade in fainter (alpha 191) and 6 px lower; Fade, alpha at 0 s, 2 s
and the last frame of a 4 s clip: Fade In and Out 0, 255, 41; Fade In 0, 255, 255; Steady 255, 255, 255; Fade Out 255, 255, 41;
where Fade In, Steady and Fade Out clips meet, the frames are identical; Colour `#ffcc00` gives text averaging (255, 204, 0);
Shadow 50 draws a shadow; Duration 3 renders a 3.00 s clip.

Found on the way: tesseract misses the small spaced-out label when it reads the label and title together, so the test reads each
band of text on its own (`--psm 7`, enlarged).

**Fonts** (`tools/fontcheck.py`): Title Font and Label Font each take any font: Montserrat Bold changes the frame, and with that control's own text emptied it changes nothing, so it reaches no other text.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 39/39 |
| 2026-10-21 | 0.13.0 | pass | 41/41 |
| 2026-10-22 | 0.13.0 | pass | 41/41 |
| 2026-10-22 | 0.13.0 | pass | 41/41 |
| 2026-10-22 | 0.14.0 | pass | 41/41 |
