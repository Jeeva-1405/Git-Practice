"""
make_sample.py — draws a card, extracts RAW pixels, and writes a .limg file
using our own codec. No PNG/JPEG is ever written for the image data.

(Pillow is used only to *draw* shapes into an in-memory pixel buffer, the same
way any drawing library would. We pull raw RGBA out with .tobytes() — we never
save a .png.)

Run:  python make_sample.py
"""

import os
from PIL import Image, ImageDraw, ImageFont
from limg import Hotspot, encode, decode

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)

W, H = 680, 420


def font(size, bold=False):
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(p, size) if os.path.exists(p) else ImageFont.load_default()


def centered(d, cx, y, text, f, fill):
    bb = d.textbbox((0, 0), text, font=f)
    d.text((cx - (bb[2] - bb[0]) / 2, y), text, font=f, fill=fill)


def draw_card():
    """Returns raw RGBA bytes for the card — no file is saved."""
    img = Image.new("RGBA", (W, H), (248, 247, 244, 255))
    d = ImageDraw.Draw(img)
    centered(d, W / 2, 34, "My Links", font(26, True), (26, 26, 24))
    centered(d, W / 2, 72, "Tap a card to open the link", font(14), (136, 135, 128))

    cards = [
        (60,  120, 180, 90, (230, 241, 251), (133, 183, 235), "My Portfolio",
         "jeeva-1405.github.io", (12, 68, 124)),
        (250, 120, 180, 90, (238, 237, 254), (175, 169, 236), "GitHub",
         "github.com/jeeva-1405", (60, 52, 137)),
        (440, 120, 180, 90, (234, 243, 222), (151, 196, 89), "Contact Email",
         "jeeva.1405@gmail.com", (39, 80, 10)),
    ]
    for (x, y, w, h, fill, border, label, value, tc) in cards:
        d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=fill, outline=border, width=2)
        centered(d, x + w / 2, y + 24, label, font(16, True), tc)
        centered(d, x + w / 2, y + 50, value, font(13), tc)

    centered(d, W / 2, 268, "Pixels stored with our own codec (no PNG inside).",
             font(13), (136, 135, 128))
    # raw RGBA out — this is the key line: we never img.save() a PNG
    return img.tobytes("raw", "RGBA")


def main():
    rgba = draw_card()
    print(f"Raw pixel bytes drawn: {len(rgba)} (= {W}x{H}x4)")

    hotspots = [
        Hotspot(60,  120, 180, 90, "url",   "https://jeeva-1405.github.io",  "My Portfolio"),
        Hotspot(250, 120, 180, 90, "url",   "https://github.com/jeeva-1405", "GitHub"),
        Hotspot(440, 120, 180, 90, "email", "jeeva.1405@gmail.com",             "Contact Email"),
    ]

    path = os.path.join(OUT, "sample.limg")
    encode(rgba, W, H, hotspots, path, compress=True)
    size = os.path.getsize(path)
    print(f"Wrote {path}  ({size} bytes)")

    # prove it round-trips: decode and compare pixels
    data = decode(path)
    assert data["rgba"] == rgba, "pixel mismatch after decode!"
    print("Round-trip OK — decoded pixels match the originals exactly.")
    print(f"  {data['width']}x{data['height']}, {len(data['hotspots'])} hotspots")
    for h in data["hotspots"]:
        print(f"    [{h.type}] {h.label}: {h.value}")


if __name__ == "__main__":
    main()
