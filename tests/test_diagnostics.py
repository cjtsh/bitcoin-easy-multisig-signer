"""Diagnostic exports carry fixed outcomes, never wallet material."""

import json
import tempfile
import unittest
from pathlib import Path

from gui import LocalApp, save_diagnostic_report


class DiagnosticTests(unittest.TestCase):
    def test_export_is_explicit_private_and_contains_only_fixed_codes(self):
        state = LocalApp()
        state.note("wallet_import", "passed")
        state.note("wallet_import", "bc1-private-address")
        with tempfile.TemporaryDirectory() as temporary:
            result = save_diagnostic_report(state, Path(temporary))
            saved = Path(result["path"])
            self.assertEqual(saved.stat().st_mode & 0o777, 0o600)
            report = json.loads(saved.read_text())
        self.assertEqual(report["events"][0]["stage"], "wallet_import")
        self.assertEqual(report["events"][0]["outcome"], "passed")
        self.assertEqual(len(report["events"]), 1)
        self.assertNotIn("bc1-private-address", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
