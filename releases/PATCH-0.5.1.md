# v0.5.1 — first published mainnet-broadcast release

## Change

Publish the 0.5.0 transaction engine — the build that was signed, notarized and
used for the project's first live mainnet payment — and correct the
change-address guidance that the live run showed to be wrong.

`wallet_service.py`, `signing.py`, `probe.py`, `network_config.py`, `gui.py`
and `desktop.py` transaction logic are identical to the 0.5.0 candidate tagged
`v0.5.0-rc1`. 0.5.1 changes wording, documentation and the published version
string only:

- Hardware signers in the tested set do not display a change address. The app
  marks the change output as belonging to the wallet, so those signers accept it
  silently. Five places in the app told the operator to check change on the
  device, which is not possible there.
- The review screen label now reads **Change — the rest comes back to your
  wallet**, and its help text says plainly that devices usually do not show this
  address and that the check belongs in the wallet software that holds the
  wallet file.
- The "About this app" note, the page footer, the prepared-payment warning and
  `DISCLAIMER.md` now describe the change check the same way.
- The website and the preview images drop the stale "dry run only" and "mainnet
  broadcasts are disabled" language, and the risk notice is restated as
  open-source community software used at the reader's own risk, with no
  warranty, guarantee, approval or audit claim.

No transaction logic changed, so the engine that sent the first live payment is
the engine published here.

## Verification

- Python 3.12 full suite: 238 tests passed.
- All `ui_*.cjs` DOM regression tests passed.
- `bash -n` on every `scripts/*.sh`; `git diff --check` clean.
- Built and published by the GitHub Actions workflow from commit
  `e833162cb4cf6d8b50a2bc76254829410d9dffd9` (run `36948967931`), not from a local
  build; the published artifact is the workflow's.
- Apple Silicon Developer ID signing — `Developer ID Application: Bitseeker LLC
  (B8G5L7M8TB)`, hardened runtime — and Apple notarization. The ticket is stapled
  to both the app and the DMG and both validate; `spctl` accepts the app as
  `Notarized Developer ID`; `hdiutil verify` reported a valid image.
- The `com.apple.security.cs.disable-library-validation` entitlement is confined to
  the nested `hwi` helper; the main app carries no entitlements (payload 0 bytes).
- Shipped `Contents/Resources/ui.html` is byte-identical to the repository copy:
  `cd3d97641e283b76798f695ad8a874cf28a9fa60535232393e6ad3573e6c42aa`.
- Main executable SHA-256
  `5b1661e9da974b49bc6b55afdd59804f0998b4bbe156adc1970652eb7dfc4cfd`;
  nested `hwi` SHA-256
  `33fc787fbe68b2f3763680c3292ae9adc5d4d4481c8f40f912bad9e871ae8329`.
- Published DMG: `Bitcoin-Easy-Signer-v0.5.1-macOS.dmg`.
  SHA-256: `73691cc4fd71591cd53acc22f08273a97b20cf09593e6c8009bd5b39706387d0`.
- Matching source archive: `bitcoin-easy-multisig-signer-v0.5.1.tar.gz`.
  SHA-256: `b1b3f7e4018fdd1d94758867ccaa05fd083c35f7624bc1ad2ba8abb1ee1c8ba9`.
- `BUILD-SBOM.json` SHA-256
  `8a31552ac5d5c1e46d589313afbc3a4554892eda9204b7d11ad95fc79b109ed6`.
  All three digests verify against the release's published `SHA256SUMS`.
- The extracted source archive reproduces the tree: `version.py` reads `0.5.1`,
  every application module and `ui.html` are byte-identical, and `releases/` holds
  21 records.

## First live mainnet payment

The owner made the project's first real mainnet payment with the 0.5.0
candidate. It was a 2-of-3 native-SegWit spend from the owner's live wallet,
signed by an OneKey Classic 1S (through HWI's Trezor backend) and a Ledger
Nano S, broadcast through the app, and confirmed on chain at block height
969509.

The transaction was verified independently of the app: the confirmed
transaction was decoded from two independent explorers, and its change output
script was compared against the change script derived locally from the wallet
file. Transaction identifiers, addresses and amounts are deliberately not
recorded here, because this repository is public and this is the owner's live
wallet. Whether to publish those identifiers at all is the owner's decision, on
legal advice; a reviewer may request them and the raw evidence.

Both signers showed the destination, amount and fee for approval. Neither
showed the change address. That observation produced the wording change above.

## Limits

- One confirmed mainnet payment is not an audit and does not establish that a
  later payment is safe.
- No independent full-tool security review has been recorded.
- The fee ceilings remain 1–25 sat/vB and 10,000 estimated sats, with no
  in-app fee bump. Transactions signal RBF.
- Whether a given firmware independently re-derives and checks the change
  script, rather than trusting the host's change marker, has not been
  established by test. An untested firmware could still mask a rewritten change
  output; the operator is now told to check change in their own wallet software
  instead.
