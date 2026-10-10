"""The GitHub-only embit update has three transparent local edits.

CT-91 added the third: the fork shipped upstream's Liquid/PSET copy, which
still rewrote a legal `nSequence=0` to `0xFFFFFFFF` in `vin` and
`blinded_vin`. The app does not import that surface, but the fork should
ship one behaviour rather than two, so the same explicit check that
`psbt.py` carries was applied there too.

These tests also hold the two claims the prose makes: the wheel is the
source archive's `src/embit` tree, and nothing that ships imports the
Liquid surface. `VENDOR_DIR` selects another directory holding the same
artifacts, which is how `break_and_watch.py` points at a scratch copy.
"""

import hashlib
import io
import os
import tarfile
import unittest
import zipfile
from pathlib import Path

from embit import compact, psbt, transaction
from embit.script import Script
from embit.transaction import TransactionError


ROOT = Path(__file__).resolve().parents[1]
VENDOR = Path(os.environ.get("VENDOR_DIR") or (ROOT / "vendor"))
SOURCE_ROOT = "embit-0.8.2+besa.1/"

EXPLICIT_SEQUENCE = "0xFFFFFFFF if self.sequence is None else self.sequence"
IMPLICIT_SEQUENCE = "self.sequence or 0xFFFFFFFF"

# The modules that ship. A test may import the Liquid surface; the app may
# not, which is what keeps this delta off a money path.
SHIPPED = (
    "gui.py",
    "desktop.py",
    "network_config.py",
    "network_settings.py",
    "probe.py",
    "safe_http.py",
    "signing.py",
    "wallet_service.py",
)


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
            ["pyproject.toml", "src/embit/liquid/pset.py", "src/embit/psbt.py"],
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
        self.assertEqual(
            patched["src/embit/liquid/pset.py"],
            upstream["src/embit/liquid/pset.py"].replace(
                b"sequence=(self.sequence or 0xFFFFFFFF)",
                b"sequence=(0xFFFFFFFF if self.sequence is None else self.sequence)"),
        )

    def test_the_wheel_carries_the_source_it_was_built_from(self):
        source = archive_files(VENDOR / "embit-0.8.2+besa.1.tar.gz")
        with zipfile.ZipFile(VENDOR / "embit-0.8.2+besa.1-py3-none-any.whl") as wheel:
            packaged = {
                name: wheel.read(name)
                for name in wheel.namelist()
                if not name.endswith("/")
            }
        in_source = {
            path[len("src/embit/"):] for path in source if path.startswith("src/embit/")
        }
        missing, mismatched = [], []
        for path in sorted(in_source):
            name = "embit/" + path
            if name not in packaged:
                missing.append(name)
            elif hashlib.sha256(packaged[name]).hexdigest() != hashlib.sha256(
                    source["src/embit/" + path]).hexdigest():
                mismatched.append(name)
        extra = sorted(
            name[len("embit/"):] for name in packaged
            if name.startswith("embit/") and name[len("embit/"):] not in in_source
        )
        self.assertEqual(
            missing, [],
            "the wheel is missing source files; it was not built from this archive",
        )
        self.assertEqual(
            mismatched, [],
            "the wheel and the vendored source disagree; rebuild one from the other",
        )
        self.assertEqual(
            extra, [],
            "the wheel carries files the vendored source does not; the delta is unstated",
        )

    def test_no_liquid_input_rewrites_a_legal_sequence_of_zero(self):
        source = archive_files(VENDOR / "embit-0.8.2+besa.1.tar.gz")
        with zipfile.ZipFile(VENDOR / "embit-0.8.2+besa.1-py3-none-any.whl") as wheel:
            packaged = wheel.read("embit/liquid/pset.py")
        for label, payload in (
            ("the source archive", source["src/embit/liquid/pset.py"]),
            ("the wheel", packaged),
        ):
            self.assertEqual(
                payload.count(IMPLICIT_SEQUENCE.encode()), 0,
                f"{label} still rewrites a legal nSequence=0 to 0xFFFFFFFF",
            )
            self.assertEqual(
                payload.count(EXPLICIT_SEQUENCE.encode()), 2,
                f"{label} does not carry the explicit check in both branches",
            )

    def test_the_documentation_states_the_liquid_delta(self):
        readme = (VENDOR / "README.md").read_text(encoding="utf-8")
        self.assertEqual(
            readme.count("liquid/pset.py"), 1,
            "vendor/README.md does not name the Liquid/PSET edit exactly once",
        )
        self.assertEqual(
            readme.count("nSequence=0"), 1,
            "vendor/README.md does not state what the sequence edits preserve",
        )
        notices = (ROOT / "THIRD-PARTY-NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("three local edits", notices)

    def test_the_application_does_not_import_the_liquid_surface(self):
        offenders = [
            name for name in SHIPPED
            if "embit.liquid" in (ROOT / name).read_text(encoding="utf-8")
            or "embit import liquid" in (ROOT / name).read_text(encoding="utf-8")
        ]
        self.assertEqual(
            offenders, [],
            "the app imports embit's Liquid/PSET code, so this delta is on a money path",
        )

    def test_bundled_wheel_is_hash_locked_and_contains_no_native_code(self):
        wheel = VENDOR / "embit-0.8.2+besa.1-py3-none-any.whl"
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        for lock in ("requirements.lock", "requirements-desktop.lock",
                     "requirements-source.lock"):
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
