# Credits: test result (2026-10-21)

**Pass: 39 of 39 checks** (version 1.2.0: the title can be left out; 1.1.0: up to five credit lines).

Run: `python3 effectcraft/titles/credits/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; no GPU;
tesseract reads the text back). It renders single transparent frames with the shadow off and writes `tests/out/` (frames,
`sheet.png`; not committed).

| Case (16x9 and 9x16) | Text read back (OCR) | Layout: bands of text, width, centre |
|---|---|---|
| Defaults (three lines) | exact | pass: 4 bands, centred within 6 px |
| Four lines | exact | pass: 5 bands |
| Five lines | exact | pass: 6 bands, the block still centred |
| No title | exact, no quotes | pass: 3 bands, the lines centred on Position |
| Line 1 empty | exact | pass: 3 bands, closed up |
| Line 2 empty | exact | pass: 3 bands, closed up |
| A 71-character title and a long line | exact | pass: the title on two lines, 5 bands, within Max Width |
| Position moved to (40 %, 30 %) of the frame | exact | pass: centred there |

Also: nothing one frame before Start; half-way through the fade in fainter (alpha 191) and 7 px lower; one frame before Duration 4
nearly gone (alpha 41); Colour `#ffcc00` gives text averaging (255, 204, 0); Shadow 50 draws a soft dark shadow below the text.

OCR reads a curly quote as straight now and then, and a middle dot (·) as a hyphen, so the comparison treats each pair alike;
the characters must still be there.

Found on the way (EffectCraft 0.13): in an expression, `String.prototype.substr` is "not a callable function" (it works in
`effectcraft-cli script`); `slice` works. A text expression that fails falls back to the plain text without a warning in the
render, so the long title first showed in lower case without quotes. `"\r"` in a text expression's result breaks the line.

**Fonts** (`tools/fontcheck.py`): Title Font and Line Font (all five lines) each take any font: Montserrat Bold changes the frame, and with that control's own text emptied it changes nothing, so it reaches no other text.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 29/29 |
| 2026-10-21 | 0.13.0 | pass | 33/33 |
| 2026-10-21 | 0.13.0 | pass | 37/37 |
| 2026-10-21 | 0.13.0 | pass | 39/39 |
| 2026-10-22 | 0.13.0 | pass | 39/39 |
| 2026-10-22 | 0.14.0 | pass | 39/39 |
| 2026-10-22 | 0.13.0 | pass | 39/39 |
