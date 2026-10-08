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
import urllib.parse

from support import bash_executable, run_bash_file, workflow_credential_scope

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check-release-credentials.sh"
REPO = "owner/repo"


def derived_scope() -> dict:
    """``{environment: [secret name, ...]}`` from the workflow text itself.

    CT-97's repository half was a five-name constant here and in the check
    script. `MAC_NOTARY_KEY_P8_BASE64` was live in build-candidate.yml while
    neither knew it existed. The watched set is derived now, and the check's own
    stdlib derivation is asserted equal to this one.
    """
    found = {}
    for _workflow, _job, environment, name in workflow_credential_scope(ROOT):
        found.setdefault(environment, set()).add(name)
    return {environment: sorted(names) for environment, names in found.items()}


DERIVED = derived_scope()
RELEASE_SECRETS = tuple(DERIVED["release-signing"])
APPLE_SECRETS = tuple(DERIVED["apple-signing"])

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
# Record the invocation so a test can pin that the check asks for every page
# rather than reading the first one and calling it the whole answer.
printf '%s\n' "$*" >> "__FIXTURES__/calls.log"
shift
path=""
for argument in "$@"; do
  case "$argument" in
    --paginate) ;;
    *) path="$argument" ;;
  esac
done
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
        # Endpoints whose fixture is withheld, so `gh api` fails for them and
        # the check's own read-error arm is exercised rather than assumed.
        self.missing_fixtures = set()
        # Fixture text written verbatim instead of json.dumps(payload), so a
        # test can serve several concatenated documents as `gh --paginate`
        # does. Keyed by the same API path as `missing_fixtures`.
        self.raw_fixtures = {}
        # Human gates that would stop a release starting on its own. The honest
        # configuration has none: the owner asked for a path any agent team can
        # run, so the check refuses a required reviewer or a wait timer.
        self.gates = {environment: [] for environment in DERIVED}
        self.policies = {environment: ["main branch"] for environment in DERIVED}
        self.secrets = {
            environment: list(names) for environment, names in DERIVED.items()
        }
        # Environments the API reports but no audited workflow names. They are
        # the attacker of the cycle-5 finding: live on the platform, invisible
        # to a check that only reads the text. `undeclared()` describes one.
        self.undeclared_environments = set()

    def undeclared(self, name, *, secrets=(), policies=(), gates=()):
        """Describe an environment the audited text never names.

        Adds it to the API's environment list and records the API answers the
        check must read for it. The default branch policy is empty, which is
        the platform default and the shape a tag dispatch can reach.
        """
        self.undeclared_environments.add(name)
        self.secrets[name] = list(secrets)
        self.policies[name] = list(policies)
        self.gates[name] = list(gates)
        return name

    def environments_in_api(self):
        """Every environment `GET /repos/{repo}/environments` reports."""
        return sorted(set(DERIVED) | self.undeclared_environments)

    def _endpoints(self):
        for name in self.environments_in_api():
            if name in self.missing_environments:
                continue
            # The platform returns names decoded but the API paths carry them
            # percent-encoded, so `*` is read and requested as `%2A`.
            quoted = urllib.parse.quote(name, safe="")
            yield f"repos/{REPO}/environments/{quoted}", {
                "protection_rules": list(self.gates[name])
            }
            yield f"repos/{REPO}/environments/{quoted}/deployment-branch-policies", {
                "branch_policies": [
                    {"name": policy.split(" ")[0], "type": policy.split(" ")[1]}
                    for policy in self.policies[name]
                ]
            }
            yield f"repos/{REPO}/environments/{quoted}/secrets", {
                "secrets": [{"name": secret} for secret in self.secrets[name]]
            }
        names = self.environments_in_api()
        yield f"repos/{REPO}/environments", {
            "total_count": len(names),
            "environments": [{"name": name} for name in names],
        }
        yield f"repos/{REPO}/actions/secrets", {
            "secrets": [{"name": secret} for secret in self.repository_secrets]
        }

    def write(self, folder: pathlib.Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        for path, payload in self._endpoints():
            if path in self.missing_fixtures:
                # Withheld on purpose: the fake `gh` exits 1 for it, which is
                # how a real API read failure reaches the check.
                continue
            (folder / f"{path.replace('/', '_')}.json").write_text(
                self.raw_fixtures.get(path, json.dumps(payload)), encoding="utf-8"
            )


class ReleaseCredentialCheckTests(unittest.TestCase):
    def run_check(self, world: CredentialWorld, workflows: pathlib.Path | None = None):
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
            args = (REPO,) if workflows is None else (REPO, str(workflows))
            result = run_bash_file(SCRIPT, *args, env=env, cwd=ROOT)
            # The fake `gh` appends every invocation beside the fixtures, which
            # the temporary directory takes with it, so read it out here and
            # hang it on the result for tests that pin the flags.
            log = fixtures / "calls.log"
            result.gh_calls = log.read_text(encoding="utf-8") if log.exists() else ""
            return result

    def test_the_check_passes_when_the_credentials_are_environment_scoped(self):
        """The positive half: the honest configuration is accepted."""
        result = self.run_check(CredentialWorld())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok:", result.stdout)

    def test_the_derivation_covers_the_notary_key_that_was_unwatched(self):
        """CT-97's repository half: the watched set comes from the workflows.

        `.github/workflows/build-candidate.yml` names
        `secrets.MAC_NOTARY_KEY_P8_BASE64` inside its notarize step. The old
        five-name constant did not, so that credential was live and unwatched:
        it could sit at repository level and reach every historical tag without
        the check saying a word.
        """
        self.assertIn("MAC_NOTARY_KEY_P8_BASE64", DERIVED["apple-signing"])
        self.assertEqual(DERIVED["release-signing"], ["GPG_PASSPHRASE", "GPG_PRIVATE_KEY"])

    def test_a_repository_level_copy_of_the_notary_key_is_refused(self):
        """The sixth name is watched now, so a repository-level copy refuses."""
        world = CredentialWorld()
        world.repository_secrets = ["MAC_NOTARY_KEY_P8_BASE64"]
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "still has a REPOSITORY-level secret named MAC_NOTARY_KEY_P8_BASE64",
            result.stderr,
        )

    def test_the_script_derivation_agrees_with_the_yaml_derivation(self):
        """The stdlib bash derivation and the PyYAML one must say the same thing.

        The check runs on the operator's `python3`, which has no PyYAML, so it
        parses the text itself. That parser is the only thing standing between a
        new credential name and a silent gap, and a hand-written parser is
        exactly the sort of code that rots. This compares it, field for field,
        against a real YAML parse of the same files.
        """
        expected = {
            (name, environment, f"{workflow}:{job}")
            for workflow, job, environment, name in workflow_credential_scope(ROOT)
        }
        self.assertTrue(expected, "the derivation found no credential at all")
        result = run_bash_file(SCRIPT, "--print-scope", cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        found = {
            tuple(line.split("\t"))
            for line in result.stdout.splitlines()
            if line.strip()
        }
        self.assertEqual(
            found, expected,
            "the check's own parser and a real YAML parse disagree; the check is "
            "watching a different set of names than the workflows name",
        )

    def test_a_workflow_that_names_a_credential_without_an_environment_is_refused(self):
        """A new unscoped `secrets.FOO` cannot ride along unnoticed.

        This is the shape of the whole finding: a job that declares no
        environment receives the secret on every ref, including a historical
        tag. The derivation must catch it from the text alone.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "hostile.yml").write_text(
                "name: hostile\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  leak:\n"
                "    runs-on: ubuntu-24.04\n"
                "    steps:\n"
                "      - run: echo \"${{ secrets.FOO }}\"\n",
                encoding="utf-8",
            )
            result = self.run_check(CredentialWorld(), workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("declares no environment", result.stderr)
        self.assertIn("FOO", result.stderr)
        self.assertIn("hostile.yml:leak", result.stderr)
        self.assertIn(
            "refusing: the release credentials are not environment-scoped",
            result.stderr,
        )

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

    def test_an_environment_that_holds_none_of_its_credentials_is_refused(self):
        """An emptied environment would make every other arm vacuous."""
        world = CredentialWorld()
        world.secrets["apple-signing"] = []
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn("holds none of the credentials its jobs reference", result.stderr)
        self.assertIn("MAC_CERT_P12_BASE64", result.stderr)

    def test_an_absent_optional_credential_is_noted_and_not_refused(self):
        """The App Store Connect key is named by the workflow and absent from the
        platform, because the Apple-ID notary route is the one in use.

        That is a fact to report, not a reason to block a release: the notary step
        reads the name as optional and falls back, and the Apple-ID route's own
        names are guarded by `: "${...:?}"`, so nothing silently skips a
        signature. This pins the one-directional rule, and it is the shape the
        live check actually runs against.
        """
        world = CredentialWorld()
        world.secrets["apple-signing"] = [
            name for name in APPLE_SECRETS if name != "MAC_NOTARY_KEY_P8_BASE64"
        ]
        result = self.run_check(world)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "ok: the release credentials are environment-scoped", result.stdout
        )
        self.assertIn("note:", result.stderr)
        self.assertIn("MAC_NOTARY_KEY_P8_BASE64", result.stderr)
        self.assertIn("optional", result.stderr)

    def test_an_environment_holding_the_other_credentials_is_refused(self):
        """Least privilege: one credential set per environment, so a job that
        needs the release key never also loads the Apple identity."""
        world = CredentialWorld()
        world.secrets["release-signing"] = list(RELEASE_SECRETS) + ["MAC_CERT_P12_BASE64"]
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn("which no job that declares release-signing references", result.stderr)
        self.assertIn("it must hold only", result.stderr)
        self.assertIn("MAC_CERT_P12_BASE64", result.stderr)

    def test_a_missing_environment_is_refused(self):
        world = CredentialWorld()
        world.missing_environments = {"apple-signing"}
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no environment named apple-signing", result.stderr)

    def test_a_missing_branch_policy_is_refused(self):
        """The main-only rule is the control for a tag dispatch (CT-97).

        An environment with no deployment branch policy at all is not the same
        as `main`-only: any ref, including a tag, may deploy into it. The
        audit's cycle-5 referee found this arm armed but unpinned, so a later
        edit could have dropped the refusal without a test going red.
        """
        world = CredentialWorld()
        world.policies["apple-signing"] = []
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("does not allow deployments from the main branch alone", result.stderr)
        self.assertIn("found: none", result.stderr)
        self.assertIn("apple-signing", result.stderr)

    def test_a_non_main_branch_policy_is_refused(self):
        """A writable branch policy is not `main`-only either."""
        world = CredentialWorld()
        world.policies["apple-signing"] = ["develop branch"]
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("found: develop branch", result.stderr)

    def test_an_undeclared_environment_holding_a_credential_is_refused(self):
        """The cycle-5 hole: the API is the authority, not the audited text.

        An environment the platform reports but no workflow here names was
        never audited at all. The attacker's shape is an environment called
        `*` whose branch policy list is empty — every ref, including a tag, may
        deploy into it — holding the release key. The old read came back `ok`
        and `unreachable from any tag` without ever asking the platform about
        it. The name is URL-encoded in the API path (`%2A`), so this pins the
        decoded refusal and the encoded request.
        """
        world = CredentialWorld()
        world.undeclared("*", secrets=["GPG_PRIVATE_KEY"])
        result = self.run_check(world)
        out = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, out)
        self.assertIn(
            "the * environment is not named by any workflow in", result.stderr
        )
        self.assertIn(
            "does not allow deployments from the main branch alone (found: none)",
            result.stderr,
        )
        self.assertNotIn("ok:", result.stdout)
        self.assertIn(
            f"api --paginate repos/{REPO}/environments/%2A/secrets",
            result.gh_calls,
        )

    def test_an_undeclared_environment_holding_no_credential_is_ignored(self):
        """The control: `github-pages` is on the platform and is not main-only.

        It holds none of the watched names, so it is not on the release path
        and must not be refused — the real repository must stay at exit 0. Its
        secrets are still read, so `holds nothing` is an answer rather than an
        assumption, and its policy is never consulted because the gate opens
        only on a watched name.
        """
        world = CredentialWorld()
        world.undeclared("github-pages", secrets=[], policies=["gh-pages branch"])
        result = self.run_check(world)
        out = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, out)
        self.assertIn("ok:", result.stdout)
        self.assertNotIn("github-pages", result.stderr)
        self.assertIn(
            f"api --paginate repos/{REPO}/environments/github-pages/secrets",
            result.gh_calls,
        )

    def test_an_undeclared_environment_with_a_human_gate_is_refused(self):
        """The same rules as a declared environment, not just the branch rule.

        The finding is `never audited`, so an undeclared environment that holds
        a watched credential must answer to every rule the declared ones do: a
        wait timer stops a release starting on its own just as it would in
        `release-signing`. Main-only is armed here so the gate is the only
        defect, and the refusal names the environment.
        """
        world = CredentialWorld()
        world.undeclared(
            "release-backdoor",
            secrets=["GPG_PRIVATE_KEY"],
            policies=["main branch"],
            gates=[wait_timer_rule()],
        )
        result = self.run_check(world)
        out = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, out)
        self.assertIn(
            "the release-backdoor environment is not named by any workflow in",
            result.stderr,
        )
        self.assertIn("declares a human gate", result.stderr)
        self.assertIn("wait_timer(5)", result.stderr)

    def test_an_unreadable_policy_endpoint_is_refused(self):
        """A platform that will not answer is not a platform that answered yes.

        The reference caches the read error by withholding the fixture, which
        makes the fake `gh` exit 1 the way a real API failure does.
        """
        world = CredentialWorld()
        world.missing_fixtures = {
            f"repos/{REPO}/environments/apple-signing/deployment-branch-policies"
        }
        result = self.run_check(world)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(
            "could not read the deployment branch policies of the apple-signing environment",
            result.stderr,
        )

    def test_a_workflow_set_that_names_no_release_credential_is_refused(self):
        """With nothing to watch the check would pass vacuously.

        A check that cannot fail is not a check, so an empty watched set is
        itself a refusal. This is the guard an auditor can otherwise satisfy by
        pointing the script at a directory that contains no workflow at all.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "plain.yml").write_text(
                "name: plain\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-24.04\n"
                "    steps:\n"
                "      - run: echo ok\n",
                encoding="utf-8",
            )
            result = self.run_check(CredentialWorld(), workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("proves nothing", result.stderr)
        self.assertIn("names a release credential", result.stderr)

    def test_a_bracket_spelled_secret_is_derived(self):
        """`secrets['NAME']` is the same context spelled differently.

        The derivation accepted the bracket form but nothing pinned it, so
        narrowing the pattern to the dot form would have silently stopped
        watching a name spelled this way. The environment here deliberately
        holds the real release names, so the refusal can only come from the
        bracket name having been derived.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "bracket.yml").write_text(
                "name: bracket\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  publish:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: release-signing\n"
                "    steps:\n"
                "      - run: echo \"${{ secrets['FOO'] }}\"\n",
                encoding="utf-8",
            )
            result = self.run_check(CredentialWorld(), workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(
            "which no job that declares release-signing references", result.stderr
        )
        self.assertIn("FOO", result.stderr)
        self.assertNotIn("proves nothing", result.stderr)

    def test_a_workflow_level_env_is_refused(self):
        """T2: the walk begins at `jobs:`, so a name above it was invisible.

        `env:` at workflow level supports the `secrets` context, so a name
        there is live on every ref while no job was seen to use it. It is now
        reported as a name with no scope, which is a refusal.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "hostile_env.yml").write_text(
                "name: hostile\n"
                "on: workflow_dispatch\n"
                "env:\n"
                "  PAT: ${{ secrets.RELEASE_PAT }}\n"
                "jobs:\n"
                "  decoy:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: apple-signing\n"
                "    steps:\n"
                "      - run: echo ok\n",
                encoding="utf-8",
            )
            result = self.run_check(CredentialWorld(), workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("cannot attribute to a job", result.stderr)
        self.assertIn("RELEASE_PAT", result.stderr)
        self.assertIn("hostile_env.yml names the release credential RELEASE_PAT", result.stderr)

    def test_a_quoted_job_key_is_read_as_its_own_job(self):
        """A quoted key is read, not merged into the job above it.

        Cycle-6 referee E showed `  "leak":` failing the two-space bare-key
        pattern, so its body was appended to the previous job and the secret it
        named was attributed to THAT job environment — the leak read as scoped.
        The quoted spelling is now a job of its own, and a job that declares no
        environment is a refusal.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "quoted.yml").write_text(
                "name: quoted\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: apple-signing\n"
                "    steps:\n"
                '      - run: echo "${{ secrets.APPLE_SIGNING_KEY }}"\n'
                '  "leak":\n'
                "    runs-on: ubuntu-24.04\n"
                "    steps:\n"
                '      - run: echo "${{ secrets.GPG_PRIVATE_KEY }}"\n',
                encoding="utf-8",
            )
            result = self.run_check(CredentialWorld(), workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("quoted.yml:leak names the release credential "
                      "GPG_PRIVATE_KEY in a job that declares no environment",
                      result.stderr)

    def test_a_four_space_indented_job_is_read(self):
        """Cycle-6 attacker: the job indent was hard-coded to two spaces, so a
        four-space file was not read as jobs at all and every reference in it
        became unattributed. The walk measures the indent now, so the credential
        is scoped to its environment exactly as in the two-space spelling.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "indented.yml").write_text(
                "name: indented\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "    publish:\n"
                "      runs-on: ubuntu-24.04\n"
                "      environment: release-signing\n"
                "      steps:\n"
                "        - run: echo \"${{ secrets.GPG_PRIVATE_KEY }}\"\n",
                encoding="utf-8",
            )
            world = CredentialWorld()
            world.secrets["release-signing"] = ["GPG_PRIVATE_KEY"]
            result = self.run_check(world, workflows)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("cannot attribute to a job", result.stderr)

    def test_a_whitespace_before_a_job_colon_is_read(self):
        """`  leak :` is a legal YAML mapping key. The old pattern required the
        colon immediately after the name, so the job was folded into the
        previous body and its environment was attributed to the wrong job
        (cycle-6 attacker: an `evil` environment holding the credential passed
        while the `leak:` control was refused).
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "spaced.yml").write_text(
                "name: spaced\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: release-signing\n"
                "    steps:\n"
                "      - run: echo ok\n"
                "  leak :\n"
                "    runs-on: ubuntu-24.04\n"
                "    steps:\n"
                "      - run: echo \"${{ secrets.GPG_PRIVATE_KEY }}\"\n",
                encoding="utf-8",
            )
            world = CredentialWorld()
            world.secrets["release-signing"] = ["GPG_PRIVATE_KEY"]
            result = self.run_check(world, workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("declares no environment", result.stderr)

    def test_a_workflow_level_env_cannot_hide_behind_a_scoped_job(self):
        """Cycle-6 referee E: `live_references` skipped any name the walk had
        attributed ANYWHERE, so naming the same credential at workflow level
        (live on every ref, no environment) was masked by one scoped mention.
        Every occurrence is now compared, not every distinct name.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "masked.yml").write_text(
                "name: masked\n"
                "on: workflow_dispatch\n"
                "env:\n"
                "  PAT: ${{ secrets.GPG_PRIVATE_KEY }}\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: release-signing\n"
                "    steps:\n"
                '      - run: echo "${{ secrets.GPG_PRIVATE_KEY }}"\n',
                encoding="utf-8",
            )
            result = self.run_check(CredentialWorld(), workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("masked.yml names the release credential GPG_PRIVATE_KEY "
                      "somewhere this check cannot attribute to a job",
                      result.stderr)

    def test_a_bracket_expression_secret_is_refused_as_unreadable(self):
        """A name spelled through `secrets[format(...)]` cannot be scoped.

        The old rule took every quoted literal in the index as a candidate and
        watched `GPG_PRIVATE_KEY`, or — for `format('{0}_KEY', 'GPG_PRIVATE')`
        — the harmless `GPG_PRIVATE`, while what the expression actually
        resolved to stayed live and unwatched (cycle-6 attacker). An index that
        is not one whole quoted literal is now a name the reader cannot read,
        and the check refuses rather than guesses.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "expr.yml").write_text(
                "name: expr\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: release-signing\n"
                "    steps:\n"
                "      - run: echo \"${{ secrets[format('{0}', "
                "'GPG_PRIVATE_KEY')] }}\"\n",
                encoding="utf-8",
            )
            world = CredentialWorld()
            world.secrets["release-signing"] = ["GPG_PRIVATE_KEY"]
            result = self.run_check(world, workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("cannot read as a single name", result.stderr)

    def test_a_single_literal_bracket_secret_is_still_derived(self):
        """`secrets["GPG_PRIVATE_KEY"]` is one whole literal, so it is a name,
        and the repository-level copy of it is still refused."""
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "literal.yml").write_text(
                "name: literal\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: release-signing\n"
                "    steps:\n"
                "      - run: echo \"${{ secrets[\'GPG_PRIVATE_KEY\'] }}\"\n",
                encoding="utf-8",
            )
            world = CredentialWorld()
            world.repository_secrets = ["GPG_PRIVATE_KEY"]
            world.secrets["release-signing"] = ["GPG_PRIVATE_KEY"]
            result = self.run_check(world, workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("still has a REPOSITORY-level secret named GPG_PRIVATE_KEY",
                      result.stderr)

    def test_a_hash_inside_a_word_does_not_hide_a_reference(self):
        """Cycle-6 attacker: `#` ended the line wherever it appeared, so
        `echo x#${{ secrets.NAME }}` — live in the shell GitHub runs, because
        the `#` sits inside a word — was stripped away and the name was watched
        by nobody. A `#` begins a comment only at a line start or after
        whitespace.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "hash.yml").write_text(
                "name: hash\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: release-signing\n"
                "    steps:\n"
                "      - run: echo x#${{ secrets.GPG_PRIVATE_KEY }}\n",
                encoding="utf-8",
            )
            world = CredentialWorld()
            world.repository_secrets = ["GPG_PRIVATE_KEY"]
            world.secrets["release-signing"] = ["GPG_PRIVATE_KEY"]
            result = self.run_check(world, workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("still has a REPOSITORY-level secret named GPG_PRIVATE_KEY",
                      result.stderr)

    def test_a_lowercase_secret_reference_is_matched_to_its_name(self):
        """Secret names are not case-sensitive to GitHub, so
        `secrets.gpg_private_key` resolves the API name `GPG_PRIVATE_KEY`.
        Comparing spellings literally left the repository-level copy unwatched
        (cycle-6 attacker); the derivation uppercases every name it reads.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "lower.yml").write_text(
                "name: lower\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: release-signing\n"
                "    steps:\n"
                "      - run: echo \"${{ secrets.gpg_private_key }}\"\n",
                encoding="utf-8",
            )
            world = CredentialWorld()
            world.repository_secrets = ["GPG_PRIVATE_KEY"]
            world.secrets["release-signing"] = ["GPG_PRIVATE_KEY"]
            result = self.run_check(world, workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("still has a REPOSITORY-level secret named GPG_PRIVATE_KEY",
                      result.stderr)

    def test_a_reference_split_across_lines_is_still_live(self):
        """Cycle-6 attacker: `secrets` and its bracket on separate lines is one
        reference. The per-line walk saw neither half; the whole-file net reads
        the joined text, so the name is live and unattributed, which is refused.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "split.yml").write_text(
                "name: split\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: release-signing\n"
                "    steps:\n"
                "      - run: echo \"${{ secrets\n"
                "        [\'GPG_PRIVATE_KEY\'] }}\"\n",
                encoding="utf-8",
            )
            world = CredentialWorld()
            world.secrets["release-signing"] = ["GPG_PRIVATE_KEY"]
            result = self.run_check(world, workflows)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("cannot attribute to a job", result.stderr)
        self.assertIn("GPG_PRIVATE_KEY", result.stderr)

    def test_a_yaml_anchor_does_not_hide_a_job_or_an_environment(self):
        """`build: &b` and `environment: &env release-signing` are YAML
        syntax, not names. The old patterns kept the anchor text, so the job or
        the environment became unreadable and an honest file was refused
        (cycle-6 attacker).
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "anchor.yml").write_text(
                "name: anchor\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  build: &b\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: &env release-signing\n"
                "    steps:\n"
                "      - run: echo \"${{ secrets.GPG_PRIVATE_KEY }}\"\n",
                encoding="utf-8",
            )
            world = CredentialWorld()
            world.secrets["release-signing"] = ["GPG_PRIVATE_KEY"]
            result = self.run_check(world, workflows)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok:", result.stdout)

    def test_a_flow_mapping_environment_is_read_as_its_name(self):
        """`environment: {name: release-signing}` is legal YAML, and PyYAML
        resolves it to a dict with a `name` key.

        The reader returned the whole brace text as the name, so an honest
        workflow was refused, and the caller word-split it into environments
        that do not exist (`{name:` and `release-signing}`). Both spellings are
        here — the plain mapping and the one with a `url:` beside the name —
        and the absence of phantoms is pinned as well as the parse.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "flow.yml").write_text(
                "name: flow\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  publish:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: {name: release-signing}\n"
                "    steps:\n"
                "      - run: echo \"${{ secrets.GPG_PRIVATE_KEY }}\"\n",
                encoding="utf-8",
            )
            (workflows / "flow-url.yml").write_text(
                "name: flow-url\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  publish:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: {name: release-signing, url: https://example.invalid}\n"
                "    steps:\n"
                "      - run: echo \"${{ secrets.GPG_PRIVATE_KEY }}\"\n",
                encoding="utf-8",
            )
            world = CredentialWorld()
            world.secrets["release-signing"] = ["GPG_PRIVATE_KEY"]
            result = self.run_check(world, workflows)
        out = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, out)
        self.assertIn("ok:", result.stdout)
        self.assertNotIn("cannot parse", out)
        self.assertNotIn("{name:", out)
        self.assertNotIn("url:", out)

    def test_an_unnameable_flow_mapping_stays_one_environment(self):
        """A mapping with no `name:` key has no environment name to read.

        Refusing it is the fail-closed answer, and the reader hands its text
        back on purpose so the refusal can say what it saw. The caller used to
        loop over the derived names unquoted, so that one text became two
        environments that do not exist (`{url:` and `https://example.invalid}`)
        and the operator got a page of phantom refusals instead of one. Exactly
        one missing-environment statement must appear.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "nameless.yml").write_text(
                "name: nameless\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  publish:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: {url: https://example.invalid}\n"
                "    steps:\n"
                "      - run: echo \"${{ secrets.GPG_PRIVATE_KEY }}\"\n",
                encoding="utf-8",
            )
            world = CredentialWorld()
            result = self.run_check(world, workflows)
        out = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, out)
        self.assertIn(
            "cannot parse ({url: https://example.invalid})", result.stderr)
        self.assertEqual(
            result.stderr.count("has no environment named"),
            1,
            f"a name with a space split into phantom environments:\n{out}",
        )
        self.assertIn(
            "has no environment named {url: https://example.invalid}, so",
            result.stderr,
        )

    def test_a_list_shaped_secret_answer_is_a_refusal_with_a_reason(self):
        """A JSON list is not a collection this reader can read.

        Before the guard it raised AttributeError, so the operator saw a host
        Python traceback and no statement of what the check failed to learn.
        """
        world = CredentialWorld()
        world.raw_fixtures[f"repos/{REPO}/actions/secrets"] = "[]"
        result = self.run_check(world)
        out = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, out)
        self.assertIn("could not read the repository secret names", out)
        self.assertNotIn("Traceback", out)

    def test_a_list_shaped_environment_answer_is_a_refusal_with_a_reason(self):
        """The protection-rules reader is the one that was not guarded."""
        world = CredentialWorld()
        world.raw_fixtures[f"repos/{REPO}/environments/apple-signing"] = "[]"
        result = self.run_check(world)
        out = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, out)
        self.assertIn(
            "could not read the protection rules of the apple-signing environment",
            out)
        self.assertNotIn("Traceback", out)

    def test_an_apostrophe_does_not_turn_a_comment_into_a_reference(self):
        """A quote opens a scalar only where a token can begin.

        `Don` + apostrophe + `t` inside a plain value opened a quoted scalar
        that never closed, so the `#` did not end the line and the name in the
        comment was watched. That refused an honest file whenever the commented
        name happened to exist at repository level.
        """
        with tempfile.TemporaryDirectory() as temporary:
            workflows = pathlib.Path(temporary)
            (workflows / "honest.yml").write_text(
                "name: honest\n"
                "on: workflow_dispatch\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-24.04\n"
                "    environment: apple-signing\n"
                "    steps:\n"
                "      - name: Don't notarize this # see ${{ secrets.GPG_PRIVATE_KEY }}\n"
                '        run: echo "${{ secrets.APPLE_SIGNING_KEY }}"\n',
                encoding="utf-8",
            )
            world = CredentialWorld()
            world.secrets = dict(world.secrets)
            world.secrets["apple-signing"] = ["APPLE_SIGNING_KEY"]
            world.repository_secrets = ["GPG_PRIVATE_KEY"]
            result = self.run_check(world, workflows)
        out = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, out)
        self.assertNotIn("GPG_PRIVATE_KEY", out)

    def test_a_repository_secret_on_a_later_page_is_refused(self):
        """Cycle-6 referee C3: the repository half read one page and called it
        the whole answer, so a copy of a watched credential that sat on page 2
        (the 31st secret) passed the sweep while every ref kept receiving it.

        `gh api --paginate` prints one JSON document per page back to back, so
        the readers must decode a stream, not a single document.
        """
        world = CredentialWorld()
        world.repository_secrets = []
        world.raw_fixtures[f"repos/{REPO}/actions/secrets"] = (
            json.dumps(
                {
                    "total_count": 31,
                    "secrets": [{"name": f"DECOY_{index}"} for index in range(30)],
                }
            )
            + json.dumps(
                {"total_count": 31, "secrets": [{"name": "GPG_PRIVATE_KEY"}]}
            )
        )
        result = self.run_check(world)
        out = result.stdout + result.stderr
        self.assertNotEqual(
            result.returncode, 0,
            f"the check accepted a repository secret on page 2:\n{out}")
        self.assertIn(
            "still has a REPOSITORY-level secret named GPG_PRIVATE_KEY", out)

    def test_the_repository_read_asks_for_every_page(self):
        """The parser merging pages only helps if `gh` is asked for them.

        A one-page read is what let the 31st secret go unseen; this pins the
        flag itself so a future edit cannot quietly drop it while the merge
        test above still passes on a fixture that hands over both pages.
        """
        result = self.run_check(CredentialWorld())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"--paginate repos/{REPO}/actions/secrets", result.gh_calls)
        for environment in sorted(DERIVED):
            self.assertIn(
                f"--paginate repos/{REPO}/environments/{environment}/secrets",
                result.gh_calls,
            )

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
    able to arm every name, and it must not leak one to GitHub's argv or to a
    log. It does not claim argv never carries a value: two local tools take a
    secret as an argument and offer no other form, so those windows are pinned
    rather than denied (CT-107).
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

    def test_every_value_sent_to_github_arrives_on_stdin(self):
        """CT-107: the stdin rule covers what leaves this machine for GitHub.

        `gh secret set` must be the single write path and no `--body` may carry
        a value. Two local commands are exceptions this test does not pretend
        away — `security export -P` and `notarytool store-credentials
        --password` take the secret in argv because neither offers another
        form — so the header must name them instead of claiming argv is never
        used at all.
        """
        text = PROVISION.read_text(encoding="utf-8")
        self.assertNotIn("set -x", text, "shell tracing would print a value")
        self.assertNotIn("--body", text, "argv is visible to ps; values must arrive on stdin")
        self.assertEqual(
            text.count("gh secret set"),
            1,
            "every write must go through the single stdin helper",
        )
        self.assertNotIn(
            "passes every value on standard input rather than in argv", text,
            "the header must not claim argv never carries a value")
        self.assertIn(
            "those argv windows exist and are pinned rather than denied", text)
        self.assertIn('-P "$pw"', text,
                      "the pinned security-export argv window must stay named")
        self.assertIn("notarytool store-credentials", text)

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
