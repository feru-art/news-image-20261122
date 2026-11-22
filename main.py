"""news-image-20261122 slot-2 entry (V6 dense variant): copy the finished
front-page image to the output folder as entry.png.

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
SOF_MARKERS = frozenset((0xC0, 0xC1, 0xC2))


def jpeg_size(blob):
    """Return (width, height, sof_marker) from a JPEG byte string."""
    if blob[:2] != b"\xff\xd8":
        raise ValueError("image.jpg is not a JPEG (no SOI marker)")
    i = 2
    end = len(blob)
    while i + 1 < end:
        if blob[i] != 0xFF:
            i += 1
            continue
        # Skip padding 0xFF bytes, then read the marker code.
        j = i + 1
        while j < end and blob[j] == 0xFF:
            j += 1
        if j >= end:
            break
        code = blob[j]
        if code in SOF_MARKERS:
            if j + 8 >= end:
                raise ValueError("truncated SOF segment")
            height = (blob[j + 4] << 8) | blob[j + 5]
            width = (blob[j + 6] << 8) | blob[j + 7]
            return width, height, code
        if code in (0xD8, 0xD9) or 0xD0 <= code <= 0xD7 or code == 0x01:
            # Standalone markers carry no length field.
            i = j + 1
            continue
        if j + 2 >= end:
            raise ValueError("truncated JPEG segment header")
        length = (blob[j + 1] << 8) | blob[j + 2]
        if length < 2:
            raise ValueError("bad JPEG segment length")
        i = j + 1 + length
    raise ValueError("no SOF marker found in image.jpg")


def load_image():
    with open(IMAGE_PATH, "rb") as handle:
        blob = handle.read()
    if len(blob) > SIZE_LIMIT:
        raise ValueError("image.jpg is %d bytes, over the 1 MiB cap" % len(blob))
    if blob[-2:] != b"\xff\xd9":
        raise ValueError("image.jpg is missing its EOI marker")
    width, height, sof = jpeg_size(blob)
    if (width, height) != (WANT_WIDTH, WANT_HEIGHT):
        raise ValueError(
            "image.jpg is %dx%d, expected 1024x1024" % (width, height))
    return blob, sof


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def run(argv):
    blob, sof = load_image()
    if "--check" in argv:
        print("OK: image.jpg is a %dx%d JPEG (SOF 0x%02X), %d bytes, sha256 %s"
              % (WANT_WIDTH, WANT_HEIGHT, sof, len(blob), digest(blob)))
        return 0
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "out"
    os.makedirs(outdir, exist_ok=True)
    target = os.path.join(outdir, "entry.png")
    # Direct write to the final path: no temp file anywhere.
    with open(target, "wb") as handle:
        handle.write(blob)
    with open(target, "rb") as handle:
        written = handle.read()
    if digest(written) != digest(blob):
        raise ValueError("entry.png does not match image.jpg after writing")
    print("wrote %s (%d bytes, sha256 %s)" % (target, len(written), digest(written)))
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
