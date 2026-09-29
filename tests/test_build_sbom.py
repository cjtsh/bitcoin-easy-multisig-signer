"""The release dependency inventory must be parseable and identify its inputs."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class BuildSbomTests(unittest.TestCase):
    def test_inventory_names_lock_commit_and_native_digest(self):
        digest = "a" * 64
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "BUILD-SBOM.json"
            subprocess.run([
                sys.executable, str(ROOT / "scripts/build-sbom.py"),
                "--libusb-sha", digest, "--output", str(target),
            ], check=True, cwd=ROOT)
            result = json.loads(target.read_text())
        self.assertEqual(result["bomFormat"], "CycloneDX")
        self.assertEqual(result["specVersion"], "1.6")
        components = {component["name"]: component
                      for component in result["components"]}
        self.assertEqual(components["libusb"]["hashes"][0]["content"], digest)
        self.assertIn("embit", components)
        properties = {entry["name"]: entry["value"]
                      for entry in result["metadata"]["properties"]}
        self.assertEqual(properties["requirements_desktop_sha256"],
                         hashlib.sha256((ROOT / "requirements-desktop.lock")
                                        .read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
