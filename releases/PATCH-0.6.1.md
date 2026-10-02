# v0.6.1 — developer-mode network gate

**Status: candidate. Not published yet.** A signed and notarized 0.6.1 candidate
was built in workflow run
[36956904445](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36956904445)
from commit `caf8b4f` with a non-publishing dispatch; its evidence is recorded
below and the artifact has not yet been installed or opened, so nothing yet shows
that 0.6.1 works. No 0.6.x version has been published; the published release remains
[v0.5.1](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.5.1).

The version moved from 0.6.0 to 0.6.1 before publication, so nothing was ever
published as 0.6.0 and no `v0.6.0` tag exists. A signed and notarized 0.6.0
candidate was built first and is superseded: workflow run
[36954844052](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36954844052)
from commit `f147141`, made with a non-publishing dispatch, so no tag and no
release were created. Opening that candidate is what found the defect 0.6.1
fixes: live Bitcoin was one of the cards inside developer mode, so one window
could say "practice coins only" and "MAINNET · REAL BITCOIN" at the same time.
The artifact names, hashes and verification immediately below are the 0.6.0
candidate's record, kept because it is what the owner opened; the 0.6.1
candidate record follows it.

## Change

Move the choice of network off the opening screen and behind a deliberate step.
The app now opens on **Bitcoin mainnet**; Mutinynet and Testnet4 are reached
through a button at the top of the opening screen labelled **Enter Developer
Mode**.

This is an interface change. `wallet_service.py`, `signing.py`, `probe.py`,
`network_config.py` and the transaction logic in `gui.py` and `desktop.py` are
unchanged from 0.5.1. No transaction or signing code was touched, so the engine
that made the project's first live mainnet payment is the engine in this build.
Nothing here is new transaction capability, and it must not be described as
such.

Why: the target operator is a spouse, executor, accountant or estate
professional who cannot evaluate a three-network radio control, and reaching a
practice network requires a second wallet file, two or three devices and coins
from somewhere the app does not provide. A control that person cannot use only
adds a way to get the network wrong. The capability is kept, not removed — it
moves, and the documentation now names it.

- The network cards and their explanation are inside a hidden panel that only
  developer mode reveals. The panel offers **Mutinynet and Testnet4 only**: live
  Bitcoin is not one of its options, because it is the network the gate returns
  to rather than a choice inside it, and `setChain("main")` is refused while the
  gate is open. The Mutinynet card no longer carries `checked`.
- **Enter Developer Mode** opens a dialog stating that the operator is leaving
  live Bitcoin, that practice coins have no value and no other use, that the app
  provides neither a practice wallet nor its coins, and that a payment to the
  wrong network cannot be undone by the app. Confirming switches the session to
  **Mutinynet**, the default practice network; Testnet4 remains selectable.
  Cancelling changes nothing.
- Entering or leaving developer mode clears the loaded wallet session, the scan
  and any prepared payment, then reloads the server settings and fee quote for
  the new network — the same clearing the network cards already performed.
- The selected network stays in memory for the session. It is written to no
  settings file, so reopening the app returns to mainnet. Before 0.6.1 it was
  already session-only; this release must not introduce persistence, because a
  practice network that outlived a restart is the specific hazard the gate could
  create.
- The gate refuses to change network while a payment is prepared, and says why.
  It is never disabled on a practice network — an earlier draft did that, which
  would have trapped the operator in developer mode with no way back.
- The orange/green viewport frame and the network badge are never hidden and
  cannot disagree: the frame is toggled by the mainnet condition alone, and the
  badge text comes from a single record of the three network names.
- Refreshing the page while the local app still holds a practice-network wallet
  reopens developer mode so the cards stay reachable and the badge matches the
  network in force.
- Removed one dead field: `broadcasting_available` was hardcoded `True` in the
  `/api/settings` response and read by nothing in `ui.html` or the tests'
  subject code. It is gone from `gui.py` and from the assertion that checked it.

Documents corrected with the code, because each still said the app opened on a
practice network: `AGENTS.md` (the opening-network invariant), `PHASE-HANDOFF.md`,
`README.md` and the public site `docs/index.html`. Developer mode is documented
in `README.md` and on the public site as a test bench that is explicitly **not**
the app's primary purpose, with the honest limits: the app cannot fund a
practice wallet, the selection is session-only, and the frame and badge always
name the network in force.

`version.py` moves to `0.6.1`. A minor version is used because the opening screen
and the default network change, not because the engine did. The version was taken
to 0.6.0 for the first candidate and to 0.6.1 before anything was published; the
engine code is identical in both.

## Verification

- Python 3.12 full suite: 240 tests passed (238 before this change, plus two new
  `tests/test_workflow_config.py` cases covering the candidate dispatch mode and
  the corrected release notes).
- All nine `ui_*.cjs` DOM regression tests passed, including the new
  `tests/ui_developer_mode.cjs` (ten numbered checks: opening state, dialog copy,
  cancel, confirm, all three networks against frame and badge, return to Bitcoin,
  refusal while a payment is prepared, the real card change handler, and page
  refresh on a restored practice wallet).
- `tests/ui_send_mode.cjs` rewritten: the network-cards-on-the-opening-screen
  assertions were the behaviour being replaced. It now asserts the app opens on
  mainnet, that cards hidden behind the gate cannot move the app even if their
  radios are checked, that a wallet opened on a practice network drives the
  selection, and that all three networks stay reachable through `setChain`.
- `tests/test_palette.py` keeps its intent — the two practice networks must
  remain distinguishable in the badge — but no longer asserts the removed
  ternary; it checks the network-name record instead.
- `bash -n` on every `scripts/*.sh`; `git diff --check` clean.
- No DMG was built locally. `scripts/build-macos.sh` gates on a pinned `libusb`
  digest that this Mac's Homebrew `libusb` does not match, so a local build is
  not the reviewed artifact. The candidate was built in CI by
  `.github/workflows/build-candidate.yml` (`workflow_dispatch`, `notarize=true`,
  `publish=false`).

## Candidate build evidence — 0.6.1

Built by a non-publishing dispatch of the manual build workflow, so the run
produced artifacts and created no tag and no release.

- Workflow run
  [36956904445](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36956904445),
  head commit `caf8b4f`, queued 2026-10-02T02:42:58Z, all five jobs successful,
  dispatched with `notarize=true` and `publish=false`. The publish job logged
  `==> Candidate build: v0.6.1 was built and NOT published.` The repository's
  releases still end at v0.5.1 and `git ls-remote --tags origin 'refs/tags/v0.6*'`
  is empty.
- `Bitcoin-Easy-Signer-v0.6.1-macOS.dmg` — 34,877,254 bytes, SHA-256
  `ce4f8a781fec2657d42fa8459b0f9d0d40e6bd4c195fa8d3df26ab85bc7b565e`
- `bitcoin-easy-multisig-signer-v0.6.1.tar.gz` — SHA-256
  `8c52b38a139cc4878ed9dbe21ce448a0f553941561d7e6ec6bb6f6d293eea54e`
- `BUILD-SBOM.json` — SHA-256
  `65c4a3f4ba574bb1b4bd53aafe38a7db931cb992809285b27feab98acf4663bd`

All three hashes match the run's `SHA256SUMS`. The workflow artifacts expire
2026-12-31T02:43:01Z.

Verification of the downloaded file: `hdiutil verify` reports the checksum VALID;
the mounted bundle reports `CFBundleShortVersionString 0.6.1`; `codesign -dvv`
reports `Authority=Developer ID Application: Bitseeker LLC (B8G5L7M8TB)` and
`TeamIdentifier=B8G5L7M8TB`; `codesign --verify --strict --deep` is OK;
`spctl -a -t exec -vv` on the app reports `accepted source=Notarized Developer ID`;
`xcrun stapler validate` works on the app inside the image and on the disk image
itself. Apple's own record (`xcrun notarytool history --keychain-profile
eas-notary`) lists the app zip `1c5a990b-37ab-4bcf-8e8a-dbbf5191b8be` and the DMG
`e00f19a2-3a37-4c1a-b818-714d17345c15`, both **Accepted** with `issues: None`. The
DMG submission's `ticketContents` contains the app's CDHash
`5a314ab32963f80bbc05f6e20f0c714c7776dee8`, which is exactly the CDHash
`codesign -dvvv` reports for the app inside the downloaded image, so the ticket
belongs to this build.

A copy was placed at `~/Downloads/Bitcoin-Easy-Signer-v0.6.1-macOS.dmg` with the
same SHA-256. The candidate has **not been installed or opened**. Nothing here
shows that 0.6.1 works: the checks show that the artifact is the one the workflow
built, signed by Bitseeker LLC and notarized by Apple. The owner's walkthrough is
what would close that gap.

## Candidate build evidence — the superseded 0.6.0 candidate

A candidate was dispatched so the owner could install and open it before anything
is published. `publish=false` is a second, independent dispatch input added for
this purpose: the release job stops before it creates a tag or a release, and the
artifacts stay on the workflow run. No `v0.6.0` tag exists and
`releases?per_page=5` still lists `v0.5.1` as the newest release.

- Run: [36954844052](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/36954844052),
  `workflow_dispatch` on `dev-mode-0.6.0`, commit
  `f147141cb69c4da5409c506eabcc63bdeb2b42f2`. All five jobs passed (Read version,
  Apple Silicon DMG, Source archive and tests, SHA256SUMS, Publish release), and
  the release job reported `==> Candidate build: v0.6.0 was built and NOT published.`
- Artifacts: `Bitcoin-Easy-Signer-v0.6.0-macOS.dmg` (34,875,710 bytes),
  `bitcoin-easy-multisig-signer-v0.6.0.tar.gz`, `BUILD-SBOM.json`, `SHA256SUMS`.
- SHA-256, taken from `SHA256SUMS` and re-computed on the downloaded file:
  DMG `2ab9d1ea5374d1975ced5b1dc34f0904dad400573cdf4078cc8551db921be99d`,
  source `5c495085f32ea14e67217c21a2f02a5c97f8965f698a9bbd7bdecbfb29833df1`,
  SBOM `61cba7ac6a7fde44a38843a04d6955bf18674e4e7321ed59449e9add84867838`.
- Checked on the downloaded file: `shasum -a 256` matches `SHA256SUMS`;
  `hdiutil verify` reports the checksum is VALID; the mounted bundle reports
  version 0.6.0 and is signed
  `Developer ID Application: Bitseeker LLC (B8G5L7M8TB)`; `codesign --verify
  --strict` passes; Gatekeeper's own assessment of the app returns `accepted
  source=Notarized Developer ID`; `stapler validate` succeeds on both the app and
  the DMG, so a first launch needs no network round trip.
- The DMG is not itself a signed disk image: `spctl -a -t open` rejects it with
  `source=no usable signature`. That is expected and unchanged from every
  published 0.4.12+ release — the app inside is signed and notarized, and the
  stapled ticket is what Gatekeeper assesses on a normal double-click.
- Notarization, from Apple's own submission history (`xcrun notarytool history`)
  and the per-submission logs (`xcrun notarytool log`): the app zip was submission
  `81f48a4e-e06f-4b28-9680-20fcfd724e10` (uploaded 02:19:26Z, **Accepted**) and the
  DMG was submission `58b5f4b8-e73b-48a4-9a5e-d372be8d68cd` (uploaded 02:20:13Z,
  **Accepted**), both with `issues: None`. The DMG's `ticketContents` names the
  app's CDHash `bddc6c8c1bd067e09ae60c3062c3b5b9e00f2347`, which is the CDHash
  reported by `codesign -dvvv` for the app inside the downloaded image, so the
  ticket belongs to exactly this build. No submission timed out and none had to be
  retried: a rejected submission cannot be stapled, and the staple is present.
- For comparison, Apple's history shows the retry pattern this project has hit
  before — two submissions for v0.4.14 and five for v0.4.13, all Accepted; each
  version in the history has an Accepted DMG and an Accepted app zip, including
  the published v0.5.1.
- Not yet done: the candidate has not been installed, opened or used by the owner.
  Until that happens, nothing here is evidence that 0.6.0 works, and no claim
  should be made that it has been tested.

## Owner decisions recorded

- The interface change and its framing: owner messages m00035, m00038, m00041.
- Build at 0.6.0, cap the words "Enter Developer Mode", document a developer mode
  for Mutinynet and Testnet4, make Mutinynet the default practice network, and
  present it to developers as an easy test bench while stating it is not the
  primary goal: owner message m00089.
- Sign-off on the written scope, the approved dialog wording as drafted, and
  confirmation switching straight to Mutinynet: m00128.
- Closing the change-address display question as not answerable on the devices,
  and asking for a notarized build to test before anything is published: m00981.
  The build was made as a candidate dispatch (`publish=false`), so the test
  artifact is the artifact that would ship, with no release created.
- After opening the 0.6.0 candidate: live Bitcoin must not be an option inside
  developer mode, only the practice networks, and the version becomes 0.6.1
  (m01190, "Live Bitcoin does not belong in the developer mode, remove it Only
  the test nets. make 1.6.1"). The panel, the refusal in `setChain`, the step-1
  note and both UI test files were changed for it; the transaction path was not.
- The full agreed scope, including the out-of-scope list, is
  [`releases/SCOPE-0.6.1.md`](SCOPE-0.6.1.md). It moved out of the repository root
  with the other per-version records so that `scripts/build-source.sh` ships it in
  the source archive, which it does for everything under `releases/`.

## Deliberately out of scope

- **F2** the custom mainnet broadcaster is not genesis-verified at broadcast time
  (`gui.py:905`); mainnet `checkpoint_height` is `None`. Low severity — the
  transaction is already signed and cannot be stolen, the explorer was checked
  during the scan, and the worst case is a silent drop — but it is not fixed here.
- **F3** `invalidateReview()` resets `finalTxid` but not `finalChain`, leaving
  stale final-screen state. Separate release.
- **F5** the `--dsh-check-libusb` debug flag still ships in
  `scripts/hwi_entry.py`.
- **F6** `xattr -cr "$app"` in `scripts/build-macos.sh` strips bundle extended
  attributes, including quarantine.
- The plain-language operator guide and the nontechnical-user walkthrough remain
  open Phase 5 items. This release documents developer mode; it does not write
  the trustee-facing guide, which the owner should shape. One paragraph of that
  guide is already owed by this change: the trustee never sees the gate, and the
  change address is checked in the wallet software that holds the wallet file,
  not on a device screen.
- The change-address display question is **closed by the owner as not answerable
  on these devices** (m00981): the small hardware signers do not display the
  change address and will not, so the experiment that would have settled whether
  each firmware re-derives the change script is no longer worth building. The app
  keeps marking the change output as belonging to the wallet in the reviewed
  PSBT, and the standing guidance is unchanged — check the change address in the
  wallet software, not on a device screen. The owner's alternative, giving the
  operator some other place where the app shows it is doing the right thing, is
  recorded here as a documentation idea for the operator guide, not as work in
  this release.

## A candidate build can now be made without publishing

Recorded separately because it changes the release machinery, not the app. The
workflow published on every successful dispatch, and `tests/test_workflow_config.py`
enforced that a dispatch was a publication. That made the first dispatch of a
version the point of no return: a published tag is never rebuilt, so the only way
to correct an artifact nobody had opened yet was to bump the version.

`workflow_dispatch` now takes a second, independent boolean, `publish`
(default `true`, so an ordinary dispatch behaves exactly as before). With
`publish=false` the release job stops before it creates a tag or a release and
writes the notes into the run summary instead; the DMG, the source archive, the
SBOM and `SHA256SUMS` stay attached to the run as artifacts. No release object
exists, so nothing becomes public and nothing can be published by accident.
`notarize` and `publish` are deliberately separate: the owner tests the artifact
that would ship, not a differently-built one.

The auto-written release notes were also corrected: they still said "Mutinynet is
the opening network", which 0.6.1 makes false. A release would have told every
downloader to expect the opposite of what the build does. A test now renders the
notes block and fails if that claim returns.
