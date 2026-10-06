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

import re
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from embit.networks import NETWORKS

import gui
import probe
from fake_explorer import three_output_wallet
from probe import (
    EXPECTED_HWI_VERSION, ProbeError, _bitcoin_message_digest, _hwi_path,
    _verify_hwi_identity, invoke_hwi, parse_bsms, prove_signer_holds_key,
    verify_signer_device,
)
from signing import SECP256K1_HALF_ORDER, SigningError, _is_low_s, verified_input_signatures
from test_money_path_pins import prepared
from test_probe import test_record
from wallet_service import build_unsigned_psbt, scan_wallet, wallet_layout


# ---------------------------------------------------------------------------
# CT-29 — source-mode HWI identity
# ---------------------------------------------------------------------------

class HwiIdentityPins(unittest.TestCase):
    def setUp(self):
        probe._verified_hwi_paths.clear()

    def _scripted_hwi(self, folder: Path, version_line: str) -> Path:
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
            return helper
        helper = Path(folder) / "hwi"
        helper.write_text(
            "#!/bin/sh\n"
            f'if [ "$1" = "--version" ]; then echo "{version_line}"; exit 0; fi\n'
            "echo '[]'\n",
            encoding="utf-8",
        )
        helper.chmod(0o755)
        return helper

    def test_a_planted_helper_that_does_not_name_the_pinned_release_is_refused(self):
        """CT-29: PATH substitution must not reach account xpubs or PSBTs."""
        with tempfile.TemporaryDirectory() as folder:
            helper = self._scripted_hwi(folder, "evil-stealer 9.9.9")
            with self.assertRaisesRegex(ProbeError, "does not identify as HWI"):
                _verify_hwi_identity(str(helper))

    def test_a_helper_that_reports_the_pinned_release_is_accepted_once(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._scripted_hwi(folder, f"hwi {EXPECTED_HWI_VERSION}")
            _verify_hwi_identity(str(helper))
            self.assertIn(str(helper), probe._verified_hwi_paths)
            with patch("probe.subprocess.run") as run:
                _verify_hwi_identity(str(helper))
            run.assert_not_called()

    def test_a_helper_that_cannot_answer_version_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            if sys.platform == "win32":
                helper = Path(folder) / "hwi.cmd"
                helper.write_text("@echo off\r\nexit /b 1\r\n", encoding="utf-8")
            else:
                helper = Path(folder) / "hwi"
                helper.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
                helper.chmod(0o755)
            with self.assertRaisesRegex(
                    ProbeError, "does not identify as HWI|could not be identified"):
                _verify_hwi_identity(str(helper))

    def test_invoke_hwi_refuses_before_it_sends_any_wallet_material(self):
        from subprocess import CompletedProcess
        with patch("probe._hwi_path", return_value="/fake/hwi"), patch(
            "probe.subprocess.run",
            return_value=CompletedProcess([], 0, "planted 0.0.1", ""),
        ) as run:
            with self.assertRaisesRegex(ProbeError, "does not identify as HWI"):
                invoke_hwi("fake", "testnet4", "enumerate")
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0], ["/fake/hwi", "--version"])

    def test_source_mode_prefers_the_interpreter_siblings_helper_over_path(self):
        """The venv's own helper is the same trust model as the frozen bundle."""
        with tempfile.TemporaryDirectory() as folder:
            helper = Path(folder) / "hwi"
            helper.write_bytes(b"")
            interpreter = Path(folder) / "python3"
            interpreter.write_bytes(b"")
            with patch.object(sys, "frozen", False, create=True), \
                    patch.object(sys, "executable", str(interpreter)), \
                    patch("probe.shutil.which", return_value="/usr/local/bin/hwi") as which:
                self.assertEqual(_hwi_path("hwi"), str(helper))
            which.assert_not_called()

    def test_an_explicit_path_is_used_as_given(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = Path(folder) / "official-hwi"
            helper.write_bytes(b"")
            self.assertEqual(_hwi_path(str(helper)), str(helper))


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
    def test_every_lock_job_pins_the_same_piptools_release(self):
        root = Path(__file__).resolve().parents[1]
        versions = set()
        for name in ("windows-inputs.yml", "linux-inputs.yml"):
            # The checkout keeps recipes in .github/workflows/; the source
            # archive ships them under ci/ (see scripts/build-source.sh).
            recipe = next((path for path in (root / ".github" / "workflows" / name,
                                             root / "ci" / name)
                           if path.is_file()), None)
            self.assertIsNotNone(
                recipe, f"{name} is missing from both .github/workflows/ and ci/")
            text = recipe.read_text(encoding="utf-8")
            found = re.findall(r"pip-tools==([0-9.]+)", text)
            self.assertTrue(found, f"{name} must pin pip-tools==…")
            versions.update(found)
            self.assertNotIn("pip install --disable-pip-version-check pip-tools\n", text)
        self.assertEqual(len(versions), 1, f"lock jobs disagree on pip-tools: {versions}")


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
