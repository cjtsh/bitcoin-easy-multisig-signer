"""The GitHub-only embit update has two transparent local edits."""

import hashlib
import io
import tarfile
import unittest
import zipfile
from pathlib import Path

from embit import compact, psbt, transaction
from embit.script import Script
from embit.transaction import TransactionError


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"


def archive_files(path):
    with tarfile.open(path) as archive:
        return {
            "/".join(member.name.split("/")[1:]): archive.extractfile(member).read()
            for member in archive if member.isfile()
        }


class EmbitVendorTests(unittest.TestCase):
    def test_source_diff_is_only_the_declared_version_and_sequence_fixes(self):
        upstream = archive_files(VENDOR / "embit-upstream-2b375a.tar.gz")
        patched = archive_files(VENDOR / "embit-0.8.2+besa.1.tar.gz")
        self.assertEqual(upstream.keys(), patched.keys())
        self.assertEqual(
            [name for name in upstream if upstream[name] != patched[name]],
            ["pyproject.toml", "src/embit/psbt.py"],
        )
        self.assertEqual(
            patched["pyproject.toml"],
            upstream["pyproject.toml"].replace(
                b'version = "0.8.1"', b'version = "0.8.2+besa.1"'),
        )
        self.assertEqual(
            patched["src/embit/psbt.py"],
            upstream["src/embit/psbt.py"].replace(
                b"sequence=(self.sequence or 0xFFFFFFFF)",
                b"sequence=(0xFFFFFFFF if self.sequence is None else self.sequence)"),
        )

    def test_bundled_wheel_is_hash_locked_and_contains_no_native_code(self):
        wheel = VENDOR / "embit-0.8.2+besa.1-py3-none-any.whl"
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        for lock in ("requirements.lock", "requirements-desktop.lock"):
            self.assertIn(digest, (ROOT / lock).read_text(encoding="utf-8"))
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            self.assertFalse(any(name.endswith((".so", ".dylib", ".dll", ".pth"))
                             for name in names))
            self.assertTrue(any(name.endswith("/licenses/LICENSE") for name in names))

    def test_psbt_global_transaction_round_trips_even_with_zero_sequence(self):
        tx = transaction.Transaction(
            version=2, locktime=500_000,
            vin=[transaction.TransactionInput(bytes.fromhex("aa" * 32), 0,
                                              sequence=0)],
            vout=[transaction.TransactionOutput(90_000, Script(b"\x6a"))],
        )
        encoded = psbt.PSBT(tx).serialize()
        stream = io.BytesIO(encoded)
        self.assertEqual(stream.read(5), b"psbt\xff")
        key = stream.read(compact.read_from(stream))
        self.assertEqual(key, b"\x00")
        global_tx = stream.read(compact.read_from(stream))
        parsed = psbt.PSBT.parse(encoded)
        self.assertEqual(parsed.tx.serialize(), global_tx)
        self.assertEqual(parsed.tx.vin[0].sequence, 0)

    def test_truncated_transaction_is_rejected_by_dependency(self):
        tx = transaction.Transaction(
            vin=[transaction.TransactionInput(bytes.fromhex("aa" * 32), 0)],
            vout=[transaction.TransactionOutput(90_000, Script(b"\x6a"))],
        )
        with self.assertRaises(TransactionError):
            transaction.Transaction.parse(tx.serialize()[:-2])


if __name__ == "__main__":
    unittest.main()
