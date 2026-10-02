"""The release dependency inventory must be parseable and identify its inputs."""

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("build_sbom", ROOT / "scripts" / "build-sbom.py")
build_sbom = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_sbom)

WINDOWS_LOCK = "requirements-desktop-windows.lock"
BOOTSTRAP = (f"{WINDOWS_LOCK} has not been committed yet; dispatch "
             ".github/workflows/windows-inputs.yml and commit what it uploads "
             "(see WINDOWS-PORT.md)")


class BuildSbomTests(unittest.TestCase):
    def requirements_lock(self) -> Path:
        """The Windows lock cannot exist until the bootstrap workflow has run.

        Skipping is safe here rather than a hole: the build workflow refuses any
        run whose suite reports a skip at all, and it refuses to build without this
        lock regardless. On the platform that can produce the lock, its absence is
        a failure instead.
        """
        lock = ROOT / WINDOWS_LOCK
        if lock.is_file():
            return lock
        if sys.platform == "win32":
            self.fail(BOOTSTRAP)
        self.skipTest(BOOTSTRAP)

    def stub_root(self) -> Path:
        """A root that has a lock but no vendored wheel, for failure-path tests."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / WINDOWS_LOCK).write_text("stub lock\n", encoding="utf-8")
        return root

    def test_inventory_names_lock_commit_and_native_digest(self):
        lock = self.requirements_lock()
        digest = "a" * 64
        result = build_sbom.build(
            digest, ROOT, {"embit", "hwi"}, {"libusb-1.0.dll": digest})
        self.assertEqual(result["bomFormat"], "CycloneDX")
        self.assertEqual(result["specVersion"], "1.6")
        components = {component["name"]: component
                      for component in result["components"]}
        self.assertEqual(components["libusb-1.0.dll"]["hashes"][0]["content"], digest)
        self.assertEqual(components["cpython"]["version"], sys.version.split()[0])
        self.assertIn("embit", components)
        self.assertEqual(
            components["embit"]["hashes"],
            [{"alg": "SHA-256",
              "content": hashlib.sha256(
                  (ROOT / build_sbom.EMBIT_WHEEL).read_bytes()).hexdigest()}],
        )
        self.assertIn("symbolic", components["embit"]["properties"][0]["value"])
        self.assertNotIn("pip", components)
        properties = {entry["name"]: entry["value"]
                      for entry in result["metadata"]["properties"]}
        self.assertEqual(properties["requirements_desktop_sha256"],
                         hashlib.sha256(lock.read_bytes()).hexdigest())
        self.assertEqual(properties["libusb_input_sha256"], digest)

    def test_a_native_library_that_changed_after_verification_is_refused(self):
        """The frozen helper's bytes and the verified input must be the same."""
        with self.assertRaisesRegex(ValueError, "not the reviewed library"):
            build_sbom.build("a" * 64, self.stub_root(), set(),
                             {"libusb-1.0.dll": "b" * 64})

    def test_an_unreviewed_native_digest_is_refused(self):
        for bad in ("", "not-a-digest", "a" * 63, "a" * 65):
            with self.subTest(digest=bad):
                with self.assertRaisesRegex(ValueError, "Expected the verified SHA-256"):
                    build_sbom.build(bad, self.stub_root(), set(), {})


if __name__ == "__main__":
    unittest.main()
