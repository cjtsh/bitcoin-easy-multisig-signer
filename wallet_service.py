"""Public-data wallet view, PSBT preparation and guarded broadcast for selected networks.

No seeds or signing keys live here. Address queries disclose queried addresses to
the configured public explorer.
"""

from __future__ import annotations

import json
import re
import ssl
import time
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request

from safe_http import open_url as urlopen  # TLS-verified, never follows a redirect

from embit import psbt, script, transaction
from embit.base import EmbitError
from embit.psbt import DerivationPath
from embit.descriptor import Descriptor
from embit.descriptor.miniscript import Multi, Sortedmulti
from embit.networks import NETWORKS

from network_config import NETWORKS as CHAIN_CONFIGS, for_record_network
from network_settings import validate_esplora_url
from version import APP_VERSION
from probe import ProbeError, WalletRecord

EXPLORERS = {chain: config.explorer_url for chain, config in CHAIN_CONFIGS.items()}
GAP_LIMIT = 20
MAX_INDEX = 100
SATOSHI_DUST_FLOOR = 546
MAX_ESTIMATED_FEE_SATS = 10_000


def supported_multisig_policy(record: WalletRecord) -> bool:
    """The currently supported wallet quorums, all with at most three keys."""
    return 2 <= len(record.keys) <= 3 and 1 <= record.threshold <= len(record.keys)


class WalletError(ProbeError):
    pass


class BroadcastOutcomeUnknown(WalletError):
    """The submit request left this app, but acceptance was not established."""


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


def broadcast_transaction(raw_transaction_hex: str, chain: str = "testnet4",
                          base_url: str | None = None,
                          mainnet_opt_in: bool = False) -> str:
    """Submit a finalised transaction to an Esplora endpoint and return its txid.

    Redirects are refused and TLS is verified, exactly as for every other outbound
    request. The endpoint's own rejection reason is surfaced, because "bad-txns-..."
    from the node is far more useful than a generic failure.
    """
    if chain not in EXPLORERS:
        raise WalletError("Unsupported broadcast network.")
    if chain == "main" and mainnet_opt_in is not True:
        raise WalletError("Explicit mainnet broadcast confirmation is required.")
    raw = (raw_transaction_hex or "").strip().lower()
    if len(raw) < 100 or len(raw) > 2_000_000 or len(raw) % 2:
        raise WalletError("The finalised transaction is not a usable size.")
    try:
        bytes.fromhex(raw)
    except ValueError as exc:
        raise WalletError("The finalised transaction is not valid hex.") from exc
    base = validate_esplora_url(base_url) if base_url is not None else EXPLORERS[chain]
    request = Request(base + "/tx", data=raw.encode("ascii"), method="POST", headers={
        "User-Agent": f"EasyMultisig/{APP_VERSION}",
        "Content-Type": "text/plain",
    })
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read(4096).decode("ascii", "replace").strip()
    except HTTPError as exc:
        try:
            detail = exc.read(2048).decode("utf-8", "replace").strip()
        except Exception:
            detail = ""
        if exc.code >= 500:
            # A server-side failure can arrive after the node has already
            # accepted and relayed the transaction. Reporting a refusal would
            # state something we cannot know, and would leave the payment
            # retryable without the pending-payment pause being armed.
            raise BroadcastOutcomeUnknown(
                "The broadcast result is unknown: the server failed while "
                f"submitting this payment (HTTP {exc.code}), and it may already "
                "have been accepted. Do not send this payment again. Check the "
                "transaction on an explorer or ask for help before proceeding."
            ) from exc
        raise WalletError(
            "The network refused this transaction"
            + (f": {detail[:300]}" if detail else f" (HTTP {exc.code}).")
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise BroadcastOutcomeUnknown(
            "The broadcast result is unknown. Do not send this payment again. "
            "Check the transaction on an explorer or ask for help before proceeding."
        ) from exc
    if len(body) != 64 or any(char not in "0123456789abcdef" for char in body.lower()):
        raise BroadcastOutcomeUnknown(
            "The broadcast result is unknown because the server did not return a "
            "transaction ID. Do not send this payment again; check an explorer first."
        )
    return body.lower()


def explorer_get(path: str, *, text: bool = False, chain: str = "testnet4",
                 base_url: str | None = None):
    """Bounded Esplora GET on an explicit network; never send xpubs."""
    if chain not in EXPLORERS:
        raise WalletError("Unsupported explorer network.")
    if not path.startswith("/") or ".." in path or "?" in path:
        raise WalletError("Invalid explorer path.")
    base = validate_esplora_url(base_url) if base_url is not None else EXPLORERS[chain]
    request = Request(base + path, headers={
        "User-Agent": f"EasyMultisig/{APP_VERSION}", "Accept": "application/json",
    })
    for attempt in range(2):
        try:
            with urlopen(request, timeout=12) as response:
                if response.length is not None and response.length > 2_000_000:
                    raise WalletError("Explorer response is unexpectedly large.")
                body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise WalletError("Explorer response is unexpectedly large.")
            return body.decode("ascii") if text else json.loads(body)
        except HTTPError as exc:
            if exc.code in (429, 502, 503, 504) and attempt == 0:
                time.sleep(1)
                continue
            if exc.code == 429:
                detail = "rate-limited requests (HTTP 429). Wait a minute and refresh."
            else:
                detail = f"returned HTTP {exc.code}. Check the explorer in Advanced network settings."
            raise WalletError(f"{chain} explorer {detail} No zero balance is claimed.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            reason = exc.reason if isinstance(exc, URLError) else exc
            if isinstance(reason, ssl.SSLError):
                raise WalletError(
                    f"Could not verify the {chain} explorer HTTPS certificate. "
                    "No zero balance is claimed."
                ) from exc
            if attempt == 0:
                time.sleep(1)
                continue
            raise WalletError(
                f"Could not connect to the {chain} explorer. Check your internet connection "
                "and the explorer in Advanced network settings. No zero balance is claimed."
            ) from exc
        except (UnicodeError, ValueError) as exc:
            raise WalletError(
                f"{chain} explorer returned invalid data. Check the explorer in Advanced "
                "network settings. No zero balance is claimed."
            ) from exc


def check_selected_outpoints(packet: psbt.PSBT, chain: str, primary_base: str,
                             secondary_base: str | None = None,
                             get: Callable = explorer_get) -> None:
    """Recheck selected coins just before use, against a second source when set.

    Only public transaction IDs and output numbers are sent. A second Esplora
    lowers the risk of trusting one stale or manipulated index but is not a
    consensus proof; a user-run node is stronger. The caller verifies each
    source's genesis before using it and never silently changes sources.
    """
    if chain not in EXPLORERS or secondary_base == primary_base:
        raise WalletError("Independent output check has no separate valid source.")
    if not packet.tx.vin:
        raise WalletError("The transaction has no inputs to verify.")
    checked_funding = set()
    for vin in packet.tx.vin:
        txid, vout = vin.txid.hex(), vin.vout
        if len(txid) != 64 or type(vout) is not int or vout < 0:
            raise WalletError("A transaction input cannot be checked.")
        for base in (primary_base, secondary_base):
            if base is None:
                continue
            if (base, txid) not in checked_funding:
                try:
                    funding = get(f"/tx/{txid}/status", chain=chain,
                                  base_url=base)
                except WalletError as exc:
                    raise WalletError(
                        "Could not confirm that the selected Bitcoin is still available. "
                        "Refresh and try again, or ask for help."
                    ) from exc
                if (not isinstance(funding, dict)
                        or funding.get("confirmed") is not True):
                    raise WalletError(
                        "A selected Bitcoin output is no longer confirmed. "
                        "Refresh your balance before preparing or sending."
                    )
                checked_funding.add((base, txid))
            try:
                status = get(f"/tx/{txid}/outspend/{vout}", chain=chain,
                             base_url=base)
            except WalletError as exc:
                raise WalletError(
                    "Could not confirm that the selected Bitcoin is still available. "
                    "Refresh and try again, or ask for help."
                ) from exc
            if not isinstance(status, dict) or type(status.get("spent")) is not bool:
                raise WalletError("An explorer gave an unclear output status; no payment was sent.")
            if status["spent"]:
                raise WalletError(
                    "A selected Bitcoin output was already spent. Refresh your balance "
                    "before preparing or sending another payment."
                )


def _chain(record: WalletRecord, selected: str | None = None) -> str:
    if selected is not None:
        if selected not in CHAIN_CONFIGS or CHAIN_CONFIGS[selected].record_network != record.network:
            raise WalletError("Wallet and scanned network differ; no transaction was prepared.")
        return selected
    try:
        return for_record_network(record.network).chain
    except ValueError as exc:
        raise WalletError(str(exc)) from exc


def _query_for(record: WalletRecord, get: Callable, base_url: str | None,
               chain: str | None = None) -> Callable:
    return (partial(explorer_get, chain=_chain(record, chain), base_url=base_url)
            if get is explorer_get else get)


@dataclass(frozen=True)
class Layout:
    receive: Descriptor
    change: Descriptor | None
    warning: str
    change_verified: bool
    change_declared: bool = False
    change_assumed: bool = False


def wallet_layout(record: WalletRecord) -> Layout:
    """Resolve paths only when the BSMS reference address anchors receive /0."""
    config = CHAIN_CONFIGS[_chain(record)]
    if not record.reference_address.startswith(config.address_prefix):
        raise WalletError("Wallet reference address does not match its network.")
    if record.reference_status == "mismatch":
        raise WalletError(
            "Reference address does not match a supported first receive address. "
            "No balance or transaction path will be guessed."
        )
    desc = record.descriptor
    text = record.descriptor_text
    suffixes = [key.suffix for key in record.keys]
    assumed = False
    declared = False
    if record.change_descriptor is not None:
        # The wallet file itself declares separate receive and change descriptors.
        receive, change = desc, record.change_descriptor
        warning = ""
        verified = True
        declared = True
    elif desc.num_branches == 2:
        receive, change = desc.branch(0), desc.branch(1)
        warning = ""
        verified = True
        declared = True
    else:
        bare_receive_only = False
        if suffixes and all(s == "/0/*" for s in suffixes):
            receive, receive_text = desc, text
        elif suffixes and all(s == "/*" for s in suffixes):
            if record.reference_status == "receive-branch-only":
                receive_text = text.replace("/*", "/0/*")
                receive = Descriptor.from_string(receive_text)
            else:
                # xpub/* can match the first address directly at xpub/0.
                # That does not anchor the BIP48 xpub/0/index branch.
                receive, receive_text = desc, text
                bare_receive_only = True
        else:
            raise WalletError("Unsupported address branches; no balance will be guessed.")
        # Nunchuk's BSMS writer emits a bare /* and "No path restrictions" for
        # ordinary BIP48 multisig. BIP48 itself defines /0/* receive and /1/*
        # change. Support that standard layout using the one recovery file the
        # owner has, but label the change branch as standard-derived rather
        # than claiming it was declared by BSMS or proven by an empty history.
        # Nonstandard/custom origins continue to fail closed.
        if bare_receive_only and record.restrictions == "/0/*,/1/*":
            raise WalletError("BSMS receive restriction disagrees with its first address.")
        declared = record.restrictions == "/0/*,/1/*"
        standard_candidate = not declared and not bare_receive_only and _standard_bip48(record)
        change = (_conventional_change(receive_text, record)
                  if declared or standard_candidate else None)
        assumed = bool(change and standard_candidate)
        verified = bool(change and declared)
        if assumed:
            warning = ("This app derives BIP48 standard change addresses. The BSMS file "
                       "does not state the change branch; check change during signing.")
        elif change is None:
            warning = ("This export does not establish a supported change branch. "
                       "Only Send All from scanned receiving addresses is available.")
        else:
            warning = ""
    network = NETWORKS[record.network]
    if receive.derive(0).address(network) != record.reference_address:
        raise WalletError("Reference address does not match the chosen receive path.")
    if change and change.derive(0).address(network) == record.reference_address:
        raise WalletError("Receive and change paths unexpectedly overlap.")
    return Layout(receive, change, warning, verified, declared, assumed)


_ZERO_BRANCH = re.compile(r"/0/\*")
_BARE_WILDCARD = re.compile(r"(?<!/\d)/\*")


def _standard_bip48(record: WalletRecord) -> bool:
    """Conservative one-file BIP48 policy: native SegWit sorted 2-of-3.

    BIP48 defines the change/index levels after the four hardened account
    levels. The first receive address still has to match this exact BSMS file;
    wallet_layout performs that check before any scan or transaction.
    """
    if (record.threshold != 2 or len(record.keys) != 3
            or not isinstance(record.descriptor.miniscript, Sortedmulti)
            or record.restrictions != "No path restrictions"):
        return False
    origins = [key.derivation for key in record.keys]
    if any(len(origin) != 4 or origin[0] != 0x80000030
           or origin[3] != 0x80000002
           or origin[2] < 0x80000000 for origin in origins):
        return False
    return len({tuple(origin) for origin in origins}) == 1


def _conventional_change(receive_text: str, record: WalletRecord) -> Descriptor | None:
    """Resolve the BIP48 internal branch from the anchored external branch.

    Callers must establish either an explicit BSMS declaration or the strict
    BIP48 policy above. Derivation alone is not evidence of Nunchuk-specific
    custom branch indices, which this one-file flow does not support.
    """
    if "/**" in receive_text or "<0;1>" in receive_text:
        return None
    try:
        if _ZERO_BRANCH.search(receive_text):
            change_text = _ZERO_BRANCH.sub("/1/*", receive_text)
        elif "/*" in receive_text:
            change_text = _BARE_WILDCARD.sub("/1/*", receive_text)
        else:
            return None
        candidate = Descriptor.from_string(change_text)
        if (not candidate.wsh or candidate.sh
                or not isinstance(candidate.miniscript, Multi)
                or candidate.miniscript.args[0].num != record.threshold
                or len(candidate.keys) != len(record.keys)
                or sorted(k.key.to_base58() for k in candidate.keys)
                   != sorted(k.key.to_base58() for k in record.keys)):
            return None
    except Exception:
        return None
    return candidate


def wallet_summary(record: WalletRecord, chain: str | None = None) -> dict:
    layout = wallet_layout(record)
    config = CHAIN_CONFIGS[_chain(record, chain)]
    network = NETWORKS[record.network]
    supported_policy = supported_multisig_policy(record)
    can_prepare = bool(layout.change and (layout.change_verified or layout.change_assumed)
                       and supported_policy)
    can_send_all = supported_policy
    if not supported_policy:
        prepare_reason = (
            "This app supports multisig wallets with two or three keys. "
            "This wallet's quorum is not supported."
        )
    elif layout.change is None:
        prepare_reason = (
            "This wallet file does not establish change ownership. You can send all "
            "confirmed Bitcoin found on its receiving addresses with no change, or "
            "import an export that declares receive and change paths for a smaller send."
        )
    else:
        prepare_reason = ""
    if layout.change_assumed:
        change_note = (
            "Leftover Bitcoin is intended to return to this multisig wallet through "
            "the standard change path, but this file does not state that path. Your "
            "devices will not display the change address. Compare it with the change "
            "addresses in the app that created this file before you approve, or send "
            "the whole balance instead so there is no change to check."
        )
        change_detail = (
            "The BSMS file proves the first receiving address but omits a separate "
            "change path. This app uses BIP48's /1/* internal branch for this strict "
            "native-SegWit 2-of-3 sorted multisig policy."
        )
    elif layout.change is not None:
        change_note = ""
        change_detail = "Change addresses are declared in your wallet file."
    else:
        change_note = ""
        change_detail = "This export does not establish change ownership; partial sends are unavailable."
    return {
        "policy": f"{record.threshold}-of-{len(record.keys)} native-SegWit multisig",
        "policy_short": f"{record.threshold}-of-{len(record.keys)} multisig wallet",
        "chain": config.label,
        "chain_short": config.short_label,
        "network": config.chain,
        "can_prepare": can_prepare,
        "can_send_all": can_send_all,
        "change_assumed": layout.change_assumed,
        "change_note": change_note,
        "change_detail": change_detail,
        "prepare_reason": prepare_reason,
        "reference_address": record.reference_address,
        "reference_status": record.reference_status,
        "descriptor_checksum": record.descriptor_checksum,
        "checksum_supplied": record.checksum_supplied,
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
            # Outputs being spent by a transaction that is not confirmed yet. The
            # address totals still count them; the UTXO list already excludes them.
            "pending_spent": pending["spent_txo_sum"],
            "used": confirmed["tx_count"] > 0 or pending["tx_count"] > 0,
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise WalletError("Explorer returned malformed address statistics.") from exc


def _utxos_agree_with_totals(confirmed_from_totals: int, confirmed_utxos: int,
                             pending_spent: int) -> bool:
    """Do the address totals and the UTXO list describe the same money?

    They legitimately differ while a payment is unconfirmed. An output that an
    unconfirmed transaction is spending still counts in the address totals -- the
    spend is not confirmed -- but it is already gone from the UTXO list. This is
    an accounting exception, independent of the one-payment-at-a-time send rule.

    A shortfall is therefore fine when unconfirmed spends account for it. UTXOs
    exceeding the totals is not: that would mean the explorer reports money it does
    not count, and no transaction should be built on it.
    """
    if confirmed_utxos > confirmed_from_totals:
        return False
    return (confirmed_from_totals - confirmed_utxos) <= pending_spent


def scan_wallet(record: WalletRecord, get: Callable = explorer_get,
                *, base_url: str | None = None, chain: str | None = None) -> dict:
    """Scan both branches until 20 unused addresses after the last used (max 100).

    The wallet file remains in local process memory. Only derived addresses and
    later explicit previous-transaction requests go to the explorer.
    """
    layout = wallet_layout(record)
    chain = _chain(record, chain)
    query = _query_for(record, get, base_url, chain)
    addresses = []
    coverage_limited = False
    for name, branch in (("receive", layout.receive), ("change", layout.change)):
        if branch is None:
            continue
        gap = 0
        with ThreadPoolExecutor(max_workers=2) as executor:
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
        "pending_outgoing": any(item["pending_spent"] > 0 for item in addresses),
        "observed_sats": confirmed + pending_delta,
        "utxo_consistent": _utxos_agree_with_totals(
            confirmed, sum(u["value"] for u in utxos if u["status"]["confirmed"]),
            sum(item.get("pending_spent", 0) for item in addresses),
        ),
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
        "range_limited": coverage_limited,
        "missing_change": layout.change is None,
        "coverage_limited": coverage_limited or layout.change is None,
        "path_warning": layout.warning,
        "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": base_url or EXPLORERS[chain],
    }


def _compact_size_length(value: int) -> int:
    if value < 253:
        return 1
    if value <= 0xFFFF:
        return 3
    if value <= 0xFFFFFFFF:
        return 5
    return 9


def _estimated_signed_vbytes(
    chosen: list[dict], output_scripts: list[script.Script],
    witness_script_lengths: dict[str, int], threshold: int = 2,
) -> int:
    """Estimate native P2WSH signed weight with 73-byte signatures.

    Signatures are not present yet; this is a conservative size estimate, not
    the guaranteed final sat/vB rate. The PSBT's absolute fee is exact.
    """
    base = (8 + _compact_size_length(len(chosen))
            + _compact_size_length(len(output_scripts)) + 41 * len(chosen))
    base += sum(8 + _compact_size_length(len(out.data)) + len(out.data)
                for out in output_scripts)
    witness = 2  # SegWit marker and flag.
    for utxo in chosen:
        size = witness_script_lengths[utxo["branch"]]
        witness += 1 + 1 + threshold * (1 + 73) + _compact_size_length(size) + size
    return (4 * base + witness + 3) // 4


def _select_inputs(
    candidates: list[dict], amount: int | None, fee_rate: int,
    output_scripts: list[script.Script], witness_script_lengths: dict[str, int],
    *, send_all: bool, threshold: int = 2,
) -> tuple[list[dict], int, int]:
    """Choose inputs and compute the fee for the transaction that will be built.

    Single source of truth for both the live fee preview and the PSBT builder, so
    the two can never disagree about which outputs are spent or what the fee is.
    Returns (chosen_utxos, total_input_sats, fee_sats).
    """
    ordered = sorted(candidates, key=lambda u: u["value"], reverse=True)
    if send_all:
        # Every confirmed output found by this scan is spent and there is no
        # change output, so the fee comes out of the recipient amount.
        total = sum(u["value"] for u in ordered)
        fee = _estimated_signed_vbytes(
            ordered, output_scripts, witness_script_lengths, threshold
        ) * fee_rate
        return ordered, total, fee
    chosen: list[dict] = []
    total = 0
    fee = 0
    for utxo in ordered:
        chosen.append(utxo)
        total += utxo["value"]
        fee = _estimated_signed_vbytes(
            chosen, output_scripts, witness_script_lengths, threshold
        ) * fee_rate
        if amount is not None and total >= amount + fee + SATOSHI_DUST_FLOOR:
            break
    return chosen, total, fee


def estimate_fee_preview(record: WalletRecord, scan: dict, send_all: bool,
                         amount: int | None = None, fee_rate: int = 2,
                         recipient: str | None = None) -> dict:
    """Live fee estimate for the transaction that would actually be built.

    For a partial send with an amount, the same greedy input selection as the
    builder is used, so the previewed size matches the review. With no amount
    (or for send-all) every confirmed scanned output is used, which is the
    conservative upper bound.
    """
    if scan.get("pending_outgoing"):
        raise WalletError("A payment from this wallet is waiting for one confirmation. Check again later before preparing another payment.")
    if not supported_multisig_policy(record):
        raise WalletError("This app supports multisig wallets with two or three keys only.")
    layout = wallet_layout(record)
    if layout.change is None and not send_all:
        raise WalletError(
            "This wallet export does not establish change ownership. Choose Send All "
            "or import an export that declares both address branches."
        )
    if (not scan.get("utxo_consistent") or scan.get("range_limited")
            or (scan.get("missing_change") and not send_all)):
        raise WalletError("Refresh a complete, consistent balance before estimating a transaction.")
    if type(fee_rate) is not int or not 1 <= fee_rate <= 25:
        raise WalletError("Fee rate must be between 1 and 25 sat/vB.")
    confirmed = [u for u in scan["utxos"] if u["status"]["confirmed"]]
    if not confirmed:
        raise WalletError("No confirmed outputs are available to estimate.")
    if not send_all and amount is not None:
        if type(amount) is not int or amount < SATOSHI_DUST_FLOOR:
            raise WalletError("Amount must be at least 546 sats.")
    else:
        amount = None
    destination = _output_script_for(recipient, record)
    output_scripts = [destination] if send_all else [
        destination, layout.change.derive(0).script_pubkey()
    ]
    script_lengths = {
        "receive": len(layout.receive.derive(0).witness_script().data),
    }
    if layout.change:
        script_lengths["change"] = len(layout.change.derive(0).witness_script().data)
    chosen, total, fee = _select_inputs(
        confirmed, amount, fee_rate, output_scripts, script_lengths,
        send_all=send_all, threshold=record.threshold,
    )
    if not chosen:
        raise WalletError("No confirmed outputs are available to estimate.")
    if not send_all and amount is not None and total < amount + fee + SATOSHI_DUST_FLOOR:
        raise WalletError("Not enough confirmed sats for amount, estimated fee, and change.")
    # The builder enforces this unconditionally, so the preview must too. A
    # preview that displays a fee the builder will then refuse is worse than no
    # preview, and the message deliberately matches check_fee_safety's.
    if fee > MAX_ESTIMATED_FEE_SATS:
        raise WalletError(
            f"Estimated fee of {fee:,} sats exceeds the 10,000-sat safety ceiling. "
            "Use fewer inputs or a lower sat/vB rate."
        )
    return {
        "estimated_vbytes": _estimated_signed_vbytes(
            chosen, output_scripts, script_lengths, record.threshold),
        "input_count": len(chosen),
        "selected_sats": total,
        "method": ("exact input selection for this amount" if amount is not None
                   else "conservative upper estimate using all confirmed scanned outputs"),
    }


def _output_script_for(recipient: str | None, record: WalletRecord) -> script.Script:
    """Real destination script when a valid address is supplied, else a P2WSH-sized stand-in."""
    if isinstance(recipient, str):
        try:
            destination = script.address_to_scriptpubkey(recipient)
            if destination.address(NETWORKS[record.network]) == recipient.lower():
                return destination
        except Exception:
            pass
    return script.Script(b"\x00\x20" + bytes(32))


def build_unsigned_psbt(
    record: WalletRecord, scan: dict, recipient: str, amount: int | None,
    fee_rate: int = 2, get: Callable = explorer_get,
    *, base_url: str | None = None, send_all: bool = False,
) -> dict:
    """Create an unsigned PSBT with previous transactions; never sign/broadcast."""
    layout = wallet_layout(record)
    chain = _chain(record, scan.get("network"))
    query = _query_for(record, get, base_url, chain)
    if scan.get("network") != chain:
        raise WalletError("Wallet and scanned network differ; no unsigned transaction was prepared.")
    if scan.get("pending_outgoing"):
        raise WalletError("A payment from this wallet is waiting for one confirmation. Check again later before preparing another payment.")
    if not supported_multisig_policy(record):
        raise WalletError(
            "This app supports multisig wallets with two or three keys only."
        )
    if layout.change is None and not send_all:
        raise WalletError(
            "Preparing a smaller send requires a supported BIP48 change path. "
            "Choose Send All or import a wallet file that declares change."
        )
    if scan.get("source") != (base_url or EXPLORERS[chain]):
        raise WalletError("Explorer changed since the balance scan; refresh before preparing.")
    if not scan.get("utxo_consistent", False):
        raise WalletError(
            "UTXOs and confirmed balance disagree; refresh or verify with your own node."
        )
    if scan.get("range_limited") or (scan.get("missing_change") and not send_all):
        raise WalletError("Change path or scan range is incomplete; no unsigned transaction will be prepared.")
    config = CHAIN_CONFIGS[chain]
    prefix = config.address_prefix
    if not isinstance(recipient, str) or not recipient.startswith(prefix):
        raise WalletError(f"{config.label} send requires a {prefix} destination address.")
    try:
        destination = script.address_to_scriptpubkey(recipient)
        if destination.address(NETWORKS[record.network]) != recipient.lower():
            raise ValueError("wrong network")
    except Exception as exc:
        raise WalletError("Destination address is invalid.") from exc
    if type(send_all) is not bool:
        raise WalletError("Choose either the full balance or a specific amount.")
    if send_all:
        if amount is not None:
            raise WalletError("Full-balance send must not include a separate amount.")
    elif type(amount) is not int or amount < SATOSHI_DUST_FLOOR:
        raise WalletError("Amount must be at least 546 sats.")
    if type(fee_rate) is not int or not 1 <= fee_rate <= 25:
        raise WalletError("Fee rate must be between 1 and 25 sat/vB.")
    candidates = [u for u in scan["utxos"] if u["status"]["confirmed"]]
    script_lengths = {
        "receive": len(layout.receive.derive(0).witness_script().data),
    }
    if layout.change:
        script_lengths["change"] = len(layout.change.derive(0).witness_script().data)
    change_script = layout.change.derive(0).script_pubkey() if layout.change else None
    output_scripts = [destination] if send_all else [destination, change_script]
    chosen, total, fee = _select_inputs(
        candidates, None if send_all else amount, fee_rate,
        output_scripts, script_lengths, send_all=send_all, threshold=record.threshold,
    )
    if send_all:
        if total != scan["confirmed_sats"]:
            raise WalletError("Confirmed outputs changed since the scan; refresh before sending all.")
        # One recipient output, no change. Include every confirmed output or refuse.
        if fee > MAX_ESTIMATED_FEE_SATS:
            raise WalletError("Sending all exceeds the 10,000-sat fee safety ceiling. "
                              "Wait for a lower fee rate or use an established wallet.")
        amount = total - fee
        if amount < SATOSHI_DUST_FLOOR:
            raise WalletError("Confirmed balance cannot cover the fee and a spendable output.")
    elif total < amount + fee + SATOSHI_DUST_FLOOR:
        raise WalletError("Not enough confirmed sats for amount, estimated fee, and change.")
    fee_warning = check_fee_safety(fee, amount, fee_rate)
    change_address = None
    change_sats = 0
    outputs = [transaction.TransactionOutput(amount, destination)]
    if not send_all:
        change_index = next(
            (i for i in range(MAX_INDEX)
             if i not in scan["used_change_indices"]),
            None,
        )
        if change_index is None:
            raise WalletError("No unused change index found within the scanned range.")
        change_desc = layout.change.derive(change_index)
        change_address = change_desc.address(NETWORKS[record.network])
        change_sats = total - amount - fee
        outputs.append(transaction.TransactionOutput(change_sats, change_desc.script_pubkey()))
    tx = transaction.Transaction(
        version=2,
        # Signal replaceability (BIP125) rather than finality. A transaction built
        # with the default 0xffffffff cannot be fee-bumped at all, so a payment that
        # sits in a quiet or hostile mempool is simply stuck: the owner's own second
        # testnet send did exactly that, and nothing could be done but wait. A
        # sequence below 0xfffffffe lets the same coins be spent again with a higher
        # fee if it ever becomes necessary.
        vin=[transaction.TransactionInput(bytes.fromhex(u["txid"]), u["vout"],
                                          sequence=0xFFFFFFFD)
             for u in chosen],
        vout=outputs,
    )
    packet = psbt.PSBT(tx)
    # Publish the wallet's account xpubs in the PSBT's global scope. A Ledger
    # refuses to sign a multisig spend without them: hwilib rebuilds the wallet
    # policy from these entries, and when it cannot it skips the input with no
    # error and no prompt on the device at all. Trezor and Jade do not need them,
    # which is why this went unnoticed until a Ledger was asked to sign.
    for key in record.keys:
        packet.xpubs[key.key] = DerivationPath(key.origin.fingerprint, key.origin.derivation)
    for scope, utxo in zip(packet.inputs, chosen):
        desc = (layout.receive if utxo["branch"] == "receive" else layout.change)
        derived = desc.derive(utxo["index"])
        try:
            raw = query(f"/tx/{utxo['txid']}/hex", text=True)
            previous = transaction.Transaction.parse(bytes.fromhex(raw))
            prevout = previous.vout[utxo["vout"]]
        except (ValueError, IndexError, TypeError, EmbitError, RuntimeError) as exc:
            raise WalletError("Explorer returned an invalid previous transaction.") from exc
        if (previous.txid().hex() != utxo["txid"].lower()
            or prevout.value != utxo["value"]
            or prevout.script_pubkey != derived.script_pubkey()):
            raise WalletError("Previous output does not match this wallet; no unsigned transaction was prepared.")
        scope.non_witness_utxo = previous
        scope.witness_utxo = prevout
        scope.witness_script = derived.witness_script()
        scope.bip32_derivations = {
            key.get_public_key(): psbt.DerivationPath(key.fingerprint, key.derivation)
            for key in derived.keys
        }
    if not send_all:
        change_scope = packet.outputs[1]
        change_scope.witness_script = change_desc.witness_script()
        change_scope.bip32_derivations = {
            key.get_public_key(): psbt.DerivationPath(key.fingerprint, key.derivation)
            for key in change_desc.keys
        }
    if packet.fee() != fee:
        raise WalletError("Transaction fee check failed; no unsigned transaction was prepared.")
    return {
        "psbt_base64": packet.to_base64(),
        "network": chain,
        # For segwit the witness is not part of the txid, so this id is already
        # final: the same id will appear on the explorer once it is broadcast.
        "txid": packet.tx.txid().hex(),
        "recipient": recipient,
        "amount_sats": amount,
        "send_all": send_all,
        "wallet_confirmed_sats": scan["confirmed_sats"],
        "remaining_confirmed_sats": scan["confirmed_sats"] - amount - fee,
        "fee_sats": fee,
        "estimated_signed_vbytes": fee // fee_rate,
        "fee_warning": fee_warning,
        "total_spend_sats": amount + fee,
        "fee_rate_estimate": fee_rate,
        "change_sats": change_sats,
        "change_address": change_address,
        "change_assumed": layout.change_assumed,
        "inputs": len(chosen),
        "change_warning": (
            "All confirmed outputs found by this scan are used, with no change output. "
            "An address beyond the scan gap or range may still hold Bitcoin. "
            "Verify wallet coverage, recipient amount and fee independently on each signer."
            if send_all else
            ("The change address comes from this wallet's standard change addresses, which "
             "are not listed in your wallet file. Compare it in the app that created this "
             "file before you approve. "
             if layout.change_assumed else "")
            + "Unsigned only. Check the destination, amount and fee on each signer, and the "
            "change address shown on the review screen."
        ),
    }
