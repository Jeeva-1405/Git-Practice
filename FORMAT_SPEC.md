# LinkImage (.limg) Format Specification v1.0

A from-scratch raster image format. Pixel data is stored with our **own**
compression — there is no PNG, JPEG, WebP, or zlib data inside a `.limg` file.
A clickable-hotspot layer is part of the format itself.

## Byte layout (all integers big-endian)

```
OFFSET  SIZE  FIELD       MEANING
0       8     MAGIC       0x89 'L' 'I' 'M' 'G' 0x0D 0x0A 0x1A
8       2     VERSION     uint16, currently 1
10      4     WIDTH       uint32, pixels
14      4     HEIGHT      uint32, pixels
18      1     COMP        0 = raw RGBA, 1 = our RLE
19      4     PIX_LEN     uint32, length of pixel block
23      …     PIX_DATA    pixel block, encoded per COMP
…       4     HOT_LEN     uint32, length of hotspot JSON
…       …     HOT_DATA    UTF-8 JSON array of hotspots
```

## Pixel codec (COMP = 1, our RLE)

The image is a stream of RGBA pixels (4 bytes each, row-major, top-left first).
Our run-length encoding collapses consecutive identical pixels:

```
one run = [COUNT: 1 byte, 1..255] [R: 1] [G: 1] [B: 1] [A: 1]
```

To decode, repeat the RGBA value COUNT times, then move to the next run, until
the pixel buffer holds WIDTH * HEIGHT * 4 bytes.

This codec is intentionally simple so it's easy to read and port (e.g. to
Kotlin for Android). It compresses flat-color graphics very well; for
photographs you would extend it with a better scheme (delta + entropy coding),
but the container format would not change.

## Hotspot JSON

```json
[
  {"x":60,"y":120,"w":180,"h":90,"type":"url","value":"https://...","label":"Site"},
  {"x":440,"y":120,"w":180,"h":90,"type":"email","value":"me@mail.com","label":"Email"}
]
```

`x,y` = top-left of the clickable rectangle; `w,h` = its size; `type` is
`"url"` or `"email"`; `value` is the destination; `label` is optional.

## How a viewer displays it

1. Verify MAGIC, read the header.
2. Read PIX_DATA and run the codec to rebuild the raw RGBA buffer.
3. Paint that buffer straight to the screen (e.g. canvas `putImageData`, or an
   Android `Bitmap`). No other image library is involved.
4. On a tap at (px, py), find the first hotspot whose rectangle contains the
   point and open its `value`.
