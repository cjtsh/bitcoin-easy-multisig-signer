"""CT-97: the platform half of the release-credential scope.

A repository secret is handed to a job on **any** ref. A dispatch at a
historical tag therefore runs that tag's own frozen (older, less guarded)
workflow text but still receives today's signing keys, because secrets are
matched by name and never by tag. Tags are immutable history, so the fix cannot
live in the tag: the credentials moved into two protected environments whose
deployment rule allows `main` only and which declare no human gate, and the two
jobs that use them declare those environments.

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
import subprocess
import tempfile
import unittest

from support import bash_executable, run_bash_file

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check-release-credentials.sh"
REPO = "owner/repo"
RELEASE_SECRETS = ("GPG_PRIVATE_KEY", "GPG_PASSPHRASE")
APPLE_SECRETS = ("MAC_CERT_P12_BASE64", "MAC_CERT_PASSWORD", "MAC_APP_SPECIFIC_PASSWORD")

# A `bash` that actually runs a script, not the WSL launcher a bare "bash"
# resolves to on Windows runners (it exits 1 with "Windows Subsystem for Linux
# has no installed distributions"). `support.bash_executable()` is the one
# definition of that rule; a later bare `bash` entry here is what broke the
# Windows leg of the 0.6.8 candidate, and tests/test_windows_portability.py
# now refuses one.
BASH = bash_executable()


def required_reviewers_rule():
    """A `required_reviewers` protection rule as the environments API returns it."""
    return {
        "type": "required_reviewers",
        "reviewers": [{"type": "User", "reviewer": {"login": "owner"}}],
    }


def wait_timer_rule(minutes=5):
    return {"type": "wait_timer", "wait_timer": minutes}

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
        # Human gates that would stop a release starting on its own. The honest
        # configuration has none: the owner asked for a path any agent team can
        # run, so the check refuses a required reviewer or a wait timer.
        self.gates = {"release-signing": [], "apple-signing": []}
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
            yield f"repos/{REPO}/environments/{name}", {
                "protection_rules": list(self.gates[name])
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

    def test_a_required_reviewer_is_refused(self):
        """Publishing must start on its own. A required reviewer pauses the
        promote run for a person, and with `prevent_self_review: false` the same
        token can then approve it, so the gate buys no separation of duties while
        giving a release a way to stall."""
        world = CredentialWorld()
        world.gates["release-signing"] = [required_reviewers_rule()]
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn("declares a human gate", result.stderr)
        self.assertIn("required_reviewers(1)", result.stderr)
        self.assertIn(
            "refusing: the release credentials are not environment-scoped",
            result.stderr,
        )

    def test_a_wait_timer_is_refused(self):
        world = CredentialWorld()
        world.gates["apple-signing"] = [wait_timer_rule()]
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn("declares a human gate", result.stderr)
        self.assertIn("wait_timer(5)", result.stderr)

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
        self.assertTrue(
            pathlib.Path(BASH).is_file() or shutil.which(BASH),
            f"these tests need a working bash; got {BASH!r}",
        )
        self.assertTrue(SCRIPT.is_file(), "the check script must exist")


PROVISION = ROOT / "scripts" / "provision-release-credentials.sh"


class ProvisionReleaseCredentialsTests(unittest.TestCase):
    """The recovery script that rebuilds the credentials from this machine.

    GitHub never returns a secret's value, so the only way back from a lost
    environment secret is to re-derive it from the master copy on this machine.
    That script now sits on the release path, so it is pinned here: it must be
    able to arm every name, and it must never be the thing that leaks one — no
    shell tracing and no value in argv, which `ps` can see.
    """

    def test_the_provision_script_exists_and_is_executable(self):
        self.assertTrue(PROVISION.is_file(), "scripts/provision-release-credentials.sh must exist")
        self.assertTrue(os.access(PROVISION, os.X_OK), "the provisioning script must be executable")

    def test_the_provision_script_is_syntactically_valid_and_prints_usage(self):
        result = subprocess.run(
            [BASH, str(PROVISION), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--dry-run", result.stdout)
        self.assertIn("--prune", result.stdout)

    def test_the_provision_script_never_passes_a_value_in_argv(self):
        text = PROVISION.read_text(encoding="utf-8")
        self.assertNotIn("set -x", text, "shell tracing would print a value")
        self.assertNotIn("--body", text, "argv is visible to ps; values must arrive on stdin")
        self.assertEqual(
            text.count("gh secret set"),
            1,
            "every write must go through the single stdin helper",
        )

    def test_the_provision_script_is_pinned_to_the_documented_material(self):
        text = PROVISION.read_text(encoding="utf-8")
        for needle in (
            "ACCC2F1CD4369128D549CC58E97285D2DD0BD6D7",
            "02624AD5998203927864C7167C461DE0E6D19707",
            "release-signing",
            "apple-signing",
            "unused-the-release-key-carries-no-passphrase",
            "check-release-credentials.sh",
            "--prune",
        ):
            self.assertIn(needle, text, f"the provisioning script must stay pinned to: {needle}")

    def test_a_dry_run_touches_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp)
            log = folder / "calls"
            for tool in ("gh", "gpg", "security", "base64", "python3"):
                fake = folder / tool
                fake.write_text(
                    "#!/bin/sh\n" f'echo "{tool} $*" >> "{log}"\n' "exit 99\n",
                    encoding="utf-8",
                )
                fake.chmod(0o755)
            result = subprocess.run(
                [BASH, str(PROVISION), "--dry-run"],
                capture_output=True,
                text=True,
                check=False,
                cwd=str(ROOT),
                env=dict(os.environ, PATH=f"{folder}{os.pathsep}{os.environ.get('PATH', '')}"),
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertFalse(log.exists(), "a dry run must not invoke any tool")
            for name in RELEASE_SECRETS + APPLE_SECRETS:
                self.assertIn(name, result.stdout, "a dry run must name every secret it would set")

    def test_the_owner_path_carries_the_value_on_stdin_only(self):
        """The one credential that can never be re-derived arrives through
        `--app-password-prompt`/`--app-password-file`. This runs that exact
        path against a fake `gh` and proves the value reaches GitHub on stdin
        and never in argv (which `ps` can see) or on stdout (which a log keeps).
        """
        with tempfile.TemporaryDirectory() as tmp:
            folder = pathlib.Path(tmp)
            value = "abcd-efgh-ijkl-mnop"
            secret_file = folder / "app-password"
            secret_file.write_text(value, encoding="utf-8")
            argv_log = folder / "argv"
            stdin_log = folder / "stdin"
            for tool in ("gpg", "security", "base64", "python3"):
                fake = folder / tool
                fake.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
                fake.chmod(0o755)
            fake_gh = folder / "gh"
            fake_gh.write_text(
                "#!/bin/sh\n"
                f'printf "%s\\n" "$*" >> "{argv_log}"\n'
                f'cat >> "{stdin_log}"\n'
                "exit 0\n",
                encoding="utf-8",
            )
            fake_gh.chmod(0o755)
            result = subprocess.run(
                [
                    BASH,
                    str(PROVISION),
                    "--repo",
                    REPO,
                    "--only",
                    "MAC_APP_SPECIFIC_PASSWORD",
                    "--app-password-file",
                    str(secret_file),
                    "--no-verify",
                ],
                capture_output=True,
                text=True,
                check=False,
                cwd=str(ROOT),
                env=dict(os.environ, PATH=f"{folder}{os.pathsep}{os.environ.get('PATH', '')}"),
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            argv = argv_log.read_text(encoding="utf-8")
            self.assertIn("secret set MAC_APP_SPECIFIC_PASSWORD --env apple-signing", argv)
            self.assertNotIn(value, argv, "the value must never appear in argv")
            self.assertNotIn(value, result.stdout, "the value must never be printed")
            self.assertNotIn(value, result.stderr, "the value must never be printed")
            self.assertEqual(stdin_log.read_text(encoding="utf-8"), value)


if __name__ == "__main__":
    unittest.main()
