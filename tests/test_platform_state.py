"""The credential wiring and the platform state, checked where they live.

W7 (CT-80, releases/PLAN-0.6.8.md:189) and M7 (:161-166). At the audited tag
81f58ec no job declared an `environment:`, so no MAC_* or GPG_* name could
resolve there -- and yet the 2026-10-07 candidate runs signed and notarized.
The wiring that made publication work lived on the platform and in nobody's
revision. Two things answer that:

* every secret name the workflow reads is declared by the environment named on
  the job that reads it, and the one name that is deliberately not declared is
  proved optional by the shape of the step that reads it, not by a comment;
* `scripts/check-platform-state.sh` re-reads the platform half -- environments,
  branch policies, required reviewers, secret names, rulesets, Actions
  permissions, workflow registrations -- and diffs it against
  releases/platform-state.json, which is the record committed with this test.

The live half cannot be asserted from a test without network access, so the
cases below prove the *differ*: a fake `gh` replays the recorded platform, a
mutation of one field must produce a named difference and a non-zero exit, and a
missing or unauthenticated `gh` must refuse rather than report a match.

Break-and-watch: add a `secrets.NEW_NAME` reference to a job, or drop a name
from the record, or mutate one field of the replayed platform -- the named case
must go red.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
RECORD = ROOT / "releases" / "platform-state.json"
SCRIPT = ROOT / "scripts" / "check-platform-state.sh"
WORKFLOW = ROOT / ".github" / "workflows" / "build-candidate.yml"
if not WORKFLOW.is_file():
    # A source archive is a source tree: build-source.sh ships the recipes under
    # ci/ rather than .github/workflows/, and the archive runs this suite.
    WORKFLOW = ROOT / "ci" / "build-candidate.yml"
PLAN = ROOT / "releases" / "PLAN-0.6.8.md"
RELEASE_PROCESS = ROOT / "RELEASE-PROCESS.md"
WORKFLOW_DIR = WORKFLOW.parent

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is a CI requirement
    yaml = None

# A secret reference is `secrets.NAME` in an expression. The lookbehind keeps a
# hyphenated filename -- scripts/scan-secrets.py, which the source job runs --
# from being read as a reference to a secret called "py".
SECRET_REFERENCE = re.compile(r"(?<![\w-])secrets\.([A-Za-z_][A-Za-z0-9_]*)")

# The five names the plan expects to be declared, and nowhere else. The optional
# route below is the reason the count is five and not six.
EXPECTED_DECLARED = {
    "MAC_CERT_P12_BASE64",
    "MAC_CERT_PASSWORD",
    "MAC_APP_SPECIFIC_PASSWORD",
    "GPG_PRIVATE_KEY",
    "GPG_PASSPHRASE",
}

FAKE_GH = '''"""A `gh` that replays releases/platform-state.json instead of the network."""
import json
import os
import pathlib
import sys

state = json.loads(pathlib.Path(os.environ["PLATFORM_STATE_FIXTURE"]).read_text())
environments = state["environments"]
mutation = os.environ.get("PLATFORM_STATE_MUTATION", "")


if mutation:
    kind, _, rest = mutation.partition(":")
    if kind == "drop-secret":
        environment, _, name = rest.partition(":")
        environments[environment]["secrets"].remove(name)
    elif kind == "add-secret":
        environment, _, name = rest.partition(":")
        environments[environment]["secrets"].append(name)
    elif kind == "reviewers":
        environment, _, count = rest.partition(":")
        environments[environment]["required_reviewers"] = int(count)
    elif kind == "add-registration":
        state["workflow_registrations"]["file"][rest] = {
            "name": "New publisher",
            "state": "active",
        }
    elif kind == "secret-scanning":
        key, _, status = rest.partition(":")
        state["secret_scanning"][key] = status
    else:
        raise SystemExit("unknown mutation: " + mutation)


def detail(name):
    entry = environments[name]
    rules = [{"type": "branch_policy"}]
    if entry["required_reviewers"]:
        rules.append({
            "type": "required_reviewers",
            "reviewers": [
                {"type": "User", "id": index}
                for index in range(entry["required_reviewers"])
            ],
        })
    return {
        "name": name,
        "can_admins_bypass": entry["can_admins_bypass"],
        "protection_rules": rules,
        "deployment_branch_policy": {
            "protected_branches": False,
            "custom_branch_policies": True,
        },
    }


argv = sys.argv[1:]
if argv[:1] == ["auth"]:
    sys.exit(0)
if argv[:1] != ["api"] or len(argv) != 2:
    sys.exit(2)

prefix = "repos/" + state["recorded_from"]
if argv[1] != prefix and not argv[1].startswith(prefix + "/"):
    sys.exit(2)
path = argv[1][len(prefix):].lstrip("/")
registrations = state["workflow_registrations"]

if path == "":
    # The repository root: the platform's own secret-scanning posture (CT-86).
    answer = {
        "security_and_analysis": {
            key: {"status": status}
            for key, status in state["secret_scanning"].items()
        }
    }
elif path == "environments":
    answer = {
        "total_count": len(environments),
        "environments": [detail(name) for name in sorted(environments)],
    }
elif path.startswith("environments/") and path.endswith("/deployment-branch-policies"):
    name = path.split("/")[1]
    answer = {
        "total_count": len(environments[name]["branch_policies"]),
        "branch_policies": [
            {"name": policy, "type": "branch"}
            for policy in environments[name]["branch_policies"]
        ],
    }
elif path.startswith("environments/") and path.endswith("/secrets"):
    name = path.split("/")[1]
    answer = {
        "total_count": len(environments[name]["secrets"]),
        "secrets": [{"name": secret} for secret in environments[name]["secrets"]],
    }
elif path.startswith("environments/") and path.endswith("/variables"):
    name = path.split("/")[1]
    answer = {
        "total_count": len(environments[name]["variables"]),
        "variables": [{"name": item} for item in environments[name]["variables"]],
    }
elif path.startswith("environments/") and path.count("/") == 1:
    answer = detail(path.split("/", 1)[1])
elif path == "actions/secrets":
    answer = {
        "total_count": len(state["repository_secrets"]),
        "secrets": [{"name": name} for name in state["repository_secrets"]],
    }
elif path == "actions/variables":
    answer = {
        "total_count": len(state["repository_variables"]),
        "variables": [{"name": name} for name in state["repository_variables"]],
    }
elif path == "rulesets":
    answer = [
        {"id": index + 1, "name": ruleset["name"]}
        for index, ruleset in enumerate(state["rulesets"])
    ]
elif path.startswith("rulesets/"):
    index = int(path.split("/")[1]) - 1
    ruleset = state["rulesets"][index]
    answer = {
        "id": index + 1,
        "name": ruleset["name"],
        "target": ruleset["target"],
        "enforcement": ruleset["enforcement"],
        "conditions": {"ref_name": {"include": ruleset["include"], "exclude": []}},
        "rules": [{"type": rule} for rule in ruleset["rules"]],
    }
elif path == "actions/permissions":
    answer = state["permissions"]["actions"]
elif path == "actions/permissions/workflow":
    answer = state["permissions"]["workflow"]
elif path == "actions/workflows":
    listed = [
        {"name": entry["name"], "path": location, "state": entry["state"]}
        for kind in ("file", "dynamic")
        for location, entry in registrations[kind].items()
    ]
    answer = {"total_count": len(listed), "workflows": listed}
else:
    sys.exit(2)

json.dump(answer, sys.stdout)
'''


def _fake_gh(folder: Path) -> Path:
    """A `gh` on disk that answers every endpoint from the fixture.

    On Windows a `#!` script is not a program: Git Bash runs it, but the
    Python side of `scripts/check-platform-state.sh` hands the path to
    `subprocess`, which raises `OSError: [WinError 193] %1 is not a valid Win32
    application`. The 0.6.6 candidate hit that with the HWI helper
    (`tests/test_hardening_pins.py`), and the 0.6.8 candidate run 38082865187
    hit it here, so the helper now takes the portable form: a `.cmd` trampoline
    that runs the Python source with this interpreter.
    """
    source = folder / "gh.py"
    source.write_text(FAKE_GH, encoding="utf-8", newline="\n")
    if sys.platform == "win32":
        program = folder / "gh.cmd"
        program.write_text(
            "@echo off\r\n"
            f'"{sys.executable}" "%~dp0gh.py" %*\r\n',
            encoding="utf-8",
        )
        program.chmod(0o755)
        return program
    program = folder / "gh"
    program.write_text(
        f"#!{sys.executable}\n{FAKE_GH}", encoding="utf-8", newline="\n")
    program.chmod(0o755)
    return program


def _workflow_files_on_disk():
    return {
        f".github/workflows/{path.name}"
        for path in WORKFLOW_DIR.iterdir()
        if path.is_file()
    }


class PlatformRecordTests(unittest.TestCase):
    """The committed record, read the way a reviewer reads it."""

    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(RECORD.read_text(encoding="utf-8"))
        cls.environments = cls.record["environments"]

    def test_the_record_declares_exactly_the_five_expected_secret_names(self):
        declared = {
            name
            for environment in self.environments.values()
            for name in environment["secrets"]
        }
        self.assertEqual(declared, EXPECTED_DECLARED)
        self.assertEqual(self.record["repository_secrets"], [],
                         "a repository-level secret would bypass every environment policy")
        self.assertIn("apple-signing", self.environments)
        self.assertIn("release-signing", self.environments)

    def test_the_signing_environments_are_pinned_to_main_with_no_reviewers(self):
        for name in ("apple-signing", "release-signing"):
            environment = self.environments[name]
            self.assertEqual(environment["branch_policies"], ["main"],
                             f"{name} could be deployed from another ref")
            self.assertEqual(environment["required_reviewers"], 0,
                             f"{name} gained an approval step: update the record and "
                             "the release process together")
            self.assertTrue(environment["can_admins_bypass"],
                            f"{name} no longer lets an administrator bypass the policy")

    def test_the_record_names_the_platform_permissions_it_measures(self):
        rulesets = {item["name"]: item for item in self.record["rulesets"]}
        self.assertEqual(sorted(rulesets), ["protect-main", "protect-tags"])
        self.assertEqual(rulesets["protect-main"]["target"], "branch")
        self.assertEqual(rulesets["protect-main"]["include"], ["refs/heads/main"])
        self.assertEqual(rulesets["protect-main"]["rules"],
                         ["deletion", "non_fast_forward"])
        self.assertEqual(rulesets["protect-tags"]["target"], "tag")
        self.assertEqual(rulesets["protect-tags"]["include"], ["refs/tags/v*"])
        self.assertEqual(rulesets["protect-tags"]["rules"],
                         ["deletion", "non_fast_forward"])
        for ruleset in rulesets.values():
            self.assertEqual(ruleset["enforcement"], "active")

        workflow = self.record["permissions"]["workflow"]
        self.assertEqual(workflow["default_workflow_permissions"], "read")
        self.assertFalse(workflow["can_approve_pull_request_reviews"])

    def test_the_record_carries_the_platform_secret_scanning_posture(self):
        """CT-86: the source job reads the bytes, and this reads the setting.

        Every status is recorded, including the disabled ones, because a record
        that named only the good news could not be diffed.
        """
        scanning = self.record["secret_scanning"]
        self.assertEqual(
            sorted(scanning),
            ["dependabot_security_updates", "secret_scanning",
             "secret_scanning_non_provider_patterns",
             "secret_scanning_push_protection",
             "secret_scanning_validity_checks"],
        )
        self.assertEqual(scanning["secret_scanning"], "enabled")
        self.assertEqual(scanning["secret_scanning_push_protection"], "enabled")

    def test_an_unenforced_platform_setting_is_named_on_the_next_cycle_list(self):
        actions = self.record["permissions"]["actions"]
        self.assertEqual(actions["allowed_actions"], "all")
        self.assertFalse(actions["sha_pinning_required"])
        plan = PLAN.read_text(encoding="utf-8")
        self.assertIn('`allowed_actions: "all"` and no platform-level action SHA pinning',
                      plan, "the accepted residual must stay on the next-cycle list")
        self.assertIn("Owner decision", plan)

    def test_the_record_states_that_it_records_names_and_not_values(self):
        self.assertIn("names only", self.record["values"])
        self.assertEqual(self.record["schema"],
                         "bitcoin-easy-multisig-signer/platform-state/1")
        self.assertEqual(self.record["recorded_from"],
                         "cjtsh/bitcoin-easy-multisig-signer")
        self.assertIn("recorded_at", self.record)


class WorkflowWiringTests(unittest.TestCase):
    """Every secret the workflow reads resolves where the job says it does."""

    @classmethod
    def setUpClass(cls):
        if yaml is None:
            raise unittest.SkipTest("PyYAML is required to read the workflow")
        cls.workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        cls.record = json.loads(RECORD.read_text(encoding="utf-8"))

    def _jobs(self):
        for name, job in self.workflow["jobs"].items():
            yield name, job, set(SECRET_REFERENCE.findall(json.dumps(job)))

    def test_every_referenced_secret_is_declared_by_the_job_environment(self):
        environments = self.record["environments"]
        optional = self.record.get("optional_secret_routes", {})
        seen = set()
        for name, job, referenced in self._jobs():
            if not referenced:
                continue
            environment = job.get("environment")
            if isinstance(environment, dict):
                environment = environment.get("name")
            self.assertIsNotNone(
                environment,
                f"job {name!r} reads {sorted(referenced)} but declares no environment, "
                "so none of those names can resolve",
            )
            self.assertIn(environment, environments,
                          f"job {name!r} names environment {environment!r}, which the "
                          "record does not have")
            allowed = optional.get(environment, {})
            for secret in sorted(referenced - set(allowed)):
                self.assertIn(
                    secret,
                    environments[environment]["secrets"],
                    f"job {name!r} reads secrets.{secret} but environment "
                    f"{environment!r} does not declare it",
                )
            for secret in sorted(referenced & set(allowed)):
                self._assert_route_is_optional(name, job, secret, environments[environment])
            seen |= referenced
        expected = EXPECTED_DECLARED | {
            secret
            for routes in self.record.get("optional_secret_routes", {}).values()
            for secret in routes
        }
        self.assertEqual(seen, expected,
                         "the workflow's secret references and the record disagree")

    def _assert_route_is_optional(self, job_name, job, secret, environment):
        """An undeclared name is only acceptable as the *other* half of a real route.

        The proof is structural: the step that reads `secrets.<optional>` must
        branch on it (`if`/`else`) and must read, in the same step, at least one
        name the environment *does* declare. A comment saying "optional" would
        not be enough, and this is the case that would catch the day someone
        deletes the working route and leaves the note behind.
        """
        readers = [
            step for step in job.get("steps", [])
            if f"secrets.{secret}" in json.dumps(step)
        ]
        self.assertTrue(readers, f"job {job_name!r} lost the step reading {secret}")
        for step in readers:
            body = json.dumps({key: step[key] for key in step if key != "name"})
            self.assertIn("else", body,
                          f"secrets.{secret} is read without a fallback branch in "
                          f"step {step.get('name')!r}")
            declared_here = {
                name for name in SECRET_REFERENCE.findall(body)
                if name in environment["secrets"]
            }
            self.assertTrue(
                declared_here,
                f"step {step.get('name')!r} reads only undeclared names, so the "
                "fallback route has no credential either",
            )

    def test_the_optional_route_annotation_only_names_real_references(self):
        referenced = set()
        for _, _, names in self._jobs():
            referenced |= names
        for environment, routes in self.record.get("optional_secret_routes", {}).items():
            self.assertIn(environment, self.record["environments"])
            for secret, reason in routes.items():
                self.assertIn(secret, referenced,
                              f"{secret} is annotated as an optional route but the "
                              "workflow no longer reads it")
                self.assertGreater(len(reason), 80, "the annotation must say why")


class WorkflowRegistrationTests(unittest.TestCase):
    """A workflow file that is not registered, or a stale registration, is drift."""

    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(RECORD.read_text(encoding="utf-8"))
        cls.registrations = cls.record["workflow_registrations"]
        cls.on_disk = _workflow_files_on_disk()

    def test_every_workflow_file_in_the_tree_is_registered(self):
        missing = sorted(self.on_disk - set(self.registrations["file"]))
        self.assertEqual(missing, [],
                         "a workflow file the platform does not know about never runs; "
                         "the record has to carry what the platform actually holds")

    def test_a_registration_whose_file_is_gone_is_recorded_as_disabled(self):
        """A deleted file does not delete the registration.

        The two retired per-platform publishers were deleted from every branch
        (M5), and the platform still holds their registrations. Disabled is the
        only acceptable state for a registration with no file behind it: any
        other state would mean a workflow that runs while no reviewer can read
        it in the tree.
        """
        for path, entry in self.registrations["file"].items():
            if path not in self.on_disk:
                self.assertEqual(entry["state"], "disabled_manually",
                                 f"{path} has no file in the tree but is {entry['state']}")

    def test_the_retired_platform_publishers_are_recorded_as_disabled(self):
        file_registrations = self.registrations["file"]
        for retired in (".github/workflows/build-linux.yml",
                        ".github/workflows/build-windows.yml"):
            self.assertEqual(file_registrations[retired]["state"], "disabled_manually",
                             f"{retired} was re-enabled: the publish sweep and the "
                             "release process both need to be revisited")
        self.assertEqual(file_registrations[".github/workflows/build-candidate.yml"]["state"],
                         "active")

    def test_the_platform_generated_workflow_is_recorded_separately(self):
        dynamic = self.registrations["dynamic"]
        self.assertEqual(list(dynamic), ["dynamic/pages/pages-build-deployment"])
        for path in dynamic:
            self.assertFalse(path.startswith(".github/workflows/"))


class PlatformCheckScriptTests(unittest.TestCase):
    """The differ itself: it must find drift, and it must refuse to find nothing."""

    @classmethod
    def setUpClass(cls):
        cls.bash = shutil.which("bash") or "/bin/bash"
        cls.record = json.loads(RECORD.read_text(encoding="utf-8"))

    def _run(self, folder, *, gh=None, record=RECORD, mutation=None, arguments=()):
        env = dict(os.environ)
        env["PLATFORM_STATE_PYTHON"] = sys.executable
        env["PLATFORM_STATE_REPO"] = self.record["recorded_from"]
        env["PLATFORM_STATE_RECORD"] = str(record)
        env["PLATFORM_STATE_GH"] = str(gh) if gh else "/nonexistent/gh-not-installed"
        env["PLATFORM_STATE_FIXTURE"] = str(folder / "fixture.json")
        shutil.copyfile(RECORD, env["PLATFORM_STATE_FIXTURE"])
        if mutation:
            env["PLATFORM_STATE_MUTATION"] = mutation
        return subprocess.run(
            [self.bash, str(SCRIPT), *arguments],
            capture_output=True, text=True, env=env, cwd=str(folder),
        )

    def test_the_script_refuses_when_gh_is_present_but_unusable(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            broken = folder / "gh"
            broken.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            broken.chmod(0o755)
            result = self._run(folder, gh=broken)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing", result.stderr)
            self.assertIn("not authenticated", result.stderr)
            self.assertNotIn("ok:", result.stdout)

    def test_the_script_refuses_when_gh_is_missing_entirely(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run(Path(tmp))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not installed", result.stderr)
            self.assertNotIn("ok:", result.stdout)

    def test_the_fake_gh_is_whatever_this_platform_can_execute(self):
        """A shebang script is not a valid Win32 application.

        The 0.6.8 candidate run 38082865187 failed seven of these tests on
        Windows with `OSError: [WinError 193] %1 is not a valid Win32
        application`: the differ's Python side runs the path through
        `subprocess`, which cannot exec the shebang form Git Bash had been
        happy with. Same lesson as the HWI plant in
        `tests/test_hardening_pins.py`; asserted from any platform.
        """
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(sys, "platform", "win32"):
                program = _fake_gh(Path(folder))
            self.assertEqual(program.name, "gh.cmd")
            body = program.read_text(encoding="utf-8")
            self.assertIn("@echo off", body)
            self.assertNotIn("#!/", body)
            self.assertIn("gh.py", body)

        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(sys, "platform", "darwin"):
                program = _fake_gh(Path(folder))
            self.assertEqual(program.name, "gh")
            self.assertIn("#!/", program.read_text(encoding="utf-8"))

    def test_a_matching_platform_reports_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            result = self._run(folder, gh=_fake_gh(folder))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ok:", result.stdout)
            self.assertIn("3 environments", result.stdout)

    def test_a_dropped_secret_is_named_in_the_difference(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            result = self._run(
                folder, gh=_fake_gh(folder),
                mutation="drop-secret:apple-signing:MAC_CERT_PASSWORD",
            )
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("apple-signing", result.stderr)
            self.assertIn("MAC_CERT_PASSWORD", result.stderr)

    def test_an_extra_approval_step_is_named_in_the_difference(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            result = self._run(folder, gh=_fake_gh(folder),
                               mutation="reviewers:release-signing:1")
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("required_reviewers", result.stderr)
            self.assertIn("recorded 0, live 1", result.stderr)

    def test_a_newly_registered_workflow_is_named_in_the_difference(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            result = self._run(
                folder, gh=_fake_gh(folder),
                mutation="add-registration:.github/workflows/restored-publisher.yml",
            )
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("restored-publisher.yml", result.stderr)

    def test_a_disabled_scanner_is_named_in_the_difference(self):
        """The setting behind the scan is watched too, not just the scan."""
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            result = self._run(
                folder, gh=_fake_gh(folder),
                mutation="secret-scanning:secret_scanning_push_protection:disabled",
            )
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("secret_scanning.secret_scanning_push_protection",
                          result.stderr)
            self.assertIn("recorded 'enabled', live 'disabled'", result.stderr)

    def test_a_missing_record_refuses_instead_of_reporting_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            result = self._run(folder, gh=_fake_gh(folder), record=folder / "absent.json")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing", result.stderr)
            self.assertNotIn("ok:", result.stdout)

    def test_re_recording_carries_the_annotations_forward(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            target = folder / "platform-state.json"
            shutil.copyfile(RECORD, target)
            result = self._run(folder, gh=_fake_gh(folder), record=target,
                               arguments=("--record",))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("carried forward", result.stdout)
            re_recorded = json.loads(target.read_text(encoding="utf-8"))
            for key in ("notes", "optional_secret_routes"):
                self.assertEqual(re_recorded[key], self.record[key],
                                 f"--record must not erase the hand-written {key}")
            self.assertEqual(re_recorded["environments"], self.record["environments"])
            self.assertIn("recorded_at", re_recorded)

    def test_the_release_process_runs_the_check(self):
        process = RELEASE_PROCESS.read_text(encoding="utf-8")
        self.assertIn("scripts/check-platform-state.sh", process)
        self.assertIn("releases/platform-state.json", process)

    def test_the_source_archive_ships_the_record_and_the_script(self):
        """A record that never leaves the repository is not evidence a reader holds."""
        source = (ROOT / "scripts" / "build-source.sh").read_text(encoding="utf-8")
        self.assertIn('if compgen -G "releases/*.json" >/dev/null; then', source,
                      "the platform record must reach the tarball, or the half of the "
                      "posture that git cannot show dies with this checkout")
        self.assertIn('cp releases/*.json "$stage/$root/releases/"', source)
        self.assertIn("releases/*.md", source)
        self.assertIn("scripts/*.sh", source)

    def test_the_script_fails_closed_by_construction(self):
        """A weak differ is the defect this whole work order is about."""
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('command -v "$gh_bin"', script)
        self.assertIn('"$gh_bin" auth status', script)
        self.assertIn("refusing", script)
        self.assertIn("NOT_OBSERVED", script)
        # Exactly one `|| true` is allowed: the optional origin lookup, whose
        # empty result the very next check turns into a refusal. Any other one
        # would be a read whose failure is silently read as "no difference".
        self.assertEqual(script.count("|| true"), 1, script)
        self.assertIn('config --get remote.origin.url 2>/dev/null || true', script)
        self.assertIn('cannot tell which repository to read', script)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
