# 0.3.0 warm safety release and owner acceptance

## Release identity

The manually dispatched [GitHub workflow run 36594024409](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36594024409) passed its source, Apple Silicon DMG, checksums and publication jobs. The immutable [v0.3.0 release](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.3.0) targets `aa40a4620e8b157720ebdd302f8de5049db1591f`. This is an ad-hoc-signed, unnotarized **test** build. It has not yet passed the owner's physical Mutinynet wallet/device walkthrough and is not accepted for mainnet broadcast.

Downloaded release assets passed `shasum -a 256 -c SHA256SUMS`; `hdiutil verify` reported a valid DMG. SHA-256: DMG `c52e50645bad35e4f8db09614e27de95b7efe1a786b6b6560917f46f9b235af4`; source `6d4a9084a2d3f031aacaf9997dc8cb4039cff6f522f4b3a2479451c106ccbf35`; SBOM `37c9cfa2c141c8ea7b8ce68a270a36d96346a0671fecf9adc7434b0d3befb6b3`.

## Changes and evidence

- A new unsigned review immediately retires the prior signer panel, signature count, final output/txid, broadcast checkbox and sent message. Late device, finalize or broadcast responses are bound to the old review and cannot repaint a new one. `tests/ui_state_reuse.cjs` clicks the real Prepare control with old final data present and checks it disappears before a network response.
- HWI 3.2.0 receives the signing PSBT through `--stdin`; the bundled HWI path was checked in the Mac workflow. `PreparedPayment` is one immutable review record, replaced as valid signatures are added. The wallet, network, scan generation, selected inputs, transaction ID and review values are checked through sign/finalize/broadcast.
- Every selected funding transaction must still be confirmed and its chosen output unspent before preparation and again before practice-network broadcast. Mainnet also cross-checks selected public outpoints with a separate Esplora operator, after the app's address-disclosure consent. This is an explorer cross-check, not consensus verification. A broadcast with an uncertain response pauses retry and points to the expected transaction ID.
- Mutinynet is an additional practice-network profile of the same PSBT engine. Its custom-Signet genesis and block-1 checkpoint are verified before scan/prepare/broadcast. Testnet4 remains selectable. The fee reference and waiting banner identify the selected network. Mainnet broadcast remains refused in the local API.
- The Python suite passed **164 tests, 8 skipped**, both from the checkout and the extracted source archive. The Node browser-state regression, packaged HWI/device/TLS checks, source integrity, SBOM and DMG checks passed in GitHub. Live Testnet4 and Mutinynet genesis/checkpoint HTTPS probes also passed locally on 29 September 2026. Synthetic signers and backend probes do not establish physical-device or end-to-end wallet acceptance.

## Single owner walkthrough still needed

1. Install the [v0.3.0 Apple Silicon test DMG](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.3.0) once. Close the old 0.2.1 app first. On first launch, right-click the app and choose **Open**; this build is unnotarized. Do not disable Gatekeeper globally.
2. Select **Mutinynet** and import a newly funded **2-of-3 native-SegWit BSMS wallet** with declared change ownership. A single-signature wallet is outside this app's scope. Use practice coins only; the Testnet4 wallet's funds do not appear on Mutinynet.
3. Prepare a small payment to an address you control. Check the destination, amount, change and fee in the review. Approve on two hardware devices and compare what each device displays. Confirm the final app screen shows that same payment, then deliberately broadcast and independently observe confirmation.
4. After one confirmation, use **Check again** and prepare a second small payment. Verify that no signer buttons, signature count, final transaction or sent message from the first payment remain. A second broadcast is optional if the panel reset and fresh review are clear; do not incur another payment solely to test styling.

If anything fails, use **Save diagnostic report** and share that JSON plus a description of the device screen. Do not share the BSMS, xpubs, addresses, PSBTs or raw signed transaction. Do not infer success for Trezor on this build until the owner reports it. Phase 5 mainnet dry run and an explicitly authorized live transaction remain separate gates.
