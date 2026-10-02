# 0.4.0 — quiet visual refresh and payment receipt

## Status and scope

Version [0.4.0](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.4.0) is published as an Apple Silicon test DMG. The owner accepted the 0.3.2 Mutinynet flow after two reported physical sends, using Ledger + Trezor and Jade + Trezor. The 0.4.0 work changes the light interface; it does not change BSMS parsing, wallet derivation, PSBT construction, HWI transport, signature verification, fee caps, outpoint checks, or the API's mainnet broadcast refusal. Phase 5 live Bitcoin work remains separate. The installed 0.4.0 window has not yet had an owner walkthrough.

## Interface decisions

- Keep a light reading surface with charcoal text, one restrained teal action color, amber waiting/caution and red errors. Preserve the strong, distinct mainnet warning treatment. A dark theme is not required for this release.
- Use calmer cards, clearer section headings and compact metric blocks. The destination, amount, network, fee, change, transaction ID and approval controls remain visible at their existing safety gates. Device-search and blockchain-scan waiting messages stay prominent.
- After a practice-network broadcast, the pending banner retains its explorer link until one confirmation. Once the same-session scan reports confirmation, a last-payment receipt keeps that link visible instead of letting it vanish with the pending banner. The receipt lives only in browser memory; it is cleared on wallet import or network change and does not claim to be durable history. No transaction identifier is written to diagnostics or local storage.
- The owner saw the opening and synthetic review/signing layout in a local browser before publication. The preview used invented addresses and amounts and could not import, sign or broadcast. It is not evidence that the packaged Mac window or hardware devices have been retested on 0.4.0.

## Verification and owner check

The checkout and extracted source archive each passed 166 Python tests (8 skipped) and both Node UI regressions. JavaScript syntax, Bash syntax and `git diff --check` passed. The UI regression checks that a confirmed receipt remains when the pending banner disappears and that network changes clear it. The manual GitHub workflow built and verified the Apple Silicon bundle, HWI and HTTPS self-checks, source archive, SBOM, checksums and DMG. No new practice-network send is needed solely for a palette change. The owner should inspect the installed 0.4.0 window once at ordinary Mac size, including the payment review and mainnet warning, before Phase 5. A short Mutinynet practice guide for a novice operator follows UI lockdown as a separate deliverable.

## Release evidence

The manual [GitHub workflow](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36615465478) passed all five jobs and published [v0.4.0](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.4.0) from merge commit `ef4169d84cd0ceac60e0898bc1dc42cddc3c2525`. The source, DMG and SBOM were independently downloaded and matched the published `SHA256SUMS`. `hdiutil verify` reported the downloaded DMG valid. SHA-256 values:

```text
4aff870f6134879683b0a1a602e05f97fdbb99fa14491a73378f536ff6d0b324  bitcoin-easy-multisig-signer-v0.4.0.tar.gz
ebca75103189577ddda553ced6c07c74d1108df54936c38276d5904bbd23e986  Bitcoin-Easy-Signer-v0.4.0-UNSIGNED-TEST.dmg
94f6bfd92d8228f3da7dd7cef3286be1cf8c27549310675edb5baeb33f902030  BUILD-SBOM.json
```
