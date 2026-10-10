"""Read-only BSMS and USB signer discovery proof. No transaction operations."""

from __future__ import annotations

import argparse
import base64
import json
import re
import secrets
import subprocess
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from embit import bip32, compact, ec, script
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
        #
        # CT-89: both branches are expanded from this one template, so they
        # carry the same signer set and threshold by construction -- a BSMS
        # record cannot express a change branch that uses different keys. The
        # `if` that used to claim to check for one could therefore never fire,
        # and a check no accepted input can trip is a claim rather than a
        # control, so it was deleted. test_probe.py pins the invariant that
        # makes it unnecessary, and CONTROLS.md records that nothing is
        # claimed here.
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
    if not 1 <= threshold <= len(keys) or not 2 <= len(keys) <= 3:
        raise ProbeError("This app supports multisig wallets with two or three keys only.")
    if any(not key.is_extended or key.is_private or key.origin is None for key in keys):
        raise ProbeError("Every signer needs a public xpub and key origin.")
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


EXPECTED_HWI_VERSION = "3.2.0"
# argparse prints '%(prog)s <version>' and prog is the basename of argv[0], so
# the line is not one fixed string across the three ways this app starts the
# helper. Exact membership in this set, not a substring test: a planted binary
# whose whole vocabulary is 'hwi-3.2.0' used to pass an `in` check.
_HWI_VERSION_LINES = frozenset({
    f"hwi {EXPECTED_HWI_VERSION}",
    f"hwi.exe {EXPECTED_HWI_VERSION}",
    f"hwi_entry.py {EXPECTED_HWI_VERSION}",
})

# Byte pins for the third-party package the in-tree entry point imports.
# Keyed by module; the files are hwilib/__init__.py and hwilib/_cli.py.
# Source mode runs scripts/hwi_entry.py under the running interpreter, so there
# is no helper binary left to substitute — the remaining swap is the hwilib
# those pins cover (CT-49).
HWI_PAYLOAD_PINS: dict[str, str] = {
    "hwilib": "3945f7ed877a64ef367741892f67662b48194ed73fc6f953bc640897623e0fc9",
    "hwilib._cli": "c0d83c4d9a90fadba88ce554dcb45744d92c3ce04dbcecd98a7c43d4f9bfe35e",
}
# Those two pins are 2 of the 115 .py files the distribution ships, so a
# poisoned hwilib/devices/trezor.py used to pass the check and then run the
# moment the helper imported the package (CT-73). This manifest records a digest
# for every file in the distribution — 157 of them in 3.2.0 — and the check
# below recomputes the whole set and refuses a missing, added or changed file.
# The two entry pins stay, as the fast pre-check that names the CT-49 surface.
HWI_PAYLOAD_MANIFEST = f"hwi-payload-{EXPECTED_HWI_VERSION}.json"
# A frozen build writes this inside the signed bundle it authenticates —
# Contents/Resources on macOS, where codesign seals it, and beside the helper on
# Windows. An explicitly named helper carries its own, beside itself. It is also
# what the SBOM records for the helper.
HWI_DIGEST_SIDECAR = "hwi.sha256"

_HWI_NO_DIGEST = (
    "The hardware-wallet tool carries no digest for this app to verify. "
    "Refusing to run it."
)
_HWI_NO_PAYLOAD_MANIFEST = (
    "The pinned hardware-wallet library carries no payload manifest. "
    "Refusing to run it."
)
_HWI_PAYLOAD_CHANGED = (
    "The pinned hardware-wallet library does not match the payload this app "
    "expects. Refusing to run it."
)
_HWI_WRONG_DIGEST = (
    "The hardware-wallet tool does not match its recorded digest. "
    "Refusing to run it."
)
_HWI_UNIDENTIFIED = (
    "The hardware-wallet tool could not be identified. "
    "Pass --hwi /path/to/the/official/hwi binary."
)
_HWI_NOT_THE_RELEASE = (
    f"The hardware-wallet tool does not identify as HWI {EXPECTED_HWI_VERSION}. "
    "Pass --hwi /path/to/the/official/hwi binary."
)

_verified_hwi_paths: set[str] = set()


def begin_signing_session() -> None:
    """Drop every cached helper identity, so the next call re-identifies.

    CT-58: the cache used to live for the whole process, so a helper swapped on
    disk after the first check would run unverified for the rest of the session.
    A signing session is the unit the owner experiences, so it is the unit this
    trust decision is bounded by.
    """
    _verified_hwi_paths.clear()


def _in_tree_hwi_entry() -> Path:
    """scripts/hwi_entry.py in this checkout. Source mode only.

    Inside a PyInstaller bundle the helper is the standalone binary beside the
    executable, not a script, and this path is not consulted.
    """
    return Path(__file__).resolve().parent / "scripts" / "hwi_entry.py"


def _hwi_path(executable: str) -> str:
    """The file whose bytes identify the helper.

    Frozen builds ship the tool beside the app as `hwi` (macOS) or `hwi.exe`
    (Windows) and never fall through to a PATH search. Source mode has no
    helper binary at all: it runs the repository's own entry point, so there is
    nothing on PATH to plant. An explicit path is used as given, and must carry
    its own digest sidecar before _verify_hwi_identity will run it.
    """
    if getattr(sys, "frozen", False):
        name = "hwi.exe" if sys.platform == "win32" else "hwi"
        bundled = Path(sys.executable).with_name(name)
        if bundled.is_file():
            return str(bundled)
        # A packaged build must never fall through to a PATH search: a
        # substituted binary would then be executed by the app. The device
        # bridge is broken either way, and failing loudly is the safe half.
        raise ProbeError(
            "The bundled hardware-wallet tool is missing from this installation."
        )
    candidate = Path(executable)
    if candidate.is_absolute() or candidate.parent != Path("."):
        if candidate.is_file():
            return str(candidate)
        raise ProbeError("HWI not found. Pass --hwi /path/to/the/official/hwi binary.")
    entry = _in_tree_hwi_entry()
    if not entry.is_file():
        raise ProbeError(
            "The hardware-wallet tool entry point is missing from this checkout."
        )
    return str(entry)


def _hwi_command(executable: str) -> list[str]:
    """The argv prefix that actually runs the helper.

    Source mode does not execute a helper binary at all: it runs the
    repository's entry point under the interpreter this app is already using.
    That is the same trust model as the frozen bundle's own copy, without a
    binary on disk for a neighbour to replace.
    """
    path = _hwi_path(executable)
    if getattr(sys, "frozen", False):
        return [path]
    candidate = Path(executable)
    if candidate.is_absolute() or candidate.parent != Path("."):
        return [path]
    return [sys.executable, path]


def _hwi_manifest_path(helper_path: str | None = None) -> Path:
    """The manifest of the payload this app is willing to run.

    Source mode reads the committed ``vendor/`` manifest: repository source, the
    same trust root as this file, and never a digest computed from the package
    being checked. A frozen or explicitly named helper carries its own beside
    it, or in Contents/Resources on macOS where the outer signature seals it.
    """
    candidates: list[Path] = []
    if helper_path is not None:
        helper = Path(helper_path)
        candidates.append(helper.with_name(HWI_PAYLOAD_MANIFEST))
        resources = helper.parent.parent / "Resources" / HWI_PAYLOAD_MANIFEST
        if resources != candidates[0]:
            candidates.append(resources)
    elif getattr(sys, "frozen", False):
        helper = Path(sys.executable).with_name("hwi.exe" if sys.platform == "win32" else "hwi")
        candidates.append(helper.with_name(HWI_PAYLOAD_MANIFEST))
        candidates.append(helper.parent.parent / "Resources" / HWI_PAYLOAD_MANIFEST)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return Path(__file__).resolve().parent / "vendor" / HWI_PAYLOAD_MANIFEST


def _hash_hwi_package() -> dict[str, str]:
    """Every file of the installed hwilib, by relative path, hashed.

    ``importlib.util.find_spec`` builds the spec from the finder without
    executing the package, so a poisoned ``__init__.py`` is hashed rather than
    run. That is the whole point of hashing here instead of importing in
    process: the check must not run the code it is about to refuse.
    """
    script = (
        "import hashlib, importlib.util, json, pathlib\n"
        "spec = importlib.util.find_spec('hwilib')\n"
        "roots = list(spec.submodule_search_locations or []) if spec else []\n"
        "if not roots:\n"
        "    raise SystemExit('hwilib is not installed')\n"
        "root = pathlib.Path(roots[0])\n"
        "seen = {}\n"
        "for path in sorted(root.rglob('*')):\n"
        "    if not path.is_file():\n"
        "        continue\n"
        "    relative = path.relative_to(root)\n"
        "    if '__pycache__' in relative.parts or relative.name.endswith('.pyc'):\n"
        "        continue\n"
        "    seen[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()\n"
        "print(json.dumps(seen))\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            **hwi_process_options(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProbeError(_HWI_UNIDENTIFIED) from exc
    if result.returncode != 0:
        raise ProbeError(
            "The pinned hardware-wallet library (hwi " + EXPECTED_HWI_VERSION +
            ") is not installed in this environment. Install it from the "
            "hash-locked source set: python -m pip install --require-hashes -r "
            "requirements-source.lock"
        )
    try:
        seen = json.loads(result.stdout or "")
    except ValueError as exc:
        raise ProbeError(_HWI_UNIDENTIFIED) from exc
    if not isinstance(seen, dict) or not seen:
        raise ProbeError(_HWI_UNIDENTIFIED)
    return {str(name): str(digest) for name, digest in seen.items()}


def _name_payload_differences(missing: list[str], added: list[str],
                              changed: list[str], *, limit: int = 6) -> str:
    """Name what differs, capped, so the refusal stays readable."""
    parts: list[str] = []
    for label, names in (("missing", missing), ("unrecorded", added), ("changed", changed)):
        if not names:
            continue
        shown = ", ".join(names[:limit - len(parts)])
        remaining = len(names) - (limit - len(parts))
        parts.append(f"{label}: {shown}" + (f" (+{remaining} more)" if remaining > 0 else ""))
        if len(parts) >= limit:
            break
    return "; ".join(parts)


def _verify_hwi_payload(manifest_path: Path | None = None) -> None:
    """Refuse a substituted hwilib before it can see an xpub or a PSBT.

    The in-tree entry point is repository source; the code that can be swapped
    out from under a running interpreter is the third-party package it imports.
    The whole package is checked here — CT-73: pinning hwilib/__init__.py and
    hwilib/_cli.py left 113 of 115 modules unchecked, so a poisoned
    hwilib/devices/trezor.py passed and then ran on import. A file that is
    missing, a file that was added, and a file whose bytes changed are all
    refused, so a new module cannot arrive unnoticed either.
    """
    path = manifest_path or _hwi_manifest_path()
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        expected = manifest["files"]
        if not isinstance(expected, dict) or not expected:
            raise ValueError("the manifest records no files")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ProbeError(_HWI_NO_PAYLOAD_MANIFEST) from exc

    seen = _hash_hwi_package()
    for module, digest in HWI_PAYLOAD_PINS.items():
        name = "__init__.py" if "." not in module else module.rpartition(".")[2] + ".py"
        if seen.get(name) != digest:
            raise ProbeError(_HWI_WRONG_DIGEST)
    missing = sorted(set(expected) - set(seen))
    added = sorted(set(seen) - set(expected))
    changed = sorted(name for name in set(expected) & set(seen)
                     if expected[name] != seen[name])
    if missing or added or changed:
        raise ProbeError(
            _HWI_PAYLOAD_CHANGED + " ("
            + _name_payload_differences(missing, added, changed) + ")"
        )


def _hwi_sidecars(path: str) -> list[Path]:
    """Every recorded digest for this helper that is actually present.

    macOS refuses to seal an .app that carries a non-code file in
    Contents/MacOS, so a frozen Mac build records the digest in
    Contents/Resources and the outer signature covers it there. Windows has no
    such rule and keeps the sidecar beside the helper; an explicitly named
    helper carries its own. All present candidates must agree with the
    helper's bytes — two sidecars that disagree are a tampering signal, not a
    choice.
    """
    helper = Path(path)
    candidates = [helper.with_name(HWI_DIGEST_SIDECAR)]
    # .../App.app/Contents/MacOS/hwi -> .../App.app/Contents/Resources/hwi.sha256
    resources = helper.parent.parent / "Resources" / HWI_DIGEST_SIDECAR
    if resources != candidates[0]:
        candidates.append(resources)
    return [candidate for candidate in candidates if candidate.is_file()]


def _verify_hwi_bytes(path: str) -> None:
    """Compare a standalone helper against a digest that is not its own claim.

    A frozen build's sidecar sits inside the signed bundle it authenticates, so
    replacing the helper means breaking that signature first. An explicitly
    named helper is refused outright without one. Source mode runs no helper
    binary at all — see _verify_hwi_payload for the surface it does pin.
    """
    sidecars = _hwi_sidecars(path)
    if not sidecars:
        raise ProbeError(_HWI_NO_DIGEST)
    actual = sha256(Path(path).read_bytes()).hexdigest()
    for sidecar in sidecars:
        recorded = sidecar.read_text(encoding="utf-8").strip().split()
        if not recorded:
            raise ProbeError(_HWI_NO_DIGEST)
        if recorded[0].lower() != actual:
            raise ProbeError(_HWI_WRONG_DIGEST)


def _verify_hwi_identity(path: str, command: list[str] | None = None) -> None:
    """Refuse a helper that is not the bytes this app expects to run.

    Byte identity comes first and is not something the helper gets to assert:
    a standalone helper must match every digest sidecar that is present — one
    beside it in source and loose layouts, and one in Contents/Resources when a
    frozen macOS bundle keeps it out of Contents/MacOS — and source mode runs
    the repository's own entry point and pins the hwilib it imports.

    Only then does the helper say what version it is, and it has to say it
    exactly (CT-29, CT-49).
    """
    if path in _verified_hwi_paths:
        return
    argv = list(command) if command is not None else [path]
    # A two-element prefix is [interpreter, entry]: the in-tree source-mode
    # helper, whose substitution surface is the package it imports. Anything
    # else is a standalone binary whose own bytes are what we pin.
    if len(argv) >= 2:
        _verify_hwi_payload()
    else:
        _verify_hwi_bytes(path)
    try:
        result = subprocess.run(
            [*argv, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            **hwi_process_options(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProbeError(_HWI_UNIDENTIFIED) from exc
    output = (result.stdout or "") + (result.stderr or "")
    first_line = output.strip().splitlines()[0].strip() if output.strip() else ""
    if result.returncode != 0 or first_line not in _HWI_VERSION_LINES:
        raise ProbeError(_HWI_NOT_THE_RELEASE)
    _verified_hwi_paths.add(path)


def verify_hwi_identity_for_command(executable: str) -> list[str]:
    """Resolve, verify and return the argv prefix that runs the helper.

    Callers that start the tool outside invoke_hwi — the build-time capability
    probe in desktop.py — go through here so nothing runs before its bytes and
    its version line have been checked.
    """
    path = _hwi_path(executable)
    command = _hwi_command(executable)
    _verify_hwi_identity(path, command)
    return command


_PATH_LIKE = re.compile(r"(/\S+|[A-Za-z]:\\\S+)")
DEFAULT_HWI_TIMEOUT_SECONDS = 60
DEVICE_AUTH_TIMEOUT_SECONDS = 180
SIGN_TIMEOUT_SECONDS = 600


def hwi_process_options() -> dict[str, Any]:
    """Keep console HWI helpers invisible when launched by the Windows GUI."""
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}


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
        options = hwi_process_options()
        if stdin_command is not None:
            options["input"] = stdin_command
        path = _hwi_path(executable)
        command = _hwi_command(executable)
        _verify_hwi_identity(path, command)
        result = subprocess.run(
            [*command, "--chain", chain, *arguments],
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


def _bitcoin_message_digest(message: bytes) -> bytes:
    """BIP-322/electrum message digest: sha256d of the Bitcoin message envelope."""
    payload = b"\x18Bitcoin Signed Message:\n" + compact.to_bytes(len(message)) + message
    return sha256(sha256(payload).digest()).digest()


def _der_from_message_signature(raw: Any) -> bytes:
    """Normalise HWI's message signature to DER, whether hex/base64 and compact/DER."""
    text = raw.strip() if isinstance(raw, str) else ""
    blobs: list[bytes] = []
    try:
        blobs.append(bytes.fromhex(text))
    except ValueError:
        pass
    try:
        blobs.append(base64.b64decode(text, validate=True))
    except Exception:
        pass
    for blob in blobs:
        if not blob:
            continue
        if 8 <= len(blob) <= 72 and blob[0] == 0x30:
            return blob
        if len(blob) == 65:
            return _compact_to_der(blob[1:33], blob[33:65])
    raise ProbeError("This device did not return a usable signature. Nothing was sent.")


def _compact_to_der(r: bytes, s: bytes) -> bytes:
    def _int(value: bytes) -> bytes:
        data = value.lstrip(b"\x00") or b"\x00"
        if data[0] & 0x80:
            data = b"\x00" + data
        return b"\x02" + bytes([len(data)]) + data

    body = _int(r) + _int(s)
    return b"\x30" + bytes([len(body)]) + body


def _verify_message_signature(pubkey_sec: bytes, message: bytes, signature: Any) -> bool:
    try:
        der = _der_from_message_signature(signature)
        parsed = ec.Signature.parse(der)
        return bool(ec.PublicKey.parse(pubkey_sec).verify(
            parsed, _bitcoin_message_digest(message)))
    except ProbeError:
        raise
    except Exception:
        return False


def prove_signer_holds_key(record: WalletRecord, executable: str, chain: str,
                           device_type: str, device_path: str, signer: int) -> None:
    """Require a signature over a fresh challenge before any PSBT is sent.

    A counterfeit USB device can echo a previously observed account xpub and
    then receive the payment PSBT (destination, amount, cosigners). Matching
    public identity is not proof of the private key. A random message signature
    verified against the wallet's known public key is (CT-14).
    """
    if type(signer) is not int or not 1 <= signer <= len(record.keys):
        raise ProbeError("Check this signing device again before approving the payment.")
    key = record.keys[signer - 1]
    challenge = "Bitcoin Easy Signer key proof " + secrets.token_hex(16)
    # Sign at the first receive address, not the account node. Trezor (and
    # OneKey on Trezor firmware) refuse signmessage on an all-hardened BIP48
    # account path with "forbidden key path"; ordinary address paths are
    # allowed. The child is under the same account xpub getxpub already
    # matched, so a valid signature still proves this device holds the key.
    address_path = _key_origin_path(key) + "/0/0"
    response = invoke_hwi(
        executable, chain, "--device-type", device_type, "--device-path", device_path,
        "signmessage", challenge, address_path,
        timeout_seconds=DEVICE_AUTH_TIMEOUT_SECONDS,
    )
    signature = response.get("signature") if isinstance(response, dict) else None
    pubkey = key.key.child(0).child(0).get_public_key().sec()
    proved = False
    if isinstance(signature, str):
        try:
            proved = _verify_message_signature(pubkey, challenge.encode("utf-8"), signature)
        except ProbeError:
            proved = False
    if not proved:
        raise ProbeError(
            "This device did not prove it holds the wallet key. Nothing was sent."
        )


def verify_signer_device(record: WalletRecord, executable: str, chain: str,
                         device_type: str, device_path: str, signer: int) -> None:
    """Bind the selected HWI path to its wallet key immediately before signing."""
    # CT-58: every signing session re-identifies the helper from its bytes.
    begin_signing_session()
    if type(signer) is not int or not 1 <= signer <= len(record.keys):
        raise ProbeError("Check this signing device again before approving the payment.")
    key = record.keys[signer - 1]
    response = invoke_hwi(
        executable, chain, "--device-type", device_type, "--device-path", device_path,
        "getxpub", _key_origin_path(key),
        timeout_seconds=DEVICE_AUTH_TIMEOUT_SECONDS,
    )
    if not isinstance(response, dict) or not isinstance(response.get("xpub"), str) \
            or not _same_xpub(key, response["xpub"]):
        raise ProbeError("This device no longer matches the wallet. Check devices again.")
    # CT-14: public identity is not private-key possession. Prove the key
    # before the caller hands over the payment PSBT.
    prove_signer_holds_key(record, executable, chain, device_type, device_path, signer)


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


def _hwi_device_label(device: dict) -> str:
    """Prefer HWI's human-readable vendor/model label when it is safe to show."""
    reported = device.get("label")
    if (isinstance(reported, str)
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 .+()_-]{0,39}", reported)):
        return reported
    return _device_label(str(device.get("model") or device.get("type") or "Device"))


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
        model = _hwi_device_label(device)
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
        # Only the command-line helpers are practice-only. The GUI does check
        # and sign mainnet wallets for the Phase 5 dry run, so saying "this
        # test-only release" here described the wrong product.
        raise ProbeError(
            "This command-line check supports practice wallets only. "
            "Use the app itself to check signers for a mainnet wallet."
        )
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
