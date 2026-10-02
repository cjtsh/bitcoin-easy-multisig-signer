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
        result = build_sbom.build(
            digest, ROOT, {"embit", "hwi"},
            {"libusb-1.0.0.dylib": "b" * 64,
             "libusb-1.0.dylib": "c" * 64})
        self.assertEqual(result["bomFormat"], "CycloneDX")
        self.assertEqual(result["specVersion"], "1.6")
        components = {component["name"]: component
                      for component in result["components"]}
        self.assertEqual(components["libusb-1.0.dylib"]["hashes"][0]["content"], "c" * 64)
        self.assertEqual(components["libusb-1.0.0.dylib"]["hashes"][0]["content"], "b" * 64)
        self.assertEqual(components["cpython"]["version"], sys.version.split()[0])
        self.assertIn("embit", components)
        self.assertNotIn("pip", components)
        properties = {entry["name"]: entry["value"]
                      for entry in result["metadata"]["properties"]}
        self.assertEqual(properties["requirements_desktop_sha256"],
                         hashlib.sha256((ROOT / "requirements-desktop.lock")
                                        .read_bytes()).hexdigest())
        self.assertEqual(properties["libusb_input_sha256"], digest)


if __name__ == "__main__":
    unittest.main()
