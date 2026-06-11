# LinkImage (.limg) — a new image format with clickable links

This is a **genuinely new raster image format**, a peer to PNG and JPEG — not a
wrapper around them. Its pixel data is encoded by **our own compression codec**
(hand-written run-length encoding). There is **no PNG, JPEG, WebP, or zlib data
anywhere inside a `.limg` file** — verified below. Clickable links/emails are
part of the format itself.

## Why this is different from a normal image

| | PNG / JPEG | `.limg` |
|---|---|---|
| Own file signature | ✅ | ✅ `\x89LIMG` |
| Own pixel codec | ✅ | ✅ our RLE (no PNG/JPEG inside) |
| Clickable links built in | ❌ | ✅ native hotspot layer |

## Proof it contains no PNG/JPEG

`make_sample.py` writes `output/sample.limg`, then you can check:

```bash
python make_sample.py
python -c "d=open('output/sample.limg','rb').read(); \
print('starts with', d[:8]); \
print('has PNG?', b'\x89PNG' in d); \
print('has JPEG?', b'\xff\xd8\xff' in d); \
print('has zlib?', b'\x78\x9c' in d)"
```

Output: starts with `\x89LIMG`, and all three checks are `False`.

## Files

```
limg/
├── FORMAT_SPEC.md      # the exact byte layout of the format
├── make_sample.py      # draws a card, stores it as .limg (no PNG written)
├── limg/
│   ├── __init__.py
│   └── core.py         # our codec + encoder + decoder
└── viewer/
    └── index.html      # rebuilds pixels from our codec, paints to canvas
```

## Run it

```bash
pip install Pillow          # only used to DRAW shapes into a pixel buffer
python make_sample.py       # creates output/sample.limg
```

Then open `viewer/index.html` in a browser and drop in `sample.limg`. The image
appears and the three cards are clickable. The viewer uses **our** JavaScript
decoder and `canvas.putImageData` — the browser never decodes a PNG or JPEG.
(The Python encoder and the JS viewer were verified to produce byte-identical
pixels.)

## The one thing no format can change — please read this

You can invent a brand-new format (this is one). But **every** image format on
earth — PNG and JPEG included — needs a **decoder/viewer** to be shown on a
screen. Your phone displays PNGs only because Android ships with a PNG decoder
built in. A brand-new format has no decoder installed anywhere yet, so:

- It shows up and works in **our viewer** (web now, Android later).
- It will **not** preview in the system gallery, WhatsApp, or Instagram until
  those apps add support for it — which they won't for a private format. Worse,
  WhatsApp/Instagram re-encode every upload to JPEG, discarding anything custom.

So "an image with clickable links that works inside WhatsApp/Instagram" is
impossible for **any** format, new or old — because those apps strip
interactivity and flatten everything to JPEG by design. That's a platform wall,
not a format problem.

## What to build next (plays to your Android strength)

Make an Android app that:
1. Registers `.limg` as a file type it can open.
2. Decodes it with a Kotlin port of `core.py`'s RLE (≈20 lines).
3. Draws the pixels to a `Bitmap`, overlays the hotspots, and opens links on tap.

That gives you a real end-to-end format with its own viewer on your platform of
choice. The codec in `core.py` is deliberately tiny so the port is easy.
