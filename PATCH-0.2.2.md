# 0.2.2 payment confirmation notice and send pause

## Why this patch exists

After the first accepted 0.2.1 Testnet4 payment, the owner observed that the next payment appeared unavailable while the previous one waited for a block. A spouse or estate professional needs the reason and a clear next step on the main screen. Version 0.2.2 presents that state explicitly and applies the same rule at the local API boundary. It makes no change to key handling, PSBT signing, finalization, network selection, or mainnet broadcast policy.

## State and behavior

1. `wallet_service.scan_wallet` sets `pending_outgoing` when any scanned wallet address reports a positive `mempool_stats.spent_txo_sum`. This is distinct from `pending_delta_sats`, which can represent an incoming payment. The existing UTXO accounting exception still checks explorer consistency; it does not authorize another payment.
2. Immediately after a successful Testnet4 broadcast, `gui.LocalApp` keeps the transaction ID in memory. On each balance refresh it asks the configured explorer for `/tx/<id>/status`. Only an explicit `confirmed: true` clears this session marker. A missing, malformed, or unreachable status keeps the pause. The scan's outgoing mempool flag also keeps it paused if the app restarts or another outgoing transaction exists.
3. Fee preview and transaction construction reject a pending outgoing payment in `wallet_service`; the local `/api/prepare` endpoint rejects it before fetching fees. The browser hides its next-send controls and shows a yellow payment notice with a **Check again** button. The accepted transaction's explorer link is present in the current session. The notice survives a page reload while the local app is running.
4. After a confirmed status and a refreshed scan with no outgoing mempool spend, the notice disappears and normal send controls return. There is no timer that claims confirmation without checking the explorer. Scans and status calls disclose the same public transaction/address information already used by the configured explorer.

## Verification and limits

- Synthetic tests cover a pending spend with another confirmed UTXO, the fee/build/API gates, the gap between broadcast acceptance and mempool visibility, explorer failure, and unlocking after explicit confirmation. Python 3.12 local and source-archive suites passed: 146 tests, 8 expected skips. JavaScript and Bash syntax checks passed.
- The [manual GitHub build](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36585936648) succeeded from commit `a97b0e4192c716c487023e69fb47049fcb33bc28`, including the Apple Silicon package, bundled HWI/device/HTTPS checks, source archive tests, SBOM, and checksum publication. The [v0.2.2 release](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.2.2) targets that commit. Downloaded assets passed `shasum -a 256 -c SHA256SUMS`; `hdiutil verify` reported a valid DMG.
- Published SHA-256: DMG `a6ba3658d84f9153449440fcee2b00f4ff4cd9db5338f9e89d5f5b60f7e02faf`; source `bb6a5aac00ef10bd234e43971a63093dbf8c741dfbf9d6077ffbe04a20b21045`; SBOM `d74ddb823efa58aae2119900fcc5f380e542b5a78635d721dbf96d2cf5abddc7`.
- A public explorer is an observation, not a consensus node. A stale explorer may leave the app paused longer. A dropped or replaced unconfirmed payment is not handled with fee bump or cancellation tools in this version. Do not assume a transaction confirmed solely because it was broadcast.
- No private wallet material or real transaction identifier is placed in this document, the source archive, or diagnostics.

## Owner testing and install timing

No separate owner install or payment is required for this small patch. The owner may complete the planned Trezor plus already verified signer check in the existing 0.2.1 app after the earlier Testnet4 payment receives one confirmation. The 0.2.2 DMG is available for a later install; its yellow notice can be observed during the next ordinary payment, with **Check again** after a block. Save the opt-in diagnostic report only if something fails. This is not a mainnet send authorization.
