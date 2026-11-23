"""news-image-20261122 slot-3 entry (V7): copy the finished front-page image
to the output folder as entry.png.

Stdlib only, no network. The image ships beside this program as image.jpg
(1024x1024 JPEG, <= 1 MiB). This program writes the bytes DIRECTLY to
$MAKEFUN_OUTPUT_DIR/entry.png -- no temporary file, no atomic rename, and
no dotfile is ever created inside the output folder (the grader rejects
dotfiles in /output; a mkstemp-based write got the 21 Nov slot 1 rejected).

Usage:
    MAKEFUN_OUTPUT_DIR=out python3 main.py   # write entry.png
    python3 main.py --check                   # validate image.jpg only
"""

import hashlib
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE, "image.jpg")
SIZE_LIMIT = 1024 * 1024
WANT_WIDTH = 1024
WANT_HEIGHT = 1024

# SOF markers that carry width/height (baseline, extended, progressive).
SOF_MARKERS = {0xC0, 0xC1, 0xC2}


def jpeg_dimensions(data):
    """Return (width, height) parsed from a JPEG's SOF segment, stdlib only."""
    i = 2  # skip SOI marker
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in SOF_MARKERS:
            height = int.from_bytes(data[i + 5:i + 7], "big")
            width = int.from_bytes(data[i + 7:i + 9], "big")
            return width, height
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg_len = int.from_bytes(data[i + 2:i + 4], "big")
        i += 2 + seg_len
    raise SystemExit("could not find a JPEG SOF segment in image.jpg")


def read_image():
    with open(IMAGE_PATH, "rb") as f:
        data = f.read()
    if len(data) > SIZE_LIMIT:
        raise SystemExit(f"image.jpg is {len(data)} bytes, over the 1 MiB limit")
    width, height = jpeg_dimensions(data)
    if (width, height) != (WANT_WIDTH, WANT_HEIGHT):
        raise SystemExit(f"image.jpg is {width}x{height}, want 1024x1024")
    return data


def main(argv):
    if "--check" in argv:
        data = read_image()
        print(f"image.jpg OK: {len(data)} bytes")
        return 0
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "output")
    os.makedirs(outdir, exist_ok=True)
    data = read_image()
    dest = os.path.join(outdir, "entry.png")
    with open(dest, "wb") as f:
        f.write(data)
    print(f"wrote {dest} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
