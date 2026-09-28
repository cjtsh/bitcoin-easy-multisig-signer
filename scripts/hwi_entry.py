"""Standalone HWI CLI entry point bundled beside the macOS app."""

import ctypes
import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    bundled_libusb = Path(sys._MEIPASS) / "libusb-1.0.0.dylib"
    if bundled_libusb.is_file():
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
            str(bundled_libusb.parent) + os.pathsep
            + os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        )
        ctypes.CDLL(str(bundled_libusb))

from hwilib._cli import main


if __name__ == "__main__":
    main()
