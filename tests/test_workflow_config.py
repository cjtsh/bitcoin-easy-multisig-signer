"""Static checks on the GitHub Actions workflow.

A broken shell block in a workflow costs a full CI round trip to discover, and a
tag-pinned action or a hardcoded version is easy to reintroduce. These checks are
cheap and run in the normal test suite.

Skipped when PyYAML is unavailable (it is deliberately NOT an application
dependency); CI installs it for the source job so the checks do run there.
"""

import pathlib
import re
import subprocess
import tempfile
import unittest

try:
    import yaml
except ImportError:  # pragma: no cover - depends on the environment
    yaml = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
ACTIVE = ROOT / ".github/workflows/build-candidate.yml"
STAGED = ROOT / "ci/build-candidate.yml"


@unittest.skipIf(yaml is None, "PyYAML not installed; workflow lint skipped")
class WorkflowConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = ACTIVE.read_text(encoding="utf-8")
        cls.data = yaml.safe_load(cls.text)

    def test_the_two_workflow_copies_are_identical(self):
        self.assertEqual(
            ACTIVE.read_text(encoding="utf-8"), STAGED.read_text(encoding="utf-8"),
            "ci/build-candidate.yml and .github/workflows/build-candidate.yml "
            "must not diverge; the source packaging script accepts either path.",
        )

    def test_every_shell_block_parses(self):
        checked = 0
        for job, spec in self.data["jobs"].items():
            for index, step in enumerate(spec.get("steps", [])):
                script = step.get("run")
                if not script:
                    continue
                checked += 1
                with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as handle:
                    handle.write(script)
                    path = handle.name
                result = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
                label = f"{job}/{step.get('name') or f'step {index}'}"
                self.assertEqual(result.returncode, 0,
                                 f"{label} has invalid shell:\n{result.stderr}")
        self.assertGreater(checked, 5, "expected to lint the workflow's shell blocks")

    def test_actions_are_pinned_to_commit_shas(self):
        uses = re.findall(r"uses:\s*(\S+)", self.text)
        self.assertTrue(uses)
        for reference in uses:
            with self.subTest(action=reference):
                self.assertRegex(
                    reference, r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$",
                    "actions must be pinned to a full commit SHA, not a tag",
                )

    def test_no_version_number_is_hardcoded(self):
        # The version is read from version.py, so bumping it needs no workflow edit.
        self.assertNotRegex(self.text, r"\b0\.1\.\d+\b",
                            "the workflow must not hardcode a version")

    def test_release_is_not_tag_gated_and_not_a_prerelease(self):
        # The owner asked for a plain release on push, not a candidate/pre-release.
        self.assertNotIn("--prerelease", self.text)
        self.assertNotIn("--clobber", self.text)
        release = self.data["jobs"]["release"]
        self.assertNotIn("if", release, "publishing must not be gated on a tag")
        self.assertEqual(release["permissions"], {"contents": "write"})

    def test_network_check_also_runs_without_ambient_trust(self):
        """Guards the check that caught the bundled-trust-store regression."""
        self.assertIn("SSL_CERT_DIR=/nonexistent/certs", self.text,
                      "CI must re-verify HTTPS with the host's CA configuration "
                      "removed, so only the bundled trust store can make it pass")


if __name__ == "__main__":
    unittest.main()
