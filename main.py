"""news-image-20261122 entry: write the approved image to /output/entry.png.

Stdlib only. No network. The image is shipped beside this program as
image.jpg (1024x1024 JPEG, <= 1 MiB). The program copies it byte-for-byte
to $MAKEFUN_OUTPUT_DIR/entry.png, writing DIRECTLY to the destination
(no temp files, no atomic rename, no dotfiles in /output -- the grader
rejects dotfiles in the output folder).

Usage:
    MAKEFUN_OUTPUT_DIR=out python3 main.py        # write entry.png
    python3 main.py --check                        # validate image.jpg only
"""

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "image.jpg")
MAX_BYTES = 1_048_576
EXPECT_W, EXPECT_H = 1024, 1024


def read_jpeg_dimensions(data):
    """Parse width/height from the first SOF marker of a JPEG byte string."""
    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        raise ValueError("not a JPEG (missing SOI marker)")
    pos = 2
    while pos + 9 < len(data):
        # Skip 0xFF fill bytes that may precede a marker.
        while pos < len(data) and data[pos] == 0xFF:
            pos += 1
        if pos + 9 >= len(data):
            break
        marker = data[pos]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 1
            continue
        seg_len = (data[pos + 1] << 8) | data[pos + 2]
        if seg_len < 2:
            raise ValueError("bad JPEG segment length at offset %d" % pos)
        if marker in (0xC0, 0xC1, 0xC2):
            height = (data[pos + 4] << 8) | data[pos + 5]
            width = (data[pos + 6] << 8) | data[pos + 7]
            return width, height
        pos += 1 + seg_len
    raise ValueError("no SOF marker found")


def load_and_validate():
    with open(SOURCE, "rb") as f:
        data = f.read()
    if len(data) > MAX_BYTES:
        raise ValueError("image.jpg is %d bytes, over the 1 MiB cap" % len(data))
    if not data.endswith(b"\xff\xd9"):
        raise ValueError("JPEG missing end marker")
    width, height = read_jpeg_dimensions(data)
    if (width, height) != (EXPECT_W, EXPECT_H):
        raise ValueError("dimensions %dx%d, expected 1024x1024" % (width, height))
    return data


def main(argv):
    if "--check" in argv:
        data = load_and_validate()
        print("OK: image.jpg %dx%d JPEG, %d bytes, sha256 %s"
              % (EXPECT_W, EXPECT_H, len(data),
                 hashlib.sha256(data).hexdigest()))
        return 0
    data = load_and_validate()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    out_path = os.path.join(outdir, "entry.png")
    # Direct write: no temp file, no rename, no dotfile in /output.
    with open(out_path, "wb") as f:
        f.write(data)
    # Verify what was written, byte for byte.
    with open(out_path, "rb") as f:
        written = f.read()
    if hashlib.sha256(written).hexdigest() != hashlib.sha256(data).hexdigest():
        raise ValueError("entry.png does not match image.jpg")
    print("wrote %s (%d bytes, sha256 %s)"
          % (out_path, len(written), hashlib.sha256(written).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
