# Basic Lower Third

A dark, slightly see-through bar slides in from the left with a title and a subtitle, holds, and fades out. The bar grows or
shrinks to fit the longer line. A line too wide for the frame shrinks until it fits; the other line keeps its size.

4 seconds at 24 fps: in by 0.5 s (eased), hold, fade out from 3.5 to 3.95 s. Two sizes: `16x9` (1920×1080) and `9x16`
(1080×1920). Both render as ProRes 4444 with alpha, to lay over a clip.

## Controls

| Control | What it does |
|---|---|
| Title | The first line, in bold. |
| Subtitle | The second line, smaller and lighter. |
| Title Font | Any installed font (Inter Bold by default). |
| Subtitle Font | Any installed font (Inter Regular by default). |

## Using it

```
python3 tools/render.py effectcraft/lower_thirds/basic --variant 16x9 --values effectcraft/lower_thirds/basic/effectcraft-0.13/examples/long.values.json --out lower_third.mov
```

No credits are needed: Inter is under the SIL Open Font License and ships with EffectCraft.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/lower_thirds/basic/effectcraft-0.13/build/build.py`.
- `examples/`: a values file with a long title.
- `tests/`: the test script and its result.

First made as the T-E1 test of the owner's motion-picture tool, then rebuilt here in Python with Inter and a font control for each line
(version 2.0.0: the single Font control, which the subtitle followed, became Title Font and Subtitle Font).
