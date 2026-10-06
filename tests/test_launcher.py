"""The source-mode launcher's substituted-embit guard must match requirements.lock.

The launcher skips the hash-verified install only when the venv's embit is
exactly the pinned build. If the guard's version string drifts from the lock,
a stale public-registry embit passes it — audit finding CT-04.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def locked_embit_version() -> str:
    lock = (ROOT / "requirements.lock").read_text(encoding="utf-8")
    match = re.search(r"file:vendor/embit-(.+?)-py3-none-any\.whl", lock)
    if not match:
        raise AssertionError("requirements.lock must pin the vendored embit wheel")
    return match.group(1)


class LauncherTests(unittest.TestCase):
    def test_embit_guard_matches_the_locked_version(self):
        launcher = (ROOT / "Start Easy Multisig.command").read_text(encoding="utf-8")
        expected = locked_embit_version()
        self.assertIn(f'm.version("embit") == "{expected}"', launcher)

    def test_reinstall_is_hash_verified_from_the_lock(self):
        launcher = (ROOT / "Start Easy Multisig.command").read_text(encoding="utf-8")
        self.assertIn("--require-hashes -r requirements.lock", launcher)


if __name__ == "__main__":
    unittest.main()
