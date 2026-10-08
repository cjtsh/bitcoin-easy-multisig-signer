"""Pin the remaining audit Lows so a future edit cannot silently weaken them.

CT-29 — source-mode HWI must identify as the pinned release
CT-34 — imported signatures must be BIP-62 low-S
CT-43 — a saved PSBT that carries signatures is not "unsigned"
CT-84 — the key-proof message digest must match published, external vectors

(CT-20's genesis-always pin lives in test_gui_integration.py next to the
scan harness. CT-17's runner pins live in test_workflow_config.py.)

Each test exists because the corresponding control is correct after the
cycle-3 fixes and nothing else in the suite would notice if a later edit
weakened it. Break-and-watch: remove the gate, watch this file go red.
"""

import hashlib
import os
import re
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from embit import ec
from embit.networks import NETWORKS

from support import find_build_recipe

import gui
import probe
from fake_explorer import three_output_wallet
from probe import (
    EXPECTED_HWI_VERSION, HWI_PAYLOAD_PINS, ProbeError, _bitcoin_message_digest,
    _hwi_command, _hwi_path, _verify_hwi_identity, _verify_message_signature,
    begin_signing_session, invoke_hwi, parse_bsms, prove_signer_holds_key,
    verify_signer_device,
)
from signing import SECP256K1_HALF_ORDER, SigningError, _is_low_s, verified_input_signatures
from test_money_path_pins import prepared
from test_probe import test_record
from wallet_service import build_unsigned_psbt, scan_wallet, wallet_layout


# ---------------------------------------------------------------------------
# CT-29 / CT-49 / CT-58 — HWI helper identity
# ---------------------------------------------------------------------------

def _write_planted_helper(folder: Path, version_line: str) -> Path:
    """Write into `folder` a helper this platform can actually execute.

    Windows CreateProcess cannot exec a shebang script (WinError 193), so the
    planted helper must be a real .cmd there and a shell script elsewhere. The
    identity gate runs [path, "--version"] either way, so both spellings have
    to answer it — a test that plants the wrong one fails on the platform
    difference and never reaches the control it is meant to pin. Returns the
    path written.
    """
    helper = Path(folder) / ("hwi.cmd" if sys.platform == "win32" else "hwi")
    if sys.platform == "win32":
        helper.write_text(
            "@echo off\r\n"
            f'if "%1"=="--version" (\r\n  echo {version_line}\r\n  exit /b 0\r\n)\r\n'
            "echo []\r\n",
            encoding="utf-8",
        )
    else:
        helper.write_text(
            "#!/bin/sh\n"
            f'if [ "$1" = "--version" ]; then echo "{version_line}"; exit 0; fi\n'
            "echo '[]'\n",
            encoding="utf-8",
        )
        helper.chmod(0o755)
    return helper


class HwiIdentityPins(unittest.TestCase):
    """The helper is pinned by bytes, not by what it says about itself.

    CT-49: a planted helper that echoes the pinned version string used to be
    believed. It is now refused unless its bytes match a digest that is not
    its own claim, and source mode does not execute a helper binary at all.
    CT-58: the identity is re-checked at every signing session.
    """

    def setUp(self):
        probe._verified_hwi_paths.clear()
        probe._verified_hwi_files.clear()

    def _planted_helper(self, folder: Path, version_line: str,
                        with_digest: bool = True) -> Path:
        helper = _write_planted_helper(Path(folder), version_line)
        if with_digest:
            digest = hashlib.sha256(helper.read_bytes()).hexdigest()
            helper.with_name("hwi.sha256").write_text(f"{digest}  hwi\n", encoding="utf-8")
        return helper

    # -- the plant itself must be executable here --------------------------

    def test_the_planted_helper_is_whatever_this_platform_can_execute(self):
        """A shebang script is not a valid Win32 application.

        This is the mistake the 0.6.7 candidate caught in its own tests: a
        helper planted as an unconditional shell script makes CreateProcess
        raise WinError 193 on Windows, so the test fails on the platform
        difference and never reaches the control it is pinning. The plant has
        to change shape with the platform, and this asserts that it does on
        every runner — a Windows machine is not required to notice it stopped.
        """
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(sys, "platform", "win32"):
                helper = _write_planted_helper(Path(folder),
                                               f"hwi {EXPECTED_HWI_VERSION}")
            self.assertEqual(helper.name, "hwi.cmd")
            body = helper.read_text(encoding="utf-8")
            self.assertIn("@echo off", body)
            self.assertNotIn("#!/", body)

        with tempfile.TemporaryDirectory() as folder:
            with patch.object(sys, "platform", "darwin"):
                helper = _write_planted_helper(Path(folder),
                                               f"hwi {EXPECTED_HWI_VERSION}")
            self.assertEqual(helper.name, "hwi")
            self.assertTrue(
                helper.read_text(encoding="utf-8").startswith("#!/bin/sh\n"))

    # -- the named CT-49 test ----------------------------------------------

    def test_a_planted_helper_that_echoes_the_pinned_version_string_is_refused(self):
        """CT-49: saying 'hwi 3.2.0' is no longer an identity.

        The bytes gate runs first and does not execute the helper at all, so
        the version string never gets a chance to be believed.
        """
        with tempfile.TemporaryDirectory() as folder:
            helper = self._planted_helper(folder, f"hwi {EXPECTED_HWI_VERSION}",
                                          with_digest=False)
            with patch("probe.subprocess.run") as run:
                with self.assertRaisesRegex(
                        ProbeError, "carries no digest for this app to verify"):
                    _verify_hwi_identity(str(helper))
            run.assert_not_called()

    # -- the positive halves ----------------------------------------------

    def test_an_honest_helper_with_a_matching_hash_sidecar_is_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._planted_helper(folder, f"hwi {EXPECTED_HWI_VERSION}")
            _verify_hwi_identity(str(helper))
            self.assertIn(str(helper), probe._verified_hwi_paths)

    def test_a_helper_that_reports_the_pinned_release_is_accepted_once(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._planted_helper(folder, f"hwi {EXPECTED_HWI_VERSION}")
            _verify_hwi_identity(str(helper))
            with patch("probe.subprocess.run") as run:
                _verify_hwi_identity(str(helper))
            run.assert_not_called()

    # -- the byte gate ----------------------------------------------------

    def test_a_frozen_build_refuses_a_helper_that_does_not_match_its_sidecar(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._planted_helper(folder, f"hwi {EXPECTED_HWI_VERSION}")
            helper.with_name("hwi.sha256").write_text(
                "0" * 64 + "  hwi\n", encoding="utf-8")
            with patch("probe.subprocess.run") as run:
                with self.assertRaisesRegex(
                        ProbeError, "does not match its recorded digest"):
                    _verify_hwi_identity(str(helper))
            run.assert_not_called()

    def test_a_standalone_helper_without_a_sidecar_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._planted_helper(folder, f"hwi {EXPECTED_HWI_VERSION}",
                                          with_digest=False)
            with self.assertRaisesRegex(
                    ProbeError, "carries no digest for this app to verify"):
                _verify_hwi_identity(str(helper))

    def test_an_empty_sidecar_is_not_a_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._planted_helper(folder, f"hwi {EXPECTED_HWI_VERSION}")
            helper.with_name("hwi.sha256").write_text("\n", encoding="utf-8")
            with self.assertRaisesRegex(
                    ProbeError, "carries no digest for this app to verify"):
                _verify_hwi_identity(str(helper))

    def test_a_frozen_macos_bundle_reads_the_sidecar_from_contents_resources(self):
        """macOS cannot keep the sidecar beside the helper.

        codesign refuses to seal an .app carrying a non-code file in
        Contents/MacOS, so the 0.6.7 build records the digest in
        Contents/Resources. The app has to look there, or a correct build is
        refused at run time and a substituted helper is checked against nothing.
        """
        with tempfile.TemporaryDirectory() as folder:
            macos = Path(folder) / "Bitcoin Easy Signer.app" / "Contents" / "MacOS"
            resources = macos.parent / "Resources"
            macos.mkdir(parents=True)
            resources.mkdir(parents=True)
            helper = _write_planted_helper(macos, f"hwi {EXPECTED_HWI_VERSION}")
            digest = hashlib.sha256(helper.read_bytes()).hexdigest()
            (resources / "hwi.sha256").write_text(f"{digest}  hwi\n", encoding="utf-8")
            self.assertEqual(probe._hwi_sidecars(str(helper)),
                             [resources / "hwi.sha256"])
            _verify_hwi_identity(str(helper))
            probe._verified_hwi_paths.clear()

    def test_two_sidecars_that_disagree_about_the_helper_are_refused(self):
        """A stale copy beside the helper must not shadow a correct one.

        Both present copies are checked. One wrong digest is a tampering signal,
        not a choice the app gets to make by picking the friendlier file. The
        correct copy is placed first in the lookup order on purpose, so a gate
        that stops at the first match, or that accepts any single match, is
        refused here rather than slipping through.
        """
        with tempfile.TemporaryDirectory() as folder:
            macos = Path(folder) / "App.app" / "Contents" / "MacOS"
            resources = macos.parent / "Resources"
            macos.mkdir(parents=True)
            resources.mkdir(parents=True)
            bundled = _write_planted_helper(macos, f"hwi {EXPECTED_HWI_VERSION}")
            digest = hashlib.sha256(bundled.read_bytes()).hexdigest()
            bundled.with_name("hwi.sha256").write_text(
                f"{digest}  hwi\n", encoding="utf-8")
            (resources / "hwi.sha256").write_text(
                "0" * 64 + "  hwi\n", encoding="utf-8")
            self.assertEqual(len(probe._hwi_sidecars(str(bundled))), 2)
            with patch("probe.subprocess.run") as run:
                with self.assertRaisesRegex(
                        ProbeError, "does not match its recorded digest"):
                    _verify_hwi_identity(str(bundled))
            run.assert_not_called()

    def test_two_sidecars_that_agree_about_the_helper_are_both_believed(self):
        """The positive half of the disagreement rule.

        Agreement across the two locations is not itself a refusal; only a
        digest that does not match is. Without this, a gate that refuses any
        helper with two records would pass the test above.
        """
        with tempfile.TemporaryDirectory() as folder:
            macos = Path(folder) / "App.app" / "Contents" / "MacOS"
            resources = macos.parent / "Resources"
            macos.mkdir(parents=True)
            resources.mkdir(parents=True)
            bundled = _write_planted_helper(macos, f"hwi {EXPECTED_HWI_VERSION}")
            record = f"{hashlib.sha256(bundled.read_bytes()).hexdigest()}  hwi\n"
            bundled.with_name("hwi.sha256").write_text(record, encoding="utf-8")
            (resources / "hwi.sha256").write_text(record, encoding="utf-8")
            self.assertEqual(len(probe._hwi_sidecars(str(bundled))), 2)
            _verify_hwi_identity(str(bundled))
            probe._verified_hwi_paths.clear()

    # -- version is exact, not a substring --------------------------------

    def test_a_helper_that_only_uses_the_version_number_as_a_substring_is_refused(self):
        """`hwi-3.2.0` and `evil hwi 3.2.0 inside` used to pass an `in` check."""
        for spelling in (f"hwi-{EXPECTED_HWI_VERSION}",
                         f"evil hwi {EXPECTED_HWI_VERSION} inside",
                         f"hwi {EXPECTED_HWI_VERSION}-evil",
                         f"hwi {EXPECTED_HWI_VERSION}",
                         f"hwi.exe {EXPECTED_HWI_VERSION}",
                         f"hwi_entry.py {EXPECTED_HWI_VERSION}"):
            expected = (spelling == f"hwi {EXPECTED_HWI_VERSION}"
                        or spelling == f"hwi.exe {EXPECTED_HWI_VERSION}"
                        or spelling == f"hwi_entry.py {EXPECTED_HWI_VERSION}")
            with self.subTest(spelling=spelling):
                with tempfile.TemporaryDirectory() as folder:
                    helper = self._planted_helper(folder, spelling)
                    if expected:
                        _verify_hwi_identity(str(helper))
                        probe._verified_hwi_paths.clear()
                    else:
                        with self.assertRaisesRegex(ProbeError, "does not identify as HWI"):
                            _verify_hwi_identity(str(helper))

    def test_a_helper_that_cannot_answer_version_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._planted_helper(folder, f"hwi {EXPECTED_HWI_VERSION}")
            if sys.platform == "win32":
                helper.write_text("@echo off\r\nexit /b 1\r\n", encoding="utf-8")
            else:
                helper.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
                helper.chmod(0o755)
            digest = hashlib.sha256(helper.read_bytes()).hexdigest()
            helper.with_name("hwi.sha256").write_text(f"{digest}  hwi\n", encoding="utf-8")
            with self.assertRaisesRegex(
                    ProbeError, "does not identify as HWI|could not be identified"):
                _verify_hwi_identity(str(helper))

    # -- source mode: no helper binary, no PATH ---------------------------

    def test_source_mode_executes_the_in_tree_entry_under_the_anchored_interpreter(self):
        entry = Path(probe.__file__).resolve().parent / "scripts" / "hwi_entry.py"
        self.assertTrue(entry.is_file(),
                        "scripts/hwi_entry.py must exist for source mode to run")
        with patch.object(sys, "frozen", False, create=True), \
                patch.object(sys, "executable", "/nowhere/python3"):
            self.assertEqual(
                _hwi_command("hwi"),
                ["/nowhere/python3", "-I", "-P", str(entry)])

    def test_the_path_lookup_fallback_is_gone(self):
        """CT-49: probe.py must not be able to resolve a helper from PATH.

        The lookup was a `shutil.which` fallback. Removing the import removes
        the capability, not just the call site.
        """
        source = Path(probe.__file__).read_text(encoding="utf-8")
        self.assertNotIn("shutil.which", source)
        self.assertNotIn("import shutil", source)
        self.assertNotIn("which(", source)

    def test_an_explicit_path_is_used_as_given(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = Path(folder) / "official-hwi"
            helper.write_bytes(b"")
            self.assertEqual(_hwi_path(str(helper)), str(helper))

    def test_source_mode_refuses_a_bare_name_whose_entry_point_is_missing(self):
        with patch.object(sys, "frozen", False, create=True), \
                patch.object(probe, "_in_tree_hwi_entry",
                             return_value=Path("/nowhere/hwi_entry.py")):
            with self.assertRaisesRegex(ProbeError, "missing from this checkout"):
                _hwi_path("hwi")

    # -- the payload pin for source mode ----------------------------------

    def test_the_payload_pins_pin_the_published_hwilib_files(self):
        """Nobody may 'update' a pin without changing this test."""
        self.assertEqual(HWI_PAYLOAD_PINS, {
            "hwilib": "3945f7ed877a64ef367741892f67662b48194ed73fc6f953bc640897623e0fc9",
            "hwilib._cli": "c0d83c4d9a90fadba88ce554dcb45744d92c3ce04dbcecd98a7c43d4f9bfe35e",
        })

    def test_a_substituted_hwilib_payload_is_refused(self):
        """A poisoned site-packages must not be believed just because it imports."""
        entry = Path(probe.__file__).resolve().parent / "scripts" / "hwi_entry.py"
        with tempfile.TemporaryDirectory() as folder:
            helper = Path(folder) / "hwi_entry.py"
            helper.write_bytes(entry.read_bytes())
            seen = "\n".join(
                f"{name} /nowhere/{name.replace('.', '_')}.py {'0' * 64}"
                for name in HWI_PAYLOAD_PINS)
            with patch("probe.subprocess.run",
                       return_value=CompletedProcess([], 0, seen, "")) as run:
                with self.assertRaisesRegex(
                        ProbeError, "does not match its recorded digest"):
                    _verify_hwi_identity(str(helper), [sys.executable, str(helper)])
        # The payload check ran before any --version question was asked.
        self.assertEqual(run.call_count, 1)
        argv = run.call_args.args[0]
        self.assertEqual(argv[:3], [sys.executable, "-I", "-P"])
        self.assertIn("hwilib", argv[-1])
        self.assertNotIn("import_module", argv[-1])

    def test_the_payload_checker_accepts_the_anchored_interpreter(self):
        entry = Path(probe.__file__).resolve().parent / "scripts" / "hwi_entry.py"
        with tempfile.TemporaryDirectory() as folder:
            helper = Path(folder) / "hwi_entry.py"
            helper.write_bytes(entry.read_bytes())
            seen = "\n".join(
                f"{name} /nowhere/{name.replace('.', '_')}.py {digest}"
                for name, digest in HWI_PAYLOAD_PINS.items())
            version = f"hwi_entry.py {EXPECTED_HWI_VERSION}"

            def fake_run(argv, **kwargs):
                if "--version" in argv:
                    return CompletedProcess(argv, 0, version, "")
                return CompletedProcess(argv, 0, seen, "")

            with patch("probe.subprocess.run", side_effect=fake_run):
                _verify_hwi_identity(str(helper), [sys.executable, str(helper)])
            self.assertIn(str(helper), probe._verified_hwi_paths)

    def test_the_check_and_the_helper_import_the_same_package(self):
        """CT-90: one interpreter, one rule, or the hashed path is not the run path.

        `-I` (isolated) implies `-E`, `-s` and `-P`: PYTHONPATH, the user site
        directory and the script's own directory are all ignored. The payload
        check and the helper are handed the same flags, so a directory the
        check cannot see is a directory the helper cannot import from either.
        """
        flags = ["-I", "-P"]
        self.assertEqual(list(probe._HWI_ISOLATION_FLAGS), flags)
        with patch.object(sys, "frozen", False, create=True), \
                patch.object(sys, "executable", "/nowhere/python3"):
            self.assertEqual(
                _hwi_command("hwi")[:3], ["/nowhere/python3", *flags])
            check = probe._hwi_payload_check_command("pass")
            self.assertEqual(check[:3], ["/nowhere/python3", *flags])
            self.assertEqual(check[-2:], ["-c", "pass"])

    def test_a_hwilib_that_lies_about_its_files_is_refused_without_running_it(self):
        """CT-90's exact attack, reproduced over a real subprocess.

        The poisoned package is reachable here -- PYTHONPATH points straight at
        it and the isolation flags are dropped for this one test -- which is the
        strongest form of the question. The old check learned its paths with
        ``importlib.import_module``, so it ran the attacker's ``__init__.py``:
        the marker appeared, the planted ``__file__`` and
        ``sys.modules['hwilib._cli']`` pointed the digests at the genuine decoy
        files, and the pin passed. ``PathFinder.find_spec`` answers without
        executing anything, so the digest is the attacker's own bytes.
        """
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            marker = root / "the-fake-ran.txt"
            decoy = root / "decoy" / "hwilib"
            decoy.mkdir(parents=True)
            (decoy / "__init__.py").write_text("# genuine\n", encoding="utf-8")
            (decoy / "_cli.py").write_text("# genuine cli\n", encoding="utf-8")
            fake = root / "site" / "hwilib"
            fake.mkdir(parents=True)
            (fake / "_cli.py").write_text("# fake cli\n", encoding="utf-8")
            (fake / "__init__.py").write_text(
                "import pathlib, sys, types\n"
                f"pathlib.Path({str(marker)!r}).write_text('ran')\n"
                f"__file__ = {str(decoy / '__init__.py')!r}\n"
                "sys.modules[__name__].__file__ = __file__\n"
                "sys.modules['hwilib._cli'] = types.ModuleType('hwilib._cli')\n"
                "sys.modules['hwilib._cli'].__file__ = "
                f"{str(decoy / '_cli.py')!r}\n",
                encoding="utf-8")
            pins = {
                "hwilib": hashlib.sha256(
                    (decoy / "__init__.py").read_bytes()).hexdigest(),
                "hwilib._cli": hashlib.sha256(
                    (decoy / "_cli.py").read_bytes()).hexdigest(),
            }
            with patch.dict(probe.HWI_PAYLOAD_PINS, pins, clear=True), \
                    patch.dict(os.environ, {"PYTHONPATH": str(root / "site")}), \
                    patch.object(probe, "_hwi_payload_check_command",
                                 lambda script: [sys.executable, "-c", script]):
                with self.assertRaisesRegex(
                        ProbeError, "does not match its recorded digest"):
                    probe._verify_hwi_payload()
            self.assertFalse(
                marker.exists(),
                "the payload check imported the package it was inspecting")

    def test_the_payload_check_accepts_a_package_whose_bytes_are_recorded(self):
        """The other half of the pin: matching bytes pass, with no import."""
        with tempfile.TemporaryDirectory() as folder:
            package = Path(folder) / "site" / "hwilib"
            package.mkdir(parents=True)
            (package / "__init__.py").write_text(
                "# pinned init\n", encoding="utf-8")
            (package / "_cli.py").write_text(
                "# pinned cli\n", encoding="utf-8")
            pins = {
                "hwilib": hashlib.sha256(
                    (package / "__init__.py").read_bytes()).hexdigest(),
                "hwilib._cli": hashlib.sha256(
                    (package / "_cli.py").read_bytes()).hexdigest(),
            }
            with patch.dict(probe.HWI_PAYLOAD_PINS, pins, clear=True), \
                    patch.dict(os.environ,
                               {"PYTHONPATH": str(package.parent)}), \
                    patch.object(probe, "_hwi_payload_check_command",
                                 lambda script: [sys.executable, "-c", script]):
                probe._verify_hwi_payload()

    # -- CT-58: re-identify at every signing session ----------------------

    def test_the_verified_helper_is_re_identified_at_each_signing_session(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._planted_helper(folder, f"hwi {EXPECTED_HWI_VERSION}")
            _verify_hwi_identity(str(helper))
            self.assertIn(str(helper), probe._verified_hwi_paths)
            record = type("R", (), {"keys": [None, None, None]})()
            # A bad signer index fails after begin_signing_session() has run.
            with self.assertRaisesRegex(ProbeError, "Check this signing device"):
                verify_signer_device(record, str(helper), "test", "trezor", "p", 99)
            self.assertNotIn(str(helper), probe._verified_hwi_paths,
                             "a signing session must not inherit a cached identity")
            with patch("probe.subprocess.run",
                       return_value=CompletedProcess(
                           [], 0, f"hwi {EXPECTED_HWI_VERSION}", "")) as run:
                _verify_hwi_identity(str(helper))
            self.assertEqual(run.call_count, 1,
                             "the next call pays the identity check again")

    def test_begin_signing_session_clears_every_cached_identity(self):
        probe._verified_hwi_paths.add("/one")
        probe._verified_hwi_paths.add("/two")
        probe._verified_hwi_files["/one"] = (("/one", "0" * 64),)
        begin_signing_session()
        self.assertEqual(probe._verified_hwi_paths, set())
        self.assertEqual(probe._verified_hwi_files, {})

    # -- CT-91: a cached verdict is a memory of bytes ----------------------

    def test_a_helper_swapped_inside_one_session_does_not_inherit_the_verdict(self):
        """CT-91: the cache remembers bytes, not permission.

        Between two calls in one signing session the file on disk can change.
        A cache keyed on the path alone returns early the second time and the
        swapped helper runs; this re-reads what was hashed and puts the new
        bytes back through the same digest gate.
        """
        with tempfile.TemporaryDirectory() as folder:
            helper = self._planted_helper(folder, f"hwi {EXPECTED_HWI_VERSION}")
            _verify_hwi_identity(str(helper))
            self.assertIn(str(helper), probe._verified_hwi_paths)
            helper.write_text(helper.read_text() + "\n# swapped after the check\n")
            with self.assertRaisesRegex(
                    ProbeError, "does not match its recorded digest"):
                _verify_hwi_identity(str(helper))
            self.assertNotIn(str(helper), probe._verified_hwi_paths,
                             "a stale verdict must not survive the swap")

    def test_an_unchanged_helper_is_still_checked_only_once(self):
        """The re-read must not cost a second --version run on the fast path."""
        with tempfile.TemporaryDirectory() as folder:
            helper = self._planted_helper(folder, f"hwi {EXPECTED_HWI_VERSION}")
            _verify_hwi_identity(str(helper))
            with patch("probe.subprocess.run",
                       return_value=CompletedProcess(
                           [], 0, f"hwi {EXPECTED_HWI_VERSION}", "")) as run:
                _verify_hwi_identity(str(helper))
            self.assertEqual(run.call_count, 0,
                             "unchanged bytes must not pay the identity check again")

    # -- nothing runs unverified ------------------------------------------

    def test_invoke_hwi_refuses_before_it_sends_any_wallet_material(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._planted_helper(folder, "planted 0.0.1")
            with patch("probe.subprocess.run",
                       return_value=CompletedProcess([], 0, "planted 0.0.1", "")) as run:
                with self.assertRaisesRegex(ProbeError, "does not identify as HWI"):
                    invoke_hwi(str(helper), "testnet4", "enumerate")
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0], [str(helper), "--version"])

    # -- the comment must describe the control it sits on ------------------

    def test_the_identity_docstring_names_every_sidecar_it_actually_reads(self):
        """A comment that understates a money-adjacent control is a finding.

        A frozen macOS bundle keeps its digest sidecar in Contents/Resources,
        so the old wording — "match the digest recorded beside it" — described
        a rule weaker than the one _verify_hwi_bytes runs. The referee reads
        the comment and the code and finds they disagree. Both halves are
        pinned: the stale phrase must stay gone, and the true rule must stay
        present.
        """
        source = (Path(__file__).resolve().parents[1] / "probe.py").read_text(
            encoding="utf-8")
        self.assertNotIn(
            "match the digest recorded beside it", source,
            "the identity docstring must not describe a sidecar-only-beside "
            "rule; a frozen macOS bundle keeps it in Contents/Resources")
        self.assertIn(
            "every digest sidecar that is present", source,
            "the identity docstring must describe the multi-sidecar rule that "
            "_verify_hwi_bytes actually runs")


# ---------------------------------------------------------------------------
# CT-34 — BIP-62 low-S on imported signatures
# ---------------------------------------------------------------------------

def _high_s_der(low_der: bytes) -> bytes:
    """Rewrite a DER signature's S to n-S, keeping it parseable-looking."""
    order = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    r_len = low_der[3]
    r_bytes = low_der[4:4 + r_len]
    s_off = 5 + r_len
    s_len = low_der[s_off]
    s = int.from_bytes(low_der[s_off + 1:s_off + 1 + s_len], "big")
    high = order - s
    s_bytes = high.to_bytes((high.bit_length() + 8) // 8, "big")
    if s_bytes[0] & 0x80:
        s_bytes = b"\x00" + s_bytes
    body = (b"\x02" + bytes([len(r_bytes)]) + r_bytes
            + b"\x02" + bytes([len(s_bytes)]) + s_bytes)
    return b"\x30" + bytes([len(body)]) + body


class LowSPins(unittest.TestCase):
    def test_a_high_s_signature_is_refused_with_the_low_s_message(self):
        """CT-34: the specific message is the tripwire.

        If the explicit gate is removed, embit's parser raises a generic
        'invalid signature' instead — and this test goes red.
        """
        packet, keys, _result = prepared()
        packet.sign_with(keys[0])
        scope = packet.inputs[0]
        pubkey, sig = next(iter(scope.partial_sigs.items()))
        der = bytes(sig)[:-1]
        high = _high_s_der(der) + b"\x01"
        scope.partial_sigs[pubkey] = high
        with self.assertRaisesRegex(SigningError, "low-S"):
            verified_input_signatures(packet)

    def test_the_genuine_low_s_signature_still_verifies(self):
        packet, keys, _result = prepared()
        for key in keys[:2]:
            packet.sign_with(key)
        verified = verified_input_signatures(packet)
        self.assertEqual(len(verified), len(packet.inputs))
        self.assertTrue(all(len(valid) == 2 for valid in verified))

    def test_s_exactly_at_half_order_is_low(self):
        r = (1).to_bytes(32, "big")
        s = SECP256K1_HALF_ORDER.to_bytes(32, "big")
        der = b"\x30\x44\x02\x20" + r + b"\x02\x20" + s
        self.assertTrue(_is_low_s(der))

    def test_s_just_above_half_order_is_high(self):
        r = (1).to_bytes(32, "big")
        s = (SECP256K1_HALF_ORDER + 1).to_bytes(32, "big")
        der = b"\x30\x44\x02\x20" + r + b"\x02\x20" + s
        self.assertFalse(_is_low_s(der))


# ---------------------------------------------------------------------------
# CT-43 — signed PSBTs are not named "unsigned"
# ---------------------------------------------------------------------------

class SaveNamingPins(unittest.TestCase):
    def test_a_psbt_without_signatures_keeps_the_unsigned_name(self):
        text, _roots = test_record(bsms_template=True)
        record = parse_bsms(text)
        layout = wallet_layout(record)
        explorer = three_output_wallet(layout, NETWORKS["test"])
        scan = scan_wallet(record, explorer)
        result = build_unsigned_psbt(
            record, scan, layout.receive.derive(5).address(NETWORKS["test"]),
            10_000, 5, explorer)

        class Prepared:
            psbt_base64 = result["psbt_base64"]

        class State:
            lock = threading.RLock()
            prepared = Prepared()
            chain = "testnet4"

        with tempfile.TemporaryDirectory() as folder:
            saved = gui.save_prepared_psbt(State, "testnet4", Path(folder))
        self.assertEqual(Path(saved["path"]).name, "testnet4-unsigned.psbt")

    def test_a_psbt_with_verified_signatures_is_not_called_unsigned(self):
        packet, keys, _result = prepared()
        for key in keys[:2]:
            packet.sign_with(key)

        class Prepared:
            psbt_base64 = packet.to_base64()

        class State:
            lock = threading.RLock()
            prepared = Prepared()
            chain = "testnet4"

        with tempfile.TemporaryDirectory() as folder:
            saved = gui.save_prepared_psbt(State, "testnet4", Path(folder))
        name = Path(saved["path"]).name
        self.assertEqual(name, "testnet4-signed.psbt")
        self.assertNotIn("unsigned", name)


# ---------------------------------------------------------------------------
# CT-14 — a counterfeit must not receive the payment PSBT
# ---------------------------------------------------------------------------

class DeviceProofPins(unittest.TestCase):
    def setUp(self):
        text, self.roots = test_record()
        self.wallet = parse_bsms(text)
        self.account = self.roots[0].derive("m/48h/1h/0h/2h")

    def _signed_response(self, message: str) -> dict:
        # Sign at the first receive child, not the account node. Trezor (and
        # OneKey on Trezor firmware) refuse signmessage on an all-hardened
        # BIP48 account path; the proof is taken at /0/0 under that account.
        digest = _bitcoin_message_digest(message.encode("utf-8"))
        return {"signature": self.account.child(0).child(0).key.sign(digest).serialize().hex()}

    def test_a_fresh_challenge_is_required_before_any_psbt_is_sent(self):
        """CT-14: echoing an account xpub is not proof of the private key."""
        seen = []
        paths = []

        def fake_hwi(_exe, _chain, *args, **options):
            if "signmessage" in args:
                message = args[args.index("signmessage") + 1]
                seen.append(message)
                paths.append(args[args.index("signmessage") + 2])
                return self._signed_response(message)
            raise AssertionError(f"unexpected HWI call: {args}")

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            prove_signer_holds_key(self.wallet, "hwi", "test", "jade", "/dev/x", 1)
        self.assertEqual(len(seen), 1)
        self.assertTrue(seen[0].startswith("Bitcoin Easy Signer key proof "))

    def test_the_proof_signs_at_the_first_receive_path_not_the_account_node(self):
        """Trezor Safe 3 / OneKey answer 'forbidden key path' on m/48h/1h/0h/2h.

        The proof must therefore travel at the first receive address under the
        same account xpub getxpub already matched.
        """
        paths = []

        def fake_hwi(_exe, _chain, *args, **options):
            paths.append(args[args.index("signmessage") + 2])
            message = args[args.index("signmessage") + 1]
            return self._signed_response(message)

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            prove_signer_holds_key(self.wallet, "hwi", "test", "trezor", "webusb:1", 1)
        self.assertEqual(paths, ["m/48h/1h/0h/2h/0/0"])
        self.assertNotEqual(paths[0], "m/48h/1h/0h/2h")

    def test_a_signature_from_the_wrong_key_is_refused(self):
        other = self.roots[1].derive("m/48h/1h/0h/2h")

        def fake_hwi(_exe, _chain, *args, **options):
            message = args[args.index("signmessage") + 1]
            digest = _bitcoin_message_digest(message.encode("utf-8"))
            return {"signature": other.child(0).child(0).key.sign(digest).serialize().hex()}

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            with self.assertRaisesRegex(ProbeError, "did not prove it holds the wallet key"):
                prove_signer_holds_key(self.wallet, "hwi", "test", "jade", "/dev/x", 1)

    def test_a_signature_from_the_account_node_itself_is_refused(self):
        """Signing with the account key must not pass — the gate is /0/0."""
        def fake_hwi(_exe, _chain, *args, **options):
            message = args[args.index("signmessage") + 1]
            digest = _bitcoin_message_digest(message.encode("utf-8"))
            return {"signature": self.account.key.sign(digest).serialize().hex()}

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            with self.assertRaisesRegex(ProbeError, "did not prove it holds the wallet key"):
                prove_signer_holds_key(self.wallet, "hwi", "test", "jade", "/dev/x", 1)

    def test_a_garbage_signature_is_refused(self):
        def fake_hwi(_exe, _chain, *args, **options):
            return {"signature": "not-a-signature"}

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            with self.assertRaisesRegex(ProbeError, "did not prove it holds the wallet key"):
                prove_signer_holds_key(self.wallet, "hwi", "test", "jade", "/dev/x", 1)

    def test_identity_check_also_demands_the_proof_before_returning(self):
        expected = self.account.to_public().to_base58()
        calls = []

        def fake_hwi(_exe, _chain, *args, **options):
            calls.append(args)
            if args[-2:] == ("getxpub", "m/48h/1h/0h/2h"):
                return {"xpub": expected}
            if "signmessage" in args:
                message = args[args.index("signmessage") + 1]
                return self._signed_response(message)
            raise AssertionError(f"unexpected HWI call: {args}")

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            verify_signer_device(self.wallet, "hwi", "test", "jade", "/dev/x", 1)
        self.assertEqual(len(calls), 2)
        self.assertIn("signmessage", calls[1])
        # The proof is taken at the first receive path so Trezor firmware
        # (and OneKey on that firmware) accept signmessage.
        self.assertEqual(calls[1][calls[1].index("signmessage") + 2],
                         "m/48h/1h/0h/2h/0/0")

    def test_identity_check_refuses_when_the_proof_fails(self):
        expected = self.account.to_public().to_base58()

        def fake_hwi(_exe, _chain, *args, **options):
            if args[-2] == "getxpub":
                return {"xpub": expected}
            return {"signature": "echo"}

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            with self.assertRaisesRegex(ProbeError, "did not prove it holds the wallet key"):
                verify_signer_device(self.wallet, "hwi", "test", "jade", "/dev/x", 1)


# ---------------------------------------------------------------------------
# CT-84 — the key-proof digest is pinned to vectors from outside this repo
# ---------------------------------------------------------------------------

class MessageDigestVectorPins(unittest.TestCase):
    """CT-84: `_bitcoin_message_digest` must match published, external vectors.

    Every other test of this function recomputes its expectation with the
    function itself, so a drifted envelope prefix, length byte or hash order
    would stay green here while every device key-proof in the field failed
    closed. The vectors below come from outside this repository:
    bitcoinjs-message's published `test/fixtures.json`, which records the
    envelope prefix byte for byte and the digest it computes for a message.

        https://github.com/bitcoinjs/bitcoinjs-message/blob/master/test/fixtures.json

    `valid.magicHash` holds the digest of a message; `valid.sign[0]` holds a
    complete triple — the declared private key `d = 1`, the message, and the
    compact signature that implementation produced over it.
    """

    # fixtures.json -> networks.bitcoin, quoted byte for byte.
    PUBLISHED_PREFIX = b"\x18Bitcoin Signed Message:\n"

    # fixtures.json -> valid.magicHash
    PUBLISHED_DIGESTS = (
        ("", "80e795d4a4caadd7047af389d9f7f220562feb6196032e2131e10563352c4bcc"),
        ("Vires is Numeris",
         "f8a5affbef4a3241b19067aa694562f64f513310817297089a8929a930f4f933"),
    )

    # fixtures.json -> valid.sign[0]: d = 1, message "vires is numeris".
    SIGNED_MESSAGE = b"vires is numeris"
    SIGNED_SIGNATURE = (
        "IF8nHqFr3K2UKYahhX3soVeoW8W1ECNbr0wfck7lzyXjCS5Q16Ek45zyBuy1Fiy9sTPKVgsqqOuPvbycuVSSVl8="
    )
    # The public key for the private key 1 is the secp256k1 generator itself.
    GENERATOR_SEC = "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"

    def test_the_envelope_is_the_published_prefix_and_variable_length(self):
        """Reassemble the published envelope here, without the function."""
        for message in (b"", b"ab", b"x" * 300):
            length = (bytes([len(message)]) if len(message) < 253 else
                      bytes([253, len(message) & 0xFF, (len(message) >> 8) & 0xFF]))
            payload = self.PUBLISHED_PREFIX + length + message
            self.assertEqual(
                hashlib.sha256(hashlib.sha256(payload).digest()).digest(),
                _bitcoin_message_digest(message),
                f"envelope digest differs for a {len(message)}-byte message",
            )

    def test_the_published_message_digests_are_reproduced(self):
        for message, expected in self.PUBLISHED_DIGESTS:
            with self.subTest(message=message):
                self.assertEqual(
                    _bitcoin_message_digest(message.encode("utf-8")).hex(), expected)

    def test_a_published_signature_verifies_against_the_published_key(self):
        """The whole proof path, against a signature this repository did not make."""
        key = ec.PrivateKey(bytes.fromhex("00" * 31 + "01"))
        self.assertEqual(key.get_public_key().sec().hex(), self.GENERATOR_SEC)
        self.assertTrue(_verify_message_signature(
            key.get_public_key().sec(), self.SIGNED_MESSAGE, self.SIGNED_SIGNATURE))

    def test_the_published_signature_is_refused_for_a_changed_message(self):
        key = ec.PrivateKey(bytes.fromhex("00" * 31 + "01"))
        self.assertFalse(_verify_message_signature(
            key.get_public_key().sec(), b"Vires is numeris", self.SIGNED_SIGNATURE))


# ---------------------------------------------------------------------------
# CT-30 — a lying-low price quote cannot suppress the large-amount prompt
# ---------------------------------------------------------------------------

class LargeAmountPins(unittest.TestCase):
    def test_the_untrusted_quote_floor_is_below_the_absolute_floor(self):
        self.assertLess(gui.LARGE_AMOUNT_SATS_UNTRUSTED_QUOTE,
                        gui.LARGE_AMOUNT_SATS_FLOOR)
        self.assertGreater(gui.LARGE_AMOUNT_SATS_UNTRUSTED_QUOTE, 0)

    def test_five_million_sats_still_count_as_large_at_a_one_dollar_quote(self):
        """CT-30: 0.05 BTC is a large payment whenever BTC is near $200k.

        A feed that reports $1 must not hide it. Without the conservative
        floor this amount is under 0.1 BTC and worth almost nothing at $1.
        """
        amount = 5_000_000
        self.assertLess(amount, gui.LARGE_AMOUNT_SATS_FLOOR)
        lying_price = 1.0
        self.assertLess(amount * lying_price / 100_000_000, 10_000)
        self.assertGreaterEqual(amount, gui.LARGE_AMOUNT_SATS_UNTRUSTED_QUOTE)


# ---------------------------------------------------------------------------
# CT-33 — lock-generation tooling is pinned on every platform
# ---------------------------------------------------------------------------

class PipToolsPinTests(unittest.TestCase):
    """Both lock jobs must resolve one pip-tools release, and agree on it.

    CT-57 moved the version pin out of the workflow text and into
    requirements-piptools.lock, so the workflows no longer spell `pip-tools==`.
    The control did not move: one release, used by both jobs, and the lock's
    input file must name that same release. This follows the pin rather than
    deleting the assertion that used to live here.
    """

    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_every_lock_job_pins_the_same_piptools_release(self):
        for name in ("windows-inputs.yml", "linux-inputs.yml"):
            # Checkout or source archive — see support.find_build_recipe.
            recipe = find_build_recipe(self.root, name)
            self.assertIsNotNone(
                recipe, f"{name} is missing from both .github/workflows/ and ci/")
            text = recipe.read_text(encoding="utf-8")
            active = "\n".join(
                line for line in text.splitlines()
                if not line.lstrip().startswith("#"))
            self.assertIn("requirements-piptools.lock", active,
                          f"{name} must install pip-tools from the committed lock")
            self.assertNotIn("pip install --disable-pip-version-check pip-tools\n", text)

        lock = (self.root / "requirements-piptools.lock").read_text(encoding="utf-8")
        releases = set(re.findall(r"^pip-tools==([0-9.a-z+]+)", lock, re.MULTILINE))
        self.assertEqual(len(releases), 1,
                         f"the lock must pin exactly one pip-tools release: {releases}")
        pinned = releases.pop()
        source = (self.root / "requirements-piptools.txt").read_text(encoding="utf-8")
        self.assertIn(f"pip-tools=={pinned}", source,
                      "the lock's input file must name the same release the lock "
                      "resolved, or the two disagree about what to regenerate")


# ---------------------------------------------------------------------------
# CT-46 / CT-71 — stale version strings are findings
# ---------------------------------------------------------------------------

# "The latest published release is 0.6.4" is the sentence CT-71 filed. It is
# stale the moment version.py moves. The digit is load-bearing: every live doc
# in this tree is allowed to quote the prohibition ("... is X"), and only an
# actual claim carries a version number. Archives and the frozen audit
# artifacts quote the finding itself and are deliberately out of scope.
_STALE_PUBLISHED_CLAIM = re.compile(
    r"(?:the\s+)?(?:latest|current)\s+published\s+(?:release|version|build)"
    r"\s+is\s+v?\d",
    re.IGNORECASE,
)
_LIVE_DOCS = ("AGENTS.md", "README.md", "CURRENT-STATUS.md",
              "PHASE-HANDOFF.md", "replit.md")


class VersionStringPins(unittest.TestCase):
    def test_agents_names_the_tree_revision_from_version_py(self):
        """CT-46: 'current published version is X' inside tag X+1 was filed."""
        root = Path(__file__).resolve().parents[1]
        version = re.search(
            r'APP_VERSION = "([^"]+)"',
            (root / "version.py").read_text(encoding="utf-8"),
        ).group(1)
        agents = (root / "AGENTS.md").read_text(encoding="utf-8").lower()
        self.assertIn(f"source revision is **{version}**".lower(), agents)
        history = (root / "RELEASE-HISTORY.md").read_text(encoding="utf-8")
        self.assertIn(f"| **{version}** |", history)
        notes = root / "releases" / f"RELEASE-NOTES-{version}.md"
        self.assertTrue(notes.is_file(), f"{notes} must exist when version.py moves")

    def test_no_live_doc_hardcodes_a_latest_published_release(self):
        """CT-71: the claim is the finding, not the wording around it.

        Every live doc points at RELEASE-HISTORY.md and the Releases page
        instead of restating a number. A later commit that puts the claim back
        goes red here rather than going stale in silence.
        """
        root = Path(__file__).resolve().parents[1]
        for name in _LIVE_DOCS:
            body = (root / name).read_text(encoding="utf-8")
            found = _STALE_PUBLISHED_CLAIM.search(body)
            if found is not None:
                self.fail(
                    f"{name} hardcodes a published-release claim: "
                    f"{found.group(0)!r}. Point at RELEASE-HISTORY.md and the "
                    f"Releases page instead.")

    def test_the_published_claim_pattern_is_not_vacuous(self):
        """The positive half, and the half that keeps the prohibitions legal.

        Without the first three assertions the pattern could match nothing and
        the test above would pass forever. Without the fourth, someone
        'tightening' it would force the prohibition sentences out of the docs
        that exist to stop this coming back.
        """
        for claim in ("The latest published release is 0.6.6.",
                      "Current published version is v0.6.6",
                      "our latest published build is 0.6.4"):
            self.assertRegex(claim, _STALE_PUBLISHED_CLAIM)
        self.assertIsNone(_STALE_PUBLISHED_CLAIM.search(
            'Do not state "the latest published release is X" here'))
        self.assertIsNone(_STALE_PUBLISHED_CLAIM.search(
            'do not restate a "current published release is X" here'))


if __name__ == "__main__":
    unittest.main()
