# Route Leg

A line draws itself along a gentle arc between two places on a map. A pin pops in at each end and the place's name fades in
beside it. Use it full frame between clips, or switch on **Corner Inset** to get a small map card in the top-right corner over
transparency to lay over a clip.

5 seconds at 24 fps: the From pin and name at 0.3 s, the line from 0.6 to 2.2 s, the To pin and name at 2.1 s, then a hold.
Two sizes: `16x9` (1920×1080) and `9x16` (1080×1920). Both render as ProRes 4444 with alpha.

## Controls

| Control | What it does |
|---|---|
| Map | The map picture. Draw it with `tools/maps.py` (below) at the frame size. |
| From Position, To Position | The pins, in the map picture's pixels. `maps.py` works these out from the places' coordinates. |
| From Name, To Name | The place names. A name sits on the side of its pin away from the line and is kept inside the map. |
| Line Colour, Pin Colour | Colours of the line and the pins. |
| Curve | How far the line bows, as a percentage of its length: 0 is straight, and a negative value bows it the other way. |
| Corner Inset | Off: the map fills the frame. On: the map becomes a bordered card in the top-right corner, with transparency around it. |
| Map Credit | Small text in the map's bottom-right corner. Leave it empty for Natural Earth maps; `maps.py` fills it with "© OpenStreetMap" when a map has OpenStreetMap detail. |
| Texture | Optional paper or grain picture laid over the map in Multiply mode. White changes nothing. |
| Name Font | Any installed font, for both names, which always match (Inter Bold by default). |
| Credit Font | Any installed font, for the map credit (Inter Regular by default). |

## Making the maps

List your places in a stops file (`examples/australia.stops.json` shows the format: a name, a subtitle, and latitude and
longitude). Then:

```
python3 tools/maps.py fetch
python3 tools/maps.py route-legs --stops my.stops.json --out maps/ --variant 16x9
```

For each pair of places in turn, this writes the map picture `map_legNN_16x9.png` and a values file `legNN_16x9.values.json`.
Render one with:

```
python3 tools/render.py effectcraft/maps/route_leg --variant 16x9 --values maps/leg01_16x9.values.json --out leg01.mov
```

How `maps.py` draws a leg:
- Each map is framed around its two places, with at least 150 km across.
- Legs shorter than 25 km are skipped, since the two pins would almost touch (`--min-leg-km`).
- Legs shorter than 200 km also get roads, towns and parks from OpenStreetMap (`--osm-km`). That detail comes from the public
  Overpass server, one query at a time, and each answer is cached under `data/osm/`. For heavy or commercial use, point
  `--overpass-url` at your own or a paid Overpass server, as its usage policy asks. Each map's query is saved beside it as
  `*.overpass.txt`.

## Credits you need

- **Natural Earth** (land, lakes, borders): public domain, no credit needed.
- **OpenStreetMap** (when a map has roads, towns or parks): keep "© OpenStreetMap" visible on the map (the Map Credit control does
  this), and put "Map data © OpenStreetMap contributors, https://www.openstreetmap.org/copyright" in the video's description or
  credits.

## Files

- `templates/`: the built templates. Rebuild them with `python3 effectcraft/maps/route_leg/effectcraft-0.13/build/build.py`.
- `assets/`: the default maps and the blank texture (`assets/SOURCES.md`).
- `examples/`: the example stops and a values file for the corner card (`inset.values.json`).
