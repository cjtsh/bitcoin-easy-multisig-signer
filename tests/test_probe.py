"""Synthetic test keys only. Never use these deterministic seeds for funds."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from embit import bip32
from embit.descriptor import Descriptor
from embit.descriptor.checksum import checksum
from embit.networks import NETWORKS

from probe import (
    ProbeError, _same_xpub, _validate_chain, funding_address,
    _device_label, _hwi_device_label, device_advice, devices_need_attention,
    invoke_hwi, load_bsms,
    main, probe_devices,
    verify_signer_device,
)


def test_record(short_path: bool = False, dual_branch: bool = False,
                bsms_template: bool = False, threshold: int = 2,
                key_count: int = 3) -> tuple[str, list[bip32.HDKey]]:
    roots = [bip32.HDKey.from_seed(bytes([i]) * 32) for i in range(1, key_count + 1)]
    path = "m/48h/1h/0h/2h"
    suffix = ("/**" if bsms_template else
              "/<0;1>/*" if dual_branch else "/*" if short_path else "/0/*")
    keys = [
        f"[{root.my_fingerprint.hex()}/48h/1h/0h/2h]"
        f"{root.derive(path).to_public().to_base58()}{suffix}"
        for root in roots
    ]
    descriptor = f"wsh(sortedmulti({threshold},{','.join(keys)}))"
    full_descriptor = descriptor + "#" + checksum(descriptor)
    canonical = (descriptor.replace("/**", "/0/*") if bsms_template else
                 descriptor.replace("/<0;1>/*", "/0/*") if dual_branch else
                 descriptor.replace("/*", "/0/*") if short_path else descriptor)
    reference = Descriptor.from_string(canonical).derive(0).address(NETWORKS["test"])
    restrictions = "/0/*,/1/*" if bsms_template else "No path restrictions"
    return (
        f"BSMS 1.0\n{full_descriptor}\n{restrictions}\n{reference}\n",
        roots,
    )


def sparrow_record() -> tuple[str, list[bip32.HDKey]]:
    """A Sparrow-shaped BSMS record.

    Sparrow exports the descriptor WITHOUT a checksum and states the derivation
    restrictions on their own line, with the paths already written into the
    descriptor as <0;1>/*. Nunchuk instead writes a checksum and the words
    "No path restrictions". Both are valid, and the app rejected the Sparrow shape
    outright, which blocked the owner's real wallets. Synthetic keys only: the
    owner's own xpubs must never enter the repository.
    """
    text, roots = test_record(dual_branch=True)
    lines = text.splitlines()
    descriptor = lines[1].rsplit("#", 1)[0]
    return "\n".join([lines[0], descriptor, "/0/*,/1/*", lines[3], ""]), roots


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic.bsms"

    def write(self, content):
        self.path.write_text(content, encoding="utf-8")
        return load_bsms(self.path)

    def test_verified_test_policy(self):
        record, _ = test_record()
        wallet = self.write(record)
        self.assertEqual((wallet.threshold, len(wallet.keys)), (2, 3))
        self.assertEqual(wallet.reference_status, "verified")
        self.assertEqual(wallet.network, "test")

    def test_any_valid_quorum_with_two_or_three_keys_is_accepted(self):
        for key_count in (2, 3):
            for threshold in range(1, key_count + 1):
                with self.subTest(threshold=threshold, key_count=key_count):
                    text, _ = test_record(threshold=threshold, key_count=key_count)
                    wallet = self.write(text)
                    self.assertEqual((wallet.threshold, len(wallet.keys)),
                                     (threshold, key_count))

    def test_more_than_three_keys_are_refused(self):
        text, _ = test_record(key_count=4)
        with self.assertRaisesRegex(ProbeError, "two or three keys"):
            self.write(text)

    def test_sparrow_style_record_without_a_checksum_is_accepted(self):
        text, _ = sparrow_record()
        wallet = self.write(text)
        self.assertEqual(wallet.reference_status, "verified")
        self.assertEqual((wallet.threshold, len(wallet.keys)), (2, 3))

    def test_the_reference_address_still_guards_an_unchecksummed_descriptor(self):
        """Dropping the checksum must not drop the protection: a descriptor that
        does not derive the stated reference address is still refused."""
        text, _ = sparrow_record()
        lines = text.splitlines()
        lines[1] = lines[1].replace("/<0;1>/*", "/<0;1>/*").replace("sortedmulti(2,",
                                                                    "sortedmulti(3,")
        wallet = self.write("\n".join(lines) + "\n")
        # A 3-of-3 reinterpretation cannot derive the same 2-of-3 address.
        self.assertEqual(wallet.reference_status, "mismatch")

    def test_a_wrong_descriptor_checksum_is_still_rejected(self):
        text, _ = test_record()
        lines = text.splitlines()
        lines[1] = lines[1][:-1] + ("0" if lines[1][-1] != "0" else "1")
        with self.assertRaises(ProbeError):
            self.write("\n".join(lines) + "\n")

    def test_more_than_one_checksum_is_rejected(self):
        text, _ = test_record()
        lines = text.splitlines()
        lines[1] = lines[1] + "#deadbeef"
        with self.assertRaises(ProbeError):
            self.write("\n".join(lines) + "\n")

    def test_receive_branch_diagnostic_never_counts_as_verified(self):
        record, _ = test_record(short_path=True)
        wallet = self.write(record)
        self.assertEqual(wallet.reference_status, "receive-branch-only")

    def test_bsms_template_expands_only_declared_receive_and_change_paths(self):
        record, _ = test_record(bsms_template=True)
        wallet = self.write(record)
        self.assertEqual(wallet.reference_status, "verified")
        self.assertEqual(wallet.restrictions, "/0/*,/1/*")
        self.assertIsNotNone(wallet.change_descriptor)
        self.assertTrue(all(key.suffix == "/0/*" for key in wallet.descriptor.keys))
        self.assertTrue(all(key.suffix == "/1/*" for key in wallet.change_descriptor.keys))

    def test_unsupported_bsms_paths_are_rejected_not_guessed(self):
        record, _ = test_record(bsms_template=True)
        with self.assertRaisesRegex(ProbeError, "supports either"):
            self.write(record.replace("/0/*,/1/*", "/0/*,/2/*"))

    def test_bad_checksum_fails_closed(self):
        record, _ = test_record()
        record = record.replace("#", "#x", 1)
        with self.assertRaisesRegex(ProbeError, "checksum"):
            self.write(record)

    def test_testnet_wallet_rejects_wrong_coin_type(self):
        text, _ = test_record()
        lines = text.splitlines()
        descriptor = lines[1].split("#")[0].replace("/48h/1h/", "/48h/0h/")
        lines[1] = descriptor + "#" + checksum(descriptor)
        with self.assertRaisesRegex(ProbeError, "coin type"):
            self.write("\n".join(lines) + "\n")

    def test_exact_xpub_matching(self):
        record, roots = test_record()
        wallet = self.write(record)
        correct = roots[0].derive("m/48h/1h/0h/2h").to_public().to_base58()
        wrong = roots[1].derive("m/48h/1h/0h/2h").to_public().to_base58()
        self.assertTrue(_same_xpub(wallet.keys[0], correct))
        self.assertFalse(_same_xpub(wallet.keys[0], wrong))

    def test_hwi_device_match_uses_xpub_not_only_fingerprint(self):
        record, roots = test_record()
        wallet = self.write(record)
        fp = roots[0].my_fingerprint.hex()
        correct = roots[0].derive("m/48h/1h/0h/2h").to_public().to_base58()

        def fake_hwi(_executable, chain, *args, **options):
            self.assertEqual(chain, "testnet4")
            if args == ("enumerate",):
                self.assertEqual(options["timeout_seconds"], 180)
                return [{"type": "jade", "model": "Jade", "path": "test-port", "fingerprint": fp}]
            self.assertEqual(args[-2:], ("getxpub", "m/48h/1h/0h/2h"))
            self.assertEqual(options["timeout_seconds"], 180)
            return {"xpub": correct}

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            result = probe_devices(wallet, "hwi", "testnet4")
        self.assertEqual(
            result, ["Jade: signer 1 of 3 public xpub matched (not a signing test)."]
        )

    def test_hwi_reported_onekey_label_is_preserved_for_matched_signer(self):
        record, roots = test_record()
        wallet = self.write(record)
        fp = roots[0].my_fingerprint.hex()
        correct = roots[0].derive("m/48h/1h/0h/2h").to_public().to_base58()

        def fake_hwi(_executable, _chain, *args, **options):
            if args == ("enumerate",):
                return [{"type": "trezor", "label": "OneKey Classic 1S",
                         "model": "trezor_1", "path": "test-port",
                         "fingerprint": fp}]
            return {"xpub": correct}

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            result = probe_devices(wallet, "hwi", "testnet4")
        self.assertEqual(
            result,
            ["OneKey Classic 1S: signer 1 of 3 public xpub matched (not a signing test)."],
        )

    def test_hwi_label_rejects_control_or_markup_characters(self):
        self.assertEqual(_hwi_device_label({"label": "OneKey Classic 1S"}),
                         "OneKey Classic 1S")
        self.assertEqual(_hwi_device_label({"label": "<script>", "model": "trezor_1"}),
                         "Trezor 1")

    def test_a_device_that_errors_reports_hwis_own_reason(self):
        """The owner's Ledger was unlocked, so "unavailable or locked" sent them
        looking for the wrong fault. HWI knew the real answer and it was discarded."""
        record, _ = test_record()
        wallet = self.write(record)
        real = ("Could not open client or get fingerprint information: "
                "Ledger is not in either the Bitcoin or Bitcoin Testnet app")

        def fake_hwi(_executable, _chain, *args, **options):
            self.assertEqual(args, ("enumerate",))
            self.assertEqual(options["timeout_seconds"], 180)
            return [{"type": "ledger", "model": "ledger_nano_s_plus",
                     "path": "DevSrvsID:1", "error": real, "code": -3}]

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            result = probe_devices(wallet, "hwi", "testnet4")
        self.assertEqual(len(result), 1)
        # The device name is readable and the reason survives intact.
        self.assertTrue(result[0].startswith("Ledger Nano S Plus: detected, but not readable."))
        self.assertIn("not in either the Bitcoin or Bitcoin Testnet app", result[0])
        self.assertNotIn("locked", result[0])
        self.assertTrue(devices_need_attention(result))
        # And the owner is told the one thing that fixes it.
        self.assertIn("open the Bitcoin Testnet app", result[0])

    def test_advice_is_specific_and_never_misleading(self):
        """The owner's complaint: nobody would work out that a Ledger needs a
        particular app opened on it. Say the one thing that applies."""
        ledger = "Ledger is not in either the Bitcoin or Bitcoin Testnet app"
        self.assertIn("Bitcoin Testnet app", device_advice("ledger", ledger))
        self.assertIn("Bitcoin Testnet app", device_advice("ledger", "error 0x5515 locked"))
        self.assertIn("Look for more devices", device_advice("ledger", "open failed"))
        self.assertIn("PIN", device_advice("jade", "Use Recovery Phrase Login or QR PIN Unlock"))
        self.assertIn("Trezor", device_advice("trezor", "Device is locked"))
        # An unrelated fault must not attract advice that does not apply.
        self.assertEqual(device_advice("ledger", "LIBUSB_ERROR_IO"), "")
        self.assertEqual(device_advice("", "locked"), "")
        self.assertEqual(device_advice("trezor", "LIBUSB_ERROR_NOT_FOUND"), "")

    def test_device_labels_and_attention(self):
        self.assertEqual(_device_label("ledger_nano_s_plus"), "Ledger Nano S Plus")
        self.assertEqual(_device_label("trezor_one"), "Trezor One")
        self.assertEqual(_device_label("coldcard_mk4"), "Coldcard Mk4")
        self.assertEqual(_device_label(""), "Device")
        self.assertEqual(_hwi_device_label({"label": "OneKey Classic 1S",
                                            "model": "trezor_1"}),
                         "OneKey Classic 1S")
        # Only a matched signer needs nothing further from the owner.
        self.assertTrue(devices_need_attention([]))
        self.assertTrue(devices_need_attention(["Ledger Nano S Plus: not a signer in this BSMS file."]))
        self.assertFalse(devices_need_attention(
            ["Jade: signer 1 of 3 public xpub matched (not a signing test)."]))

    def test_hwi_fingerprint_match_with_wrong_xpub_stops_short_of_claiming_match(self):
        record, roots = test_record()
        wallet = self.write(record)
        fp = roots[0].my_fingerprint.hex()
        wrong = roots[1].derive("m/48h/1h/0h/2h").to_public().to_base58()

        def fake_hwi(_executable, _chain, *args, **options):
            if args == ("enumerate",):
                self.assertEqual(options["timeout_seconds"], 180)
                return [{"type": "ledger", "path": "test-port", "fingerprint": fp}]
            self.assertEqual(options["timeout_seconds"], 180)
            return {"xpub": wrong}

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            result = probe_devices(wallet, "hwi", "testnet4")
        # Device names are presented for a person to read, not as HWI spells them.
        self.assertEqual(result, ["Ledger: fingerprint matched, but xpub DID NOT MATCH."])

    def test_explicit_testnet4_chain_and_guarded_funding_address(self):
        text, _ = test_record()
        wallet = self.write(text)
        _validate_chain(wallet, "testnet4")
        self.assertEqual(funding_address(wallet, "testnet4"), text.splitlines()[3])
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                main(["funding-address", str(self.path), "--chain", "testnet4"]), 0
            )
        self.assertIn(text.splitlines()[3], output.getvalue())
        self.assertIn("not inferred from tb1", output.getvalue())
        with self.assertRaisesRegex(ProbeError, "conflicts"):
            _validate_chain(wallet, "regtest")
        # The command-line helpers are practice-only. The wording says so rather
        # than calling the whole release test-only, because the GUI does check
        # and sign mainnet wallets for the Phase 5 dry run.
        with self.assertRaisesRegex(ProbeError, "practice wallets only"):
            _validate_chain(
                wallet.__class__(
                    wallet.descriptor, wallet.threshold, "main",
                    wallet.restrictions, wallet.reference_status,
                ),
                "testnet4",
            )

    def test_mismatched_reference_cannot_be_used_as_funding_address(self):
        text, _ = test_record(short_path=True)
        wallet = self.write(text)
        with self.assertRaisesRegex(ProbeError, "no funding address"):
            funding_address(wallet, "testnet4")

    def test_hwi_invoked_with_explicit_testnet4_flag(self):
        from subprocess import CompletedProcess

        with patch("probe._hwi_path", return_value="/fake/hwi"), patch(
            "probe.subprocess.run",
            return_value=CompletedProcess([], 0, "[]", ""),
        ) as run:
            self.assertEqual(invoke_hwi("fake", "testnet4", "enumerate"), [])
        self.assertEqual(
            run.call_args.args[0],
            ["/fake/hwi", "--chain", "testnet4", "enumerate"],
        )
        self.assertEqual(run.call_args.kwargs["timeout"], 60)

    def test_windows_hwi_launch_hides_console_and_preserves_stdin(self):
        from subprocess import CompletedProcess
        with patch("probe.sys.platform", "win32"), patch(
            "probe.subprocess.CREATE_NO_WINDOW", 0x08000000, create=True
        ), patch("probe._hwi_path", return_value="hwi.exe"), patch(
            "probe.subprocess.run", return_value=CompletedProcess([], 0, "[]", "")
        ) as run:
            invoke_hwi("hwi", "testnet4", "--stdin", stdin_command="synthetic\n")
        self.assertEqual(run.call_args.kwargs["creationflags"], 0x08000000)
        self.assertEqual(run.call_args.kwargs["input"], "synthetic\n")
        self.assertTrue(run.call_args.kwargs["capture_output"])

    def test_other_platforms_do_not_receive_windows_process_flags(self):
        from probe import hwi_process_options
        for platform in ("darwin", "linux"):
            with self.subTest(platform=platform), patch("probe.sys.platform", platform):
                self.assertEqual(hwi_process_options(), {})

    def test_windows_child_has_no_console_and_retains_pipes(self):
        import subprocess
        import sys
        from probe import hwi_process_options
        if sys.platform != "win32":
            self.assertEqual(hwi_process_options(), {})
            return
        child = subprocess.run(
            [sys.executable, "-c",
             "import ctypes, sys; "
             "print(ctypes.windll.kernel32.GetConsoleWindow()); "
             "print(sys.stdin.read(), end=''); "
             "print('synthetic error', file=sys.stderr)"],
            input="synthetic input", capture_output=True, text=True, timeout=10,
            **hwi_process_options(),
        )
        self.assertEqual(child.returncode, 0)
        self.assertEqual(child.stdout, "0\nsynthetic input")
        self.assertEqual(child.stderr, "synthetic error\n")

    def test_signing_psbt_goes_over_stdin_not_process_arguments(self):
        from subprocess import CompletedProcess
        from probe import sign_psbt_with_device

        packet = "cHNidP8="
        with patch("probe._hwi_path", return_value="/fake/hwi"), patch(
            "probe.subprocess.run",
            return_value=CompletedProcess([], 0, '{"psbt":"cHNidP8="}', ""),
        ) as run:
            self.assertEqual(sign_psbt_with_device(
                "fake", "testnet4", "trezor", "webusb:1", packet), packet)
        args = run.call_args.args[0]
        self.assertEqual(args, ["/fake/hwi", "--chain", "testnet4",
                                "--device-type", "trezor", "--device-path", "webusb:1",
                                "--stdin"])
        self.assertNotIn(packet, args)
        self.assertEqual(run.call_args.kwargs["input"], "signtx " + packet + "\n")
        self.assertEqual(run.call_args.kwargs["timeout"], 600)

    def test_signing_rechecks_the_device_xpub_at_the_wallet_origin(self):
        text, roots = test_record()
        wallet = self.write(text)
        expected = roots[0].derive("m/48h/1h/0h/2h").to_public().to_base58()
        with patch("probe.invoke_hwi", return_value={"xpub": expected}) as invoke:
            verify_signer_device(wallet, "hwi", "test", "jade", "/dev/test", 1)
        self.assertEqual(invoke.call_args.args[-2:], ("getxpub", "m/48h/1h/0h/2h"))
        self.assertEqual(invoke.call_args.kwargs["timeout_seconds"], 180)
        with patch("probe.invoke_hwi", return_value={"xpub": "wrong"}):
            with self.assertRaisesRegex(ProbeError, "no longer matches"):
                verify_signer_device(wallet, "hwi", "test", "jade", "/dev/test", 1)

    def test_signing_psbt_cannot_inject_another_stdin_command(self):
        from probe import sign_psbt_with_device

        with patch("probe.subprocess.run") as run:
            with self.assertRaisesRegex(ProbeError, "malformed"):
                sign_psbt_with_device("fake", "testnet4", "jade", "/dev/fake",
                                      "cHNidP8=\nenumerate")
        run.assert_not_called()

    def test_hwi_failure_keeps_hwis_own_reason(self):
        """When a device will not connect, the app must say what HWI said. A
        generic "check the device" is useless to the person holding it."""
        from probe import _hwi_reason
        self.assertEqual(_hwi_reason("Device not found"), "Device not found")
        self.assertEqual(_hwi_reason(""), "")
        # Paths must not travel into the interface.
        self.assertEqual(_hwi_reason("cannot open /usr/local/lib/libusb-1.0.0.dylib"),
                         "cannot open <path>")
        self.assertNotIn("/dev/", _hwi_reason("Could not connect to /dev/hidraw3"))
        # Long output is capped and control characters are dropped.
        self.assertLessEqual(len(_hwi_reason("x" * 400)), 160)
        self.assertNotIn("\x07", _hwi_reason("bell\x07here"))


if __name__ == "__main__":
    unittest.main()
