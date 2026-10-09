"""Read-only BSMS and USB signer discovery proof. No transaction operations."""

from __future__ import annotations

import argparse
import base64
import json
import re
import secrets
import subprocess
import sys
import sysconfig
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


def _key_material(key: Any) -> tuple[bytes, bytes]:
    """The identity of a signer key: its public point and its chain code.

    A base58 string is a *spelling*, not a key: the same secp256k1 point and
    chain code serialize to different text under each network version
    (``xpub``/``tpub``/``ypub``/``zpub``), and two such strings compare unequal.
    Anything that asks "is this the same signer?" must compare these bytes
    (CT-72), the same pair `_same_xpub` already binds a device to.
    """
    inner = key.key
    return (inner.key.sec(), inner.chain_code)


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
    # Exactly one leading BOM is removed. load_bsms already reads the file with
    # utf-8-sig, so the only BOM this can meet is the one a GUI upload supplies;
    # `lstrip` was a character-set strip, so a record that carried two BOMs was
    # silently accepted as if it were well-formed text (CT-114).
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines()
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
    if not 1 <= threshold <= len(keys) or not 2 <= len(keys) <= 3:
        raise ProbeError("This app supports multisig wallets with two or three keys only.")
    if any(not key.is_extended or key.is_private or key.origin is None for key in keys):
        raise ProbeError("Every signer needs a public xpub and key origin.")
    if change_descriptor is not None:
        change_keys = change_descriptor.keys
        if (not change_descriptor.wsh or change_descriptor.sh
            or not isinstance(change_descriptor.miniscript, Multi)
            or change_descriptor.miniscript.args[0].num != threshold
            or len(change_keys) != len(keys)
            or sorted(_key_material(key) for key in change_keys)
               != sorted(_key_material(key) for key in keys)):
            raise ProbeError("BSMS receive and change descriptors do not use the same multisig keys.")
    if len({key.fingerprint for key in keys}) != len(keys):
        raise ProbeError("Duplicate signer fingerprints are ambiguous in this proof.")
    # CT-72: two origin fingerprints can label the SAME xpub. The receive list
    # then reads as an honest m-of-n with two cosigner cards while one device
    # approval finalizes it, so the screen would show a quorum that does not
    # exist. A fingerprint is the signer's label and a base58 string is a
    # spelling; the key bytes are the signer, so only the bytes can answer "how
    # many keys must approve this payment". Comparing serializations let the
    # same key through as xpub next to tpub, so this compares the material
    # itself — public point plus chain code — which no re-spelling can change.
    if len({_key_material(key) for key in keys}) != len(keys):
        raise ProbeError(
            "The same signer key is listed more than once in this wallet file. "
            "A multisig proof must name each cosigner key exactly once."
        )
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

# CT-90 (whole tree): the two files above are what ran, not what imported.
# `hwilib/commands.py` is imported by the entry point and executed on every
# device call, and it is not one of them; a poisoned sibling module with both
# named files genuine passed the old two-file pin. The whole installed package
# is therefore covered: every source file hwilib ships is listed here by its
# package-relative path and its SHA-256. A file that is missing, altered, or
# added to the package fails the check, so the pin no longer names a subset of
# the code the helper can reach.
#
# Recorded from hwi 3.2.0 (`hwilib.__version__ == "3.2.0"`). Byte-pinning every
# file is deliberate: RECORD cannot be the pinned authority here because it is
# itself a file an attacker with write access to site-packages can rewrite, and
# a rewritten RECORD would then validate a rewritten tree. A literal value in
# this file cannot be rewritten by touching the environment the app inspects.
# `tests/test_hardening_pins.py` recomputes the tree digest from this table, so
# the derivation is executable documentation rather than a remembered number.
HWI_PAYLOAD_MANIFEST: dict[str, str] = {
    "__init__.py": "3945f7ed877a64ef367741892f67662b48194ed73fc6f953bc640897623e0fc9",
    "_base58.py": "dd5d3fc11eae7c81ba2414cd39f6ef5106e9cb3894ae2c1773bf23af46468ad6",
    "_bech32.py": "7080dafd7d9fe20f07d15b10a95a770a14ab48334acd8943e829b412709f2244",
    "_cli.py": "c0d83c4d9a90fadba88ce554dcb45744d92c3ce04dbcecd98a7c43d4f9bfe35e",
    "_gui.py": "b74ac4d73204cee8a943e30fc98c0321a0eabf81f5a9d5954047995b97f8299a",
    "_script.py": "4531b3dc525b1c776398e95a776ef5f38b8a79121e0cda345827e9dc31976422",
    "_serialize.py": "291c5c19c303dd86104914d7a7b0bcc32d8fb6f9a1e0a7d90500b16b5b396bb5",
    "commands.py": "c8a9bc917a90e19ea31db7e9d01d2c8b13f13fbad8b876a9e25d381743e28e06",
    "common.py": "a4d8a88cc284d9a0db9db73c9e977518675ae803bc3b476655de3fb8bd0fdf4f",
    "descriptor.py": "d33fd58edc4a83d926e72b5ae02ce2d381bd1641766f477d0cecefa80c1da2da",
    "devices/__init__.py": "dcf0fcbee38dba8b5da135f36f2664856393beec09fd3b02065f82f18515101d",
    "devices/bitbox02.py": "daf565c88bf5276b2350f2c39c624a054c88f55f7371f7484c5224cc172b1f95",
    "devices/bitbox02_lib/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "devices/bitbox02_lib/bitbox02/__init__.py": "c4d7e877144707d04391aced5edc31be508a3f87ef54ee0724a1aadb36ec4015",
    "devices/bitbox02_lib/bitbox02/bitbox02.py": "4cef48feb1334680dcea72f9608b56ab96e3bfc8aaa00709f45baef78e14fa55",
    "devices/bitbox02_lib/bitbox02/bootloader.py": "3c01220249a0ee25f93b63b90814283cec76b16009da6f2c9ae94ea47c34a6b6",
    "devices/bitbox02_lib/bitbox02/secp256k1.py": "211188addd99feaf0d69cb39ce1d2eb46038b1a4aa04ac511d2c4aa56cb75544",
    "devices/bitbox02_lib/communication/__init__.py": "27a6ebcf635dc37b54270cfa02813873b6bf12dba2e420acb4304c9050f0b840",
    "devices/bitbox02_lib/communication/bitbox_api_protocol.py": "d4d193437f0176257d133d9da3fb432305fb21fc35df2f827107e8458d28aa1f",
    "devices/bitbox02_lib/communication/communication.py": "9d17dac870f6970cbf544656172be83effdfcaf3348d37a44ec154c6b2de63ab",
    "devices/bitbox02_lib/communication/devices.py": "b7df789a1ea9b91ab9b0e47c9f508ce1e4b3fc3121c683e19364d8944aac57f6",
    "devices/bitbox02_lib/communication/generated/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "devices/bitbox02_lib/communication/generated/antiklepto_pb2.py": "002c48b4a60d4ccffed0d11a0c9404042ee25ebfe11eafe363d0eb3e383ad33f",
    "devices/bitbox02_lib/communication/generated/backup_commands_pb2.py": "76a031ae9de53c9cfee71697e9c30ef36e3cdf6aa5c93a0cb6181d94905eb116",
    "devices/bitbox02_lib/communication/generated/bitbox02_system_pb2.py": "da182415ec0a254804a198f239beb09df6f6d5b4c1da059b88f6adc0549878a4",
    "devices/bitbox02_lib/communication/generated/bluetooth_pb2.py": "e1b063fbcae61d5359b0f75ae7e27239e0b1330f13b7fdba49bf6ff48301113e",
    "devices/bitbox02_lib/communication/generated/btc_pb2.py": "0dc0b0ab5c2117d7a276998ef549f84089e4c28e43b3fea0f180f2464f567c97",
    "devices/bitbox02_lib/communication/generated/cardano_pb2.py": "7438e0c6df1a52b61d83ae7b37c508d1abcb23c08d68d7c5a98b97dcd337aa84",
    "devices/bitbox02_lib/communication/generated/common_pb2.py": "9e59c79b7d180c517f2138924317b691312cda06555dc58d5b6e33ff9eb68a65",
    "devices/bitbox02_lib/communication/generated/eth_pb2.py": "f946089b8a3be946efac305e31b074dbedab697614c6df6febaa2a2bdb30bbd8",
    "devices/bitbox02_lib/communication/generated/hww_pb2.py": "be2776cae43bd1cb65ed5d3d9e5c70b98bb61bd641a8cc5d0c25f6268709b3d5",
    "devices/bitbox02_lib/communication/generated/keystore_pb2.py": "7091d1da13a58ff1b137ea60e2613bee2531351d4ba3bbdeef8ea36e54f09598",
    "devices/bitbox02_lib/communication/generated/mnemonic_pb2.py": "c30ee7944adbbac452288b0b7580c9da11e24cf6ba3fb4b42ca5cce259cf4eec",
    "devices/bitbox02_lib/communication/generated/perform_attestation_pb2.py": "4177a19aae7d7b3ffa532606295188ba87475e9650bb4af0ef55906bd8d7e014",
    "devices/bitbox02_lib/communication/generated/system_pb2.py": "52405697ace035f84e1743af4ae4046f550c6de80a10a9ef9af3bad8a3bb9b6e",
    "devices/bitbox02_lib/communication/u2fhid/__init__.py": "20baa5ad6e5175e292a0c3be870b317e000ff1cbbd4430f4ec30d039453a737b",
    "devices/bitbox02_lib/communication/u2fhid/u2fhid.py": "b3eedfb5cc11c918ed0939a184bd5f3bc363a98f9aaa62c48a741b66960ff534",
    "devices/bitbox02_lib/util.py": "631d60ca3190467ca5c128bdb5c6aa1c32568114530844b2f9131e57a249aff4",
    "devices/ckcc/__init__.py": "59722096c55d5add9a829dd5b7c6aa0a59f0d659f580cc5297f7078b8562509f",
    "devices/ckcc/client.py": "11b01d4d2ebd149847cbe055062531347c67f99ae9e79a1eb811e207e5db364f",
    "devices/ckcc/constants.py": "82a07eee60c90522de58c606b4d1e5a6eaae4a32ae2f62e1724bf1dfc9aa8973",
    "devices/ckcc/protocol.py": "161a691512a690c6bed7abdc59cde77dec8d567ea2e2c75f7ff525994602a719",
    "devices/ckcc/sigheader.py": "ad96d00fa79ed58bf6f54dd1f93cf7885046fc87911cae6a9f3a47230a3f71d5",
    "devices/ckcc/utils.py": "e2598d86ae6c1abfac87300edd5965f8358ed1f12f68731fb587f5a8307b9a78",
    "devices/coldcard.py": "0bd86ac44a2ce025ce6472a74a379ae17a76be478bd9efefda1897b2691b165d",
    "devices/digitalbitbox.py": "ff41b1e973df86015cc603ec78f645f36dfc5f7bbf7af6a71fad2fc12900c7b4",
    "devices/jade.py": "b4f569ca53a3fffd1987752ef951f4783b62ac9fc0fe484633b549715400bc5c",
    "devices/jadepy/__init__.py": "8f9d9d1e183f538df910c0319ce02e07028c731c9a5c835b2e254e52b29d124d",
    "devices/jadepy/jade.py": "938ccf984e4023cdce5b22a6177f22f567cf559763c967142036adb9857fe249",
    "devices/jadepy/jade_error.py": "a50a952a33a1924cc9e26fe465270ecfcb21e3d5f55ff3b3e69e697bd0790cbd",
    "devices/jadepy/jade_serial.py": "55bd3c7c9de3751a82f51bba7c18a350597bcc5f1ee667014d8066074fcb0943",
    "devices/jadepy/jade_tcp.py": "9ea17cf844fe568b2add6615cbc52c2079711d1740147fa3fb8df2c6eec8776f",
    "devices/keepkey.py": "17dee77d4863376483ee50a8c23fd8da29eddd7b0afa7383c0afb8889b57701a",
    "devices/ledger.py": "8918c5264206e731ce2fd24ee7d649335cce819fd62acb523bc74f559a47d79b",
    "devices/ledger_bitcoin/__init__.py": "49c97303d77c7a385bb029c05b4c7d16becdf81c2037f06cfc4d9882fb88ae28",
    "devices/ledger_bitcoin/btchip/__init__.py": "c66532426414107c998bd42995a5671235fa191a1d36d84f78689e5263a0773b",
    "devices/ledger_bitcoin/btchip/bitcoinTransaction.py": "53a7f02ab5b82995026f6951d6c55f5610300dbe3c86365d0a814a965e67ae71",
    "devices/ledger_bitcoin/btchip/bitcoinVarint.py": "be2fbf248a1ade9c4b984c336596e107ab2af7935e2aefa58ccd9b06934e0e2a",
    "devices/ledger_bitcoin/btchip/btchip.py": "3996c7340de192ecfe1cd6326da8c92b6ea2d5bddbe8e3ad9cd77fe6957233ad",
    "devices/ledger_bitcoin/btchip/btchipException.py": "4b7826c3ce10ba396346ee293bd63d425feea94747041ebc8ca1faeea08e59d8",
    "devices/ledger_bitcoin/btchip/btchipHelpers.py": "c085af543c5b0117f969415e103fb6895335dd2113e098a54460872c40d10c16",
    "devices/ledger_bitcoin/btchip/btchipUtils.py": "e871f1a9e4c9f78aa368cdbcf6b23b072b49536bf829d1c3870a72081d6c7e8c",
    "devices/ledger_bitcoin/btchip/ledgerWrapper.py": "d9b17848d62d699114562545e2e4de7a734f8a03951eb4bf7cf1c44801795001",
    "devices/ledger_bitcoin/client.py": "8e09cbc9bc72db81e3b6d3375e9ad49bb4ca2326ac3af728ae1bbdf8979efdda",
    "devices/ledger_bitcoin/client_base.py": "c376aabe89bfb19f43df6b498625e3e4877fe42a7d665ad204dd410e27f3adeb",
    "devices/ledger_bitcoin/client_command.py": "cfc24efe646838d6e40de5835926ab3b9aa497055d0788fcb9ab8c5d079b42e0",
    "devices/ledger_bitcoin/client_legacy.py": "6dc42eaff68a93f45a75a6bdc68b4fd40657ac279fffb0f1f50c694ad3edd62a",
    "devices/ledger_bitcoin/command_builder.py": "fe9c18a5f8c0934b67ea72cde0b036e6333e0c4050b9b41a91eefb6b14df5ea3",
    "devices/ledger_bitcoin/errors.py": "43fa7a4f7c85cb7d164753e22e92edcbe8fe7b51018a5042cdc87f3d5f655972",
    "devices/ledger_bitcoin/exception/__init__.py": "3e6ff7c4e337aeee8feae8f33196c5c3f8b7cce4609e1d42ff09bf3624dd8ff0",
    "devices/ledger_bitcoin/exception/device_exception.py": "0801e42c7602be20a80eda5895dd7f1569bb45ad71bdbb4545b0aaae54221796",
    "devices/ledger_bitcoin/exception/errors.py": "a3daa36e873de4070de7906cf66a324472281340e4d33d1e31baad5a9516c2ba",
    "devices/ledger_bitcoin/ledgercomm/__init__.py": "5cb2baf9a3d6af938df804eb26e4fac8a2ef964a17119bdc707b159384628d5b",
    "devices/ledger_bitcoin/ledgercomm/interfaces/__init__.py": "6a1c5fdfd5dc1fe69d7aa24fb94902994eb8fc16b471105d0c7e04e407491b9e",
    "devices/ledger_bitcoin/ledgercomm/interfaces/comm.py": "395909d51b2ae567e8647e654a13543cac0c25330d7aa9b7b58b6a933f3b1afa",
    "devices/ledger_bitcoin/ledgercomm/interfaces/hid_device.py": "43fa3cbf2198526cbbac1220de68f17bd6c23fbcb95e69734160556dfb0968b0",
    "devices/ledger_bitcoin/ledgercomm/interfaces/tcp_client.py": "990281b72bd60264579bbcc941f84b9248223bcb02940daf1a9224ebaab68dbb",
    "devices/ledger_bitcoin/ledgercomm/log.py": "9ee3a4e583c96c0d016dcf065d695228156d6b92082b6d4285018630dc9277d6",
    "devices/ledger_bitcoin/ledgercomm/transport.py": "c93c39c907c2751788bcbba9ddd3a1b6bebf81cc4e0b8920d1b5a5deacffb312",
    "devices/ledger_bitcoin/merkle.py": "32ff9240ffe2b9a573f7ae5233d7d2a8afb7a6213e9bf2440aae2c7a36b7593d",
    "devices/ledger_bitcoin/wallet.py": "965e0f3ebbef143206802ab8b14f5351e692cb627a344ba38f9c06f1110daa54",
    "devices/trezor.py": "225f79cbd04f8d7411bfbc6eccf57d8834c1d027ea4f4fb71f14fbb8dd57528c",
    "devices/trezorlib/__init__.py": "4f36c54a1ef972bb1861c340afdc05d7d2531cb01386b888ddaa68e224e9518f",
    "devices/trezorlib/btc.py": "a5c23a305d4c23601abe7e699dc03fe2fcb852a1d9cf6e5392ff20f4ad8dc48a",
    "devices/trezorlib/client.py": "0d8e185c2339df8b0809c1d454f66162c984d85f7dbd2448f70b5020afb2a273",
    "devices/trezorlib/debuglink.py": "948aa6e6821b3ed39febe12033fec19a72798a8bde45ed71493d7ffb47b7d93d",
    "devices/trezorlib/device.py": "0eb133ba6690c4087c94ed30f8d6901201abc540116eda46e4f772fec5dcdc81",
    "devices/trezorlib/exceptions.py": "19d2bd924094bb757e83dba75ab543e58fd6e345182c9eff4826a086d72ed955",
    "devices/trezorlib/firmware.py": "f5cce86eeebb53dc68fd735b7bc42117bf687850c6547a83690b362e42fbebe3",
    "devices/trezorlib/log.py": "a198bf46ac4dd3e88c20609e7809be1d77755f5abf9b79ed977dd27d3ad8531f",
    "devices/trezorlib/mapping.py": "768c1b1223fa13108b16b09e6048e2e45db15283109dd115befb1cb56ef8875f",
    "devices/trezorlib/messages.py": "cfa33678bf354254ae2860ef10b64c23b3c7f6abc2bc43777b2f60591fc6a2b6",
    "devices/trezorlib/models.py": "879b35839975f1c963940262d83e36ecfc8fe2443a58454025dae7596fad377a",
    "devices/trezorlib/protobuf.py": "2ee0f3e07cf6819f075329345872840f09f9ee6ea285ea98c0b7068cae6cbb1e",
    "devices/trezorlib/tools.py": "dfd21888c87575ebbcadc8abf69b36bccbbb0c049e87a8d04f9ab2405f7ed091",
    "devices/trezorlib/transport/__init__.py": "79716a20967e9f9af9e81be54221b607f2541f117dfaa89e0846bf85a288ff7f",
    "devices/trezorlib/transport/hid.py": "f4a7416bd187202fdef7821fdb1694527da87458396a3f363114bb7293c07953",
    "devices/trezorlib/transport/protocol.py": "148782565da7af550658cb1e72ddb3f012ad80b9bde4081e5a6d0bf8a4b2feba",
    "devices/trezorlib/transport/udp.py": "24b85df4eff68c2d27cd4c0e51bf52f688b7da46ec7e25c03a34848d9ce9e152",
    "devices/trezorlib/transport/webusb.py": "560260fda58b84a9c0a314ba4255b97d96fa6e1f1d9edfad10009def62d9f371",
    "errors.py": "0e1bacca8c8a23b516c068d87f266f8875b72c39b62cee92c0e3d4049e208d2f",
    "hwwclient.py": "763a2c9dc708ab5973507036c1d3a72659067663d42810664d10182d114efc27",
    "key.py": "d28925c3e87623991d2b37fb0fc5dd0e6a1bb967cbcfe491c52ac5d71a71fce4",
    "psbt.py": "12b56ff86596ba162701c5ffdd752b4138a1ae971d04bd2a40627803bf476a2c",
    "tx.py": "42ee8983aa15cee6aedb976453e49e6da2cc80bb9ebcef24dcaa3ee3cf4e89f9",
    "udevinstaller.py": "739b3b9ad970b28ff0213811a827a00ed0b53e4efc16f5e84c935e8aa8909bb4",
    "ui/ui_bitbox02pairing.py": "e86b7b29166b5bffd7d0321c22324f25c17e64edeecc0c4b506e7f5980404554",
    "ui/ui_displayaddressdialog.py": "d1a36ff01f7e2ef6d6b92b5212124bccc8c4bf27fdd0283cb4649c673164cf35",
    "ui/ui_getkeypooloptionsdialog.py": "387b38576956be0cc1348a10c932c088e7680fbe1d5da665ae232d1fbe91e766",
    "ui/ui_getxpubdialog.py": "a3e6c1675b350c5dc3a1cfb1c1dbc9e87cf8e45042d852bbc7033590559b5f6e",
    "ui/ui_mainwindow.py": "37338409fd23c71e8e1dff8b315bcaf26552980ddc239fcc336700a0f8229452",
    "ui/ui_sendpindialog.py": "053dcf30bf377b917c995951104720d3c56a548ca46b74fc477eae9ae5eff3d8",
    "ui/ui_setpassphrasedialog.py": "622a944a6ff99c9eb03b97586c1b2dd02582ed5c6790c0fa2f14923bde0a42ea",
    "ui/ui_signmessagedialog.py": "ad0032707d8eb677722c2c882576b1dc80b21a64e20eaaef3fc5682835dc2978",
    "ui/ui_signpsbtdialog.py": "dd4e901b413022703c2268520561df53bc52840d4f44ba29f4eefc74d36f0069",
}
# A frozen build writes this beside the helper — Contents/Resources on macOS,
# where codesign seals it into the bundle, and the helper's own directory on
# Windows. What that is worth depends on the platform, and the difference is
# real: on macOS replacing the helper means breaking a signature the owner can
# check, while on Windows nothing signs either file and the sidecar only proves
# the build is complete and uncorrupted. An explicitly named helper carries its
# own, beside itself. It is also what the SBOM records for the helper (CT-105).
HWI_DIGEST_SIDECAR = "hwi.sha256"

_HWI_NO_DIGEST = (
    "The hardware-wallet tool carries no digest for this app to verify. "
    "Refusing to run it."
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
# What was hashed when each path was verified, so a reuse can re-read it
# instead of trusting a remembered verdict (CT-91).
_verified_hwi_files: dict[str, tuple[tuple[str, str], ...]] = {}


def _require_unchanged(verified: tuple[tuple[str, str], ...]) -> None:
    """Re-read the bytes the check child just hashed, at the spawn.

    The check and the helper are separate processes. A deterministic swap
    written into the package between the child's exit and the helper's exec
    would otherwise run code that no verdict ever covered, so the parent reads
    the same files again here -- immediately before the argv it is about to
    execute (CT-90). This narrows the check-to-use window to the exec itself;
    it does not replace running from an open handle, which source mode cannot
    do while the package is imported by name.
    """
    for file_path, expected in verified:
        try:
            if sha256(Path(file_path).read_bytes()).hexdigest() != expected:
                raise ProbeError(_HWI_WRONG_DIGEST)
        except OSError as exc:
            raise ProbeError(_HWI_WRONG_DIGEST) from exc


def _cached_identity_holds(path: str, payload: bool = False) -> bool:
    """True only while the whole fact a cached verdict stands for still holds.

    A path is not an identity. A helper can be replaced on disk between two
    calls in the same session — behind the app's back, in the window CT-91
    names — so a cached entry is re-hashed before it is believed. Anything
    unreadable now is not trusted either.

    A source-mode verdict is not a set of files: it is the whole-tree claim the
    payload walk made, so ``payload`` re-establishes it by re-running that walk
    and comparing the result to what was recorded. Re-hashing the recorded pairs
    alone cannot see a file *added* after the walk, and a forged
    ``__pycache__/<module>.cpython-312.pyc`` with a header copied from the
    genuine source is exactly such a file: CPython trusts that header, so a warm
    verdict used to load code a cold walk refuses (CT-102).
    """
    recorded = _verified_hwi_files.get(path)
    if recorded is None:
        return False
    if payload:
        try:
            if _verify_hwi_payload() != recorded:
                return False
        except ProbeError:
            return False
    for file_path, expected in recorded:
        try:
            if sha256(Path(file_path).read_bytes()).hexdigest() != expected:
                return False
        except OSError:
            return False
    return True


def begin_signing_session() -> None:
    """Drop every cached helper identity, so the next call re-identifies.

    CT-58: the cache used to live for the whole process, so a helper swapped on
    disk after the first check would run unverified for the rest of the session.
    A signing session is the unit the owner experiences, so it is the unit this
    trust decision is bounded by. CT-91: even inside one session the cached
    entry is re-read, never merely trusted.
    """
    _verified_hwi_paths.clear()
    _verified_hwi_files.clear()


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


# CT-90: the check child and the helper must be the same interpreter, or the
# path that was hashed is not the path that runs. `-I` is Python's isolated
# mode -- it implies `-E`, `-s` and `-P`, so PYTHONPATH, the user site
# directory and the working directory are all ignored -- and `-P` is named
# explicitly because that is the flag keeping a directory next to the script
# off sys.path. What the check can see, the helper imports, and the reverse.
#
# CT-90 (site hooks): `-I` does NOT stop `site` from running, so a `.pth` file
# in the environment's site directory executes arbitrary code at interpreter
# start-up -- before the first line of a child -- and can describe a different
# `hwilib` than the one on disk while standing inside the inspection meant to
# catch it, or put a decoy ahead of the pinned tree after the check child has
# already passed. Both children therefore add `-S`, which skips site
# processing entirely. `-S` also drops site-packages from a child's own
# `sys.path`, which is why each child's search path is handed over explicitly:
# the check child receives the package roots as arguments, and the helper
# receives a `-c` bootstrap that appends the verified roots AFTER its own
# entries -- never before them: a verified root's parent IS the site directory,
# so prepending it would let a file beside the pinned package shadow a
# standard-library module inside the helper (see `_helper_command`).
_HWI_CHECK_FLAGS = ("-I", "-S", "-P")

# The helper runs under that same strict isolation: what the check child hashed
# is what the helper imports. It is a second literal rather than an alias on
# purpose -- these are two separate trust decisions, and an edit that weakens
# one must not silently weaken the other.
_HWI_ISOLATION_FLAGS = ("-I", "-S", "-P")


def _hwi_package_roots(search_path: list[str] | None = None) -> list[str]:
    """Every hwilib package on the interpreter's own import path.

    Taken from ``sys.path`` entries that hold a ``hwilib/__init__.py`` -- that
    is the set the helper resolves the package through, because it runs under
    this same interpreter. Deliberately not a ``find_spec`` answer: a meta-path
    hook can describe a package the helper will never import, and the check has
    to hash what the helper will actually reach.
    """
    roots: list[str] = []
    for entry in (sys.path if search_path is None else search_path):
        if not entry:
            continue
        candidate = Path(entry) / "hwilib"
        if (candidate / "__init__.py").is_file():
            roots.append(str(candidate))
    return roots


def _hwi_payload_check_command(script: str, roots: list[str]) -> list[str]:
    """The argv that runs the payload check under those same rules.

    The package roots travel as arguments, because the child runs without site
    processing (see `_HWI_CHECK_FLAGS`) and must not be redirectable to another
    package by the very environment it is auditing.
    """
    return [sys.executable, *_HWI_CHECK_FLAGS, "-c", script, *roots]


# The `-c` program the helper runs under. It is a single fixed string, and
# every value that varies -- the entry script, the search directories and the
# helper's own arguments -- arrives as a real argv element, never interpolated
# into this text, so a path containing quotes or spaces cannot change what
# runs. argv layout: [entry, directory count, *directories, *helper args].
#
# The directories are APPENDED, never prepended. A verified root is a
# `hwilib` package directory, so the directory that has to be importable is
# its PARENT -- in an installed environment, site-packages itself. Prepending
# that directory put every other file in it ahead of the interpreter's own
# modules, so a planted `<site-packages>/ctypes.py` ran attacker code inside
# the helper that had just passed the identity check. Appending keeps the
# standard library and the bundled extension modules first.
_HWI_HELPER_BOOTSTRAP = (
    "import runpy, sys\n"
    "entry = sys.argv[1]\n"
    "directories = int(sys.argv[2])\n"
    "sys.path.extend(sys.argv[3:3 + directories])\n"
    "sys.argv = [entry, *sys.argv[3 + directories:]]\n"
    "runpy.run_path(entry, run_name='__main__')\n"
)


def _hwi_helper_search_dirs(roots: list[str]) -> list[str]:
    """The helper's ``sys.path`` additions: the verified tree, then site-packages.

    Each root is a ``hwilib`` package directory, so the entry that has to be
    importable is its parent -- in an installed environment, site-packages
    itself, which ``-S`` removed from the child and which also holds every
    dependency the pinned tree imports. The bootstrap APPENDS these
    directories after the interpreter's own entries, so the standard library
    and the bundled extension modules always win and nothing here can shadow
    them. What the pin still does not cover is the rest of site-packages: a
    substituted dependency (``typing_extensions``, say) is executed by the
    helper. That is a disclosed residual rather than a fixable one here,
    because the pin exists to pin ``hwilib``'s own bytes and writing
    site-packages already means writing the interpreter's environment.
    """
    directories: list[str] = []
    for root in roots:
        parent = str(Path(root).parent)
        if parent not in directories:
            directories.append(parent)
    paths = sysconfig.get_paths()
    for key in ("purelib", "platlib"):
        directory = paths.get(key)
        if directory and directory not in directories:
            directories.append(directory)
    return directories


def _helper_command(entry: str, search_dirs: list[str]) -> list[str]:
    """The argv that runs the in-tree helper with an explicit ``sys.path``.

    The helper runs under the same strict isolation as the payload check
    (``-I -S -P``), so ``site`` never starts and no ``.pth`` file can slip a
    directory ahead of the pinned tree after the check has passed. ``-S`` also
    means the child has no site-packages of its own, so the bootstrap appends
    the search path explicitly -- the verified roots' parents, then this
    interpreter's site-packages -- after the interpreter's own entries, and
    hands the entry point the argv it would
    have seen as a script. Every path and argument travels as a real argv
    value, never string-interpolated into the ``-c`` program.
    """
    return [
        sys.executable, *_HWI_ISOLATION_FLAGS, "-c", _HWI_HELPER_BOOTSTRAP,
        entry, str(len(search_dirs)), *search_dirs,
    ]


def _hwi_command(executable: str) -> list[str]:
    """The argv prefix that actually runs the helper.

    Source mode does not execute a helper binary at all: it runs the
    repository's entry point under the interpreter this app is already using,
    with the same isolation as the payload check (CT-90). That is the same
    trust model as the frozen bundle's own copy, without a binary on disk for a
    neighbour to replace.
    """
    path = _hwi_path(executable)
    if getattr(sys, "frozen", False):
        return [path]
    candidate = Path(executable)
    if candidate.is_absolute() or candidate.parent != Path("."):
        return [path]
    return _helper_command(path, _hwi_helper_search_dirs(_hwi_package_roots()))


def _hwi_payload_check_script() -> str:
    """The child that hashes the package without executing any of it.

    ``importlib.import_module`` is what made the old check porous (CT-90): it
    runs ``hwilib/__init__.py`` before a byte is hashed, so attacker code sat
    inside its own inspection -- it wrote a marker, repointed ``__file__`` and
    planted ``sys.modules['hwilib._cli']`` at the genuine files, and the pin
    passed. This child imports nothing of the package and reads no module
    object: it walks the package directory, hashes every source file in it, and
    prints what it found. The parent decides. So a poisoned sibling module
    (``hwilib/commands.py``), a file added to the package, or a file removed
    from it fails against the recorded tree rather than being believed.

    The package roots arrive in ``sys.argv``: under ``-S`` the child has no
    site-packages, and the roots are the directories this interpreter actually
    imports from, not whatever a meta-path hook would claim (CT-90).

    Every file under the package is judged, not only the ``.py`` files. A
    ``.pyc`` the interpreter would load is code that no literal in
    ``HWI_PAYLOAD_MANIFEST`` covers, and CPython trusts the timestamp and size
    in its header before it trusts the body, so a forged header is enough to
    make an attacker's marshal run. A bytecode file that validates against the
    recorded source -- the same compile the interpreter would itself have
    written -- is that interpreter's own artifact and is tolerated, and so is
    any file the import machinery cannot load (``.pyi``, ``py.typed``, ``.ui``,
    ``.rules``, ``.md``). An unverifiable bytecode file, or any other loadable
    suffix, fails the tree. A bytecode file whose header is stale is inert:
    CPython ignores it and recompiles the verified source.
    """
    return (
        "import hashlib, importlib.util, marshal, os, pathlib, sys\n"
        f"manifest = {HWI_PAYLOAD_MANIFEST!r}\n"
        "LOADABLE = ('.py', '.pyc', '.pyo', '.so', '.pyd', '.dll', '.dylib')\n"
        "def digest(path):\n"
        "    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()\n"
        "def walk(root_path):\n"
        "    files = []\n"
        "    def visit(directory):\n"
        "        with os.scandir(directory) as entries:\n"
        "            for entry in entries:\n"
        "                if entry.is_dir(follow_symlinks=False):\n"
        "                    visit(entry.path)\n"
        "                elif entry.is_file(follow_symlinks=False):\n"
        "                    files.append(pathlib.Path(entry.path))\n"
        "                else:\n"
        "                    # A symlink is neither: `is_dir`/`is_file` with"
        " follow_symlinks=False\n"
        "                    # answer False for it, so a symlinked cache dir"
        " cannot be\n"
        "                    # walked past (cycle-6 referee B: rglob never"
        " descended it).\n"
        "                    raise SystemExit(2)\n"
        "    visit(root_path)\n"
        "    return files\n"
        "def fingerprint(item):\n"
        "    # A code object reduces to its fields; a tuple or frozenset recurses\n"
        "    # so a nested code object cannot hide behind identity comparison;\n"
        "    # every other constant is compared by value AND by type. Value alone\n"
        "    # is not enough: `code.replace(co_consts=...)` keeps co_code and the\n"
        "    # line table identical while swapping 1 for 1.0 or True, and\n"
        "    # `1.0 == True == 1`, so a pyc that is not the compiled source passed.\n"
        "    # A float or complex constant also goes through repr, because\n"
        "    # `0.0 == -0.0` while the two are not the same constant.\n"
        "    if hasattr(item, 'co_code'):\n"
        "        return ('code',\n"
        "                item.co_argcount, item.co_posonlyargcount,\n"
        "                item.co_kwonlyargcount, item.co_nlocals,\n"
        "                item.co_stacksize, item.co_flags,\n"
        "                item.co_code, tuple(item.co_names),\n"
        "                tuple(item.co_varnames), tuple(item.co_freevars),\n"
        "                tuple(item.co_cellvars),\n"
        "                tuple(fingerprint(const) for const in item.co_consts),\n"
        "                item.co_name, item.co_qualname, item.co_firstlineno,\n"
        "                item.co_linetable, item.co_exceptiontable)\n"
        "    if isinstance(item, tuple):\n"
        "        return tuple(fingerprint(const) for const in item)\n"
        "    if isinstance(item, frozenset):\n"
        "        return frozenset(fingerprint(const) for const in item)\n"
        "    if isinstance(item, (float, complex)):\n"
        "        return (type(item).__name__, repr(item))\n"
        "    return (type(item).__name__, item)\n"
        "def bytecode_is_the_recorded_source(rel, path, root):\n"
        "    parent = pathlib.PurePosixPath(rel).parent\n"
        "    if parent.name != '__pycache__':\n"
        "        return False\n"
        "    source_rel = (parent.parent\n"
        "                  / (path.name.split('.')[0] + '.py')).as_posix()\n"
        "    if source_rel not in manifest:\n"
        "        return False\n"
        "    data = path.read_bytes()\n"
        "    if len(data) < 16 or data[:4] != importlib.util.MAGIC_NUMBER:\n"
        "        return False\n"
        "    source = root / source_rel\n"
        "    # PEP 552: 0 is a timestamp pyc, 1 and 3 are hash-based (the 8 bytes\n"
        "    # at 8:16 are the source hash, not a timestamp or a size). Any other\n"
        "    # flag is a shape this reader does not know and must refuse.\n"
        "    flags = int.from_bytes(data[4:8], 'little')\n"
        "    if flags not in (0, 1, 3):\n"
        "        return False\n"
        "    if flags == 0:\n"
        "        stat = source.stat()\n"
        "        if (int.from_bytes(data[8:12], 'little') != int(stat.st_mtime) & 0xffffffff\n"
        "                or int.from_bytes(data[12:16], 'little') != stat.st_size & 0xffffffff):\n"
        "            return True\n"
        "    # A hash-based pyc never takes the stale shortcut above: the\n"
        "    # interpreter uses it without consulting the source's timestamp, so\n"
        "    # its body has to be proved equal to the compiled source below.\n"
        "    # Compare the code by value, not the recorded filename and not the\n"
        "    # marshal bytes: pip installs a wheel from a staging directory and\n"
        "    # the compiler writes THAT path into the pyc (cycle-6 referee E),\n"
        "    # and marshal encodes string-interning/ref-flag state, so two code\n"
        "    # objects with equal constants can dump to different bytes -- a\n"
        "    # genuine `compileall` tree was refused for exactly that reason.\n"
        "    # The unmarshalled body is never executed, and a stream this\n"
        "    # interpreter cannot read is a refusal.\n"
        "    try:\n"
        "        recorded = marshal.loads(data[16:])\n"
        "    except Exception:\n"
        "        return False\n"
        "    code = compile(source.read_bytes(), str(source), 'exec', dont_inherit=True)\n"
        "    return fingerprint(recorded) == fingerprint(code)\n"
        "roots = sys.argv[1:]\n"
        "if not roots:\n"
        "    raise SystemExit(3)\n"
        "manifested = {}\n"
        "for root in roots:\n"
        "    root_path = pathlib.Path(root)\n"
        "    files = walk(root_path)\n"
        "    found = {path.relative_to(root_path).as_posix(): path for path in files\n"
        "             if path.relative_to(root_path).as_posix() in manifest}\n"
        "    if set(found) != set(manifest):\n"
        "        raise SystemExit(2)\n"
        "    for name, path in sorted(found.items()):\n"
        "        if digest(path) != manifest[name]:\n"
        "            raise SystemExit(2)\n"
        "    for path in files:\n"
        "        rel = path.relative_to(root_path).as_posix()\n"
        "        if rel in manifest:\n"
        "            continue\n"
        "        if path.suffix in ('.pyc', '.pyo'):\n"
        "            if not bytecode_is_the_recorded_source(rel, path, root_path):\n"
        "                raise SystemExit(2)\n"
        "        elif path.suffix.lower() in LOADABLE:\n"
        "            raise SystemExit(2)\n"
        "    # Every root prints its own files: a swap of an earlier root\n"
        "    # between the check and the spawn is otherwise never re-read\n"
        "    # (cycle-6 referee B).\n"
        "    for name, path in sorted(found.items()):\n"
        "        manifested[(name, str(path))] = manifest[name]\n"
        "for (name, path), recorded in sorted(manifested.items()):\n"
        "    print(name + ' ' + path + ' ' + recorded)\n"
    )


def _verify_hwi_payload(
    search_path: list[str] | None = None,
) -> tuple[tuple[str, str], ...]:
    """Refuse a substituted hwilib before it can see an xpub or a PSBT.

    The in-tree entry point is repository source; the code that can be swapped
    out from under a running interpreter is the third-party package it imports.
    Every source file behind the pinned HWI release is hashed without a line of
    the package running, in a child that carries no site-packages and so cannot
    be reached by a site hook, and the whole recorded tree must match in both
    directions -- a missing file, an altered file and an added file are each a
    substitution (CT-90).

    It returns every file it hashed, so a later call can re-read all of those
    bytes instead of trusting a remembered verdict (CT-91).
    """
    roots = _hwi_package_roots(search_path)
    if not roots:
        raise ProbeError(
            "The pinned hardware-wallet library is not installed in this "
            "environment. Install hwi " + EXPECTED_HWI_VERSION + " to use devices."
        )
    try:
        result = subprocess.run(
            _hwi_payload_check_command(_hwi_payload_check_script(), roots),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            **hwi_process_options(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProbeError(_HWI_UNIDENTIFIED) from exc
    if result.returncode == 2:
        raise ProbeError(_HWI_WRONG_DIGEST)
    if result.returncode != 0:
        raise ProbeError(
            "The pinned hardware-wallet library is not installed in this "
            "environment. Install hwi " + EXPECTED_HWI_VERSION + " to use devices."
        )
    seen: dict[str, list[tuple[str, str]]] = {}
    for line in (result.stdout or "").splitlines():
        # "<relative path> <path> <sha256>", split from the right so that a
        # path with spaces in it survives.
        parts = line.split(" ")
        if len(parts) >= 3:
            seen.setdefault(parts[0], []).append(
                (" ".join(parts[1:-1]), parts[-1].strip()))
    verified: list[tuple[str, str]] = []
    for name in sorted(HWI_PAYLOAD_MANIFEST):
        found = seen.get(name)
        if not found:
            raise ProbeError(_HWI_WRONG_DIGEST)
        # EVERY root's copy is recorded, not the last one to print: with more
        # than one package root the earlier roots were never re-read at the
        # spawn (cycle-6 referee B).
        for path, digest in found:
            if digest != HWI_PAYLOAD_MANIFEST[name]:
                raise ProbeError(_HWI_WRONG_DIGEST)
            verified.append((path, digest))
    return tuple(verified)


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


def _verify_hwi_bytes(path: str) -> tuple[tuple[str, str], ...]:
    """Compare a standalone helper against a digest that is not its own claim.

    What the sidecar proves depends on where the platform can put it. On macOS a
    frozen build records it in Contents/Resources, inside the bundle codesign
    sealed, so replacing the helper means breaking that signature first. On
    Windows the sidecar sits beside hwi.exe in the same directory, and neither
    file is signed, so there it proves the build is complete and uncorrupted —
    not that a local writer did not replace both files together (CT-105). That
    is the Windows trust model as built, and it is documented as such in
    SIGNING.md rather than claimed away. An explicitly named helper is refused
    outright without one. Source mode runs no helper binary at all — see
    _verify_hwi_payload for the surface it does pin.

    It returns the file it hashed, for the reason _verify_hwi_payload does: a
    later call re-reads those bytes instead of trusting a verdict (CT-91).
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
    return ((str(path), actual),)


def _verify_hwi_identity(path: str, command: list[str] | None = None) -> None:
    """Refuse a helper that is not the bytes this app expects to run.

    Byte identity comes first and is not something the helper gets to assert:
    a standalone helper must match every digest sidecar that is present — one
    beside it in source and loose layouts, and one in Contents/Resources when a
    frozen macOS bundle keeps it out of Contents/MacOS — and source mode runs
    the repository's own entry point and pins the hwilib it imports.

    Only then does the helper say what version it is, and it has to say it
    exactly (CT-29, CT-49).

    The cache remembers bytes, not permission: a path verified earlier is
    re-read here, and anything that changed since is put back through the whole
    check instead of inheriting the earlier verdict (CT-91). In source mode the
    cached verdict is the whole-tree claim, so it is re-established by the
    payload walk rather than by the files that walk once happened to record
    (CT-102).
    """
    argv = list(command) if command is not None else [path]
    # A two-element prefix is [interpreter, entry]: the in-tree source-mode
    # helper, whose substitution surface is the package it imports. Anything
    # else is a standalone binary whose own bytes are what we pin.
    source_mode = len(argv) >= 2
    if path in _verified_hwi_paths:
        if _cached_identity_holds(path, source_mode):
            return
        _verified_hwi_paths.discard(path)
        _verified_hwi_files.pop(path, None)
    if source_mode:
        verified = _verify_hwi_payload()
        # Re-walk the package immediately before the exec below. Re-reading the
        # recorded files catches a rewrite of any of them; only a second walk
        # catches a file *added* after the first one, which the recorded pairs
        # cannot name (CT-90).
        if _verify_hwi_payload() != verified:
            raise ProbeError(_HWI_WRONG_DIGEST)
    else:
        verified = _verify_hwi_bytes(path)
    # Then re-read every recorded file, so the argv below runs only if those
    # bytes are still the bytes that were hashed (CT-90).
    _require_unchanged(verified)
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
    _verified_hwi_files[path] = verified
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
