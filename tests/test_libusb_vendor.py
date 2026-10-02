"""Provenance checks for the native library redistributed in the Mac app."""

import hashlib
import tarfile
import unittest
from pathlib import Path


VENDOR = Path(__file__).resolve().parents[1] / "vendor"


class LibusbVendorTests(unittest.TestCase):
    def test_reviewed_binary_and_corresponding_source_are_pinned(self):
        self.assertEqual(
            hashlib.sha256((VENDOR / "libusb-1.0.0.dylib").read_bytes()).hexdigest(),
            "8f6ad6c17c16f1e7769ad2f780ed2ddf98234ae6580cf5d87d9648cee1769201",
        )
        source = VENDOR / "libusb-1.0.30.tar.bz2"
        self.assertEqual(
            hashlib.sha256(source.read_bytes()).hexdigest(),
            "fea36f34f9156400209595e300840767ab1a385ede1dc7ee893015aea9c6dbaf",
        )
        with tarfile.open(source) as archive:
            license_text = archive.extractfile("libusb-1.0.30/COPYING").read()
        self.assertEqual((VENDOR / "libusb-COPYING").read_bytes(), license_text)


if __name__ == "__main__":
    unittest.main()
