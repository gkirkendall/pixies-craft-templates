# Glint Set

Six glints already placed and timed, one after another, across a title-sized band about the frame's centre, over transparency.
Drop it over a title picture and fit it with Spread. Each glint is the [Glint](../../glint/README.md) template's star and glow.

24 fps, as long as the Duration control (3.5 s by default, up to 30 s). Two sizes: `16x9` (1920×1080) and `9x16` (1080×1920). Both
render as ProRes 4444 with transparency, to lay over footage.

## Controls

| Control | What it does |
|---|---|
| Spread | How far apart the glints sit, in % about the frame's centre (100 by default); fit it to the title. |
| Size | Width of the biggest glint: 50 is the normal 140 px (the default), 100 is double; the others are 0.55 to 0.9 of it. |
| Colour | The glints' colour (warm white `#fff6dc` by default). |
| Glow | Strength of the soft glow, 0 to 100 (60 by default). |
| Duration | Length of the rendered clip in seconds (3.5 by default; the last glint is gone at 2.8 s). |

## Using it

```
python3 tools/render.py effectcraft/overlays/glint_set --variant 16x9 --values set.values.json --out glints.mov
```

with, for example, `set.values.json`: `{"Spread": 80}`. The glints start at 0.3, 0.6, 0.9, 1.2, 1.5 and 1.8 s, alternating left and
right so the eye travels across the title, and each lasts 1 s. To place glints one by one instead, use Glint.

No credits are needed.

## How it works

Six star-and-glow pairs built as in Glint, each at a fixed offset from the frame's centre (x as a fraction of 0.9 × the frame
width, y as a fraction of its shorter side, so the set keeps its shape in both sizes) times Spread/100, with its own start time and
relative size written into its expressions (`GLINTS` in `build/build.py`).

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/overlays/glint_set/effectcraft-0.13/build/build.py`.
- `previews/`: the demo reel and the `demo.json` it is made from.
- `tests/`: the test script and its result.
