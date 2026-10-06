"""Keep source archives limited to the project's explicit document allowlist."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class BuildSourceTests(unittest.TestCase):
    def test_worktree_only_markdown_files_are_not_archive_inputs(self):
        script = (ROOT / "scripts" / "build-source.sh").read_text(encoding="utf-8")
        self.assertIn("root_docs=(", script)
        self.assertIn('cp "${root_docs[@]}" LICENSE THIRD-PARTY-NOTICES.md', script)
        self.assertIn('for file in "${root_docs[@]}" LICENSE THIRD-PARTY-NOTICES.md;', script)
        self.assertNotIn("for file in ./*.md", script)

    def test_the_archive_carries_what_its_own_tests_read(self):
        """The suite runs again inside the archive, so nothing it needs may be left out.

        The archive is extracted and the tests are re-run from inside it. A test that
        reads a file the archive did not copy fails there, and a missing reviewed
        native library fails the provenance check -- so the archive has to carry both
        libraries and both workflow recipes, in the shape the tests look for.
        """
        script = (ROOT / "scripts" / "build-source.sh").read_text(encoding="utf-8")
        for name in ("vendor/libusb-1.0.0.dylib", "vendor/libusb-1.0.dll",
                     "vendor/libusb-1.0.30.tar.bz2", "vendor/libusb-COPYING"):
            self.assertIn(name, script, f"the archive must ship {name}")
        self.assertIn("requirements-desktop-windows.lock", script)
        self.assertIn(
            "for recipe in build-candidate.yml windows-inputs.yml linux-inputs.yml",
            script, "the archive must ship the unified pipeline and both inputs recipes")
        self.assertIn('cp "$workflow" "$stage/$root/ci/$recipe"', script)


if __name__ == "__main__":
    unittest.main()
