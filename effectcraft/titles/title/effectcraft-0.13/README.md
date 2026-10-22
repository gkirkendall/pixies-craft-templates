# Title

One title line (Inter Bold) with an optional small label over it (Inter SemiBold, in spaced-out capitals), over transparency.
Place puts it in the centre, at the bottom centre or in a corner, Margin from the frame's edges. Each line shrinks on its own to
fit Max Width; with no label the title closes up. It fades and rises in at Start and fades out over the last 0.5 s before
Duration; the Fade control can leave out either, to hold a title steady across several clips (as Corner Logo does).

24 fps, as long as the Duration control (5 s by default, up to 60 s). Two sizes: `16x9` (1920×1080) and `9x16` (1080×1920). Both
render as ProRes 4444 with transparency, to lay over footage.

## Controls

| Control | What it does |
|---|---|
| Title | The title line. |
| Label | The small line over it, shown in spaced-out capitals; leave it empty for none. |
| Title Font | Inter Bold by default. |
| Label Font | Inter SemiBold by default. |
| Place | Centre (default), Bottom Centre, Bottom Left, Bottom Right, Top Left or Top Right. |
| Margin | Distance from the frame's edges for every Place but Centre, in pixels (96 in 16x9, 80 in 9x16). |
| Max Width | Widest either line may be, in % of the frame width (default 86: 1651 px on 1920 wide, 929 on 1080). |
| Colour | The text's colour (white by default). |
| Shadow | Strength of the soft shadow under the text, 0 to 100 (50 by default). |
| Fade | Fade In and Out (default), Fade In (then full to the end), Steady (full throughout) or Fade Out (full from the first frame, then fades out). |
| Start | When it starts to fade and rise in, in seconds (0.3 by default; fully in 0.6 s later); not used by Steady and Fade Out. |
| Duration | Length of the rendered clip in seconds (5 by default). |

## Using it

```
python3 tools/render.py effectcraft/titles/title --variant 16x9 --values effectcraft/titles/title/effectcraft-0.13/examples/australia.values.json --out title.mov
```

In a values file Place and Fade are the item's name (`"Place": "Bottom Left"`); `tools/render.py` refuses any other.

**Fonts:** Inter ships with EffectCraft (and is in this repository's `fonts/inter/`, SIL Open Font License). No credits are needed.

## How it works

Two text layers (Label, Title) and a "Controls" null. The label's text expression makes it capitals, and a Tracking text animator
over all of it spaces it out. One layout expression in both layers measures each with `sourceRectAtTime`, fits it to Max Width,
stacks the label 0.3 × the title's font size above the title (nothing when the label is empty), and places the block by Place:
its left, right or middle edge and its top, bottom or middle Margin from the frame. Opacity and a 24-pixel rise follow one eased
fade in and one eased fade out, which Fade can switch off. Fill effects colour the text from Colour, and a Drop Shadow sits under
it. Place and Fade are Dropdown Menu Controls.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/titles/title/effectcraft-0.13/build/build.py`.
- `examples/`: the values for the Australia trip's opening title.
- `previews/`: the demo reel and the `demo.json` it is made from.
- `tests/`: the test script and its result.
