"""The release dependency inventory must be parseable and identify its inputs."""

import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path

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
        result = build_sbom.build(digest, ROOT, {"embit", "hwi"}, shipped)
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


if __name__ == "__main__":
    unittest.main()
