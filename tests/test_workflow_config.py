"""Contract tests for the Windows build workflow.

These are not style checks. Each one pins a decision that was expensive to learn,
because a workflow is the only part of this project that can turn an untested
artifact into a published one:

  * a candidate is built with `publish=false`, tested, and only then promoted by a
    later dispatch that names that exact run id - so a release is never built and
    published in one unverified step;
  * an unsigned Windows build cannot be published unless the dispatcher says so in
    writing, and that acknowledgement is recorded in the candidate manifest;
  * a version that has a tag is never rebuilt, because silently replacing the
    bytes behind a released tag is what happened to v0.1.11 five times;
  * checksums are verified, and every action is pinned to a commit, before
    anything becomes public.

The macOS pipeline these mirror lived in .github/workflows/build-candidate.yml.
Nothing macOS-specific survives here: no .dmg, no codesign, no hdiutil, no
notarisation, and no macos-* runner.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _recipe(name: str) -> Path:
    """The workflow, from the repository or from an extracted source archive.

    The repository keeps both recipes in .github/workflows/; scripts/build-source.sh
    ships them under ci/, and this suite runs in both trees. Reading only one of the
    two locations is how an archive would pass a suite that never inspected it.
    """
    for candidate in (ROOT / ".github" / "workflows" / name, ROOT / "ci" / name):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"{name} is missing from both .github/workflows/ and ci/ under {ROOT}"
    )


WORKFLOW = _recipe("build-windows.yml")
INPUTS_WORKFLOW = _recipe("windows-inputs.yml")

try:
    import yaml
except ImportError:  # pragma: no cover - the CI lock installs PyYAML
    yaml = None


def bash_executable() -> str:
    """The bash the workflow's ``shell: bash`` steps run in, not the WSL stub.

    On Windows ``bash`` on PATH is often C:\\Windows\\System32\\bash.exe, the WSL
    launcher. With no distribution installed it exits 1 having run nothing and
    with an empty stderr, which is how every shell block came back "not valid
    shell" the first time this suite ran on the Windows runner. GitHub Actions runs
    ``shell: bash`` with Git for Windows, so these tests do too.
    """
    candidates: list[str] = []
    if os.name == "nt":
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"),
                     os.environ.get("ProgramW6432")):
            if base:
                candidates.append(os.path.join(base, "Git", "bin", "bash.exe"))
                candidates.append(os.path.join(base, "Git", "usr", "bin", "bash.exe"))
    found = shutil.which("bash")
    if found and "system32" not in found.lower():
        candidates.append(found)
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    raise AssertionError(
        "no bash for the shell-block checks; looked for " + ", ".join(candidates)
    )


class WorkflowConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if yaml is None:
            raise unittest.SkipTest("PyYAML is required to inspect the build workflow")
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.document = yaml.safe_load(cls.text)
        # PyYAML reads the bare `on:` key as the boolean True.
        cls.triggers = cls.document[True]
        cls.jobs = cls.document["jobs"]

    def shell_blocks(self) -> list[tuple[str, str, str, str]]:
        blocks = []
        for name, job in self.jobs.items():
            for step in job.get("steps", []):
                if "run" in step:
                    shell = step.get("shell") or (
                        job.get("defaults", {}).get("run", {}).get("shell") or "bash"
                    )
                    blocks.append((name, step.get("name", "<unnamed>"), shell, step["run"]))
        return blocks

    # ---- the trigger and its defaults -------------------------------------

    def test_the_workflow_runs_on_the_windows_branch_and_on_request(self) -> None:
        # The port lives on its own branch, so the workflow must exist there and
        # nowhere else. A push to that branch builds a candidate; it can never
        # publish, because the release notes come from a dispatch and the
        # promotion step requires a workflow_dispatch run.
        self.assertEqual(set(self.triggers), {"workflow_dispatch", "push"})
        self.assertEqual(self.triggers["push"]["branches"], ["windows-port"])
        for forbidden in ("pull_request", "schedule", "release"):
            self.assertNotIn(forbidden, self.triggers)

    def test_publishing_is_off_by_default(self) -> None:
        inputs = self.triggers["workflow_dispatch"]["inputs"]
        self.assertIs(inputs["publish"]["default"], False)
        self.assertIs(inputs["allow_unsigned"]["default"], False)
        self.assertIs(inputs["candidate_run_id"]["required"], False)

    def test_publishing_an_unsigned_build_needs_a_second_acknowledgement(self) -> None:
        refusal = self.step_body("Require an unsigned publication to be acknowledged")
        self.assertIn('"$ALLOW_UNSIGNED" != "true"', refusal)
        self.assertIn("is not code-signed", refusal)
        manifest = self.heredoc_body("cat > dist/CANDIDATE-MANIFEST.txt <<EOF")
        self.assertIn("allow_unsigned=${{ inputs.allow_unsigned }}", manifest)
        self.assertIn("publish=${{ inputs.publish }}", manifest)

    def test_a_release_must_come_from_the_windows_branch_with_a_named_candidate(self) -> None:
        guard = self.step_body("Require the Windows branch for publication")
        self.assertIn("refs/heads/windows-port", guard)
        self.assertIn("$CANDIDATE_RUN_ID", guard)
        self.assertIn("^[0-9]+$", guard)
        # The audited macOS release owns main. A Windows release must never be
        # published from there, so the old guard must be gone, not just relaxed.
        self.assertNotIn("refs/heads/main", self.text)
        promotion = self.step_body("Download and verify the tested candidate artifacts")
        self.assertIn('and .head_branch == "windows-port"', promotion)
        # A push run also uploads candidate artifacts. Only a dispatch is a
        # candidate a human chose to test, so only a dispatch can be promoted.
        self.assertIn('.event == "workflow_dispatch"', promotion)

    def test_the_release_tag_carries_the_platform_suffix(self) -> None:
        # v0.6.4 is an audited macOS release. Reusing that tag, or tagging the
        # Windows build v0.6.4, would make two different artifacts answer to one
        # version. The Windows release is v<version>-windows-x64 and nothing else.
        publish = self.step_body("Publish the release")
        self.assertIn('tag="v${VERSION}-windows-x64"', publish)
        self.assertIn('release_title="$tag"', publish)
        self.assertNotIn('tag="v${VERSION}"', publish)

    # ---- the jobs ---------------------------------------------------------

    def test_the_bundle_is_built_on_windows_and_everything_else_on_linux(self) -> None:
        self.assertEqual(self.jobs["windows"]["runs-on"], "windows-latest")
        for name in ("version", "source", "checksums", "release"):
            self.assertEqual(self.jobs[name]["runs-on"], "ubuntu-latest", name)
        self.assertIn("Require an x64 Windows runner", self.text)
        runner = self.step_body("Require an x64 Windows runner")
        self.assertIn("PROCESSOR_ARCHITECTURE", runner)
        self.assertIn("AMD64", runner)

    def test_promotion_can_never_start_before_the_bundle_was_built(self) -> None:
        self.assertEqual(self.jobs["source"]["needs"], "version")
        self.assertEqual(self.jobs["windows"]["needs"], "version")
        self.assertEqual(self.jobs["checksums"]["needs"], ["version", "source", "windows"])
        self.assertEqual(self.jobs["release"]["needs"],
                         ["version", "source", "windows", "checksums"])

    def test_only_the_release_job_may_write_to_the_repository(self) -> None:
        self.assertEqual(self.jobs["release"]["permissions"], {"contents": "write"})
        self.assertNotIn("if", self.jobs["release"])
        for name, job in self.jobs.items():
            if name == "release":
                continue
            self.assertNotEqual((job.get("permissions") or {}).get("contents"), "write",
                                f"{name} must not be able to write to the repository")
        self.assertEqual(self.document["permissions"], {"contents": "read"})

    def test_every_action_is_pinned_to_a_commit(self) -> None:
        used = re.findall(r"uses:\s*(\S+)", self.text)
        self.assertTrue(used)
        for reference in used:
            self.assertRegex(reference, r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$",
                             f"{reference} is not pinned to a full commit")

    def test_every_shell_block_parses(self) -> None:
        bash = bash_executable()
        for name, step, shell, body in self.shell_blocks():
            if "pwsh" in shell or "powershell" in shell:
                continue
            # On stdin, not on a temp file: a Windows temp path handed to bash as
            # C:\Users\... is not the path MSYS bash opens, which makes a valid
            # block look like a syntax error.
            result = subprocess.run([bash, "-n"], input=body, capture_output=True,
                                    text=True)
            self.assertEqual(result.returncode, 0,
                             f"{name}/{step} is not valid shell:\n{result.stderr}")

    # ---- the artifact inputs ---------------------------------------------

    def test_the_workflow_refuses_to_build_without_its_windows_inputs(self) -> None:
        guard = self.step_body("Verify the Windows build inputs are present")
        self.assertIn("requirements-desktop-windows.lock", guard)
        self.assertIn("vendor/libusb-1.0.dll", guard)
        self.assertIn("windows-inputs.yml", guard)

    def test_the_windows_lock_is_resolved_on_windows(self) -> None:
        inputs = INPUTS_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("runs-on: windows-latest", inputs)
        self.assertIn("piptools compile --allow-unsafe --generate-hashes", inputs)
        # Proof that the lock really came from a Windows resolve rather than a
        # macOS one with the platform markers stripped.
        self.assertIn("pythonnet", inputs)
        self.assertIn("pyobjc|macholib", inputs)

    def test_the_libusb_input_is_compiled_from_the_pinned_source(self) -> None:
        inputs = INPUTS_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("fea36f34f9156400209595e300840767ab1a385ede1dc7ee893015aea9c6dbaf", inputs)
        # The pinned tarball is libusb's autotools dist: it carries the MSVC
        # projects and configure, but no CMakeLists.txt, so the DLL is built with
        # upstream's own MSVC project rather than with CMake.
        self.assertIn(r"msvc\libusb_dll.vcxproj", inputs)
        self.assertIn("/p:Platform=x64", inputs)
        # A statically linked C runtime keeps the Visual C++ redistributable out
        # of the install instructions.
        self.assertIn("/p:Configuration=Release-MT", inputs)
        self.assertIn("LIBUSB_WINDOWS_SHA256", inputs)

    # ---- the build itself -------------------------------------------------

    def test_dependencies_are_lock_installed_before_the_build(self) -> None:
        prepare = self.step_index("Prepare the hash-locked build environment", job="windows")
        build = self.step_index("Build the Windows bundle", job="windows")
        self.assertLess(prepare, build)
        # PREPARE_ONLY and BUILD_DEPS_PREPARED are step-level env, not shell text.
        self.assertIn("PREPARE_ONLY", self.step_env("Prepare the hash-locked build environment"))
        self.assertIn("BUILD_DEPS_PREPARED", self.step_env("Build the Windows bundle"))
        self.assertIn("LIBUSB_SHA256", self.step_env("Build the Windows bundle"))

    def test_the_ci_lock_is_installed_with_hashes_and_only_where_it_belongs(self) -> None:
        self.assertEqual(self.text.count("--require-hashes -r requirements-ci.lock"), 2)
        self.assertIn("--require-hashes -r requirements.lock", self.text)
        self.assertNotIn("pip install --quiet", self.text)
        desktop = (ROOT / "requirements-desktop.txt").read_text(encoding="utf-8").lower()
        self.assertNotIn("pyyaml", desktop, "a test dependency must not become a shipped one")

    def test_the_built_bundle_is_verified_before_it_is_uploaded(self) -> None:
        verify = self.step_body("Verify the built bundle")
        for flag in ("--check-bundle", "--check-save", "--check-network", "--check-devices"):
            self.assertIn(flag, verify)
        self.assertIn("SSL_CERT_DIR=/nonexistent/certs", verify)
        self.assertIn("hwi.exe", verify)
        layout = self.step_body("Check the bundle's layout, icon and archive")
        self.assertIn("scripts/verify-windows-bundle.py", layout)
        inventory = self.step_body("Inventory the built dependencies")
        self.assertIn("scripts/build-sbom.py", inventory)
        # The verification has to happen in the job that built it, before upload,
        # and the inventory has to precede the layout check, because that check
        # reads dist/BUILD-SBOM.json and refuses to pass without one.
        self.assertLess(self.step_index("Verify the built bundle", job="windows"),
                        self.step_index("Inventory the built dependencies", job="windows"))
        self.assertLess(self.step_index("Inventory the built dependencies", job="windows"),
                        self.step_index("Check the bundle's layout, icon and archive",
                                        job="windows"))
        self.assertLess(self.step_index("Check the bundle's layout, icon and archive",
                                        job="windows"),
                        len(self.jobs["windows"]["steps"]) - 1)

    def test_the_uploaded_artifact_is_the_zip_and_the_sbom(self) -> None:
        upload = self.jobs["windows"]["steps"][-1]
        self.assertEqual(upload["with"]["name"], "windows-bundle")
        self.assertIn("dist/*.zip", upload["with"]["path"])
        self.assertIn("dist/BUILD-SBOM.json", upload["with"]["path"])
        self.assertEqual(upload["with"]["if-no-files-found"], "error")

    # ---- publication ------------------------------------------------------

    def test_the_candidate_is_promoted_by_identity_not_by_hope(self) -> None:
        promotion = self.step_body("Download and verify the tested candidate artifacts")
        for marker in ("gh api", "gh run download", "head_sha", "conclusion", "head_branch",
                       ".path == \".github/workflows/build-windows.yml\"",
                       "CANDIDATE-MANIFEST.txt", "allow_unsigned=true", "publish=false",
                       "sha256sum -c SHA256SUMS", "windows-bundle"):
            self.assertIn(marker, promotion)
        self.assertIn("run_id=$CANDIDATE_RUN_ID", promotion)

    def test_checksums_are_verified_before_anything_is_published(self) -> None:
        self.assertLess(self.text.index("sha256sum -c SHA256SUMS"),
                        self.text.index("gh release create"))
        self.assertIn("sha256sum *.tar.gz *.zip BUILD-SBOM.json > SHA256SUMS", self.text)
        self.assertLess(self.text.index("Verify downloaded release bytes"),
                        self.text.index("Publish the release"))

    def test_a_published_version_is_never_rebuilt(self) -> None:
        publish = self.step_body("Publish the release")
        self.assertIn('git ls-remote --exit-code --tags origin "refs/tags/$tag"', publish)
        self.assertIn("Bump version.py", publish)
        self.assertIn("Could not verify remote tag state; refusing publication.", publish)
        self.assertLess(publish.index("git ls-remote"), publish.index("gh release create"))

    def test_no_publication_escape_hatches(self) -> None:
        for verb in ("--clobber", "--draft", "--prerelease", "gh release delete",
                     "gh release edit", "--latest"):
            self.assertNotIn(verb, self.text)

    def test_the_candidate_stops_before_anything_is_created(self) -> None:
        publish = self.step_body("Publish the release")
        self.assertIn('if [[ "${{ inputs.publish }}" != "true" ]]', publish)
        self.assertIn("was built and NOT published", publish)
        self.assertIn("exit 0", publish)

    def test_the_release_notes_are_generated_and_extended(self) -> None:
        publish = self.step_body("Publish the release")
        self.assertIn('release_notes="releases/RELEASE-NOTES-${VERSION}.md"', publish)
        self.assertIn('cat "$release_notes" >> notes.md', publish)

    def test_no_macos_step_survived_the_port(self) -> None:
        # Checked against the shell bodies, not the header comment, which explains
        # the difference from the macOS pipeline on purpose.
        combined = "\n".join(body for _, _, _, body in self.shell_blocks())
        for residue in (".dmg", "codesign", "hdiutil", "PlistBuddy", "Developer ID",
                        "--options runtime", "hwi-entitlements", "notarize", "macos-",
                        "shasum", ".icns", "candidate-macos"):
            self.assertNotIn(residue, combined, f"{residue} is macOS residue")
        self.assertIn("build-windows.yml", combined)

    # ---- helpers ----------------------------------------------------------

    def step_index(self, name: str, job: str = "version") -> int:
        for index, step in enumerate(self.jobs[job].get("steps", [])):
            if step.get("name") == name:
                return index
        raise AssertionError(f"{job} has no step named {name!r}")

    def step_body(self, name: str, job: str | None = None) -> str:
        jobs = [job] if job else list(self.jobs)
        for candidate in jobs:
            for step in self.jobs[candidate].get("steps", []):
                if step.get("name") == name:
                    self.assertIn("run", step, f"step {name!r} has no shell body")
                    return step["run"]
        raise AssertionError(f"no step named {name!r}")

    def step_env(self, name: str, job: str | None = None) -> dict:
        jobs = [job] if job else list(self.jobs)
        for candidate in jobs:
            for step in self.jobs[candidate].get("steps", []):
                if step.get("name") == name:
                    return step.get("env") or {}
        raise AssertionError(f"no step named {name!r}")

    def heredoc_body(self, opener: str) -> str:
        """The body of a bash heredoc, de-indented the way the runner delivers it.

        The body is indented to match the TERMINATOR, not the opener: a heredoc
        opened inside an ``if`` sits two spaces deeper than its own body, and the
        runner strips the block's common indentation, not the opener's.
        """
        lines = self.text.splitlines()
        start = next(index for index, line in enumerate(lines) if opener in line)
        opener_indent = len(lines[start]) - len(lines[start].lstrip())
        for index in range(start + 1, len(lines)):
            stripped = lines[index].strip()
            if stripped != "EOF":
                continue
            indent = len(lines[index]) - len(lines[index].lstrip())
            if indent > opener_indent:
                continue
            return "\n".join(
                line[indent:] if line.startswith(" " * indent) else line.lstrip()
                for line in lines[start + 1:index]
            )
        raise AssertionError(f"the heredoc opened by {opener!r} is not closed")


class ReleaseNotesTests(unittest.TestCase):
    """Run the workflow's own note generation rather than trusting a copy of it."""

    VERSION = "9.9.9"

    def generate(self) -> str:
        text = WORKFLOW.read_text(encoding="utf-8")
        lines = text.splitlines()
        # Start where the shell defines what the notes interpolate, not at the
        # heredoc, so zip_name/build_kind are real values rather than empty strings.
        opener = next(index for index, line in enumerate(lines)
                      if 'tag="v${VERSION}-windows-x64"' in line)
        indent = len(lines[opener]) - len(lines[opener].lstrip())
        closer = next(index for index in range(opener + 1, len(lines))
                      if lines[index][indent:] == "EOF")
        script = "\n".join(
            line[indent:] if line.startswith(" " * indent) else line.lstrip()
            for line in lines[opener:closer + 1]
        )
        script = (script
                  .replace("${{ inputs.publish }}", "false")
                  .replace("${{ inputs.allow_unsigned }}", "false")) + "\n"
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / "notes.md").write_text("", encoding="utf-8")
            # The script writes the candidate manifest into dist/, exactly as the
            # runner's workspace has it.
            (work / "dist").mkdir()
            environment = dict(
                os.environ,
                VERSION=self.VERSION,
                GITHUB_REF_NAME="windows-port",
                GITHUB_SHA="abcdef1234567890",
                GITHUB_RUN_ID="12345",
                # as_posix(), because this path is handed to bash: on Windows a
                # C:\Users\... value is not a path MSYS bash can open, so the step
                # summary redirect fails where the runner's own step would succeed.
                GITHUB_STEP_SUMMARY=(work / "summary.md").as_posix(),
            )
            # The script arrives on stdin rather than as a -c argument: bash reads a
            # command string off argv with platform-specific quirks on Windows, and
            # `shell: bash` feeds the step a file.
            result = subprocess.run([bash_executable()], input=script, cwd=work,
                                    env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0,
                             f"{result.stderr}\n{result.stdout}")
            return (work / "notes.md").read_text(encoding="utf-8")

    def test_the_notes_say_what_was_built_and_from_where(self) -> None:
        notes = self.generate()
        self.assertIn(f"## v{self.VERSION}", notes)
        self.assertIn("Built from `windows-port` at commit `abcdef1234567890`.", notes)
        self.assertIn(f"Bitcoin-Easy-Signer-v{self.VERSION}-windows-x64.zip", notes)
        self.assertIn("SHA256SUMS", notes)
        self.assertIn("BUILD-SBOM.json", notes)
        self.assertIn("Bitcoin Easy Signer.exe", notes)

    def test_the_notes_admit_the_build_is_unsigned(self) -> None:
        notes = self.generate()
        self.assertIn("Unsigned", notes)
        self.assertIn("SmartScreen", notes)
        self.assertNotIn("notariz", notes.lower())
        self.assertNotIn("Apple", notes)

    def test_the_notes_keep_the_network_story_straight(self) -> None:
        notes = self.generate()
        self.assertIn("Opens on Bitcoin mainnet", notes)
        self.assertIn("Enter Developer Mode", notes)
        self.assertIn("the app reopens on mainnet", notes)
        self.assertNotIn("Mutinynet is the opening network", notes)

    def test_the_notes_do_not_carry_stale_boilerplate(self) -> None:
        notes = self.generate()
        for stale in ("Sparrow", "Nunchuk", "UNSIGNED-TEST", "right-click → Open", "Apple Silicon"):
            self.assertNotIn(stale, notes)

    def test_the_notes_keep_the_risk_statement(self) -> None:
        notes = self.generate()
        self.assertIn("**Use at your own risk.**", notes)
        self.assertIn("never retried", notes)


if __name__ == "__main__":
    unittest.main()
