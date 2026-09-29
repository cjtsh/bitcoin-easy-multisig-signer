# Bitcoin Easy Signer

**0.4.1 correction:** the installed 0.4.0 app rejected a Jade signer response after approval. The privacy-limited diagnostic report does not identify which PSBT metadata changed. Version 0.4.1 keeps the reviewed PSBT, imports only device signatures that verify against it, and discards all signer-returned metadata. See [the correction record](PATCH-0.4.1.md). Automated tests pass for this boundary; a physical Jade Mutinynet payment remains the acceptance check. Mainnet broadcast is still disabled.

Bitcoin Easy Signer helps a spouse, estate professional, or other nontechnical person send Bitcoin from an **existing** 2-of-3 multisig wallet. It does not create a wallet, generate keys, or ask for seeds or PINs. The intended screen is simple: open the wallet definition, see the balance, enter a destination, review the payment, approve it on two hardware devices, and confirm the final transaction.

**This source is version 0.4.1, an experimental Apple Silicon correction build.** [Version 0.4.0](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.4.0) is the previous published visual release. Earlier versions produced confirmed Testnet4 payments with Jade, Trezor Safe 3, and Ledger Nano S Plus. Version 0.3.0 added warm safety checks and Mutinynet practice through the same engine, and fixed an old signed payment remaining visible below a new review. Version 0.3.1 made Mutinynet the opening network and required an explicit Send All choice. Version 0.3.2 restored standard BIP48 custom sends from one Nunchuk BSMS file. The owner reports two successful physical Mutinynet sends using Ledger + Trezor and Jade + Trezor, including a second payment without restarting the app; see [the walkthrough record](PATCH-0.3.2.md). Version 0.4.0 changes the interface and keeps an explorer receipt visible after confirmation in the current session; see [the release record](PATCH-0.4.0.md). Mainnet preparation, signing, and finalization are available for a controlled dry run, but **mainnet broadcast is refused in code**. No real-Bitcoin transaction has been tested. This is not yet a production recovery tool. Read [the risk notice](DISCLAIMER.md).

The 0.4.1 correction is in [`PATCH-0.4.1.md`](PATCH-0.4.1.md); the 0.4.0 visual release is in [`PATCH-0.4.0.md`](PATCH-0.4.0.md); 0.3.2 release and owner evidence are in [`PATCH-0.3.2.md`](PATCH-0.3.2.md). Mutinynet needs a funded 2-of-3 BSMS wallet; existing Testnet4 coins cannot move between networks. The installed 0.2.1 app could show stale signing/final details when a new payment was prepared; **never broadcast from a screen that mixes two payments**.

**0.3.1 correction published:** the first 0.3.0 Mutinynet import exposed a receive-only Nunchuk BSMS export. The app safely refused a smaller payment but preselected Send All. Do not send a sweep to work around this. The 0.3.1 release leaves Send All unchecked, explains the missing change path beside the amount, opens on Mutinynet, and keeps custom amounts blocked when change is absent from the wallet definition. The current Nunchuk BSMS export lacks that policy. See [`PATCH-0.3.1.md`](PATCH-0.3.1.md).

**0.3.2 correction published:** the one-file recovery flow derives `/0/*` receive and `/1/*` change under strict BIP48 2-of-3 native-SegWit sorted-multisig conditions. It checks the BSMS first receiving address and shows standard-derived change plainly in the review. No Nunchuk database or second export is required. Custom branch layouts remain outside this fallback; see [`PATCH-0.3.2.md`](PATCH-0.3.2.md).

## What this version does

- Imports a BSMS 1.0 definition for a 2-of-3 native-SegWit multisig wallet. The app checks its reference receive address, public cosigner identities, and selected network.
- Scans receive and established change branches through a selected Esplora server. A gap-limited scan is an observation, not proof of a complete balance. Derived addresses are disclosed to that server after consent; seeds and private keys remain on hardware.
- Builds a PSBT from confirmed, independently checked previous outputs. Partial sends use a BSMS-declared change branch or the strict BIP48 standard `/1/*` branch for an anchored 2-of-3 native-SegWit sorted wallet. The latter is labelled as standard-derived, since the BSMS does not explicitly declare it. If neither route applies, the owner can explicitly choose **Send All confirmed outputs found by the scan**, producing no change.
- Checks connected hardware signers through bundled Bitcoin Core HWI, asks them to sign, retains only signatures that verify against the reviewed transaction, and discards all returned wallet metadata before finalization. Each device must display the intended payment; the person using the app must check its screen.
- Shows the destination, amount, network, every change output, fee, effective fee rate, and transaction ID together at the final confirmation. Practice-network broadcast requires a separate explicit action. Mainnet broadcast remains disabled.
- After an outgoing payment is accepted, shows a prominent notice that it is waiting for one confirmation and offers **Check again**. Another payment from that wallet is paused until the refreshed explorer state confirms it. Pending incoming funds alone do not pause confirmed outputs.
- In 0.4.0, after that confirmation the app keeps a visible explorer-link receipt for the latest payment in the current browser session. It is cleared when opening a different wallet or changing networks and is not long-term transaction history.
- Can save an unsigned PSBT and, on request, a privacy-limited diagnostic report in Downloads. The report has fixed pass/fail codes and timestamps, without wallet identifiers, balances, transaction bytes, or device paths.

The app uses **one** wallet/PSBT/signing engine. [`network_config.py`](network_config.py) supplies the selected network's address prefix, BIP48 coin type, Esplora endpoint, genesis hash and any custom-Signet checkpoint. A mainnet wallet uses BIP48 coin type `0'`, while both practice networks use `1'`; each network needs its own correct wallet definition and coins. `gui.py` retains explicit mainnet safety gates; there is no separate mainnet transaction implementation.

## Mac installation and one-session test

The published DMG is for Apple Silicon. Until Developer ID enrollment and notarization are complete, it is ad-hoc signed and macOS requires **right-click → Open** on first launch. Verify the download against the release's `SHA256SUMS` before opening it. Do not disable Gatekeeper globally.

The 0.4.0 DMG is published and its downloaded image was verified. The owner imported the funded Nunchuk BSMS alone and reported two successful Mutinynet payments, including a second payment in the same app session. This is owner-reported device acceptance for 0.3.2, without transaction IDs or diagnostic records for independent verification. The installed 0.4.0 visual changes still need one owner inspection. Any further payment should still be checked on each hardware device: destination, amount, fee and change must match the intended payment. Save the diagnostic report only if something fails or a reviewer needs evidence; the button is at the bottom of the window. Keep wallet files, xpubs, addresses, PSBTs, and raw signed transactions out of public issue reports and the repository.

If neither declared nor guarded standard change is available, the app offers a no-change Send All path. **Do not sweep a real wallet merely to test this feature.**

## Supported scope and limitations

| Item | Published 0.4.0 support |
| --- | --- |
| Wallet | Existing BSMS 1.0, 2-of-3 P2WSH multisig with xpub origins |
| Networks | Testnet4, Mutinynet and mainnet through one engine; mainnet broadcast disabled |
| Hardware tested before 0.2.0 | Jade, Trezor Safe 3, Ledger Nano S Plus on the owner's Testnet4 wallet |
| Distribution | Apple Silicon test DMG, source archive; no trusted/notarized release yet |
| Fees | Mainnet mempool.space guidance for mainnet/Testnet4; Mutinynet's Esplora reference in Mutinynet mode; 1–25 sat/vB and 10,000-sat estimated fee caps |
| Scan | 20-address unused gap, at most 100 addresses per known branch; historical or unusual funds can be missed |
| Recovery | No built-in fee bump, no support for arbitrary wallet policies or legacy address types |

## Developer and reviewer entry point

Read [`AGENTS.md`](AGENTS.md), [`PHASE-HANDOFF.md`](PHASE-HANDOFF.md), [`PATCH-0.4.0.md`](PATCH-0.4.0.md), [`PATCH-0.3.2.md`](PATCH-0.3.2.md), the [original audit](AUDIT-BASELINE-0.1.27.md), the [0.2.0 fix record](SECURITY-REVIEW-0.2.0.md), and [the 0.3.0 release and acceptance record](PATCH-0.3.0.md) before editing. [`PROJECT-HISTORY.md`](PROJECT-HISTORY.md) and [`ROADMAP.md`](ROADMAP.md) preserve earlier decisions. Current behavior in source and tests takes precedence over historical descriptions.

Use Python 3.12 for the Mac build (HWI 3.2.0 does not support 3.13+). Source tests:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python -m unittest discover -s tests -q
```

The Mac build installs [`requirements-desktop.lock`](requirements-desktop.lock) with hashes. A reviewed `LIBUSB_SHA256` is mandatory. [`scripts/build-source.sh`](scripts/build-source.sh) creates the source archive; [`scripts/build-macos.sh`](scripts/build-macos.sh) creates the DMG on Apple Silicon. The GitHub workflow is **manual dispatch only** and publishes an immutable version with `BUILD-SBOM.json` and `SHA256SUMS` after its tests and bundled checks pass. Never republish under an existing version; use a new 0.3.x patch tag for a correction after 0.3.0.

## External components

- [embit](https://github.com/diybitcoinhardware/embit): descriptors, derivation, Bitcoin transactions and PSBTs.
- [Bitcoin Core HWI](https://github.com/bitcoin-core/HWI): hardware discovery and signing requests; no USB driver or private-key code is written here.
- [pywebview](https://pywebview.flowrl.com/): native Mac WebKit window over the loopback-only local app.
- [PyInstaller](https://pyinstaller.org/): bundled runtime and binaries.
- [Esplora](https://github.com/Blockstream/esplora): public address/UTXO/transaction API and practice-network broadcast endpoints.

These components do not remove the need to verify release provenance, wallet policy, signer display, and the final transaction.
