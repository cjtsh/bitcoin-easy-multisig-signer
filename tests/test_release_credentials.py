"""CT-97: the platform half of the release-credential scope.

A repository secret is handed to a job on **any** ref. A dispatch at a
historical tag therefore runs that tag's own frozen (older, less guarded)
workflow text but still receives today's signing keys, because secrets are
matched by name and never by tag. Tags are immutable history, so the fix cannot
live in the tag: the credentials moved into two protected environments whose
deployment rule allows `main` only, and the two jobs that use them declare those
environments.

`scripts/check-release-credentials.sh` is the standing check for that half — no
unit test can see a GitHub setting. These tests run the **real** script against
a fake `gh` that answers from fixture JSON, so each refusal is demonstrated
rather than asserted by reading the script's text. At least one positive case
runs the honest path to completion.
"""

import json
import os
import pathlib
import shutil
import tempfile
import unittest

from support import run_bash_file

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check-release-credentials.sh"
REPO = "owner/repo"
RELEASE_SECRETS = ("GPG_PRIVATE_KEY", "GPG_PASSPHRASE")
APPLE_SECRETS = ("MAC_CERT_P12_BASE64", "MAC_CERT_PASSWORD", "MAC_APP_SPECIFIC_PASSWORD")

# A fake `gh`: it answers only the read-only `api` paths the check reads, one
# JSON fixture per path, and fails closed for anything else. The slug replaces
# `/` with `_`, which is why every fixture path is a single flat filename.
FAKE_GH = """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" != "api" ]]; then
  echo "fake gh: unsupported invocation: $*" >&2
  exit 64
fi
path="${2:-}"
slug="$(printf '%s' "$path" | tr '/' '_')"
fixture="__FIXTURES__/$slug.json"
if [[ ! -f "$fixture" ]]; then
  echo "fake gh: no fixture for $path" >&2
  exit 1
fi
cat "$fixture"
"""


class CredentialWorld:
    """The GitHub-side facts the check reads, as fixture JSON.

    Defaults describe a fully-armed control, so each test can break exactly one
    thing and the refusal it expects is unambiguous.
    """

    def __init__(self):
        self.repository_secrets = []  # names still at repository level
        self.missing_environments = set()
        self.reviewers = {"release-signing": 1, "apple-signing": 0}
        self.policies = {
            "release-signing": ["main branch"],
            "apple-signing": ["main branch"],
        }
        self.secrets = {
            "release-signing": list(RELEASE_SECRETS),
            "apple-signing": list(APPLE_SECRETS),
        }

    def _endpoints(self):
        for name in ("release-signing", "apple-signing"):
            if name in self.missing_environments:
                continue
            reviewers = [
                {"type": "User", "reviewer": {"login": "owner"}}
                for _ in range(self.reviewers[name])
            ]
            yield f"repos/{REPO}/environments/{name}", {
                "protection_rules": (
                    [{"type": "required_reviewers", "reviewers": reviewers}]
                    if reviewers
                    else []
                )
            }
            yield f"repos/{REPO}/environments/{name}/deployment-branch-policies", {
                "branch_policies": [
                    {"name": policy.split(" ")[0], "type": policy.split(" ")[1]}
                    for policy in self.policies[name]
                ]
            }
            yield f"repos/{REPO}/environments/{name}/secrets", {
                "secrets": [{"name": secret} for secret in self.secrets[name]]
            }
        yield f"repos/{REPO}/actions/secrets", {
            "secrets": [{"name": secret} for secret in self.repository_secrets]
        }

    def write(self, folder: pathlib.Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        for path, payload in self._endpoints():
            (folder / f"{path.replace('/', '_')}.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )


class ReleaseCredentialCheckTests(unittest.TestCase):
    def run_check(self, world: CredentialWorld):
        """Run the real script with the fake `gh` first on PATH."""
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            fixtures = root / "fixtures"
            world.write(fixtures)
            bindir = root / "bin"
            bindir.mkdir()
            fake = bindir / "gh"
            fake.write_text(
                FAKE_GH.replace("__FIXTURES__", str(fixtures)), encoding="utf-8"
            )
            fake.chmod(0o755)
            env = dict(os.environ)
            env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
            return run_bash_file(SCRIPT, REPO, env=env, cwd=ROOT)

    def test_the_check_passes_when_the_credentials_are_environment_scoped(self):
        """The positive half: the honest configuration is accepted."""
        result = self.run_check(CredentialWorld())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok:", result.stdout)

    def test_a_repository_level_copy_of_a_release_key_is_refused(self):
        """The load-bearing refusal: environment secrets are ADDED to
        repository secrets, so a surviving repository copy keeps the key
        reachable from every historical tag."""
        world = CredentialWorld()
        world.repository_secrets = ["GPG_PRIVATE_KEY"]
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "still has a REPOSITORY-level secret named GPG_PRIVATE_KEY", result.stderr
        )
        self.assertIn(
            "refusing: the release credentials are not environment-scoped",
            result.stderr,
        )

    def test_a_tag_that_could_deploy_into_an_environment_is_refused(self):
        world = CredentialWorld()
        world.policies["apple-signing"] = ["main branch", "v1 tag"]
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not allow deployments from the main branch alone", result.stderr)
        self.assertIn("v1 tag", result.stderr)

    def test_the_release_environment_must_require_a_reviewer(self):
        world = CredentialWorld()
        world.reviewers["release-signing"] = 0
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must require a reviewer", result.stderr)

    def test_an_environment_missing_a_credential_is_refused(self):
        world = CredentialWorld()
        world.secrets["apple-signing"] = ["MAC_CERT_P12_BASE64", "MAC_CERT_PASSWORD"]
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must hold exactly", result.stderr)
        self.assertIn("MAC_APP_SPECIFIC_PASSWORD", result.stderr)

    def test_an_environment_holding_the_other_credentials_is_refused(self):
        """Least privilege: one credential set per environment, so a job that
        needs the release key never also loads the Apple identity."""
        world = CredentialWorld()
        world.secrets["release-signing"] = list(RELEASE_SECRETS) + ["MAC_CERT_P12_BASE64"]
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must hold exactly", result.stderr)
        self.assertIn("MAC_CERT_P12_BASE64", result.stderr)

    def test_a_missing_environment_is_refused(self):
        world = CredentialWorld()
        world.missing_environments = {"apple-signing"}
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no environment named apple-signing", result.stderr)

    def test_the_check_changes_nothing(self):
        """It is a read-only verifier; a check that mutates the platform would
        be a new privileged path on the release chain."""
        text = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("--method", "-X POST", "-X PUT", "-X DELETE", "gh secret set"):
            self.assertNotIn(forbidden, text, f"the check must never change anything: {forbidden}")

    def test_the_check_is_runnable_here(self):
        """Guards the fixture plumbing itself: without `gh` on PATH the fake
        would be irrelevant and every refusal test would pass for the wrong
        reason (gh missing, not the defect)."""
        self.assertTrue(shutil.which("bash"), "these tests need bash")
        self.assertTrue(SCRIPT.is_file(), "the check script must exist")


if __name__ == "__main__":
    unittest.main()
