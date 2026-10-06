#!/usr/bin/env python3
"""Regenerate assets/AppIcon.ico from the reviewed assets/AppIcon.icns.

The macOS build script had a sibling, scripts/make-icon.sh, that rendered
assets/icon.svg through qlmanage and then masked it to the squircle the SVG
specifies. qlmanage has no Windows equivalent, so this port does not re-render the
artwork: it derives the .ico from the .icns that make-icon.sh already produced and
that the audit covers. Deriving is the honest choice here - re-rendering the same
SVG through a different rasteriser would produce a DIFFERENT icon, and the
published icon is part of what a user recognises.

Icon and .ico are the only formats involved; nothing here reads a wallet file.

Run on any machine with Pillow (it is in the desktop lock) and assets/AppIcon.icns:

    python scripts/make-windows-icon.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "AppIcon.icns"
TARGET = ROOT / "assets" / "AppIcon.ico"

# Windows asks for these; 256 is what Explorer uses for large thumbnails and
# 16/32 are what the taskbar and Alt-Tab use.
SIZES = (16, 32, 48, 64, 128, 256)


def largest_frame(source: Path) -> Image.Image:
    """The highest-resolution frame, so every smaller size is downsampled once.

    An .icns records (width, height, scale) triples, not pixel counts: the "512"
    entry with scale 2 is a 1024px image. Comparing the decoded pixels against the
    bare widths would call a perfectly good icon inconsistent.
    """
    with Image.open(source) as handle:
        frames = [frame.copy() for frame in ImageSequence.Iterator(handle)]
        sizes = handle.info.get("sizes") or ()
    if not frames:
        raise SystemExit(f"{source} contains no image frames.")
    # Pillow hands back one frame; 'sizes' is what lists the resolutions inside.
    if sizes:
        widest = max(width * scale for width, _, scale in sizes)
        if frames[0].width != widest:
            raise SystemExit(
                f"Pillow decoded {frames[0].width}px from {source} but it claims "
                f"{widest}px; the source icon is not what it appears to be."
            )
    frame = frames[0].convert("RGBA")
    if frame.width != frame.height:
        raise SystemExit(f"{source} is not square ({frame.width}x{frame.height}).")
    return frame


def main() -> int:
    if not SOURCE.is_file():
        raise SystemExit(f"{SOURCE} is missing; it is the reviewed icon master.")
    master = largest_frame(SOURCE)
    if master.width < max(SIZES):
        raise SystemExit(
            f"{SOURCE} is only {master.width}px; {max(SIZES)}px is the largest "
            "size Windows asks for."
        )
    # The corners are transparent because the artwork is a squircle. If they are
    # not, the mask was lost somewhere and every Windows launcher would show a
    # white square.
    if master.getpixel((0, 0))[3] != 0:
        raise SystemExit(f"{SOURCE} has an opaque corner; the squircle mask was lost.")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    master.save(TARGET, format="ICO", sizes=[(size, size) for size in SIZES])
    with Image.open(TARGET) as written:
        if written.size != (max(SIZES), max(SIZES)):
            raise SystemExit("the written .ico did not keep its largest size")
    print(f"Wrote {TARGET.relative_to(ROOT)} ({TARGET.stat().st_size} bytes, "
          f"sizes {', '.join(str(size) for size in SIZES)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
