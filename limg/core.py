"""
LinkImage (.limg) — a from-scratch raster image format.

UNLIKE the previous version, this stores pixels with its OWN compression
(a hand-written run-length encoder). There are NO PNG, JPEG, zlib, or WebP
bytes inside a .limg file. It is a true peer to those formats.

A viewer reconstructs the raw RGBA pixels from our codec and paints them
directly — nothing else decodes the image.

See FORMAT_SPEC.md for the byte layout.
"""

import struct
import json

MAGIC = b"\x89LIMG\x0d\x0a\x1a"
VERSION = 1

COMP_RAW = 0   # pixels stored uncompressed
COMP_RLE = 1   # pixels stored with our own run-length encoding


# --------------------------------------------------------------------------
# Our own pixel codec — this is what makes .limg a real format, not a wrapper.
# A "run" = [count: 1 byte (1-255)] [R] [G] [B] [A].
# Consecutive identical pixels collapse into one run.
# --------------------------------------------------------------------------
def rle_encode(rgba: bytes) -> bytes:
    out = bytearray()
    n = len(rgba)
    i = 0
    while i < n:
        r, g, b, a = rgba[i], rgba[i + 1], rgba[i + 2], rgba[i + 3]
        run = 1
        j = i + 4
        while j + 3 < n and run < 255:
            if (rgba[j] == r and rgba[j + 1] == g
                    and rgba[j + 2] == b and rgba[j + 3] == a):
                run += 1
                j += 4
            else:
                break
        out.append(run)
        out.extend((r, g, b, a))
        i += run * 4
    return bytes(out)


def rle_decode(data: bytes, width: int, height: int) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        run = data[i]
        r, g, b, a = data[i + 1], data[i + 2], data[i + 3], data[i + 4]
        out.extend(bytes((r, g, b, a)) * run)
        i += 5
    expected = width * height * 4
    if len(out) != expected:
        raise ValueError(f"pixel count mismatch: got {len(out)}, expected {expected}")
    return bytes(out)


class Hotspot:
    """A rectangular clickable region (link or email)."""

    def __init__(self, x, y, w, h, type, value, label=""):
        if type not in ("url", "email"):
            raise ValueError("type must be 'url' or 'email'")
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)
        self.type, self.value, self.label = type, value, label

    def to_dict(self):
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h,
                "type": self.type, "value": self.value, "label": self.label}

    @staticmethod
    def from_dict(d):
        return Hotspot(d["x"], d["y"], d["w"], d["h"],
                       d["type"], d["value"], d.get("label", ""))


def encode(rgba_bytes, width, height, hotspots, output_path, compress=True):
    """
    Write a .limg file directly from RAW RGBA pixel bytes.

    rgba_bytes : raw pixels, length must be width*height*4
    width,height: image dimensions
    hotspots   : list of Hotspot
    compress   : use our RLE codec (True) or store raw (False)
    """
    if len(rgba_bytes) != width * height * 4:
        raise ValueError("rgba_bytes length must equal width*height*4")

    if compress:
        comp = COMP_RLE
        pix = rle_encode(rgba_bytes)
    else:
        comp = COMP_RAW
        pix = bytes(rgba_bytes)

    hot_json = json.dumps([h.to_dict() for h in hotspots]).encode("utf-8")

    with open(output_path, "wb") as f:
        f.write(MAGIC)                          # 8
        f.write(struct.pack(">H", VERSION))     # 2
        f.write(struct.pack(">I", width))       # 4
        f.write(struct.pack(">I", height))      # 4
        f.write(struct.pack(">B", comp))        # 1
        f.write(struct.pack(">I", len(pix)))    # 4
        f.write(pix)                            # pixel block (OUR encoding)
        f.write(struct.pack(">I", len(hot_json)))
        f.write(hot_json)
    return output_path


def decode(limg_path):
    """Read a .limg file. Returns raw RGBA pixels + metadata + hotspots."""
    with open(limg_path, "rb") as f:
        if f.read(8) != MAGIC:
            raise ValueError("Not a valid .limg file (bad magic bytes)")
        version = struct.unpack(">H", f.read(2))[0]
        width = struct.unpack(">I", f.read(4))[0]
        height = struct.unpack(">I", f.read(4))[0]
        comp = struct.unpack(">B", f.read(1))[0]
        pix_len = struct.unpack(">I", f.read(4))[0]
        pix = f.read(pix_len)
        hot_len = struct.unpack(">I", f.read(4))[0]
        hotspots = [Hotspot.from_dict(d)
                    for d in json.loads(f.read(hot_len).decode("utf-8"))]

    if comp == COMP_RLE:
        rgba = rle_decode(pix, width, height)
    elif comp == COMP_RAW:
        rgba = pix
    else:
        raise ValueError(f"unknown compression id {comp}")

    return {"version": version, "width": width, "height": height,
            "rgba": rgba, "hotspots": hotspots}
