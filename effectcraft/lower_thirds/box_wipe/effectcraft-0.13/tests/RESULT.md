# Box Wipe Lower Third: test result (2026-10-21)

**Pass: 17 of 17 checks.**

Run: `python3 effectcraft/lower_thirds/box_wipe/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; no
GPU; tesseract reads the text back). It renders single transparent frames and writes `tests/out/` (frames, `sheet.png`; not
committed).

| Check | Result |
|---|---|
| At rest, 16x9 and 9x16: title and subtitle read back exactly (Caveat Brush) | exact |
| Box's bottom-left corner at Position | within 1 px |
| Text inside the box with room to spare; nothing drawn outside the box but the line along its top | pass |
| Empty at the first and last frames | pass |
| Wipes open (361 px wide at 0.3 s) and shut (narrower at 4.65 s, text already gone); 478 px at rest | pass |
| A 54-letter title wraps onto two lines that read back exactly; the box is 1100 px, Max Width | pass |
| No subtitle: the box closes up (157 px tall against 208) | pass |
| Position near each corner of the frame puts the box there | pass |
| Title Font and Subtitle Font each change only their own line (Montserrat Bold) | pass |
| Box Colour `#ff0000` at Box Opacity 40 gives (255, 0, 0, 102); Duration 3 renders 3.00 s | pass |

The long-title case uses Inter Bold, which OCR reads reliably; the wrap itself does not depend on the font.

Fixed on the way: a long title in a wide font still overflowed Max Width after wrapping; each line now also shrinks to fit.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 17/17 |
| 2026-10-21 | 0.13.0 | pass | 17/17 |
