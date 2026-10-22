# Corner Logo

A logo picture of any shape, fitted inside a square box in a chosen corner of the frame, over transparency. It fades and rises in
at Start and fades out over the last 0.5 s before Duration; the Fade control can leave out either, to run a logo across a
whole video. One of the three end-card templates (with Credits and Sign-off, stacked over the last clip), and also the logo for
a corner of a commercial video.

24 fps, as long as the Duration control (5 s by default, up to 60 s). Two sizes: `16x9` (1920×1080) and `9x16` (1080×1920). Both
render as ProRes 4444 with transparency, to lay over footage.

## Controls

| Control | What it does |
|---|---|
| Logo | The logo picture, any shape (a PNG with transparency works best), fitted inside the Size box and centred. Default: a sample mark. An empty (transparent) picture shows nothing. |
| Corner | Top Left, Top Right, Bottom Right (default) or Bottom Left. |
| Size | Side of the square box the logo fits inside, in pixels (180 by default). |
| Margin | Distance from the box to the frame's two edges, in pixels (60 by default). |
| Opacity | How solid the logo is once it has faded in, 0 to 100 (90 by default). |
| Fade | Fade In and Out (default), Fade In (fades in, then full to the end), Steady (full from the first frame to the last) or Fade Out (full from the first frame, then fades out). |
| Start | When it starts to fade and rise in, in seconds (0.3 by default; fully in 0.5 s later); not used by Steady and Fade Out. |
| Duration | Length of the rendered clip in seconds (5 by default); with Fade In and Out or Fade Out the logo fades out over its last 0.5 s. |

## Using it

```
python3 tools/render.py effectcraft/logos/corner_logo --variant 16x9 --values logo.values.json --out logo.mov
```

with, for example, `logo.values.json`: `{"Logo": "my_logo.png", "Corner": "Top Left", "Duration": 8}` (the picture's path is
relative to the values file). In a values file Corner is the item's name; `tools/render.py` refuses any other.

### A logo across a whole video

Render one clip per photo or clip, each as long as it, and lay each over its own photo. Use `"Fade": "Fade In"` on the first,
`"Fade": "Steady"` on every one between and `"Fade": "Fade Out"` on the last; keep Corner, Size, Margin and Opacity the same.
The logo then fades in once, holds perfectly still across every cut, and fades out at the end. A single picture uses the
default, Fade In and Out.

No credits are needed.

## How it works

One Logo layer whose anchor is its own centre (so a swapped-in picture of any size stays centred), scaled by
min(Size / width, Size / height), and placed at the centre of a Size square Margin from the chosen corner's two edges. Its opacity
and a 24-pixel rise follow one eased fade in and one eased fade out, which Fade can switch off. Corner and Fade are Dropdown Menu Controls on the "Controls" null.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/logos/corner_logo/effectcraft-0.13/build/build.py`.
- `assets/`: the sample logo and an empty picture (see `assets/SOURCES.md`).
- `previews/`: the demo reels and the `demo*.json` they are made from.
- `tests/`: the test script and its result.
