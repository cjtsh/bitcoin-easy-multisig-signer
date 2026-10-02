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


if __name__ == "__main__":
    unittest.main()
