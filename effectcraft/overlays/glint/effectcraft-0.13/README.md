# Glint

One four-point star that pops in at its Start time, turns a little and shrinks away over 1 s, with a soft glow behind it, over
transparency. Made to be used many times in one video: stack instances, each with its own Position, Start and Size, to catch the
light on a sail, a wave or a title.

24 fps, as long as the Duration control (2 s by default, up to 30 s). Two sizes: `16x9` (1920×1080) and `9x16` (1080×1920). Both
render as ProRes 4444 with transparency, to lay over footage.

## Controls

| Control | What it does |
|---|---|
| Position | Where the glint's centre is, in frame pixels. |
| Start | When it appears, in seconds; it is gone 1 s later (0.5 by default). |
| Size | Width of the star at its biggest: 50 is the normal 140 px (the default), 100 is double. |
| Colour | The star's and glow's colour (warm white `#fff6dc` by default). |
| Glow | Strength of the soft glow behind the star, 0 to 100 (60 by default). |
| Duration | Length of the rendered clip in seconds (2 by default). Make it at least Start + 1. |

## Using it

```
python3 tools/render.py effectcraft/overlays/glint --variant 16x9 --values glint.values.json --out glint.mov
```

with, for example, `glint.values.json`: `{"Position": [690, 142], "Start": 0.4, "Size": 61}`. For several glints, render one clip
per glint and lay them over each other, as `previews/demo.json` does over the Opera House. For a ready-made set of six, see
[Glint Set](../../glint_set/README.md).

No credits are needed.

## How it works

Two four-point star shapes (inner radius 0.11 of the outer, rounded 60 %): the star itself, and a 1.25× copy behind it, blurred by
Size/8, as the glow. Their scale follows one expression: from 0 at Start, eased out to full size at Start + 0.25 s, then eased in
to 0 at Start + 1 s; they turn 60° a second. Every control is an expression on a "Controls" null, so the template has no keyframes
to move.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/overlays/glint/effectcraft-0.13/build/build.py`.
- `previews/`: the demo reel and the `demo.json` it is made from.
- `tests/`: the test script and its result.
