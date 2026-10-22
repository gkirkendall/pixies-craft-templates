# Sign-off: test result (2026-10-21)

**Pass: 32 of 32 checks** (version 1.1.0: the Blink option).

Run: `python3 effectcraft/titles/sign_off/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; no GPU;
tesseract reads the text back). It renders single transparent frames with the shadow off and writes `tests/out/` (frames,
`sheet.png`; not committed).

| Case (16x9 and 9x16) | Text read back (OCR) | Hearts | Row |
|---|---|---|---|
| Default ("Thank you for watching") | exact | equal, 46 px (41 in 9x16), 26–31 px from the text | centred on Position, within 1 px |
| "Bye!" | exact | the same hearts, close in to the short line | centred |
| An 80-character line | exact | shrunk with the row (28 px; 16 in 9x16), same proportions | exactly Max Width |
| Position moved to (40 %, 30 %) | exact | as default | centred there |

The gaps on the two sides differ by up to 5 px: the text's box includes the font's side bearings ("T" and "g" sit differently in
it), so the check allows 10 % of the font size.

Also: nothing one frame before Start; 0.2 s after Start the text shows and the hearts do not; at 0.55 s they overshoot (the row
914 px wide vs 910 once in); one frame before Duration 4 nearly gone (alpha 41); Text Colour and Heart Colour colour all the solid
pixels; Shadow 50 draws a shadow; Duration 3 renders a 3.00 s clip. Blink at 60 beats a minute: the hearts are drawn at 2.6 s (in the
"on" part of a beat) and not at 3.1 s (the "off" part), the text's box is the same at both, and with Blink off the hearts are
there at 3.1 s.

Checked by eye in the demo: over the Opera House, white text on the white sails is hard to read even with the shadow, so the demo
puts the line on the water. Place it on a darker part of the picture, or raise Shadow.

**Fonts** (`tools/fontcheck.py`): Font takes any font: Montserrat Bold changes the frame.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 30/30 |
| 2026-10-21 | 0.13.0 | pass | 31/31 |
| 2026-10-21 | 0.13.0 | pass | 32/32 |
| 2026-10-22 | 0.13.0 | pass | 32/32 |
| 2026-10-22 | 0.14.0 | pass | 32/32 |
