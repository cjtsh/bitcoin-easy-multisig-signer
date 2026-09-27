"""Read-only BSMS and USB signer discovery proof. No transaction operations."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from embit import bip32, script
from embit.descriptor import Descriptor
from embit.descriptor.checksum import checksum as descriptor_checksum
from embit.descriptor.miniscript import Multi
from embit.networks import NETWORKS

MAX_BSMS_BYTES = 65_536


class ProbeError(Exception):
    """A safe-to-display error with no wallet keys or identifiers."""


@dataclass(frozen=True)
class WalletRecord:
    descriptor: Descriptor
    threshold: int
    network: str
    restrictions: str
    reference_status: str

    @property
    def keys(self) -> list[Any]:
        return self.descriptor.keys


def _network_for_address(address: str) -> str:
    if address.startswith("bc1"):
        return "main"
    if address.startswith("tb1"):
        return "test"  # Testnet4, legacy testnet, and Signet all share tb1.
    if address.startswith("bcrt1"):
        return "regtest"
    raise ProbeError("Only bc1, tb1, and bcrt1 reference addresses are supported.")


def _reference_status(descriptor_text: str, reference: str, network: str) -> str:
    try:
        desc = Descriptor.from_string(descriptor_text)
        if desc.derive(0).address(NETWORKS[network]) == reference:
            return "verified"

        # Diagnostic only: some wallet exports put /* where a receiver
        # expects /0/*. Never accept the substituted path as verification.
        if descriptor_text.count("/*") == len(desc.keys):
            receive_text = descriptor_text.replace("/*", "/0/*")
            receive_desc = Descriptor.from_string(receive_text)
            if receive_desc.derive(0).address(NETWORKS[network]) == reference:
                return "receive-branch-only"
        return "mismatch"
    except Exception:
        return "mismatch"


def load_bsms(path: Path) -> WalletRecord:
    try:
        if path.stat().st_size > MAX_BSMS_BYTES:
            raise ProbeError("BSMS file is unexpectedly large.")
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise ProbeError("Could not read the BSMS file.") from exc
    except UnicodeError as exc:
        raise ProbeError("BSMS file must be UTF-8 text.") from exc

    if len(lines) != 4 or lines[0] != "BSMS 1.0":
        raise ProbeError("Expected a four-line BSMS 1.0 wallet record.")
    descriptor_with_checksum, restrictions, reference = lines[1:]
    if descriptor_with_checksum.count("#") != 1:
        raise ProbeError("A descriptor with one checksum is required.")
    descriptor_text, supplied_checksum = descriptor_with_checksum.rsplit("#", 1)
    try:
        if descriptor_checksum(descriptor_text) != supplied_checksum:
            raise ProbeError("Descriptor checksum mismatch.")
    except ProbeError:
        raise
    except Exception as exc:
        raise ProbeError("Descriptor checksum could not be checked.") from exc

    if restrictions != "No path restrictions":
        raise ProbeError(
            "This first probe only supports 'No path restrictions' BSMS records."
        )
    network = _network_for_address(reference)
    try:
        script.address_to_scriptpubkey(reference)  # Validate address encoding.
        descriptor = Descriptor.from_string(descriptor_text)
    except Exception as exc:
        raise ProbeError("Address or descriptor format is invalid.") from exc
    if not descriptor.wsh or descriptor.sh or not isinstance(descriptor.miniscript, Multi):
        raise ProbeError("This proof supports native-SegWit m-of-n multisig only.")

    keys = descriptor.keys
    threshold = descriptor.miniscript.args[0].num
    if not 1 <= threshold <= len(keys) or not 2 <= len(keys) <= 20:
        raise ProbeError("Multisig threshold or signer count is unsupported.")
    if any(not key.is_extended or key.is_private or key.origin is None for key in keys):
        raise ProbeError("Every signer needs a public xpub and key origin.")
    if len({key.fingerprint for key in keys}) != len(keys):
        raise ProbeError("Duplicate signer fingerprints are ambiguous in this proof.")
    if network == "test" and any(
        key.derivation[:2] != [0x80000030, 0x80000001] for key in keys
    ):
        raise ProbeError("Test wallet signers must use BIP48 coin type 1'.")

    return WalletRecord(
        descriptor=descriptor,
        threshold=threshold,
        network=network,
        restrictions=restrictions,
        reference_status=_reference_status(descriptor_text, reference, network),
    )


def _hwi_path(executable: str) -> str:
    found = shutil.which(executable)
    if found is None:
        raise ProbeError("HWI not found. Pass --hwi /path/to/the/official/hwi binary.")
    return found


def invoke_hwi(executable: str, chain: str, *arguments: str) -> Any:
    """Run HWI without a shell; never include raw HWI output in errors."""
    try:
        result = subprocess.run(
            [_hwi_path(executable), "--chain", chain, *arguments],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        if result.returncode != 0:
            raise ProbeError("HWI could not complete the request; check the device.")
        data = json.loads(result.stdout)
        if isinstance(data, dict) and "error" in data:
            raise ProbeError("HWI reported a device error; check its unlock state.")
        return data
    except subprocess.TimeoutExpired as exc:
        raise ProbeError("HWI timed out; reconnect or unlock the device.") from exc
    except json.JSONDecodeError as exc:
        raise ProbeError("HWI did not return valid JSON.") from exc


def _key_origin_path(key: Any) -> str:
    parts = []
    for part in key.derivation:
        hardened = part >= 0x80000000
        parts.append(f"{part & 0x7FFFFFFF}{'h' if hardened else ''}")
    return "m/" + "/".join(parts)


def _same_xpub(expected: Any, received: str) -> bool:
    try:
        actual = bip32.HDKey.from_base58(received)
        wanted = expected.key
        if actual.is_private or wanted.is_private:
            return False
        return (
            actual.get_public_key().sec() == wanted.get_public_key().sec()
            and actual.chain_code == wanted.chain_code
            and actual.depth == wanted.depth
            and actual.fingerprint == wanted.fingerprint
            and actual.child_number == wanted.child_number
        )
    except Exception:
        return False


def probe_devices(record: WalletRecord, executable: str, chain: str) -> list[str]:
    devices = invoke_hwi(executable, chain, "enumerate")
    if not isinstance(devices, list):
        raise ProbeError("HWI enumeration returned an unexpected response.")
    statuses: list[str] = []
    for device in devices:
        if not isinstance(device, dict):
            statuses.append("Unrecognized USB response; no match claimed.")
            continue
        model = "".join(
            char
            for char in str(device.get("model") or device.get("type") or "Device")
            if char.isprintable()
        )[:40] or "Device"
        if device.get("error"):
            statuses.append(f"{model}: detected but unavailable or locked.")
            continue
        fingerprint = str(device.get("fingerprint") or "").lower()
        dev_type = device.get("type")
        dev_path = device.get("path")
        if not (dev_type and dev_path and len(fingerprint) == 8):
            statuses.append(f"{model}: no usable public identity yet.")
            continue
        possible = [
            (index, key)
            for index, key in enumerate(record.keys, start=1)
            if key.fingerprint.hex() == fingerprint
        ]
        if not possible:
            statuses.append(f"{model}: not a signer in this BSMS file.")
            continue
        index, key = possible[0]
        try:
            response = invoke_hwi(
                executable,
                chain,
                "--device-type",
                str(dev_type),
                "--device-path",
                str(dev_path),
                "getxpub",
                _key_origin_path(key),
            )
            if not isinstance(response, dict) or not isinstance(response.get("xpub"), str):
                statuses.append(f"{model}: signer {index} could not be verified.")
            elif _same_xpub(key, response["xpub"]):
                statuses.append(
                    f"{model}: signer {index} of {len(record.keys)} public xpub matched "
                    "(not a signing test)."
                )
            else:
                statuses.append(f"{model}: fingerprint matched, but xpub DID NOT MATCH.")
        except ProbeError:
            statuses.append(f"{model}: signer {index} could not be verified (device error).")
    return statuses


def _validate_chain(record: WalletRecord, chain: str) -> None:
    if record.network == "main":
        raise ProbeError("This test-only release will not probe or fund a mainnet wallet.")
    if record.network == "test" and chain in ("testnet4", "signet", "test"):
        return
    if record.network == "regtest" and chain == "regtest":
        return
    raise ProbeError("Selected HWI chain conflicts with the BSMS address encoding.")


def funding_address(record: WalletRecord, chain: str) -> str:
    """Return an address only when the test descriptor and reference agree."""
    _validate_chain(record, chain)
    if record.network != "test" or chain not in ("testnet4", "signet"):
        raise ProbeError("Funding-address output supports Testnet4 or Signet only.")
    if record.reference_status != "verified":
        raise ProbeError(
            "Reference address is not verified against the literal descriptor; "
            "no funding address will be shown."
        )
    return record.descriptor.derive(0).address(NETWORKS["test"])


def _print_wallet(record: WalletRecord) -> None:
    print(f"BSMS policy: {record.threshold} of {len(record.keys)} native-SegWit multisig")
    if record.network == "test":
        print(
            "Address encoding: tb1 (shared by Testnet4, Signet, and legacy testnet; "
            "the file does not establish which chain holds coins)."
        )
    else:
        print(f"Address network: {record.network}")
    if record.reference_status == "verified":
        print("Reference address: VERIFIED against the literal descriptor.")
    elif record.reference_status == "receive-branch-only":
        print(
            "Reference address: MISMATCH with literal descriptor; it matches "
            "a /0/0 receive-branch convention. Not verified for sending."
        )
    else:
        print("Reference address: MISMATCH. Not verified for sending.")
    print("Mode: read-only; no transaction signing or broadcasting.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect_cmd = commands.add_parser("inspect", help="Inspect BSMS policy offline.")
    inspect_cmd.add_argument("bsms", type=Path)
    devices_cmd = commands.add_parser("devices", help="Find matching USB signers via HWI.")
    devices_cmd.add_argument("bsms", type=Path)
    devices_cmd.add_argument(
        "--hwi", default="hwi", help="Path to HWI or a compatible emulator adapter."
    )
    devices_cmd.add_argument(
        "--chain", choices=["testnet4", "signet", "test", "regtest"], required=True,
        help="Select the actual chain; HWI 3.2.0 supports testnet4.",
    )
    funding_cmd = commands.add_parser(
        "funding-address", help="Show first verified test-wallet address for a faucet."
    )
    funding_cmd.add_argument("bsms", type=Path)
    funding_cmd.add_argument("--chain", choices=["testnet4", "signet"], required=True)
    args = parser.parse_args(argv)
    try:
        record = load_bsms(args.bsms)
        _print_wallet(record)
        if args.command == "devices":
            _validate_chain(record, args.chain)
            print(f"Selected HWI chain: {args.chain} (explicit; not inferred from tb1).")
            print("Checking USB devices (read-only)...")
            statuses = probe_devices(record, args.hwi, args.chain)
            if not statuses:
                print("No devices found. Connect and unlock a test device.")
            for status in statuses:
                print(status)
        elif args.command == "funding-address":
            address = funding_address(record, args.chain)
            print(f"Selected chain: {args.chain} (explicit; not inferred from tb1).")
            print(f"First verified test-wallet address: {address}")
            print(
                "Confirm this address independently on your test signers and "
                "confirm they can sign before requesting test sats."
            )
        return 0
    except ProbeError as exc:
        print(f"Stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())