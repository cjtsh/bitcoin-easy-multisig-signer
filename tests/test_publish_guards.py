"""Behaviour tests for the release pipeline's guards (CT-72, CT-74, CT-75).

These run the workflow's own ``run:`` bodies through tests/workflow_harness.py
and assert on outcomes — exit status, tool calls, files created — rather than
on the words a guard contains. The distinction is the whole finding: for two
cycles every release guard was "pinned" by asserting its refusal sentence and
the string ``exit 1`` were present, and every one of those pins stayed green
while the guard was defeated (an inverted condition, ``if: ${{ false }}``,
``|| true`` appended to a checksum check, a predicate OR-ed with ``true``).

CT-72 is the sharpest case. The step that validates ``candidate_run_id`` was
itself the step that executed it:

    if [[ ! "${{ inputs.candidate_run_id }}" =~ ^[0-9]+$ ]]; then

GitHub substitutes the free-text input into the script text before bash parses
it, so the regex gates nothing. The tests below dispatch payloads that have
already been demonstrated to execute — including one that runs its payload
*and* makes the guard pass — and require the marker file to be absent
afterwards. A test that only asserted the refusal message would pass on the
vulnerable workflow; that is exactly how this survived.

``run_step`` gives each step the environment the runner would give it: the
``github.*`` context becomes ``GITHUB_*``, and the step's own ``env:`` block is
rendered from the context. A test therefore fails if the ``env:`` entry that
carries a value is deleted, not only if the comparison is inverted.
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from workflow_harness import (
    EXPRESSION,
    Stub,
    active_workflow,
    evaluate_if,
    find_step,
    load_workflow,
    run_step,
    step_runs,
    yaml_available,
)

GUARD = "Require the default branch for publication"
GUARD_JOB = "version"
SWEEP_GUARD = "Refuse a second publish path on any ref"
UNSIGNED_GUARD = "Refuse an unsigned public release"
VERIFY_STEP = "Verify downloaded release bytes"
PUBLISH_STEP = "Publish the release"
RELEASE_JOB = "release"


def context(**overrides) -> dict:
    """A minimal dispatcher context, as the runner would see it."""
    values = {
        "inputs.candidate_run_id": "12345",
        "inputs.publish": True,
        "inputs.notarize": True,
        "github.ref": "refs/heads/main",
        "github.ref_name": "main",
        "github.sha": "0" * 40,
        "github.run_id": "999999",
        "github.repository": "cjtsh/bitcoin-easy-multisig-signer",
        "github.event_name": "workflow_dispatch",
        "github.token": "stub-token",
        "needs.version.outputs.version": "9.9.9",
    }
    values.update(overrides)
    return values


def write_dist(workdir: Path, *, version: str = "9.9.9", tamper: bool = False) -> Path:
    """A dist/ with one asset and a matching SHA256SUMS."""
    dist = workdir / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    asset = dist / f"Bitcoin-Easy-Signer-v{version}-macOS.dmg"
    payload = b"asset-bytes"
    asset.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    (dist / "SHA256SUMS").write_text(f"{digest}  {asset.name}\n", encoding="utf-8")
    if tamper:
        asset.write_bytes(b"tampered-after-checksums")
    return dist


@unittest.skipUnless(yaml_available(), "PyYAML is required to read the workflow")
class CandidateRunIdInjectionTests(unittest.TestCase):
    """CT-72: the guard that validates the input must not execute it."""

    @classmethod
    def setUpClass(cls):
        cls.workflow = load_workflow()
        cls.step = find_step(cls.workflow, GUARD_JOB, GUARD)

    def run_guard(self, candidate_run_id: str, *, ref="refs/heads/main"):
        return run_step(
            self.step,
            context(**{"inputs.candidate_run_id": candidate_run_id, "github.ref": ref}),
        )

    def test_a_numeric_candidate_run_id_is_accepted(self):
        result = self.run_guard("12345")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_missing_candidate_run_id_is_refused(self):
        result = self.run_guard("")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Publishing requires the run ID of a successful notarized candidate.", result.stderr)

    def test_a_non_numeric_candidate_run_id_is_refused(self):
        result = self.run_guard("abc")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Publishing requires the run ID of a successful notarized candidate.", result.stderr)

    def test_money_path_the_guard_still_refuses_a_non_main_ref(self):
        result = self.run_guard("12345", ref="refs/heads/feature")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Public releases must be dispatched from main.", result.stderr)

    def test_a_command_substitution_payload_does_not_run(self):
        with tempfile.TemporaryDirectory() as workspace:
            marker = Path(workspace) / "PWNED"
            result = self.run_guard(f"$(touch {marker})")
            self.assertFalse(
                marker.exists(),
                "the candidate_run_id guard executed its own input (CT-72)",
            )
            self.assertNotEqual(result.returncode, 0, "the payload must not pass the guard")

    def test_a_payload_that_also_makes_the_guard_pass_does_not_run(self):
        """The worst variant: the substitution runs and the guard still passes.

        `$(touch <marker>; printf 12345)` renders as a valid numeric-looking
        operand, so a workflow that interpolates the input proceeds to publish
        after the payload has already run.
        """
        with tempfile.TemporaryDirectory() as workspace:
            marker = Path(workspace) / "PWNED"
            result = self.run_guard(f"$(touch {marker}; printf 12345)")
            self.assertFalse(
                marker.exists(),
                "the candidate_run_id guard executed its own input (CT-72)",
            )
            self.assertNotEqual(
                result.returncode, 0,
                "an input that is not literally numeric must be refused",
            )

    def test_a_quote_breaking_payload_does_not_run(self):
        with tempfile.TemporaryDirectory() as workspace:
            marker = Path(workspace) / "PWNED"
            payload = f'1" ]] || touch {marker}; [[ "1'
            result = self.run_guard(payload)
            self.assertFalse(
                marker.exists(),
                "the candidate_run_id guard executed its own input (CT-72)",
            )
            self.assertNotEqual(result.returncode, 0)

    def test_the_guard_step_is_actually_reached(self):
        """A guard behind an impossible condition is not a guard."""
        self.assertTrue(step_runs(self.step, context()))
        self.assertFalse(step_runs(self.step, context(**{"inputs.publish": False})))


@unittest.skipUnless(yaml_available(), "PyYAML is required to read the workflow")
class ReleaseGuardBehaviourTests(unittest.TestCase):
    """CT-74/CT-75: every publish guard, exercised, not quoted.

    Each guard below is run with inputs that must fail and inputs that must
    succeed. Defeating the guard's logic — replacing its ``if:`` with
    ``${{ false }}``, inverting a comparison, appending ``|| true`` to a
    checksum check — changes one of these outcomes and turns the test red.
    """

    @classmethod
    def setUpClass(cls):
        cls.workflow = load_workflow()

    # -- "Refuse an unsigned public release" (version job) -------------------

    def test_the_unsigned_release_guard_runs_exactly_on_publish_without_notarize(self):
        step = find_step(self.workflow, GUARD_JOB, UNSIGNED_GUARD)
        runs = [
            (publish, notarize)
            for publish in (True, False)
            for notarize in (True, False)
            if step_runs(step, context(**{"inputs.publish": publish, "inputs.notarize": notarize}))
        ]
        self.assertEqual(
            runs,
            [(True, False)],
            "the unsigned-release guard must run on a publish dispatch that did "
            "not request notarization, and on nothing else",
        )

    def test_the_unsigned_release_guard_refuses_and_names_the_reason(self):
        step = find_step(self.workflow, GUARD_JOB, UNSIGNED_GUARD)
        result = run_step(step, context(**{"inputs.notarize": False}))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Publishing requires a signed and notarized build.", result.stderr)

    # -- "Refuse a second publish path on any ref" (version job) -------------

    def test_the_sweep_gate_fails_the_run_when_the_sweep_fails(self):
        step = find_step(self.workflow, GUARD_JOB, SWEEP_GUARD)
        result = run_step(
            step,
            context(),
            stubs={"bash": [Stub(contains=("check-publish-paths.sh",), exit=1)]},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("A non-main ref can publish.", result.stderr)

    def test_the_sweep_gate_runs_the_sweep_and_passes_when_it_passes(self):
        step = find_step(self.workflow, GUARD_JOB, SWEEP_GUARD)
        result = run_step(
            step,
            context(),
            stubs={"bash": [Stub(contains=("check-publish-paths.sh",), exit=0)]},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            result.called("bash", "check-publish-paths.sh", "origin"),
            "the gate must actually run the sweep against origin",
        )

    # -- "Verify downloaded release bytes" (release job) --------------------

    def test_a_tampered_asset_fails_the_checksum_verification(self):
        """The defeat this must kill: `shasum -c SHA256SUMS || true`."""
        with tempfile.TemporaryDirectory() as workspace:
            workdir = Path(workspace)
            write_dist(workdir, tamper=True)
            step = find_step(self.workflow, RELEASE_JOB, VERIFY_STEP)
            result = run_step(step, context(**{"inputs.publish": False}), cwd=workdir)
            self.assertNotEqual(
                result.returncode, 0,
                "the checksum verification must fail on a changed asset",
            )

    def test_the_candidate_path_verifies_checksums_and_stops(self):
        with tempfile.TemporaryDirectory() as workspace:
            workdir = Path(workspace)
            write_dist(workdir)
            step = find_step(self.workflow, RELEASE_JOB, VERIFY_STEP)
            result = run_step(step, context(**{"inputs.publish": False}), cwd=workdir)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_publish_path_requires_the_signature_and_the_public_key(self):
        with tempfile.TemporaryDirectory() as workspace:
            workdir = Path(workspace)
            dist = write_dist(workdir)
            step = find_step(self.workflow, RELEASE_JOB, VERIFY_STEP)

            missing_signature = run_step(step, context(), cwd=workdir)
            self.assertNotEqual(missing_signature.returncode, 0)
            self.assertIn("SHA256SUMS.asc is missing.", missing_signature.stderr)

            (dist / "SHA256SUMS.asc").write_text("signature", encoding="utf-8")
            missing_key = run_step(step, context(), cwd=workdir)
            self.assertNotEqual(missing_key.returncode, 0)
            self.assertIn("signing-key.asc is not committed.", missing_key.stderr)

    def test_the_publish_path_verifies_the_signature_and_refuses_a_bad_one(self):
        with tempfile.TemporaryDirectory() as workspace:
            workdir = Path(workspace)
            dist = write_dist(workdir)
            (dist / "SHA256SUMS.asc").write_text("signature", encoding="utf-8")
            (workdir / "signing-key.asc").write_text("public key", encoding="utf-8")
            step = find_step(self.workflow, RELEASE_JOB, VERIFY_STEP)

            good = run_step(step, context(), cwd=workdir, stubs={"gpg": [Stub(exit=0)]})
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertTrue(good.called("gpg", "--verify", "SHA256SUMS.asc"))

            # The import and the verification are stubbed separately. A single
            # failing gpg stub also failed `--batch --import`, so the step
            # refused for the wrong reason and a `|| true` bolted onto the
            # verify line went unnoticed — the exact defeat this test exists to
            # catch, and one the break-and-watch matrix found.
            bad = run_step(step, context(), cwd=workdir, stubs={
                "gpg": [Stub(contains=("--import",), exit=0),
                        Stub(contains=("--verify",), exit=1)],
            })
            self.assertNotEqual(
                bad.returncode, 0,
                "a signature that does not verify must fail the release",
            )

    # -- "Publish the release" (release job) --------------------------------

    def publish(self, workdir: Path, *, tag_status: int = 2, **inputs):
        step = find_step(self.workflow, RELEASE_JOB, PUBLISH_STEP)
        return run_step(
            step,
            context(**inputs),
            cwd=workdir,
            stubs={
                "git": [Stub(contains=("ls-remote",), exit=tag_status)],
                "gh": [Stub()],
            },
        )

    def test_a_candidate_writes_a_manifest_and_publishes_nothing(self):
        with tempfile.TemporaryDirectory() as workspace:
            workdir = Path(workspace)
            write_dist(workdir)
            result = self.publish(workdir, **{"inputs.publish": False, "inputs.notarize": False})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.called("gh", "release", "create"), [])
            manifest = (workdir / "dist" / "CANDIDATE-MANIFEST.txt").read_text(encoding="utf-8")
            self.assertIn("publish=false", manifest)
            self.assertIn("notarize=false", manifest)

    def test_an_unnotarized_publish_is_refused(self):
        with tempfile.TemporaryDirectory() as workspace:
            workdir = Path(workspace)
            write_dist(workdir)
            result = self.publish(workdir, **{"inputs.publish": True, "inputs.notarize": False})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing to publish an unsigned or unnotarized build.", result.stderr)
            self.assertEqual(result.called("gh", "release", "create"), [])

    def test_an_existing_tag_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as workspace:
            workdir = Path(workspace)
            write_dist(workdir)
            result = self.publish(workdir, tag_status=0)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("The tag v9.9.9 already exists.", result.stderr)
            self.assertEqual(
                result.called("gh", "release", "create"), [],
                "the run must not reach gh release create when the tag exists",
            )

    def test_an_unverifiable_tag_state_refuses_publication(self):
        with tempfile.TemporaryDirectory() as workspace:
            workdir = Path(workspace)
            write_dist(workdir)
            result = self.publish(workdir, tag_status=1)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Could not verify remote tag state; refusing publication.", result.stderr)
            self.assertEqual(result.called("gh", "release", "create"), [])

    def test_a_notarized_publish_of_an_absent_tag_reaches_the_release_command(self):
        with tempfile.TemporaryDirectory() as workspace:
            workdir = Path(workspace)
            write_dist(workdir)
            result = self.publish(workdir, tag_status=2)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                result.called("gh", "release", "create", "v9.9.9"),
                "a signed candidate on an absent tag must publish",
            )


@unittest.skipUnless(yaml_available(), "PyYAML is required to read the workflow")
class InterpolationLintTests(unittest.TestCase):
    """M2 / CT-72 class: template expansion is code generation.

    Any ``${{ ... }}`` left inside a ``run:`` body is text substituted into a
    shell program before bash parses it. Most of the current sites are benign
    booleans, but "benign today" is how this class survives: the next input
    someone adds arrives through the same door. Values belong in ``env:``,
    which the shell treats as data and never as syntax.
    """

    def test_no_run_body_interpolates_a_github_expression(self):
        workflow = load_workflow()
        offenders = []
        for job_name, job in workflow["jobs"].items():
            for step in job.get("steps", []):
                body = step.get("run")
                if not body:
                    continue
                for match in EXPRESSION.finditer(body):
                    offenders.append(
                        f"{job_name} / {step.get('name')!r}: {match.group(0)}"
                    )
        self.assertEqual(
            offenders,
            [],
            "a run: body interpolates an expression into shell text "
            "(pass it through env: instead): " + "; ".join(offenders),
        )

    def test_the_step_that_uses_each_expression_still_receives_it(self):
        """The lint must be satisfiable without silently dropping a value.

        This is the positive half: after the interpolation is moved into env:,
        the env: key must still carry the same expression, so removing the
        value fails here rather than passing both tests.
        """
        workflow = load_workflow()
        guard = find_step(workflow, GUARD_JOB, GUARD)
        body = guard.get("run", "")
        self.assertIn(
            "CANDIDATE_RUN_ID",
            body,
            "the guard must read the run id from a shell variable",
        )
        env = guard.get("env", {}) or {}
        self.assertEqual(
            env.get("CANDIDATE_RUN_ID"),
            "${{ inputs.candidate_run_id }}",
            "the run id must still reach the step, through env: rather than "
            "through the script text",
        )


if __name__ == "__main__":
    unittest.main()
