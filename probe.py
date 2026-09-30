"""Read-only BSMS and USB signer discovery proof. No transaction operations."""

from __future__ import annotations

import argparse
import json
import re
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

from network_config import NETWORKS as CHAIN_CONFIGS, for_record_network

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
    reference_address: str = ""
    descriptor_text: str = ""
    change_descriptor: Descriptor | None = None
    # The checksum of the descriptor as the file gave it, computed rather than
    # trusted, plus whether the file actually carried one. Sparrow's BSMS export
    # omits the checksum that its own PDF backup prints, so showing this lets the
    # owner compare the two documents by eye.
    descriptor_checksum: str = ""
    checksum_supplied: bool = False

    @property
    def keys(self) -> list[Any]:
        return self.descriptor.keys


def _network_for_address(address: str) -> str:
    for config in CHAIN_CONFIGS.values():
        if address.startswith(config.address_prefix):
            return config.record_network  # tb1 is ambiguous; GUI selects Testnet4.
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
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ProbeError("Could not read the BSMS file.") from exc
    except UnicodeError as exc:
        raise ProbeError("BSMS file must be UTF-8 text.") from exc
    return parse_bsms(text)


def parse_bsms(text: str) -> WalletRecord:
    """Parse a BSMS record in memory so GUI uploads never touch disk."""
    if len(text.encode("utf-8")) > MAX_BSMS_BYTES:
        raise ProbeError("BSMS file is unexpectedly large.")
    lines = text.lstrip("\ufeff").splitlines()
    if len(lines) != 4 or lines[0] != "BSMS 1.0":
        raise ProbeError("Expected a four-line BSMS 1.0 wallet record.")
    descriptor_field, restrictions, reference = lines[1:]
    if descriptor_field.count("#") > 1:
        raise ProbeError("This descriptor carries more than one checksum.")
    if "#" in descriptor_field:
        descriptor_text, supplied_checksum = descriptor_field.rsplit("#", 1)
        try:
            if descriptor_checksum(descriptor_text) != supplied_checksum:
                raise ProbeError("Descriptor checksum mismatch.")
        except ProbeError:
            raise
        except Exception as exc:
            raise ProbeError("Descriptor checksum could not be checked.") from exc
    else:
        # A checksum is optional: Nunchuk writes one, Sparrow does not. Nothing is
        # weakened by accepting its absence, because the reference address below
        # must still derive from this exact descriptor and a mismatch stops the
        # wallet outright -- which catches the transcription errors a checksum
        # would, and does so against an independently supplied address.
        descriptor_text = descriptor_field

    change_descriptor = None
    if restrictions == "No path restrictions":
        receive_descriptor_text = descriptor_text
    elif restrictions == "/0/*,/1/*" and "/**" in descriptor_text:
        # BIP 129 descriptor templates use /** with explicit derivation-path
        # restrictions. Expand only the conventional receive/change pair; do
        # not infer a change path from a receive-only wildcard.
        if descriptor_text.count("/**") < 2:
            raise ProbeError("BSMS receive/change template is incomplete.")
        receive_descriptor_text = descriptor_text.replace("/**", "/0/*")
        change_descriptor_text = descriptor_text.replace("/**", "/1/*")
        try:
            change_descriptor = Descriptor.from_string(change_descriptor_text)
        except Exception as exc:
            raise ProbeError("BSMS change descriptor template is invalid.") from exc
    elif restrictions == "/0/*,/1/*":
        # Sparrow states the restrictions and ALSO writes them into the descriptor,
        # as <0;1>/* or explicit /0/* and /1/* paths. The branches are declared in
        # the descriptor itself, so it is used exactly as given and the change
        # branch is resolved from it rather than from this line.
        receive_descriptor_text = descriptor_text
    else:
        raise ProbeError(
            "This version supports either 'No path restrictions' or the explicit "
            "BSMS receive/change restrictions '/0/*,/1/*'."
        )
    network = _network_for_address(reference)
    try:
        script.address_to_scriptpubkey(reference)  # Validate address encoding.
        descriptor = Descriptor.from_string(receive_descriptor_text)
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
    if change_descriptor is not None:
        change_keys = change_descriptor.keys
        if (not change_descriptor.wsh or change_descriptor.sh
            or not isinstance(change_descriptor.miniscript, Multi)
            or change_descriptor.miniscript.args[0].num != threshold
            or len(change_keys) != len(keys)
            or sorted(key.key.to_base58() for key in change_keys)
               != sorted(key.key.to_base58() for key in keys)):
            raise ProbeError("BSMS receive and change descriptors do not use the same multisig keys.")
    if len({key.fingerprint for key in keys}) != len(keys):
        raise ProbeError("Duplicate signer fingerprints are ambiguous in this proof.")
    if network in ("test", "main"):
        config = for_record_network(network)
        if any(key.derivation[:2] != [0x80000030, config.bip48_coin_type]
               for key in keys):
            raise ProbeError(
                f"{config.label} signers must use BIP48 coin type "
                f"{config.bip48_coin_type & 0x7FFFFFFF}'."
            )

    return WalletRecord(
        descriptor=descriptor,
        threshold=threshold,
        network=network,
        restrictions=restrictions,
        reference_status=_reference_status(receive_descriptor_text, reference, network),
        reference_address=reference,
        descriptor_text=receive_descriptor_text,
        change_descriptor=change_descriptor,
        descriptor_checksum=descriptor_checksum(descriptor_text),
        checksum_supplied="#" in descriptor_field,
    )


def _hwi_path(executable: str) -> str:
    if getattr(sys, "frozen", False):
        bundled = Path(sys.executable).with_name("hwi")
        if bundled.is_file():
            return str(bundled)
        # A packaged build must never fall through to a PATH search: a
        # substituted binary would then be executed by the app. The device
        # bridge is broken either way, and failing loudly is the safe half.
        raise ProbeError(
            "The bundled hardware-wallet tool is missing from this installation."
        )
    found = shutil.which(executable)
    if found is None:
        raise ProbeError("HWI not found. Pass --hwi /path/to/the/official/hwi binary.")
    return found


_PATH_LIKE = re.compile(r"(/\S+|[A-Za-z]:\\\S+)")
DEFAULT_HWI_TIMEOUT_SECONDS = 60
DEVICE_AUTH_TIMEOUT_SECONDS = 180
SIGN_TIMEOUT_SECONDS = 600


def _hwi_reason(text: str) -> str:
    """The first useful line of HWI output, made safe to show.

    HWI says things like "Device not found" or "Please open the Bitcoin app",
    which is exactly what a person needs to hear when a device will not connect.
    It never carries keys, but it can carry paths, so collapse anything that
    looks like a path, drop control characters and cap the length.
    """
    lines = [" ".join(line.split()) for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return ""
    if lines[0].startswith("Traceback (most recent call last)"):
        # A crash rather than a device message. Only the final line names the
        # fault; repeating "Traceback (most recent call last):" tells nobody
        # anything, and that is exactly what a locked Trezor used to produce.
        reason = lines[-1]
    else:
        reason = lines[0]
    reason = _PATH_LIKE.sub("<path>", reason)
    reason = "".join(char for char in reason if char.isprintable())
    return reason[:160]


def invoke_hwi(executable: str, chain: str, *arguments: str,
               stdin_command: str | None = None,
               timeout_seconds: int = DEFAULT_HWI_TIMEOUT_SECONDS) -> Any:
    """Run HWI without a shell; optionally send a sensitive command on stdin.

    HWI 3.2.0's --stdin mode appends a shlex-parsed command from standard input.
    A signing PSBT must stay out of argv, where same-user process listings can
    expose it. Only the fixed 'signtx <base64>' form is sent by this app.
    """
    try:
        options = {"input": stdin_command} if stdin_command is not None else {}
        result = subprocess.run(
            [_hwi_path(executable), "--chain", chain, *arguments],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            **options,
        )
        if result.returncode != 0:
            reason = _hwi_reason(result.stderr) or _hwi_reason(result.stdout)
            raise ProbeError("HWI could not complete the request: " + reason
                             if reason else
                             "HWI could not complete the request; check the device.")
        data = json.loads(result.stdout)
        if isinstance(data, dict) and "error" in data:
            reason = _hwi_reason(str(data.get("error")))
            raise ProbeError("HWI reported a device error: " + reason
                             if reason else
                             "HWI reported a device error; check its unlock state.")
        return data
    except subprocess.TimeoutExpired as exc:
        raise ProbeError("HWI timed out; reconnect or unlock the device.") from exc
    except json.JSONDecodeError as exc:
        raise ProbeError("HWI did not return valid JSON.") from exc


def sign_psbt_with_device(executable: str, chain: str, device_type: str,
                          device_path: str, psbt_base64: str) -> str:
    """Ask one hardware device to add its signature, returning the updated PSBT.

    The device shows the destination, amount and fee on its own screen and the owner
    approves it there; this app cannot bypass that, which is the point.
    """
    if (not isinstance(psbt_base64, str) or len(psbt_base64) > 2_000_000
            or not re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", psbt_base64)):
        raise ProbeError("The transaction sent to the device is malformed.")
    response = invoke_hwi(
        executable, chain,
        "--device-type", str(device_type), "--device-path", str(device_path),
        "--stdin", stdin_command="signtx " + psbt_base64 + "\n",
        timeout_seconds=SIGN_TIMEOUT_SECONDS,
    )
    if not isinstance(response, dict) or not isinstance(response.get("psbt"), str):
        raise ProbeError("The device did not return a signed transaction.")
    return response["psbt"]


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


_DEVICE_BRANDS = {"ledger": "Ledger", "trezor": "Trezor", "coldcard": "Coldcard",
                 "bitbox": "BitBox", "bitbox02": "BitBox02", "digitalbitbox": "Digital BitBox"}
_DEVICE_SHORT = {"s": "S", "x": "X", "t": "T"}


def _device_label(model: str) -> str:
    """ledger_nano_s_plus -> "Ledger Nano S Plus", for a person to read."""
    words = [word for word in re.split(r"[_\s]+", model) if word]
    pretty = []
    for word in words:
        low = word.lower()
        if low in _DEVICE_BRANDS:
            pretty.append(_DEVICE_BRANDS[low])
        elif low in _DEVICE_SHORT:
            pretty.append(_DEVICE_SHORT[low])
        else:
            pretty.append(word.capitalize())
    label = " ".join(pretty)
    return "".join(char for char in label if char.isprintable())[:40] or "Device"


SIGNER_MATCHED = "public xpub matched"

# What to tell the owner, given the device and what HWI said. A generic list of
# tips makes everyone read five things when only one applies; the owner's own
# complaint was that nobody would work out that a Ledger needs a particular app
# opened on it. Each entry is (device keyword, reason keywords, instruction) and
# the reason must match, so an unrelated USB fault never gets advice that is wrong.
_DEVICE_ADVICE: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("ledger", ("open failed",),
     "Close Ledger Live and Nunchuk if they are using the device. Reconnect the Ledger, unlock it, open the Bitcoin Testnet app, then choose Look for more devices."),
    ("ledger", ("bitcoin", "5515", "locked", "lock"),
     "On the Ledger itself: unlock it, then open the Bitcoin Testnet app."),
    ("jade", ("unlock", "pin", "recovery", "wallet", "auth"),
     "On the Jade itself: enter your PIN. This app never receives it."),
    ("trezor", ("lock", "pin", "passphrase", "bootloader"),
     "On the Trezor itself: unlock it, then try again."),
    ("coldcard", ("lock", "pin"),
     "On the Coldcard itself: unlock it, then try again."),
    ("bitbox", ("lock", "pin"),
     "On the BitBox itself: unlock it, then try again."),
)


def device_advice(device_type: str, reason: str) -> str:
    """A short instruction for the owner, or "" when HWI's words are enough."""
    kind = (device_type or "").lower()
    said = (reason or "").lower()
    for keyword, triggers, instruction in _DEVICE_ADVICE:
        if keyword in kind and any(trigger in said for trigger in triggers):
            return instruction
    return ""


def devices_need_attention(statuses: list[str]) -> bool:
    """True when the owner still has something to do.

    No device at all, or a device that could not be read or did not match, all
    warrant the troubleshooting list. A device that matched needs nothing from them.
    """
    return not statuses or any(SIGNER_MATCHED not in status for status in statuses)


def probe_devices_detailed(record: WalletRecord, executable: str, chain: str) -> dict:
    """Enumerate devices: readable statuses, plus which ones can actually sign."""
    detailed: dict[str, list] = {"statuses": [], "signable": []}
    _probe_devices_into(record, executable, chain, detailed)
    return detailed


def probe_devices(record: WalletRecord, executable: str, chain: str) -> list[str]:
    return probe_devices_detailed(record, executable, chain)["statuses"]


def _probe_devices_into(record: WalletRecord, executable: str, chain: str,
                        detailed: dict) -> None:
    # HWI's Jade enumeration constructs JadeClient and runs auth_user(), which
    # can require two PIN interactions on the small device screen. The normal
    # one-minute transport bound would interrupt a careful operator mid-PIN.
    devices = invoke_hwi(executable, chain, "enumerate",
                         timeout_seconds=DEVICE_AUTH_TIMEOUT_SECONDS)
    if not isinstance(devices, list):
        raise ProbeError("HWI enumeration returned an unexpected response.")
    statuses: list[str] = detailed["statuses"]
    signable: list[dict] = detailed["signable"]
    for device in devices:
        if not isinstance(device, dict):
            statuses.append("Unrecognized USB response; no match claimed.")
            continue
        model = _device_label(str(device.get("model") or device.get("type") or "Device"))
        if device.get("error"):
            # HWI knows exactly what is wrong -- "Ledger is not in either the
            # Bitcoin or Bitcoin Testnet app", for instance -- and replacing that
            # with a guess about locking sent the owner looking for the wrong fault.
            reason = _hwi_reason(str(device.get("error"))) or "the device reported an error"
            advice = device_advice(str(device.get("type") or model), reason)
            statuses.append(f"{model}: detected, but not readable. {reason}"
                            + (f" {advice}" if advice else ""))
            continue
        fingerprint = str(device.get("fingerprint") or "").lower()
        dev_type = device.get("type")
        dev_path = device.get("path")
        if not (dev_type and dev_path and len(fingerprint) == 8):
            advice = device_advice(str(dev_type or model), "unlock pin")
            statuses.append(f"{model}: no usable public identity yet."
                            + (f" {advice}" if advice else ""))
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
                timeout_seconds=DEVICE_AUTH_TIMEOUT_SECONDS,
            )
            if not isinstance(response, dict) or not isinstance(response.get("xpub"), str):
                statuses.append(f"{model}: signer {index} could not be verified.")
            elif _same_xpub(key, response["xpub"]):
                statuses.append(
                    f"{model}: signer {index} of {len(record.keys)} {SIGNER_MATCHED} "
                    "(not a signing test)."
                )
                # A matched device is one that can add a signature.
                signable.append({
                    "type": str(dev_type), "path": str(dev_path), "model": model,
                    "signer": index, "keys": len(record.keys),
                    "fingerprint": fingerprint,
                })
            else:
                statuses.append(f"{model}: fingerprint matched, but xpub DID NOT MATCH.")
        except ProbeError as exc:
            reason = _hwi_reason(str(exc)) or "device error"
            statuses.append(f"{model}: signer {index} could not be verified ({reason}).")


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
