"""CT-88: the vendored digests are stated in vendor/README.md as prose, and
nothing checked them against the bytes. This module is the machine check.

Three things are asserted, and each one is a way a prose digest goes wrong:

  * every registered file hashes to the digest the README states;
  * the README states every registered digest (so editing the prose alone
    breaks the check instead of silently changing what the project claims);
  * every file in vendor/ is either registered or listed below with a reason
    (so a new vendored artifact cannot arrive without a digest).

The digest the README states is not the authority; this map is, and the
`digests()` half of the check runs the same command the README documents
(`python scripts/vendor-digests.py`) so the instruction is exercised too.

Regeneration after a deliberate replacement:

    python scripts/vendor-digests.py
    ... update vendor/README.md and DIGESTS here in the same commit.

`VENDOR_DIR` is read from the environment so the break-and-watch can flip one
byte in a disposable copy rather than in the committed file:

    cp -R vendor /tmp/vendor-scratch
    printf 'x' | dd of=/tmp/vendor-scratch/embit-upstream-2b375a.tar.gz \
        bs=1 seek=100 count=1 conv=notrunc
    VENDOR_DIR=/tmp/vendor-scratch python -m unittest tests.test_vendor_pins
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = Path(os.environ.get("VENDOR_DIR") or (ROOT / "vendor"))
REGENERATE = ROOT / "scripts" / "vendor-digests.py"

# artifact -> the SHA-256 vendor/README.md states. A changed byte here is a
# changed input to a signed release: replacing one is a deliberate act.
DIGESTS = {
    "embit-upstream-2b375a.tar.gz":
        "3323c77583432be513b346bdc54f86f7ef5fb259e1db0e60975dc51bcbceb0a3",
    "embit-0.8.2+besa.1.tar.gz":
        "6974ac6dec0866ebbb5ab1f6e17cc78b187bedb40a31e514c94d50d2a3df0ad6",
    "embit-0.8.2+besa.1-py3-none-any.whl":
        "41a5e7e850a09f58cae0819ead68a96c4600f90b4e83a5a82f6af49b9d5660ba",
    "libusb-1.0.0.dylib":
        "8f6ad6c17c16f1e7769ad2f780ed2ddf98234ae6580cf5d87d9648cee1769201",
    "libusb-1.0.30.tar.bz2":
        "fea36f34f9156400209595e300840767ab1a385ede1dc7ee893015aea9c6dbaf",
    "libusb-1.0.dll":
        "f7ca6ca40f70e06140e1fab01deedb262464b45bface9eff62c1864e74ff1311",
    "appimage-runtime-x86_64":
        "2fca8b443c92510f1483a883f60061ad09b46b978b2631c807cd873a47ec260d",
}

# Files that carry no digest in vendor/README.md, and why. Anything else in
# vendor/ without an entry in DIGESTS is an unrecorded input.
UNREGISTERED = {
    "README.md": "the prose that states these digests",
    "libusb-COPYING": "the upstream licence text, bundled unmodified",
    "hwi-payload-3.2.0.json":
        "a generated manifest, checked against the installed wheel by "
        "scripts/build-hwi-manifest.py --check (CT-73)",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class VendorPinTests(unittest.TestCase):
    def readme(self) -> str:
        return (VENDOR / "README.md").read_text(encoding="utf-8")

    def test_every_registered_file_hashes_to_the_digest_the_readme_states(self):
        readme = self.readme()
        for name, expected in sorted(DIGESTS.items()):
            with self.subTest(artifact=name):
                artifact = VENDOR / name
                self.assertTrue(artifact.is_file(), f"{name} is missing")
                self.assertIn(
                    expected, readme,
                    f"vendor/README.md does not state the SHA-256 of {name}")
                self.assertEqual(
                    sha256(artifact), expected,
                    f"{name} does not match its recorded digest; if this was a "
                    "deliberate replacement, run python scripts/vendor-digests.py "
                    "and update vendor/README.md and DIGESTS here together")

    def test_no_vendored_file_is_left_without_a_recorded_digest(self):
        present = {path.name for path in VENDOR.iterdir() if path.is_file()}
        unrecorded = present - set(DIGESTS)
        self.assertEqual(
            unrecorded, set(UNREGISTERED),
            "vendor/ holds a file that is neither pinned nor listed as "
            "deliberately unpinned: " + ", ".join(sorted(unrecorded)))
        missing = set(DIGESTS) - present
        self.assertEqual(
            missing, set(),
            "DIGESTS names a file that is not vendored: " + ", ".join(sorted(missing)))

    def test_the_readme_documents_the_command_that_reproduces_them(self):
        readme = self.readme()
        self.assertIn("python scripts/vendor-digests.py", readme,
                      "vendor/README.md must document the regeneration command")
        printed = subprocess.run(
            [sys.executable, str(REGENERATE), str(VENDOR)],
            capture_output=True, text=True)
        self.assertEqual(
            printed.returncode, 0,
            f"python scripts/vendor-digests.py failed:\n{printed.stderr}")
        stated = {}
        for line in printed.stdout.splitlines():
            digest, _, name = line.partition("  ")
            if name:
                stated[name] = digest
        for name, expected in sorted(DIGESTS.items()):
            with self.subTest(artifact=name):
                self.assertEqual(
                    stated.get(name), expected,
                    f"the documented command reports {stated.get(name)} for "
                    f"{name}, the README and this test say {expected}")


if __name__ == "__main__":
    unittest.main()
