# 0.4.2 — Jade device authorization wait

## Owner observation

In the installed 0.4.1 app, the owner completed a Mutinynet payment with Ledger and Jade. The privacy-limited report recorded two verified signer responses, a verified final transaction and an accepted broadcast. The owner supplied a public transaction link; a read-only query to Mutinynet's Esplora API reported it confirmed. The report does not name which verified response came from which device, so the device pairing comes from the owner's account. No wallet file, address, PSBT, raw transaction or diagnostic file is committed here.

The owner then noted that Jade setup during **Check connected devices** can require two PIN interactions on its small screen. Careful entry, menu corrections and unfamiliarity can take two or three minutes or longer. Version 0.4.1's one-minute device-search timeout could interrupt this before signing begins. Bitcoin Core HWI 3.2.0 constructs a `JadeClient` during `enumerate` and calls `auth_user` in its constructor, so the long wait belongs to device discovery itself. The selected Jade `getxpub` check may also authenticate again. This is separate from the ten-minute transaction-signing limit added for Ledger in 0.4.1.

## Change

- Bound HWI enumeration to 180 seconds to allow Jade authorization. HWI enumerates all connected devices in one call, so the overall discovery call has this bound even when the device is not Jade.
- Give every matched device `getxpub` verification call 180 seconds; it may ask for further authorization. Keep explicit transaction signing at 600 seconds.
- Tell the operator that Jade PIN entry can take up to three minutes and that device discovery signs nothing. No PIN is entered into or stored by the app.
- Keep the same network-independent wallet and signing engine. No transaction construction, signature verification, broadcast, fee or mainnet gate changes.

## Verification and remaining gate

Synthetic tests assert the exact timeout passed to HWI enumeration, Jade xpub verification, other-device xpub verification and signing. Existing local API and interface regressions remain in the release gate. A physical multi-minute Jade PIN-entry test has not been performed in this build; the owner should use 0.4.2 on the next ordinary Mutinynet device check rather than make a payment solely to test the timer. Mainnet broadcast remains disabled.

## Published release evidence

- GitHub's [manual 0.4.2 workflow](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36628229636) passed the source archive tests, Apple Silicon app tests and packaging checks, checksum generation, and release publication from commit `13a78cb0892890f3f29a8d8d2f1e5413e9eee16c`.
- The [v0.4.2 release](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.4.2) contains the DMG, source archive, dependency inventory, and checksum file. Downloaded release assets matched `SHA256SUMS`; `hdiutil verify` also accepted the DMG.
- SHA-256: DMG `435c611133f9e66972f0a868d4f56b0a21f452398e06d71cdc2e99717613b7e6`; source `da21b8bb771cbeb8e67b406981882db11eb615f4580b3f82899be5e25e3402e8`; SBOM `c9318094ee3f3e1ce630691cc7e470193ef5949b6f9053fec249d0d63e8f9424`.
- The first manual run failed its source job because `ci/build-candidate.yml` had diverged from `.github/workflows/build-candidate.yml`; [PR #15](https://github.com/cjtsh/bitcoin-easy-multisig-signer/pull/15) synchronized them and the successful run used that correction. No 0.4.2 artifact was published from the failed run.
- The owner's physical Ledger + Jade payment is evidence for installed 0.4.1. The longer 0.4.2 authorization window is still awaiting incidental physical use. It does not require a new payment just to test the timer.
