# Glint: test result (2026-10-21)

**Pass: 13 of 13 checks.**

Run: `python3 effectcraft/overlays/glint/effectcraft-0.13/tests/run.py --effectcraft-cli <path>` (EffectCraft 0.13.0; no GPU). It
renders single transparent frames and writes `tests/out/` (frames, a clip, `sheet.png`; not committed).

Two separately placed instances in each size (16x9: Start 0.5 Size 140 and Start 1.25 Size 220; 9x16: Start 0.5 Size 140 and
Start 1.0 Size 200), each checked three ways:

- empty one frame before Start and drawn one frame after it (the start is right within one frame);
- at its peak (Start + 0.25 s) its centre is on Position within 1 % of the frame, and nothing is drawn further than 0.8 × Size
  from it;
- gone by Start + 1.05 s.

Also: Duration 2.5 renders a 2.50 s clip.

Checked by eye in the demo: six glints over the Opera House photo. Glints on the white sails barely show, so the demo puts them
on the sail tips against the sky and on the water; a darker Colour would suit a pale background.

## Tested versions

Written by `tools/verify.py`; newest last.

| Date | EffectCraft | Result | Checks |
|---|---|---|---|
| 2026-10-21 | 0.13.0 | pass | 13/13 |
| 2026-10-21 | 0.13.0 | pass | 13/13 |
| 2026-10-22 | 0.13.0 | FAIL | 9/13 |
| 2026-10-22 | 0.13.0 | pass | 13/13 |
| 2026-10-22 | 0.14.0 | pass | 13/13 |
| 2026-10-22 | 0.13.0 | pass | 13/13 |
