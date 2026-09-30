"""Diagnostic exports carry fixed outcomes, never wallet material."""

import json
import tempfile
import unittest
from pathlib import Path

from gui import (DIAGNOSTIC_ROUTE_STAGES, DIAGNOSTIC_STAGES, LocalApp,
                 save_diagnostic_report)


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

    def test_every_rejected_route_is_attributed_to_a_real_stage(self):
        """A refused signature must not look like a refused fee estimate.

        Until 0.4.8 every rejection was recorded as an unattributable "request":
        the route name and the stage name never matched ("prepare" vs
        "transaction_prepare"), so only /api/broadcast lined up by coincidence.
        """
        for route, stage in DIAGNOSTIC_ROUTE_STAGES.items():
            self.assertIn(stage, DIAGNOSTIC_STAGES,
                          f"{route} is attributed to an unknown stage")
        self.assertEqual(DIAGNOSTIC_ROUTE_STAGES["import"], "wallet_import")
        self.assertEqual(DIAGNOSTIC_ROUTE_STAGES["prepare"], "transaction_prepare")
        self.assertEqual(DIAGNOSTIC_ROUTE_STAGES["devices"], "signer_check")
        self.assertEqual(DIAGNOSTIC_ROUTE_STAGES["sign"], "signer_response")
        self.assertEqual(DIAGNOSTIC_ROUTE_STAGES["finalize"], "final_transaction")
        # The catch-all is gone: an unlisted route records nothing at all, so
        # interface chatter cannot crowd the 80-event buffer.
        self.assertNotIn("request", DIAGNOSTIC_STAGES)
        for noisy in ("estimate", "price", "status", "settings", "clear"):
            self.assertNotIn(noisy, DIAGNOSTIC_ROUTE_STAGES)

    def test_each_event_records_the_network_and_the_device_class(self):
        """Both change what a failure means, and neither is wallet material."""
        state = LocalApp()
        state.chain = "mutinynet"
        state.note("wallet_import", "passed")
        state.note("signer_response", "verified", device="JADE")
        state.note("signer_check", "passed", found=["Trezor", "jade", "jade"])
        state.note("signer_response", "verified", device="/dev/disk4 private-xpub")
        with tempfile.TemporaryDirectory() as temporary:
            result = save_diagnostic_report(state, Path(temporary))
            report = json.loads(Path(result["path"]).read_text())

        events = report["events"]
        self.assertEqual(len(events), 4)
        for event in events:
            self.assertEqual(event["chain"], "mutinynet",
                             "every event must say which network it happened on")
        self.assertEqual(events[1]["device"], "jade",
                         "the device class is recorded, lowercased")
        self.assertEqual(events[2]["found"], ["jade", "trezor"],
                         "a check records which device classes it saw, sorted and deduped")
        # A check that saw nothing must say so explicitly. An absent key used to
        # carry the same meaning, and a real report showed two of four checks in
        # that state, where a reader cannot tell it from a field never written.
        state.note("signer_check", "passed", found=[])
        with tempfile.TemporaryDirectory() as temporary:
            again = json.loads(
                Path(save_diagnostic_report(state, Path(temporary))["path"]).read_text())
        self.assertEqual(again["events"][-1]["found"], [],
                         "a check that found no usable device must write an empty list")
        self.assertNotIn("found", again["events"][0],
                         "a stage with no device check must not carry the key")
        # Anything that is not a plain token is dropped rather than escaped into
        # the report: a path is an identity, and free text is how wallet material
        # leaks. The event survives; the value does not.
        self.assertNotIn("device", events[3])
        written = json.dumps(report)
        self.assertNotIn("private-xpub", written)
        self.assertNotIn("/dev/", written)


if __name__ == "__main__":
    unittest.main()
