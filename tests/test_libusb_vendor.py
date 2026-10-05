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

    def test_the_build_script_itself_refuses_an_unverified_dylib(self):
        """LIBUSB_SHA256 is mandatory in the script, not only in CI (CT-12)."""
        script = (VENDOR.parent / "scripts" / "build-macos.sh").read_text(
            encoding="utf-8")
        self.assertIn('LIBUSB_SHA256 is required; refusing an unverified native '
                      'library.', script)
        self.assertIn('reviewed_libusb_sha256='
                      '"8f6ad6c17c16f1e7769ad2f780ed2ddf98234ae6580cf5d87d9648cee1769201"',
                      script)
        self.assertIn('Refusing to bundle a native library that does not match '
                      'LIBUSB_SHA256.', script)


if __name__ == "__main__":
    unittest.main()
