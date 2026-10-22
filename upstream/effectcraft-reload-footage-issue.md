Found while building a trip-video project in EffectCraft 0.14.0 (macOS, Apple Silicon): photos filled to the frame, which people swap for their own.

Steps:
1. Import a 1920×1080 photo `Photo_2.jpg` and use it in a comp.
2. Overwrite `Photo_2.jpg` on disk with a photo of another shape (for example 1080×1350).
3. Reload Footage.

Expected: the item takes the new picture's size.
Seen: the item keeps 1920×1080, so anything sized from the item's width and height (a fill-the-frame expression, here) uses the old size, and the new picture comes out cropped. File ▸ Replace Footage with the same file reads the new size correctly.

Suggested fix: re-read the picture's size when footage is reloaded, as Replace Footage does.
