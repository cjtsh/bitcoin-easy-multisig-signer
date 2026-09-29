# 0.4.0 — quiet visual refresh and payment receipt

## Status and scope

Version 0.4.0 is a candidate until the manual GitHub release workflow publishes an immutable DMG. The owner accepted the 0.3.2 Mutinynet flow after two reported physical sends, using Ledger + Trezor and Jade + Trezor. The 0.4.0 work changes the light interface; it does not change BSMS parsing, wallet derivation, PSBT construction, HWI transport, signature verification, fee caps, outpoint checks, or the API's mainnet broadcast refusal. Phase 5 live Bitcoin work remains separate.

## Interface decisions

- Keep a light reading surface with charcoal text, one restrained teal action color, amber waiting/caution and red errors. Preserve the strong, distinct mainnet warning treatment. A dark theme is not required for this release.
- Use calmer cards, clearer section headings and compact metric blocks. The destination, amount, network, fee, change, transaction ID and approval controls remain visible at their existing safety gates. Device-search and blockchain-scan waiting messages stay prominent.
- After a practice-network broadcast, the pending banner retains its explorer link until one confirmation. Once the same-session scan reports confirmation, a last-payment receipt keeps that link visible instead of letting it vanish with the pending banner. The receipt lives only in browser memory; it is cleared on wallet import or network change and does not claim to be durable history. No transaction identifier is written to diagnostics or local storage.
- The owner saw the opening and synthetic review/signing layout in a local browser before publication. The preview used invented addresses and amounts and could not import, sign or broadcast. It is not evidence that the packaged Mac window or hardware devices have been retested on 0.4.0.

## Verification and owner check

Run the full Python suite, both Node UI regressions, JS syntax, `git diff --check`, Bash syntax checks, and tests from the extracted source archive. The UI regression must check that a confirmed receipt remains when the pending banner disappears and that wallet/network changes clear it. The manual GitHub workflow must build and verify the Apple Silicon bundle, HWI and HTTPS self-checks, source archive, SBOM, checksums and DMG; record its release URL and digest below after publication. No new practice-network send is needed solely for a palette change. The owner should inspect the installed 0.4.0 window once at ordinary Mac size, including the payment review and mainnet warning, before Phase 5.

## Release evidence

Pending workflow publication.
