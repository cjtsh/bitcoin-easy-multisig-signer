"""Synthetic test keys only. Never use these deterministic seeds for funds."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from embit import bip32
from embit.descriptor import Descriptor
from embit.descriptor.checksum import checksum
from embit.networks import NETWORKS

from probe import ProbeError, _same_xpub, load_bsms, probe_devices


def test_record(short_path: bool = False) -> tuple[str, list[bip32.HDKey]]:
    roots = [bip32.HDKey.from_seed(bytes([i]) * 32) for i in (1, 2, 3)]
    path = "m/48h/1h/0h/2h"
    suffix = "/*" if short_path else "/0/*"
    keys = [
        f"[{root.my_fingerprint.hex()}/48h/1h/0h/2h]"
        f"{root.derive(path).to_public().to_base58()}{suffix}"
        for root in roots
    ]
    descriptor = f"wsh(sortedmulti(2,{','.join(keys)}))"
    full_descriptor = descriptor + "#" + checksum(descriptor)
    canonical = descriptor.replace("/*", "/0/*") if short_path else descriptor
    reference = Descriptor.from_string(canonical).derive(0).address(NETWORKS["signet"])
    return (
        f"BSMS 1.0\n{full_descriptor}\nNo path restrictions\n{reference}\n",
        roots,
    )


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
        self.assertEqual(wallet.network, "signet")

    def test_receive_branch_diagnostic_never_counts_as_verified(self):
        record, _ = test_record(short_path=True)
        wallet = self.write(record)
        self.assertEqual(wallet.reference_status, "receive-branch-only")

    def test_bad_checksum_fails_closed(self):
        record, _ = test_record()
        record = record.replace("#", "#x", 1)
        with self.assertRaisesRegex(ProbeError, "checksum"):
            self.write(record)

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

        def fake_hwi(_executable, _chain, *args):
            if args == ("enumerate",):
                return [{"type": "jade", "model": "Jade", "path": "test-port", "fingerprint": fp}]
            self.assertEqual(args[-2:], ("getxpub", "m/48h/1h/0h/2h"))
            return {"xpub": correct}

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            result = probe_devices(wallet, "hwi", "signet")
        self.assertEqual(result, ["Jade: signer 1 of 3 verified."])

    def test_hwi_fingerprint_match_with_wrong_xpub_stops_short_of_claiming_match(self):
        record, roots = test_record()
        wallet = self.write(record)
        fp = roots[0].my_fingerprint.hex()
        wrong = roots[1].derive("m/48h/1h/0h/2h").to_public().to_base58()

        def fake_hwi(_executable, _chain, *args):
            if args == ("enumerate",):
                return [{"type": "ledger", "path": "test-port", "fingerprint": fp}]
            return {"xpub": wrong}

        with patch("probe.invoke_hwi", side_effect=fake_hwi):
            result = probe_devices(wallet, "hwi", "signet")
        self.assertEqual(result, ["ledger: fingerprint matched, but xpub DID NOT MATCH."])


if __name__ == "__main__":
    unittest.main()