# v0.6.0 — developer-mode network gate

**Status: candidate. Not published yet.** Nothing in this file is a claim that a
0.6.0 build has been signed, notarized, downloaded or used. The published
release remains [v0.5.1](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.5.1).
Publication is a manual workflow dispatch, and the artifact, hashes and run
number belong in this file only once that run exists.

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
  developer mode reveals. The Mutinynet card no longer carries `checked`.
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
  settings file, so reopening the app returns to mainnet. Before 0.6.0 it was
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

`version.py` moves to `0.6.0`. A minor version is used because the opening
screen and the default network change, not because the engine did.

## Verification

- Python 3.12 full suite: 238 tests passed.
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
  not the reviewed artifact. Build and publish through
  `.github/workflows/build-candidate.yml` (`workflow_dispatch`, `notarize=true`).

## Owner decisions recorded

- The interface change and its framing: owner messages m00035, m00038, m00041.
- Build at 0.6.0, cap the words "Enter Developer Mode", document a developer mode
  for Mutinynet and Testnet4, make Mutinynet the default practice network, and
  present it to developers as an easy test bench while stating it is not the
  primary goal: owner message m00089.
- Sign-off on the written scope, the approved dialog wording as drafted, and
  confirmation switching straight to Mutinynet: m00128.
- The full agreed scope, including the out-of-scope list, is
  [`releases/SCOPE-0.6.0.md`](SCOPE-0.6.0.md). It moved out of the repository root
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
  guide is already owed by this change: the trustee never sees the gate, and a
  practice send does not by itself prove how a given firmware displays a change
  address.
- The untested device question stands: neither the OneKey Classic 1S nor the
  Ledger Nano S displayed the change address on the first live payment. Whether
  each firmware independently re-derives and checks the change script rather than
  trusting the host's marker is still unknown. A practice transaction whose
  change output deliberately points elsewhere is the experiment that would settle
  it, and it must never be run on mainnet.
