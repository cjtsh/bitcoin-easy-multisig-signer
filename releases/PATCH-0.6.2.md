# v0.6.2 — retiring a review also retires its network

**Published 2026-10-02** as tag
[v0.6.2](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.2)
from commit `7b4db85`, built by workflow run
[36959242210](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36959242210)
with a publishing dispatch, after the candidate below had been built and
verified. This record covers what the fix is, what it does not change, and how
it was verified.

## Why this release exists

The owner chose it as the next piece of work after 0.6.1 was published
(m01412), from a short list that also held the plain-language operator guide and
the F2/F5/F6 findings. It is the defect recorded as **F3**.

`ui.html` keeps the network that the final screen was built for in
`finalChain`, and the broadcast posts that value as the backend's mainnet
opt-in:

```js
confirm: true, mainnet_opt_in: finalChain === "main",
```

`invalidateReview()` retired every other part of a finished review — the
prepared PSBT, the review id, `finalTxid`, every value on the final panel — but
not `finalChain`. Two other places that retire a review had the same gap: the
clear-signed handler, which discards the signed bytes, and the signer-step reset
that runs when a new payment is prepared.

**This was not reachable and is not a fund risk.** A broadcast also requires a
non-null `finalTxid`, and `finalTxid` is only ever set beside `finalChain` in
`showFinal()`, so a broadcast could not be sent from a retired review at all.
The stale value mattered because it was the one field feeding the mainnet opt-in
that outlived the payment it described, and the honest description of a
defence-in-depth fix is that it is one — not a vulnerability.

## Change

All three sites now clear the chain together with the rest of the review:

- `ui.html` `invalidateReview()` — `finalTxid = null; finalChain = null;`
- `ui.html` clear-signed handler — `finalTxid = null; finalChain = null;`
- `ui.html` signer-step reset — `if (reset) { … finalTxid = null; finalChain = null; }`

A comment at each site records why the network belongs to the review: the
broadcast derives its mainnet opt-in from it.

## Verification

`tests/ui_broadcast_outcome.cjs` now reads the body of the broadcast request and
pins three things:

1. after `invalidateReview()`, `finalChain` is `null`;
2. a broadcast sent with no finalized network carries `mainnet_opt_in: false`
   and still names the transaction it was given;
3. a payment genuinely finalized on mainnet still carries
   `mainnet_opt_in: true`, so the opt-in itself is untouched.

The first assertion was checked against the unfixed file, where it fails:

```
AssertionError [ERR_ASSERTION]: retiring a review must also retire the chain the mainnet opt-in is read from
  expected: null,
```

The full gate was re-run with the fix in place: 240 Python tests, all nine
`tests/ui_*.cjs`, `git diff --check`, `bash -n` on every shell script, the
workflow YAML parse, and the source-archive build.

## What did not change

- The transaction and signing engine is unchanged from 0.5.1. Nothing about how
  a payment is built, signed, finalized or submitted changed.
- No user-visible behaviour changes. The final panel, the gate, the frame and
  the badge are as 0.6.1 left them.
- The mainnet opt-in still defaults to `False` in the backend, and the
  final-screen confirmation is unchanged.

## Deliberately out of scope

- **F2** — the custom mainnet broadcaster is not genesis-verified at broadcast
  time (`gui.py:905`; the mainnet `checkpoint_height` is `None`). Low severity:
  the transaction is already signed, so it cannot be stolen, and the explorer is
  verified during the scan. Left as recorded, not fixed here.
- **F5** — the `--dsh-check-libusb` debug flag ships in production
  `scripts/hwi_entry.py`.
- **F6** — `xattr -cr "$app"` in `scripts/build-macos.sh` strips bundle extended
  attributes, including quarantine.
- The plain-language operator guide and the nontechnical walkthrough remain
  deferred to the owner.

## Published build — 2026-10-02

Published as tag
[v0.6.2](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.2)
from commit `7b4db85` (workflow run
[36959242210](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36959242210),
`notarize=true publish=true`), release published 2026-10-02T03:18:57Z with four
assets:

- `Bitcoin-Easy-Signer-v0.6.2-macOS.dmg` — 34,875,852 bytes, SHA-256
  `5f648aa1728127970c1182760026c742d1c66be400fa171f7a1f19470ef1ab53`
- `bitcoin-easy-multisig-signer-v0.6.2.tar.gz` — 709,626 bytes, SHA-256
  `a901a66bf7f4ab0144c09ad510720e4443e16f93ff0bb71d7c51c9d29eb5f0d5`
- `BUILD-SBOM.json` — 7,023 bytes, SHA-256
  `4e49843bb6adf2df4bb22c057d49680dd7dc9b92985b7a5b15944d8654a37168`
- `SHA256SUMS`

Both artifact hashes recomputed from the downloaded release assets match the
published `SHA256SUMS`. The published DMG is **not byte-identical** to the
candidate below (34,874,193 bytes), because it is a fresh build of the same
commit; the published hashes above are the ones that apply to the download.

Verified on the downloaded published DMG: `hdiutil verify` VALID; the bundle
reports `CFBundleShortVersionString 0.6.2`; `codesign -dvvv` reports
`Authority=Developer ID Application: Bitseeker LLC (B8G5L7M8TB)`,
`TeamIdentifier=B8G5L7M8TB` and
`CDHash=a6452a56e2fa875a4bc48ab25e77813441ad6c4b`; `codesign --verify --strict
--deep` OK; `spctl -a -t exec -vv` accepts it from a Notarized Developer ID;
`xcrun stapler validate` works on the app inside the image and on the DMG itself.
Apple's record lists the DMG `fa13c97f-3786-4d36-81bc-6baefefa6c43` and the app
zip `07fda595-4cc7-475d-8e1c-1a97848601db`, both **Accepted**.

The published build has not been installed or opened. The checks show that the
published files are the ones the workflow built, signed by Bitseeker LLC and
notarized by Apple.

## Candidate build evidence — the superseded candidate (run 36958728418, commit `8712dca`)

A non-publishing dispatch (`notarize=true publish=false`): workflow run
[36958728418](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36958728418)
from commit `8712dca` ("0.6.2: retire the network with the review it belonged
to"), queued 2026-10-02T03:07:07Z and successful. Nothing was published: no
`v0.6.2` tag and no release were created, and the published release is still
[v0.6.1](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.6.1).

Artifacts downloaded from the run:

- `Bitcoin-Easy-Signer-v0.6.2-macOS.dmg` — 34,874,193 bytes, SHA-256
  `6e448a22526fa9017fc3c072820996f05fd727262f337ba4a5bbceabe3546a76`
- `bitcoin-easy-multisig-signer-v0.6.2.tar.gz` — 708,671 bytes, SHA-256
  `7439ef199ba2aee0ddaadcfee98845381e295df81476d24a1599df4f207fa83f`
- `BUILD-SBOM.json` — 7,023 bytes, SHA-256
  `7dba727b3424f8408be9ba0fe4d779b9c76c31cf7f226a89744474c5c2021316`

All three recomputed from the download match the run's `SHA256SUMS`. A copy of
the DMG sits at `~/Downloads/Bitcoin-Easy-Signer-v0.6.2-macOS.dmg` for
double-clicking.

Verified on the downloaded DMG: `hdiutil verify` VALID; the bundle reports
`CFBundleShortVersionString 0.6.2`; `codesign -dvvv` reports
`Authority=Developer ID Application: Bitseeker LLC (B8G5L7M8TB)`,
`TeamIdentifier=B8G5L7M8TB` and
`CDHash=5d17d33075d7e924dd2e817339958ce7f1835dfa`; `codesign --verify --strict
--deep` OK; `spctl -a -t exec -vv` reports `accepted source=Notarized Developer
ID`; `xcrun stapler validate` works on the app inside the image and on the DMG
itself. Apple's record (`xcrun notarytool history --keychain-profile eas-notary`)
lists the DMG `85e4ee74-43b7-4b2a-b0f1-0056b995e944` and the app zip
`37cd7d26-c2df-424c-863a-2f3c9a9aabab`, both **Accepted**.

The candidate has not been installed or opened, so nothing here shows that 0.6.2
works; the checks show that the artifact is the one the workflow built, signed
by Bitseeker LLC and notarized by Apple.

## Owner decisions

- The owner asked for the stale-review state to be fixed as 0.6.2, choosing it
  from three offered pieces of work (m01412).
