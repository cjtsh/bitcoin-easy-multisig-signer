"""Provenance checks for the native library redistributed in the app.

Both builds ship libusb 1.0.30, and both ship it as bytes somebody had to review:
macOS redistributes an audited arm64 dylib, and Windows compiles its own DLL from
the same pinned upstream tarball in .github/workflows/windows-inputs.yml.

The DLL cannot be produced anywhere except Windows, so it arrives in two commits:
one that adds the artifact, and one that records its digest here. A build that
vendored the DLL without pinning it must fail rather than skip the check -- an
unpinned native library is exactly the thing this test exists to prevent.
"""

import hashlib
import tarfile
import unittest
from pathlib import Path

VENDOR = Path(__file__).resolve().parents[1] / "vendor"

# The upstream source both platform builds are accountable to.
LIBUSB_SOURCE = "libusb-1.0.30.tar.bz2"
LIBUSB_SOURCE_SHA256 = "fea36f34f9156400209595e300840767ab1a385ede1dc7ee893015aea9c6dbaf"

# file name -> reviewed SHA-256. The Windows digest came from
# .github/workflows/windows-inputs.yml run 37035301559 and is recorded in three
# other places (vendor/README.md, scripts/build-windows.ps1, and the
# LIBUSB_WINDOWS_SHA256 repository variable). Replacing one is a deliberate act:
# it is the moment the project claims "this is the library we ship".
REVIEWED = {
    "darwin": (
        "libusb-1.0.0.dylib",
        "8f6ad6c17c16f1e7769ad2f780ed2ddf98234ae6580cf5d87d9648cee1769201",
    ),
    "win32": (
        "libusb-1.0.dll",
        "f7ca6ca40f70e06140e1fab01deedb262464b45bface9eff62c1864e74ff1311",
    ),
}

PINNING_INSTRUCTIONS = (
    "Build the library with .github/workflows/windows-inputs.yml, review the "
    "uploaded artifact, commit it to vendor/{name}, then record its SHA-256 in "
    "vendor/README.md, in tests/test_libusb_vendor.py and in the "
    "$reviewedLibusbSha256 value of scripts/build-windows.ps1, and set the "
    "LIBUSB_WINDOWS_SHA256 repository variable."
)


class LibusbVendorTests(unittest.TestCase):
    def test_the_shipped_native_libraries_are_the_reviewed_ones(self):
        """Every committed native library, checked on every host platform.

        The files are committed, so anyone can verify the bytes the project
        ships; the check is deliberately not platform-gated, because the build
        workflow refuses a run whose suite reports a skip anywhere.
        """
        for name, digest in sorted(REVIEWED.values()):
            path = VENDOR / name
            if digest is None:
                self.fail(f"vendor/{name} has not been pinned yet. "
                          + PINNING_INSTRUCTIONS.format(name=name))
            if not path.is_file():
                self.fail(f"vendor/{name} is missing. "
                          + PINNING_INSTRUCTIONS.format(name=name))
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest,
                             f"vendor/{name} is not the reviewed library")

    def test_the_pinned_source_still_matches_its_digest(self):
        source = VENDOR / LIBUSB_SOURCE
        self.assertTrue(source.is_file(), f"vendor/{LIBUSB_SOURCE} is missing")
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), LIBUSB_SOURCE_SHA256)
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
    def test_the_windows_dll_is_built_from_that_same_source(self):
        """A different tarball would make the two platforms different libraries."""
        root = Path(__file__).resolve().parents[1]
        # The repository keeps the recipe in .github/workflows/ and the source
        # archive ships it under ci/, where this suite also runs.
        inputs = next((path for path in (root / ".github" / "workflows" / "windows-inputs.yml",
                                         root / "ci" / "windows-inputs.yml")
                       if path.is_file()), None)
        if inputs is None:
            self.fail("windows-inputs.yml is missing from both .github/workflows/ and ci/")
        text = inputs.read_text(encoding="utf-8")
        self.assertIn(LIBUSB_SOURCE_SHA256, text)
        self.assertIn(LIBUSB_SOURCE, text)
        # The tarball is the autotools dist, so the DLL comes from libusb's own
        # MSVC project -- x64, Release, static C runtime -- and not from CMake.
        self.assertIn(r"msvc\libusb_dll.vcxproj", text)
        self.assertIn("/p:Platform=x64", text)
        self.assertIn("/p:Configuration=Release-MT", text)
        # No CMake step survives: the pinned tarball has nothing for it to read.
        self.assertNotIn("cmake -S", text)
        self.assertNotIn("cmake --build", text)



if __name__ == "__main__":
    unittest.main()
