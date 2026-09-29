"""The two network backends for one wallet/PSBT engine.

Price and sat/vB quotes are a separately labelled mainnet reference in both
modes. Only wallet address, UTXO, and previous-transaction requests are routed
through these backends.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkConfig:
    chain: str
    record_network: str
    address_prefix: str
    explorer_url: str
    label: str
    bip48_coin_type: int
    genesis_hash: str
    web_url: str
    short_label: str


NETWORKS = {
    "testnet4": NetworkConfig(
        "testnet4", "test", "tb1", "https://mempool.space/testnet4/api",
        "Testnet4 (selected in this app; tb1 alone cannot identify a chain)",
        0x80000001,
        "00000000da84f2bafbbc53dee25a72ae507ff4914b867c565be350b0da8bf043",
        "https://mempool.space/testnet4",
        "Testnet4",
    ),
    "main": NetworkConfig(
        "main", "main", "bc1", "https://mempool.space/api",
        "Bitcoin mainnet", 0x80000000,
        "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
        "https://mempool.space",
        "Bitcoin mainnet",
    ),
}

# An independently operated source for selected mainnet outpoint checks.
# Testnet4 has no reviewed, reliably available second public Esplora yet;
# its selected outpoints are still rechecked against the configured explorer.
SECONDARY_EXPLORERS = {"main": "https://blockstream.info/api", "testnet4": None}


def for_record_network(record_network: str) -> NetworkConfig:
    for config in NETWORKS.values():
        if config.record_network == record_network:
            return config
    raise ValueError("Only mainnet and Testnet4 wallets are supported.")
