# 0.4.15 candidate — OneKey Classic 1S HWI compatibility

## Scope

HWI 3.2.0 already recognizes OneKey Classic 1S through OneKey's Trezor
Compatibility Mode. Direct HWI 3.2.0 enumeration on the owner's Mac returned
`type=trezor`, `label=OneKey Classic 1S`, and `model=trezor_1`. No HWI upgrade,
new device driver, or Python change is needed.

The installed hardened HWI helper failed before enumeration because macOS library
validation rejected the helper's bundled libusb. A temporary copy of that helper,
signed with Apple's `com.apple.security.cs.disable-library-validation` runtime
exception, enumerated the connected OneKey. The candidate scopes the exception to
the HWI subprocess; the main GUI app remains signed with the existing entitlements
(none) and hardened-runtime policy.

The app now preserves a safe HWI-provided label, so the device is shown as
**OneKey Classic 1S** instead of deriving **Trezor 1** from `trezor_1`. The Mac
build runs bundled `hwi --chain test enumerate` before producing a distribution
image, so a missing or unusable libusb fails the build.

## Apple distribution

Apple documents this entitlement as a Hardened Runtime exception for loading
third-party-signed plug-ins or libraries and notes that Gatekeeper applies extra
checks when it is used. It is attached only to the separate HWI helper, not the
application UI. The same Developer ID signing and notarization workflow remains
in place. The local candidate was accepted by Apple's notary service, stapled,
and passed the packaged-app Gatekeeper checks below. This project currently
distributes a Developer ID-signed and notarized DMG outside the Mac App Store; a
Mac App Store submission is a separate distribution target.

## Verification

- Direct HWI 3.2.0 with Python 3.12 enumerated the physical device as OneKey
  Classic 1S through the Trezor backend.
- A temporary Developer ID-signed hardened HWI helper with the scoped runtime
  entitlement enumerated the same device successfully.
- All 237 Python tests passed; all `tests/ui_*.cjs` checks passed. `bash -n`,
  Python compile checks, `git diff --check`, and the source archive build passed.
- The local Developer ID signed build and strict code-signature verification
  passed. Its packaged HWI USB preflight loaded libusb and queried USB descriptors
  without opening the wallet.
- The local 0.4.15 build submitted both the app archive and DMG to Apple using the
  `eas-notary` keychain profile. Both submissions were **Accepted**; the app and DMG
  were stapled and validated. The app copy mounted from the DMG passed Gatekeeper
  assessment as `Notarized Developer ID`. The finished DMG was copied to the
  owner's Downloads folder and its SHA-256 matched the build artifact.
- The first candidate scan returned `LIBUSB_ERROR_ACCESS` while another wallet app
  was running; a later standalone scan observed the device disappearing during
  connection. After those apps were closed and the OneKey was reconnected/unlocked,
  the candidate's bundled HWI enumerated it as `type=trezor`,
  `label=OneKey Classic 1S`, `model=trezor_1`.
- The owner reports that the locally notarized 0.4.15 app worked perfectly with
  the OneKey Classic 1S and its newly created wallet. The subsequent mainnet dry run
  provides more specific physical acceptance evidence below.
- The owner subsequently reports that the live-Bitcoin checks were good. The
  screenshot shows a mainnet dry run reaching final review with two of three
  signatures and the app's explicit "cannot broadcast real Bitcoin" state. The
  privacy-limited diagnostic report records a declared change path, a consistent
  complete scan, transaction preparation, two verified signer responses, and
  verified finalization. No broadcast is reported. The signer UI identified the
  OneKey Classic 1S as one of the two signers. Addresses, amounts, signed bytes,
  and transaction ID are intentionally omitted.
- A follow-up screenshot confirms the signed transaction was cleared from the app
  session. This dry run is not a mainnet payment or Phase 5 broadcast authorization.
- This is a locally built and notarized owner-test candidate. It has not been
  published as a GitHub release. The manual GitHub release workflow remains the
  publication route.
- The OneKey walkthrough and mainnet dry run are owner-reported physical acceptance.
  The dry run did not broadcast. Do not treat it as evidence of a completed on-chain
  payment or authorization to enable mainnet broadcast.

No wallet files, public keys, addresses, device paths, serials, transaction data,
or diagnostic reports are included in this record. Mainnet broadcast remains
disabled.
