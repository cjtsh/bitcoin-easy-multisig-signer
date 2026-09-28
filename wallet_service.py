"""Public-data mainnet/Testnet4 wallet view and unsigned PSBT preparation.

No seeds, signing keys, signing operations, or broadcast endpoints live here.
Address queries disclose the queried addresses to the configured public explorer.
"""

from __future__ import annotations

import json
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from embit import psbt, script, transaction
from embit.descriptor import Descriptor
from embit.networks import NETWORKS

from probe import ProbeError, WalletRecord

EXPLORERS = {
    "main": "https://mempool.space/api",
    "testnet4": "https://mempool.space/testnet4/api",
}
GAP_LIMIT = 20
MAX_INDEX = 100
SATOSHI_DUST_FLOOR = 546
MAX_ESTIMATED_FEE_SATS = 10_000


class WalletError(ProbeError):
    pass


def check_fee_safety(fee: int, amount: int, fee_rate: int) -> str:
    """Hard stop on extreme fees; return an extra-review warning for unusual ones."""
    if fee > MAX_ESTIMATED_FEE_SATS:
        raise WalletError(
            f"Estimated fee of {fee:,} sats exceeds the 10,000-sat safety ceiling. "
            "Use fewer inputs or a lower sat/vB rate."
        )
    if fee > max(1_000, amount // 4) or fee_rate >= 10:
        return (
            f"Unusually high fee: {fee:,} sats at {fee_rate} sat/vB for a "
            f"{amount:,}-sat send. Confirm the units and total before downloading."
        )
    return ""


def explorer_get(path: str, *, text: bool = False, chain: str = "testnet4"):
    """Bounded Esplora GET on an explicit network; never send xpubs."""
    if chain not in EXPLORERS:
        raise WalletError("Unsupported explorer network.")
    if not path.startswith("/") or ".." in path or "?" in path:
        raise WalletError("Invalid explorer path.")
    request = Request(
        EXPLORERS[chain] + path,
        headers={"User-Agent": "EasyMultisig/0.0.6", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=12) as response:
            if response.length is not None and response.length > 2_000_000:
                raise WalletError("Explorer response is unexpectedly large.")
            body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise WalletError("Explorer response is unexpectedly large.")
        return body.decode("ascii") if text else json.loads(body)
    except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError) as exc:
        raise WalletError(
            "Bitcoin explorer is unavailable or returned invalid data. "
            "No zero balance is claimed; try Refresh later."
        ) from exc


def _chain(record: WalletRecord) -> str:
    if record.network == "main":
        return "main"
    if record.network == "test":
        return "testnet4"
    raise WalletError("Only mainnet and Testnet4 wallets are supported.")


def _query_for(record: WalletRecord, get: Callable) -> Callable:
    return partial(explorer_get, chain=_chain(record)) if get is explorer_get else get


@dataclass(frozen=True)
class Layout:
    receive: Descriptor
    change: Descriptor | None
    warning: str
    change_verified: bool


def wallet_layout(record: WalletRecord) -> Layout:
    """Resolve paths only when the BSMS reference address anchors receive /0."""
    chain = _chain(record)
    prefix = "bc1" if chain == "main" else "tb1"
    if not record.reference_address.startswith(prefix):
        raise WalletError("Wallet reference address does not match its network.")
    if record.reference_status == "mismatch":
        raise WalletError(
            "Reference address does not match a supported first receive address. "
            "No balance or transaction path will be guessed."
        )
    desc = record.descriptor
    text = record.descriptor_text
    suffixes = [key.suffix for key in record.keys]
    if desc.num_branches == 2:
        receive, change = desc.branch(0), desc.branch(1)
        warning = ""
        verified = True
    elif suffixes and all(s == "/0/*" for s in suffixes):
        receive = desc
        change = (None if chain == "main"
                  else Descriptor.from_string(text.replace("/0/*", "/1/*")))
        warning = (
            "Mainnet change is not declared; balance may be incomplete and "
            "transaction preparation is disabled."
            if chain == "main" else
            "Change branch /1/* is inferred from the BIP48 convention, not declared in the BSMS file."
        )
        verified = False
    elif suffixes and all(s == "/*" for s in suffixes):
        if record.reference_status == "receive-branch-only":
            receive = Descriptor.from_string(text.replace("/*", "/0/*"))
            change = (None if chain == "main"
                      else Descriptor.from_string(text.replace("/*", "/1/*")))
            warning = (
                "The mainnet /* descriptor does not literally match the reference. "
                "Only the matching /0/* receive path is scanned; change is not guessed. "
                "Balance is partial and transaction preparation is disabled."
                if chain == "main" else
                "The file's /* descriptor does not literally produce its reference address. "
                "Receive /0/* matches that address; change /1/* is inferred. "
                "Treat the displayed total as provisional until the wallet's paths are confirmed."
            )
            verified = False
        else:
            receive, change = desc, None
            warning = (
                "Only the literal /* branch can be checked. No change branch is defined; "
                "the displayed amount may not be the wallet's full balance."
            )
            verified = False
    else:
        raise WalletError("Unsupported address branches; no balance will be guessed.")
    network = NETWORKS[record.network]
    if receive.derive(0).address(network) != record.reference_address:
        raise WalletError("Reference address does not match the chosen receive path.")
    if change and change.derive(0).address(network) == record.reference_address:
        raise WalletError("Receive and change paths unexpectedly overlap.")
    return Layout(receive, change, warning, verified)


def wallet_summary(record: WalletRecord) -> dict:
    layout = wallet_layout(record)
    chain = _chain(record)
    network = NETWORKS[record.network]
    return {
        "policy": f"{record.threshold}-of-{len(record.keys)} native-SegWit multisig",
        "chain": ("Bitcoin mainnet" if chain == "main" else
                  "Testnet4 (selected in this app; tb1 alone cannot identify a chain)"),
        "network": chain,
        "can_prepare": (bool(layout.change_verified and layout.change
                             and record.threshold == 2 and len(record.keys) == 3)
                        if chain == "main" else bool(layout.change)),
        "reference_address": record.reference_address,
        "reference_status": record.reference_status,
        "receive_address": layout.receive.derive(0).address(network),
        "change_address": (
            layout.change.derive(0).address(network) if layout.change else None
        ),
        "warning": layout.warning,
        "keys": [
            {"number": i, "fingerprint": key.fingerprint.hex(),
             "origin": str(key.origin),
             "public_key": key.key.to_base58(version=network["xpub"]),
             "suffix": key.suffix}
            for i, key in enumerate(record.keys, start=1)
        ],
    }


def _address_stats(address: str, get: Callable) -> dict:
    data = get(f"/address/{address}")
    if not isinstance(data, dict):
        raise WalletError("Explorer returned malformed address information.")
    try:
        confirmed = data["chain_stats"]
        pending = data["mempool_stats"]
        values = [confirmed[k] for k in ("funded_txo_sum", "spent_txo_sum", "tx_count")]
        values += [pending[k] for k in ("funded_txo_sum", "spent_txo_sum", "tx_count")]
        if any(type(v) is not int or v < 0 for v in values):
            raise ValueError()
        return {
            "confirmed": confirmed["funded_txo_sum"] - confirmed["spent_txo_sum"],
            "pending_delta": pending["funded_txo_sum"] - pending["spent_txo_sum"],
            "used": confirmed["tx_count"] > 0 or pending["tx_count"] > 0,
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise WalletError("Explorer returned malformed address statistics.") from exc


def scan_wallet(record: WalletRecord, get: Callable = explorer_get) -> dict:
    """Scan both branches until 20 unused addresses after the last used (max 100).

    The wallet file remains in local process memory. Only derived addresses and
    later explicit previous-transaction requests go to the explorer.
    """
    layout = wallet_layout(record)
    chain = _chain(record)
    query = _query_for(record, get)
    addresses = []
    coverage_limited = False
    for name, branch in (("receive", layout.receive), ("change", layout.change)):
        if branch is None:
            continue
        gap = 0
        with ThreadPoolExecutor(max_workers=4) as executor:
            for start in range(0, MAX_INDEX, 10):
                chunk = [
                    (index, branch.derive(index).address(NETWORKS[record.network]))
                    for index in range(start, min(start + 10, MAX_INDEX))
                ]
                stats = list(executor.map(lambda item: _address_stats(item[1], query), chunk))
                for (index, address), stat in zip(chunk, stats):
                    addresses.append(
                        {"branch": name, "index": index, "address": address, **stat}
                    )
                    gap = 0 if stat["used"] else gap + 1
                if gap >= GAP_LIMIT:
                    break
            else:
                coverage_limited = True
    # Request only active addresses' UTXOs. No xpub or descriptor is sent.
    utxos = []
    outpoints = set()
    for item in addresses:
        if not item["used"]:
            continue
        raw = query(f"/address/{item['address']}/utxo")
        if not isinstance(raw, list):
            raise WalletError("Explorer returned malformed UTXO information.")
        for entry in raw:
            try:
                txid, vout, value = entry["txid"], entry["vout"], entry["value"]
                confirmed = entry["status"]["confirmed"]
                if (not isinstance(txid, str) or len(txid) != 64
                    or bytes.fromhex(txid).hex() != txid.lower()
                    or type(vout) is not int or vout < 0
                    or type(value) is not int or value <= 0
                    or type(confirmed) is not bool):
                    raise ValueError()
            except (KeyError, TypeError, ValueError) as exc:
                raise WalletError("Explorer returned malformed UTXO data.") from exc
            outpoint = (txid.lower(), vout)
            if outpoint in outpoints:
                raise WalletError("Explorer repeated an output across addresses; scan stopped.")
            outpoints.add(outpoint)
            utxos.append({**entry, "branch": item["branch"], "index": item["index"],
                           "address": item["address"]})
    confirmed = sum(item["confirmed"] for item in addresses)
    pending_delta = sum(item["pending_delta"] for item in addresses)
    return {
        "network": chain,
        "confirmed_sats": confirmed, "pending_delta_sats": pending_delta,
        "observed_sats": confirmed + pending_delta,
        "utxo_consistent": sum(
            u["value"] for u in utxos if u["status"]["confirmed"]
        ) == confirmed,
        "addresses": [
            item for item in addresses
            if item["used"] or (item["branch"] == "receive" and item["index"] == 0)
        ],
        "utxos": utxos,
        "used_change_indices": [
            item["index"] for item in addresses
            if item["branch"] == "change" and item["used"]
        ],
        "scanned": len(addresses),
        "coverage_limited": coverage_limited or layout.change is None,
        "path_warning": layout.warning,
        "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": EXPLORERS[chain],
    }


def build_unsigned_psbt(
    record: WalletRecord, scan: dict, recipient: str, amount: int,
    fee_rate: int = 2, get: Callable = explorer_get,
) -> dict:
    """Create an unsigned PSBT with previous transactions; never sign/broadcast."""
    layout = wallet_layout(record)
    chain = _chain(record)
    query = _query_for(record, get)
    if scan.get("network", chain) != chain:
        raise WalletError("Wallet and scanned network differ; no PSBT built.")
    if chain == "main":
        if not layout.change_verified or record.threshold != 2 or len(record.keys) != 3:
            raise WalletError("Mainnet PSBTs require an explicit 2-of-3 receive/change descriptor.")
        if not scan.get("utxo_consistent", False):
            raise WalletError(
                "Mainnet UTXOs and confirmed balance disagree; refresh or verify with your own node."
            )
    if layout.change is None or scan.get("coverage_limited"):
        raise WalletError("Change path or scan coverage is incomplete; no PSBT will be built.")
    prefix = "bc1" if chain == "main" else "tb1"
    if not isinstance(recipient, str) or not recipient.startswith(prefix):
        raise WalletError(f"{'Mainnet' if chain == 'main' else 'Testnet4'} send requires a {prefix} destination address.")
    try:
        destination = script.address_to_scriptpubkey(recipient)
        if destination.address(NETWORKS[record.network]) != recipient.lower():
            raise ValueError("wrong network")
    except Exception as exc:
        raise WalletError("Destination address is invalid.") from exc
    if type(amount) is not int or amount < SATOSHI_DUST_FLOOR:
        raise WalletError("Amount must be at least 546 sats.")
    if type(fee_rate) is not int or not 1 <= fee_rate <= 25:
        raise WalletError("Fee rate must be between 1 and 25 sat/vB.")
    candidates = sorted(
        (u for u in scan["utxos"] if u["status"]["confirmed"]),
        key=lambda u: u["value"], reverse=True,
    )
    chosen, total, fee = [], 0, 0
    for utxo in candidates:
        chosen.append(utxo)
        total += utxo["value"]
        # Conservative 2-of-3 P2WSH input estimate; fee is a displayed estimate.
        fee = (20 + 150 * len(chosen) + 50 * 2) * fee_rate
        if total >= amount + fee + SATOSHI_DUST_FLOOR:
            break
    if total < amount + fee + SATOSHI_DUST_FLOOR:
        raise WalletError("Not enough confirmed sats for amount, estimated fee, and change.")
    fee_warning = check_fee_safety(fee, amount, fee_rate)
    change_index = next(
        (i for i in range(MAX_INDEX)
         if i not in scan["used_change_indices"]),
        None,
    )
    if change_index is None:
        raise WalletError("No unused change index found within the scanned range.")
    change_desc = layout.change.derive(change_index)
    change_address = change_desc.address(NETWORKS[record.network])
    outputs = [
        transaction.TransactionOutput(amount, destination),
        transaction.TransactionOutput(total - amount - fee, change_desc.script_pubkey()),
    ]
    tx = transaction.Transaction(
        version=2,
        vin=[transaction.TransactionInput(bytes.fromhex(u["txid"]), u["vout"])
             for u in chosen],
        vout=outputs,
    )
    packet = psbt.PSBT(tx)
    for scope, utxo in zip(packet.inputs, chosen):
        desc = (layout.receive if utxo["branch"] == "receive" else layout.change)
        derived = desc.derive(utxo["index"])
        try:
            raw = query(f"/tx/{utxo['txid']}/hex", text=True)
            previous = transaction.Transaction.parse(bytes.fromhex(raw))
            prevout = previous.vout[utxo["vout"]]
        except (ValueError, IndexError, TypeError) as exc:
            raise WalletError("Explorer returned an invalid previous transaction.") from exc
        if (previous.txid().hex() != utxo["txid"].lower()
            or prevout.value != utxo["value"]
            or prevout.script_pubkey != derived.script_pubkey()):
            raise WalletError("Previous output does not match this wallet; no PSBT built.")
        scope.non_witness_utxo = previous
        scope.witness_utxo = prevout
        scope.witness_script = derived.witness_script()
        scope.bip32_derivations = {
            key.get_public_key(): psbt.DerivationPath(key.fingerprint, key.derivation)
            for key in derived.keys
        }
    change_scope = packet.outputs[1]
    change_scope.witness_script = change_desc.witness_script()
    change_scope.bip32_derivations = {
        key.get_public_key(): psbt.DerivationPath(key.fingerprint, key.derivation)
        for key in change_desc.keys
    }
    if packet.fee() != fee:
        raise WalletError("PSBT fee check failed; no PSBT built.")
    return {
        "psbt_base64": packet.to_base64(),
        "recipient": recipient,
        "amount_sats": amount,
        "fee_sats": fee,
        "fee_warning": fee_warning,
        "total_spend_sats": amount + fee,
        "fee_rate_estimate": fee_rate,
        "change_sats": total - amount - fee,
        "change_address": change_address,
        "inputs": len(chosen),
        "change_warning": layout.warning or (
            "Unsigned only. Verify destination, amount, fee, and change on each signer."
        ),
    }