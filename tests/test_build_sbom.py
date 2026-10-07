"""The release dependency inventory must be parseable and identify its inputs."""

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("build_sbom", ROOT / "scripts" / "build-sbom.py")
build_sbom = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_sbom)


class BuildSbomTests(unittest.TestCase):
    def test_inventory_names_lock_commit_and_native_digest(self):
        digest = "a" * 64
        # The native library names and the lock file differ per platform; the
        # module is the one authority on both.
        names = build_sbom.native_library_names()
        shipped = {name: chr(ord("b") + index) * 64
                   for index, name in enumerate(names)}
        result = build_sbom.build(digest, ROOT, {"embit", "hwi"}, shipped,
                                  helper_sha="c" * 64)
        self.assertEqual(result["bomFormat"], "CycloneDX")
        self.assertEqual(result["specVersion"], "1.6")
        components = {component["name"]: component
                      for component in result["components"]}
        for name in names:
            self.assertEqual(components[name]["hashes"][0]["content"], shipped[name])
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
                         hashlib.sha256((ROOT / build_sbom.LOCK_FILE)
                                        .read_bytes()).hexdigest())
        self.assertEqual(properties["libusb_input_sha256"], digest)
        self.assertEqual(properties["hwi_helper_sha256"], "c" * 64)


class HelperDigestPins(unittest.TestCase):
    """CT-49: the helper's digest is recorded and checked, not assumed.

    probe.py refuses to run a helper whose bytes disagree with the hwi.sha256
    beside it. The SBOM must publish the same digest, and must fail rather than
    publish when the sidecar is missing or wrong — an SBOM that disagrees with
    the artifact is worse than no SBOM.
    """

    def _tree(self, folder: str) -> Path:
        helper = Path(folder) / "hwi"
        helper.write_bytes(b"synthetic helper bytes\n")
        return helper

    def test_the_recorded_digest_is_the_helper_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._tree(folder)
            digest = hashlib.sha256(helper.read_bytes()).hexdigest()
            helper.with_name("hwi.sha256").write_text(f"{digest}  hwi\n")
            with patch.object(build_sbom, "frozen_helper", return_value=helper):
                self.assertEqual(build_sbom.helper_digest(ROOT), digest)

    def test_a_missing_sidecar_fails_rather_than_publishing_a_weaker_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._tree(folder)
            with patch.object(build_sbom, "frozen_helper", return_value=helper):
                with self.assertRaisesRegex(ValueError, "Missing hwi.sha256"):
                    build_sbom.helper_digest(ROOT)

    def test_a_disagreeing_sidecar_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._tree(folder)
            helper.with_name("hwi.sha256").write_text("0" * 64 + "  hwi\n")
            with patch.object(build_sbom, "frozen_helper", return_value=helper):
                with self.assertRaisesRegex(ValueError, "does not match hwi"):
                    build_sbom.helper_digest(ROOT)

    def test_every_platform_build_writes_the_sidecar_next_to_the_helper(self):
        """The digest the app checks has to be produced by the build that ships.

        Pinned against the write, not the mention: an echo or a comment that
        says 'hwi.sha256' does not create the file, and a first version of this
        test went green while the write had been renamed away. Break-and-watch:
        rename the redirection target, watch this go red.
        """
        for name in ("build-macos.sh", "build-linux.sh", "build-windows.ps1"):
            with self.subTest(script=name):
                text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
                writes = [
                    line for line in text.splitlines()
                    if "hwi.sha256" in line
                    and not line.lstrip().startswith("#")
                    and (" > " in line or "Set-Content" in line)
                ]
                self.assertTrue(
                    writes,
                    f"{name} must redirect a digest into hwi.sha256; "
                    f"naming it in prose is not a write",
                )
                self.assertTrue(
                    any("CT-49" in line or "CT-49" in text for line in writes)
                    or "CT-49" in text,
                    f"{name} must say why it writes the sidecar",
                )


if __name__ == "__main__":
    unittest.main()
