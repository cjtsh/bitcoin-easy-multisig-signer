"""CT-94: the note that says how to verify one published attestation.

W20 (CT-94, releases/PLAN-0.6.8.md:207). The audit's first attempt reported
that ``GET /repos/.../attestations/tags/v0.6.7`` and a request "by subject
digest" both returned 404, while ``gh attestation verify`` succeeded for every
asset. The finding is that the digest in that API's path is not the bare hex
SHA-256 -- the documented form is ``sha256:HEX_DIGEST`` -- and that nothing is
indexed by tag, so the 404 described the shape of the request, not a missing
attestation.

The documentation is the deliverable here, so the control executes it: the URL
is read out of RELEASE-PROCESS.md and expanded by the same shell an operator
would use, with a known digest, then compared with the prefixed path. A note
that drops the prefix, or that points at a tag, renders a different URL and
goes red. That is what a test can do offline; the live check is
``gh attestation verify``, which the note names as the supported path.

Break-and-watch: drop the ``sha256:`` prefix from the documented REST URL, or
change it to a ``tags/`` path (both caught by the URL case), or rename the
runnable verify command (caught by the command case, which reads the command
line rather than the prose).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "RELEASE-PROCESS.md"

REPO = "cjtsh/bitcoin-easy-multisig-signer"
DOCUMENTED_COMMAND = re.compile(r'^gh attestation verify "\$ASSET" --repo (\S+)$', re.M)
DOCUMENTED_URL = re.compile(r'gh api "(repos/[^"]*/attestations/[^"]*)"')
DIGEST = "0f9043c88f7a0bbc6b9bbbf8289de9f67bc8c5678b83c7c4358cee68ab14a015"


class AttestationVerificationNoteTests(unittest.TestCase):
    """The note must keep the command that works and record why 404 misled."""

    @classmethod
    def setUpClass(cls):
        cls.text = DOC.read_text(encoding="utf-8")
        cls.bash = shutil.which("bash") or "/bin/bash"

    def test_the_note_names_the_supported_verification_command(self):
        matches = DOCUMENTED_COMMAND.findall(self.text)
        self.assertEqual(
            len(matches), 1,
            "RELEASE-PROCESS.md must carry exactly one runnable `gh attestation "
            "verify \"$ASSET\" --repo ...` command line; GitHub's HTTP API "
            "cannot verify a signature over an asset, it only returns the "
            f"bundle. Found {len(matches)}.")
        self.assertEqual(
            matches[0], REPO,
            "the verification command must name the repository an operator is "
            "verifying against, or the note is not re-runnable as written")

    def test_the_documented_rest_url_carries_the_sha256_prefix(self):
        matches = DOCUMENTED_URL.findall(self.text)
        self.assertEqual(
            len(matches), 1,
            "expected exactly one `gh api \"repos/.../attestations/...\"` line "
            f"in RELEASE-PROCESS.md, found {len(matches)}")
        url = matches[0]
        rendered = subprocess.run(
            [self.bash, "-c", f'DIGEST={DIGEST}; printf %s "{url}"'],
            capture_output=True, text=True)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertEqual(
            rendered.stdout,
            f"repos/{REPO}/attestations/sha256:{DIGEST}",
            "the documented REST URL must expand to the `sha256:`-prefixed "
            "subject digest. A bare hex digest is not the API's key -- it "
            "returns 404 exactly like a subject that has no attestation -- and "
            "no tag-indexed endpoint exists at all (CT-94).")

    def test_the_note_records_both_misleading_404_shapes(self):
        marker = "attestations/sha256:"
        self.assertIn(marker, self.text)
        index = self.text.index(marker)
        start = self.text.rindex("\n### ", 0, index)
        end = self.text.find("\n## ", index)
        note = self.text[start:end if end != -1 else len(self.text)]
        self.assertIn(
            "404", note,
            "the note must record the failure that started CT-94, or the next "
            "reader pays for it again")
        self.assertIn(
            "tags/", note,
            "the note must say that a tag-shaped path is not an endpoint; that "
            "was half of the original 404")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
