# 0.2.2 payment confirmation notice and send pause

## Why this patch exists

After the first accepted 0.2.1 Testnet4 payment, the owner observed that the next payment appeared unavailable while the previous one waited for a block. A spouse or estate professional needs the reason and a clear next step on the main screen. Version 0.2.2 presents that state explicitly and applies the same rule at the local API boundary. It makes no change to key handling, PSBT signing, finalization, network selection, or mainnet broadcast policy.

## State and behavior

1. `wallet_service.scan_wallet` sets `pending_outgoing` when any scanned wallet address reports a positive `mempool_stats.spent_txo_sum`. This is distinct from `pending_delta_sats`, which can represent an incoming payment. The existing UTXO accounting exception still checks explorer consistency; it does not authorize another payment.
2. Immediately after a successful Testnet4 broadcast, `gui.LocalApp` keeps the transaction ID in memory. On each balance refresh it asks the configured explorer for `/tx/<id>/status`. Only an explicit `confirmed: true` clears this session marker. A missing, malformed, or unreachable status keeps the pause. The scan's outgoing mempool flag also keeps it paused if the app restarts or another outgoing transaction exists.
3. Fee preview and transaction construction reject a pending outgoing payment in `wallet_service`; the local `/api/prepare` endpoint rejects it before fetching fees. The browser hides its next-send controls and shows a yellow payment notice with a **Check again** button. The accepted transaction's explorer link is present in the current session. The notice survives a page reload while the local app is running.
4. After a confirmed status and a refreshed scan with no outgoing mempool spend, the notice disappears and normal send controls return. There is no timer that claims confirmation without checking the explorer. Scans and status calls disclose the same public transaction/address information already used by the configured explorer.

## Verification and limits

- Synthetic tests cover a pending spend with another confirmed UTXO, the fee/build/API gates, the gap between broadcast acceptance and mempool visibility, and unlocking after explicit confirmation. The full suite, source archive suite, JS syntax, and Mac package checks are required before release.
- A public explorer is an observation, not a consensus node. A stale explorer may leave the app paused longer. A dropped or replaced unconfirmed payment is not handled with fee bump or cancellation tools in this version. Do not assume a transaction confirmed solely because it was broadcast.
- No private wallet material or real transaction identifier is placed in this document, the source archive, or diagnostics.

## Owner walkthrough

After the pending Testnet4 payment receives one confirmation, install the published 0.2.2 DMG once and make one small self-owned Testnet4 payment with Trezor plus an already verified signer. Check each device's destination and amount. After broadcast, confirm the yellow notice and disabled next-send path; later use **Check again** after a block. Send the opt-in diagnostic report only if something fails. This is not a mainnet send authorization.
