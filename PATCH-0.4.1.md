# 0.4.1 — hardware signer response correction

## Incident and evidence

The owner installed 0.4.0 and reported that Jade approval ended with “The device changed the reviewed transaction or its wallet data.” The privacy-limited diagnostic file records a successful wallet import, consistent scan, prepared payment, device checks and two rejected signer responses. It does not identify the changed PSBT fields. The signing engine and HWI dependency were unchanged from the owner-tested 0.3.2 release, so the precise reason Jade's returned PSBT differed is unproven. Do not attribute the incident to the visual refresh or claim a confirmed firmware cause.

The 0.4.0 comparison required every non-signature PSBT field from a device to equal the app's original field. HWI passes a PSBT through Jade's native PSBT signer, which may return a rewritten map. Rejecting every such rewrite caused this failure even when the response might contain a valid signature. Do not accept or save a signer-controlled replacement PSBT wholesale.

The owner then tried Ledger in the same installed 0.4.0 build. Ledger asked the owner to review the payment twice; the app failed. The second diagnostic report has a rejected request about 46 seconds after device checking, consistent with the old 45-second HWI timeout, though its privacy-limited codes cannot prove which request hit that limit. A later screenshot said “HWI reported a device error: open failed”; no signer response was recorded for that attempt. This is a device-open failure before a signature response, separate from Jade's PSBT rejection. The specific USB contention or disconnection cause is unknown.

Version 0.4.1 allows up to 600 seconds for an explicit signing request while allowing 60 seconds for enumeration and public identity checks. The screen explains that Ledger can ask for two review rounds and may take several minutes. An `open failed` result gets actionable reconnect and app-conflict guidance; the app does not automatically retry a signing action or claim to repair the underlying USB condition.

## Correction and security boundary

`accept_signature_update` checks the returned unsigned transaction bytes and input/output counts, requires earlier signatures to survive, clones the app's reviewed PSBT, imports **only** returned partial signatures, and cryptographically verifies all of them against the original transaction, independently checked previous outputs and witness scripts. No returned global, input or output metadata enters prepared state. `gui.py` stores this canonical clone and uses it for signer status, finalization and broadcast. A changed output/transaction, invalid signature or removed prior signature still fails. The same engine and rule apply to Mutinynet, Testnet4 and mainnet; mainnet broadcast remains disabled.

## Verification and physical gate

Unit tests simulate signer-added or rewritten PSBT metadata, invalid signatures, changed unsigned outputs, the signing-only timeout and the Ledger open-failure guidance. The local API test simulates a Jade-like response with altered metadata, then adds a second signer and finalizes the original reviewed transaction. These tests establish the boundary in code, not actual device behavior. The requested owner check is one small Mutinynet payment using Ledger and Jade, with Trezor available as a fallback if either cannot finish. Check destination, amount, fee and change on both devices and the final review before broadcast. If Ledger again says “open failed,” close other wallet apps using it, reconnect, unlock, open Bitcoin Testnet, and run device search again. Do not send live Bitcoin to test this correction.

## Release evidence

The manual [GitHub workflow](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36624835443) passed all five jobs and published [v0.4.1](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.4.1) from merge commit `1f8e7066c37006444906f910add576be32cde0e1`. The full local suite passed 170 Python tests (8 skipped); GitHub ran tests in the checkout, source archive and Apple Silicon build, plus bundle, HWI, HTTPS, code signature and DMG checks. Independently downloaded release files matched `SHA256SUMS`, and `hdiutil verify` accepted the downloaded DMG. SHA-256 values:

```text
8b4628817dbfa1a252c8a8df506477d9d53ac092b463a18f81a2790da550f3c0  bitcoin-easy-multisig-signer-v0.4.1.tar.gz
76182be6ec7a37d41f9f8376944dd01eeb054a9364a37594830495356bcb8566  Bitcoin-Easy-Signer-v0.4.1-UNSIGNED-TEST.dmg
1b2fd716be75c79ae88d8d4a2045d3fe2dc44795833416f3ea8abb85a86a035d  BUILD-SBOM.json
```

The physical Jade/Ledger correction remains **unverified** until the owner completes a practice-network signer walkthrough on the installed 0.4.1 app. Do not treat release checks as device acceptance or enable mainnet broadcast on their basis.
