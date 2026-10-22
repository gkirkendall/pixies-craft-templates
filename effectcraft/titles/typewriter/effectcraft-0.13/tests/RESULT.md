# Typewriter: test result (2026-10-21)

**Pass: 15 of 15 checks.**

Run: `python3 effectcraft/titles/typewriter/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; no GPU;
tesseract reads the text back). It renders single transparent frames with the shadow off and writes `tests/out/` (frames,
`sheet.png`; not committed).

| Check | Result |
|---|---|
| Typed, 16x9 and 9x16: reads back exactly, centred on Position | exact, centred to the pixel |
| Part-way (4 and 15 letters), 16x9 and 9x16: reads exactly the letters typed by then; left edge where the finished line's is | exact; same left edge to the pixel |
| Nothing before Start without a cursor | pass |
| Bar: drawn while typing; once typed, on at 3.25 s and off at 3.75 s (then the right edge is the text's own) | pass |
| Underscore sits on the baseline | pass |
| Erase: part-way it reads the first 19 letters; gone 0.25 s before Duration | exact; gone |
| A 72-letter line shrinks to Max Width; Colour `#ffcc00` gives (255, 204, 0); Duration 3 renders 3.00 s | pass (1653 of 1651) |

**Fonts** (`tools/fontcheck.py`): Font takes any font: Montserrat Bold changes the frame.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 14/14 |
| 2026-10-21 | 0.13.0 | pass | 15/15 |
