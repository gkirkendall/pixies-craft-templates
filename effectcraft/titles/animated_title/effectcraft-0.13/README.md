# Animated Title

A title that animates in letter by letter, word by word or line by line, holds, and animates out the same way before Duration,
over transparency. Eight Styles: Fade Up, Slide, Scale Pop, Turn, Blur, Spread In (the letters close in from wide spacing), Wave
(rise with a little overshoot) and Bounce (drop in and bounce). Words typed between stars, `*like this*`, take the Highlight
Colour; the stars are not shown. The Fade control can leave out the move in or the move out, to hold a title across several clips.
Centred on Position; a title too wide shrinks to Max Width.

24 fps, as long as the Duration control (4 s by default, up to 60 s). Two sizes: `16x9` (1920×1080) and `9x16` (1080×1920). Both
render as ProRes 4444 with transparency, to lay over footage.

## Controls

| Control | What it does |
|---|---|
| Text | The title. Words between stars take the Highlight Colour. A line break (`\r` in a values file) makes a second line. |
| Font | Inter Bold by default. |
| Style | Fade Up (default), Slide, Scale Pop, Turn, Blur, Spread In, Wave or Bounce. |
| By | Letters (default), Words or Lines: what moves on its own, one after another. |
| Stagger | Seconds between one letter, word or line starting and the next (0.05 by default). For a long text it is shortened so the move in takes at most a third of Duration. Spread In moves every letter together. |
| Ease | 0 (even speed) to 100 (a fast start that settles slowly); 50 by default. Scale Pop, Wave and Bounce keep their own curves. |
| Fade | Fade In and Out (default: in and out), Fade In (in only), Steady (neither: still from the first frame to the last) or Fade Out (out only). |
| Position | Centre of the title, in frame pixels ([960, 540] in 16x9, [540, 960] in 9x16). |
| Size | Font size in pixels (120 in 16x9, 96 in 9x16). |
| Max Width | Widest the title may be, in pixels (86 % of the frame width: 1651 or 929). |
| Colour | The text's colour (white by default). |
| Highlight Colour | The colour of the starred words (a warm yellow, `#ffd166`, by default). |
| Shadow | Strength of the soft shadow under the text, 0 to 100 (40 by default). |
| Start | When the first letter, word or line starts to move in, in seconds (0.3 by default). Each takes 0.6 s to arrive. |
| Duration | Length of the rendered clip in seconds (4 by default); the move out ends 0.1 s before it. |

## Using it

```
python3 tools/render.py effectcraft/titles/animated_title --variant 16x9 --values effectcraft/titles/animated_title/effectcraft-0.13/examples/australia.values.json --out title.mov
```

In a values file Style, By and Fade are the item's name (`"Style": "Bounce"`); `tools/render.py` refuses any other.

**Fonts:** Inter ships with EffectCraft (and is in this repository's `fonts/inter/`, SIL Open Font License). No credits are needed.

## How it works

A hidden "Raw" text layer holds the Text and Font controls. Three title layers, one each for Letters, Words and Lines (a text
selector's Based On and a layer's Anchor Point Grouping can be set only as values, not by an expression), show Raw's text without
its stars in Raw's style (`style.setText`); By shows one of them. Each has three text animators: one colours all of it, one gives
the starred words the Highlight Colour (an Expression Selector based on words that reads Raw's text), and one moves it: its
Position, Scale, Rotation, Opacity, Blur and Tracking hold where a unit is when fully "away", chosen by Style, and an Expression
Selector gives each unit (`textIndex` of `textTotal`) its eased amount from Start, Stagger and Duration. Scale Pop and Wave
overshoot (a negative amount), Bounce bounces. The layer's scale fits it to Size and Max Width, and its position centres it on
Position. A Drop Shadow sits under it.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/titles/animated_title/effectcraft-0.13/build/build.py`.
- `examples/`: the values for the Australia trip's opening title.
- `previews/`: the demo reel and the `demo.json` it is made from.
- `tests/`: the test script and its result.
