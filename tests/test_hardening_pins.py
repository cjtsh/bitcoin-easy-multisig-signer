"""Pin the remaining audit Lows so a future edit cannot silently weaken them.

CT-29 — source-mode HWI must identify as the pinned release
CT-34 — imported signatures must be BIP-62 low-S
CT-43 — a saved PSBT that carries signatures is not "unsigned"

(CT-20's genesis-always pin lives in test_gui_integration.py next to the
scan harness. CT-17's runner pins live in test_workflow_config.py.)

Each test exists because the corresponding control is correct after the
cycle-3 fixes and nothing else in the suite would notice if a later edit
weakened it. Break-and-watch: remove the gate, watch this file go red.
"""

import hashlib
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

from embit.networks import NETWORKS

import gui
import probe
from fake_explorer import three_output_wallet
from probe import (
    EXPECTED_HWI_VERSION, HWI_PAYLOAD_PINS, ProbeError, _bitcoin_message_digest,
    _hwi_command, _hwi_path, _verify_hwi_identity, begin_signing_session,
    invoke_hwi, parse_bsms, prove_signer_holds_key, verify_signer_device,
)
from signing import SECP256K1_HALF_ORDER, SigningError, _is_low_s, verified_input_signatures
from test_money_path_pins import prepared
from test_probe import test_record
from wallet_service import build_unsigned_psbt, scan_wallet, wallet_layout


# ---------------------------------------------------------------------------
# CT-29 / CT-49 / CT-58 — HWI helper identity
# ---------------------------------------------------------------------------

class HwiIdentityPins(unittest.TestCase):
    """The helper is pinned by bytes, not by what it says about itself.

    CT-49: a planted helper that echoes the pinned version string used to be
    believed. It is now refused unless its bytes match a digest that is not
    its own claim, and source mode does not execute a helper binary at all.
    CT-58: the identity is re-checked at every signing session.
    """

    def setUp(self):
        probe._verified_hwi_paths.clear()

    def _planted_helper(self, folder: Path, version_line: str,
                        with_digest: bool = True) -> Path:
        # Windows CreateProcess cannot exec a shebang script (WinError 193),
        # so the planted helper must be a real .cmd there and a shell script
        # elsewhere. The identity gate runs [path, "--version"] either way.
        if sys.platform == "win32":
            helper = Path(folder) / "hwi.cmd"
            helper.write_text(
                "@echo off\r\n"
                f'if "%1"=="--version" (\r\n  echo {version_line}\r\n  exit /b 0\r\n)\r\n'
                "echo []\r\n",
                encoding="utf-8",
            )
        else:
            helper = Path(folder) / "hwi"
            helper.write_text(
                "#!/bin/sh\n"
                f'if [ "$1" = "--version" ]; then echo "{version_line}"; exit 0; fi\n'
                "echo '[]'\n",
                encoding="utf-8",
            )
            helper.chmod(0o755)
        if with_digest:
            digest = hashlib.sha256(helper.read_bytes()).hexdigest()
            helper.with_name("hwi.sha256").write_text(f"{digest}  hwi\n", encoding="utf-8")
        return helper

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
            self.assertEqual(_hwi_command("hwi"), ["/nowhere/python3", str(entry)])

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
            seen = "\n".join(f"{name} {'0' * 64}" for name in HWI_PAYLOAD_PINS)
            with patch("probe.subprocess.run",
                       return_value=CompletedProcess([], 0, seen, "")) as run:
                with self.assertRaisesRegex(
                        ProbeError, "does not match its recorded digest"):
                    _verify_hwi_identity(str(helper), [sys.executable, str(helper)])
        # The payload check ran before any --version question was asked.
        self.assertEqual(run.call_count, 1)
        self.assertIn("hwilib", run.call_args.args[0][2])

    def test_the_payload_checker_accepts_the_anchored_interpreter(self):
        entry = Path(probe.__file__).resolve().parent / "scripts" / "hwi_entry.py"
        with tempfile.TemporaryDirectory() as folder:
            helper = Path(folder) / "hwi_entry.py"
            helper.write_bytes(entry.read_bytes())
            seen = "\n".join(
                f"{name} {digest}" for name, digest in HWI_PAYLOAD_PINS.items())
            version = f"hwi_entry.py {EXPECTED_HWI_VERSION}"

            def fake_run(argv, **kwargs):
                if "--version" in argv:
                    return CompletedProcess(argv, 0, version, "")
                return CompletedProcess(argv, 0, seen, "")

            with patch("probe.subprocess.run", side_effect=fake_run):
                _verify_hwi_identity(str(helper), [sys.executable, str(helper)])
            self.assertIn(str(helper), probe._verified_hwi_paths)

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
        begin_signing_session()
        self.assertEqual(probe._verified_hwi_paths, set())

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
            # The checkout keeps recipes in .github/workflows/; the source
            # archive ships them under ci/ (see scripts/build-source.sh).
            recipe = next((path for path in (self.root / ".github" / "workflows" / name,
                                             self.root / "ci" / name)
                           if path.is_file()), None)
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
# CT-46 — stale version strings are findings
# ---------------------------------------------------------------------------

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


if __name__ == "__main__":
    unittest.main()
