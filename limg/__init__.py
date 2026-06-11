"""LinkImage (.limg) — a from-scratch image format with clickable links."""
from .core import (Hotspot, encode, decode,
                   rle_encode, rle_decode,
                   MAGIC, VERSION, COMP_RAW, COMP_RLE)

__version__ = "1.0.0"
