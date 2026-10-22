MAKE MAPS: map pictures for your own places
===========================================

The map shots in the trip video ("Stop 1" to "Stop 6") are example places. The map picture and the positions of the pins are drawn
by the script in this folder, maps.py, from a list of places. You only need this if you want maps of your own places. The names,
the pin colour and the credit line can be typed in the app without it.

One-time set-up
---------------
1. Install Python 3 (https://www.python.org/downloads/ : Windows, Mac and Linux). On Windows tick "Add Python to PATH".
2. Open a terminal in this folder ("Make Maps"): on Mac, right-click the folder and choose Services > New Terminal at Folder; on
   Windows, open the folder in File Explorer, click the address bar, type cmd and press Enter.
3. Install the one package the script needs (a picture library):

       python3 -m pip install pillow

   (On Windows use  python -m pip install pillow  and  python maps.py ...  wherever you see python3 below.)
4. Download the map data, once (about 52 MB; Natural Earth, public domain). It goes into a "data" folder here:

       python3 maps.py fetch

Your places
-----------
Open my.stops.json in a text editor and replace the six example places with yours, in travel order. Each place is a name, a short
subtitle (may be empty), and its latitude and longitude (right-click a place in Google Maps or Apple Maps to copy them; south and
west are negative numbers):

       {"name": "Stop 1", "subtitle": "", "lat": -38.618, "lon": 142.915}

Make the map pictures
---------------------
Full-screen route cards, one per leg (stop 1 to 2, 2 to 3, ...), for 16x9 (or 9x16 for the tall video):

       python3 maps.py route-legs --stops my.stops.json --out maps --variant 16x9

Small corner insets instead (to lay over a photo), add --inset:

       python3 maps.py route-legs --stops my.stops.json --out maps --variant 16x9 --inset

A "you are here" card for one place (0 is the first place):

       python3 maps.py locator --stops my.stops.json --stop 0 --out maps --variant 16x9

Short legs fetch roads and parks from OpenStreetMap (a little internet, one request at a time); the map's credit line says so.
Each command writes into the "maps" folder: a picture (map_leg01_16x9.png ...) and a "values" file beside it
(leg01_16x9.values.json ...) listing what to type for that card.

Use them in the video
---------------------
1. In EffectCraft, drag the new map picture (map_leg01_16x9.png) into the Project panel.
2. Click the map layer in the timeline (for example "Shot 5 · Route Leg map card").
3. In Window > Essential Graphics: pick your picture in Map, then type the numbers from the values file into From Position and
   To Position (the two pairs of numbers), and the names into From Name and To Name. For a locator card: Map, Place Position,
   Place Name. Turn Corner Inset on for the small version, off for full screen.

Credits: Natural Earth (public domain). OpenStreetMap data is (c) OpenStreetMap contributors, https://www.openstreetmap.org/copyright.
