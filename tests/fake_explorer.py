"""Deterministic Esplora stand-in for tests.

Never contains real wallet data: every key, address and transaction is derived
from the synthetic seeds in ``test_probe.test_record``.
"""

from embit import transaction


class FakeExplorer:
    """Minimal Esplora surface: address stats, address UTXOs, previous tx hex."""

    def __init__(self, layout, network, utxo_spec):
        self.layout = layout
        self.network = network
        self.paths = []
        self.prev = {}
        self.by_address = {}
        for n, (address, value, branch, index) in enumerate(utxo_spec):
            tx = transaction.Transaction(
                vin=[transaction.TransactionInput(bytes.fromhex("11" * 31 + f"{n:02x}"), 0)],
                vout=[transaction.TransactionOutput(value, self.script(branch, index))],
            )
            txid = tx.txid().hex()
            self.prev[txid] = tx
            self.by_address.setdefault(address, []).append(
                {"txid": txid, "vout": 0, "value": value, "status": {"confirmed": True}}
            )

    def script(self, branch, index):
        desc = self.layout.receive if branch == "receive" else self.layout.change
        return desc.derive(index).script_pubkey()

    def __call__(self, path, *, text=False):
        self.paths.append(path)
        if path.startswith("/tx/") and path.endswith("/hex"):
            txid = path[4:-4]
            if txid not in self.prev:
                raise AssertionError(f"unknown previous transaction requested: {path}")
            return self.prev[txid].serialize().hex()
        if path.endswith("/utxo"):
            return self.by_address.get(path[len("/address/"):-len("/utxo")], [])
        if path.startswith("/address/"):
            utxos = self.by_address.get(path[len("/address/"):], [])
            funded = sum(u["value"] for u in utxos)
            return {
                "chain_stats": {"funded_txo_sum": funded, "spent_txo_sum": 0,
                                "tx_count": len(utxos)},
                "mempool_stats": {"funded_txo_sum": 0, "spent_txo_sum": 0, "tx_count": 0},
            }
        raise AssertionError(f"unexpected explorer path: {path}")


def three_output_wallet(layout, network, values=(100_000, 50_000, 25_000)):
    """One funded receive branch (two outputs on /0, one on /1)."""
    receive0 = layout.receive.derive(0).address(network)
    receive1 = layout.receive.derive(1).address(network)
    spec = [
        (receive0, values[0], "receive", 0),
        (receive0, values[1], "receive", 0),
        (receive1, values[2], "receive", 1),
    ]
    return FakeExplorer(layout, network, spec)
