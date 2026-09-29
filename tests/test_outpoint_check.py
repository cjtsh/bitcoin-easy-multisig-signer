"""Fresh selected-output checks, using only synthetic public transaction IDs."""

import unittest
from unittest.mock import patch

from embit import psbt, transaction
from embit.script import Script

from gui import independent_explorer, verify_selected_outpoints
from wallet_service import WalletError, check_selected_outpoints


PRIMARY = "https://mempool.space/api"
SECONDARY = "https://blockstream.info/api"


def packet_with_one_input():
    tx = transaction.Transaction(
        vin=[transaction.TransactionInput(bytes(range(32)), 1)],
        vout=[transaction.TransactionOutput(1000, Script(b"\x6a"))],
    )
    return psbt.PSBT(tx)


class OutpointCheckTests(unittest.TestCase):
    def test_mainnet_uses_a_distinct_operator_even_if_primary_is_blockstream(self):
        self.assertEqual(independent_explorer("main", PRIMARY), SECONDARY)
        self.assertEqual(independent_explorer("main", SECONDARY), PRIMARY)
        self.assertIsNone(independent_explorer("testnet4", "https://mempool.space/testnet4/api"))
        packet = packet_with_one_input()
        with patch("gui.verify_esplora") as genesis, patch(
            "gui.check_selected_outpoints"
        ) as check, patch("gui.explorer_get", side_effect=["900000\n", "900001"]) as heights:
            verify_selected_outpoints(packet.to_base64(), "main", PRIMARY)
        genesis.assert_called_once_with("main", SECONDARY)
        self.assertEqual(heights.call_count, 2)
        self.assertEqual(check.call_args.args[1:], ("main", PRIMARY, SECONDARY))

    def test_divergent_or_malformed_chain_tip_fails_closed(self):
        for heights in (("900000", "899990"), ("900000", "unknown")):
            with self.subTest(heights=heights), patch("gui.verify_esplora"), patch(
                "gui.explorer_get", side_effect=heights
            ), patch("gui.check_selected_outpoints") as check:
                with self.assertRaises(WalletError):
                    verify_selected_outpoints(packet_with_one_input(), "main", PRIMARY)
                check.assert_not_called()

    def test_both_sources_must_report_unspent(self):
        seen = []

        def get(path, *, chain, base_url):
            seen.append((path, chain, base_url))
            return {"confirmed": True} if path.endswith("/status") else {"spent": False}

        check_selected_outpoints(packet_with_one_input(), "main", PRIMARY,
                                 SECONDARY, get)
        self.assertEqual(seen, [
            ("/tx/" + bytes(range(32)).hex() + "/status", "main", PRIMARY),
            ("/tx/" + bytes(range(32)).hex() + "/outspend/1", "main", PRIMARY),
            ("/tx/" + bytes(range(32)).hex() + "/status", "main", SECONDARY),
            ("/tx/" + bytes(range(32)).hex() + "/outspend/1", "main", SECONDARY),
        ])

    def test_spent_or_unclear_status_fails_closed(self):
        for reply in ({"spent": True}, {"spent": "false"}, {}, []):
            with self.subTest(reply=reply):
                def get(path, **_kwargs):
                    return {"confirmed": True} if path.endswith("/status") else reply
                with self.assertRaises(WalletError):
                    check_selected_outpoints(
                        packet_with_one_input(), "main", PRIMARY, SECONDARY,
                        get,
                    )

    def test_unconfirmed_funding_is_refused_even_if_outspend_is_false(self):
        with self.assertRaisesRegex(WalletError, "no longer confirmed"):
            check_selected_outpoints(
                packet_with_one_input(), "main", PRIMARY, SECONDARY,
                lambda _path, **_kwargs: {"confirmed": False},
            )

    def test_outage_and_same_source_fail_closed(self):
        with self.assertRaisesRegex(WalletError, "separate valid source"):
            check_selected_outpoints(packet_with_one_input(), "main", PRIMARY,
                                     PRIMARY, lambda *_args, **_kwargs: {"spent": False})

        def outage(_path, **_kwargs):
            raise WalletError("offline")

        with self.assertRaisesRegex(WalletError, "Could not confirm"):
            check_selected_outpoints(packet_with_one_input(), "main", PRIMARY,
                                     SECONDARY, outage)


if __name__ == "__main__":
    unittest.main()
