# Scope — version 0.6.1: the developer-mode network gate

Status: **signed off by the owner (m00128: "Use my draft as written", "Yes —
confirm switches to Mutinynet", "Build it now") and implemented on the
`dev-mode-0.6.0` branch, off `main` at `fcaa327`.** The implementation, tests and
documentation are complete, and the release is **not published**: no published
DMG exists and nothing has been published under any 0.6.x version. `version.py`
was taken to 0.6.0 for a first candidate and moved to **0.6.1** before
publication, after the owner opened that candidate and directed that live
Bitcoin must not be an option inside developer mode (m01190); the amendment at
the end of this file records exactly what changed. The delivered record is
[`PATCH-0.6.1.md`](PATCH-0.6.1.md); this file stays as the agreed scope it was
written against and is not rewritten to match apart from that amendment. It sits
in `releases/` with
the other per-version records, which is where the source archive picks it up.

## Why this release exists

The main screen currently offers three networks as a radio choice: Mutinynet,
Testnet4 and Bitcoin LIVE. That control is correct for a developer and wrong for
everyone this app is built for.

The product goal is a nontechnical person — spouse, executor, trustee, lawyer,
accountant — spending from an existing multisig wallet with a BSMS file and the
hardware they already own. That person cannot use a test network even if offered
one: reaching it needs a second wallet built in Sparrow, two or three devices,
a freshly imported wallet file and a faucet for a Signet they have never heard
of. A control whose value the operator cannot evaluate does not belong in the
flow they must complete to send money.

The owner's decision (recorded here as instructed, rather than raised as a
question):

> Test networks stay fully supported. They come off the main screen and sit
> behind an explicit **Enter Developer Mode** gate on a warning dialog. The
> opening network becomes Bitcoin. Documentation tells developers the gate is
> there and that it is a good test bench.

## What is already built — do not rebuild it

This was verified in the current source, not assumed. The network *signalling*
already exists and matches the owner's intent:

- `ui.html` defines a `--frame` role in both themes: `#4ade80` light, `#22c55e`
  dark, overridden to `#f97316` (orange) by `body.live-mode`. The frame is drawn
  as a fixed, `pointer-events:none` `body::after` border, so it surrounds the
  viewport at any page height and can never swallow a press.
- The source comment already states the rationale in the owner's own terms:
  *"Real Bitcoin wears an orange frame; practice coins wear green. That single
  change is the whole of mainnet mode… A frame is a better signal than a
  repaint. It is peripheral, so it never competes with the amount or the
  destination for attention; it is unmistakable, because it surrounds
  everything."*
- `updateNetworkUI()` (around `ui.html:800`) already sets the badge text
  (`● MAINNET · REAL BITCOIN` / `● <NETWORK> · NO REAL BITCOIN`), toggles
  `body.live-mode`, and shows or hides the mainnet `#live-banner`.
- Network selection is **already session-only and in memory**. It is held in the
  backend session as `state.chain` (`gui.py:395`, set at `gui.py:644`) and read
  back by `/api/status` (`gui.py:709`). The only file on disk is
  `network_settings.py`'s `settings.json`, which stores **server URLs only** —
  never the selected network. A restart therefore returns to the opening
  network with no file write involved.

The consequence is worth stating plainly: **the "sticky test network" hazard
does not exist today, and this release must not introduce it.** No new
persistence is added by this work.

## Decisions made by the agent, under the owner's delegation

The owner directed that delegated decisions be made, explained and recorded
rather than brought back as questions. These are the judgements made here; any
of them can be overruled at sign-off.

1. **Opening network is Bitcoin.** The `checked` attribute moves from the
   Mutinynet radio to none, and the app's initial in-memory chain becomes
   `main`. This directly contradicts a written invariant — see
   "Invariant that must change" below.
2. **Developer mode is session-scoped; no settings-file write.** Entering the
   mode lives in app memory exactly as `state.chain` does. Closing the app
   returns to Bitcoin on next launch.
3. **Mutinynet is the default practice network.** The owner directed this
   explicitly. It is the fast, cheap test path and already the default test
   network in the radio group.
4. **Confirming the "leaving live Bitcoin" dialog selects Mutinynet and switches
   the active chain.** The alternative — reveal the picker but stay on Bitcoin
   until a second click — leaves the app on a chain the operator did not
   confirm while displaying practice-network chrome. One deliberate
   confirmation crossing the gate is the clearer contract, and it matches the
   owner's description: pressing the button *"takes you to the Mutinynet switch
   or the Testnet4 switch."*
5. **A prepared payment blocks the transition. Wallet state alone does not.**
   If a payment is prepared or signed, **Enter Developer Mode** is disabled with
   a plain-language explanation, because `AGENTS.md` requires the frozen
   `PreparedPayment` to stay bound to its selected chain. With no prepared
   payment, entering or leaving developer mode clears the loaded wallet session
   and its scan and resets to the new chain — the same clean transition the app
   already performs when the operator changes network. Guessing across a chain
   boundary is exactly the failure this release is meant to prevent.
6. **The orange/green frame and the network badge are never removed.** We hide
   the *picker*, never the *state*. The active network stays legible on the main
   screen, the review screen and the final screen, in developer mode or out of
   it. The frame and the badge must never be able to disagree: it must be
   impossible to be on a practice network with an orange frame, or on Bitcoin
   with a green one. A DOM test will assert this pairing.
7. **F4 is deleted in this pass.** `broadcasting_available` is hardcoded `True`
   and referenced nowhere in `ui.html`; this release is already the network UI
   pass, so leaving a dead network field behind for a third release is worse
   than removing it. F2, F3, F5 and F6 stay out of scope: F3 is a real
   stale-state bug but a separate one, and mixing it into an interface release
   would muddy the "no transaction-logic change" claim this release depends on.

## The one invariant that must change

`AGENTS.md` currently ends the change-policy bullet with:

> Mutinynet is the opening network; all networks remain selectable.

The new rule is that **Bitcoin is the opening network, and all networks remain
selectable through the developer-mode gate**. The second half is preserved — the
owner expressly wants the capability kept and documented, not rolled back — but
the first half is a deliberate, recorded change and the sentence must be
rewritten rather than quietly contradicted. The same claim appears in
`PHASE-HANDOFF.md` ("Mutinynet is the fast practice path") and in
`CURRENT-STATUS.md`; each needs the same correction so no document still says
the app opens on a practice network.

## Interface change

**Placed where:** at the top of the screen beside the theme toggle
(`.theme-toggle`, `ui.html:135-138`), which is already the established home for
a quiet secondary control. Label text is exactly **Enter Developer Mode**,
title-cased as the owner specified.

**Removed from the main screen:** the `chain-choice` radio group
(`ui.html:332-343`) and the radio cards' CSS. The explanatory line at
`ui.html:345` — *"Mutinynet and Testnet4 are separate test networks. Each needs
its own wallet and its own coins to work."* — is now relevant only inside
developer mode and moves there with the picker.

**Revealed inside developer mode:** the same three-way choice (Mutinynet,
Testnet4, Bitcoin LIVE) so a developer can move between practice networks and
back to real Bitcoin, plus a persistent indicator stating which practice
network is active.

**Proposed warning-dialog copy, for the owner's approval before it is built.**
Written to the project's public-language rules: no "safe", "approved",
"verified", "guaranteed", "production-ready".

> **Enter Developer Mode**
>
> You are leaving the live Bitcoin network.
>
> Mutinynet and Testnet4 are practice networks. They use test coins that have no
> value, and they allow you to try this app without spending real Bitcoin.
>
> Reaching a practice network needs its own wallet and its own test coins, which
> this app does not provide. Your real Bitcoin is left untouched while you are
> here. A payment made to the wrong network cannot be undone by this app.
>
> [ Cancel ]  [ Enter Developer Mode ]

**Proposed persistent in-mode indicator**, replacing the plain practice badge so
the mode is unmistakable:

> ● DEVELOPER MODE · MUTINYNET · PRACTICE COINS

with the green frame active, and the network name following the selected
practice network. Exiting developer mode returns the app to Bitcoin and the
orange frame.

## Out of scope — must stay untouched

- `wallet_service.py`, `signing.py`, `probe.py`, PSBT construction, signer
  binding and finalization: **no transaction-logic change at all.**
- The backend `mainnet_opt_in` default of `False` and the transport-helper
  refusal: unchanged, and still described as one operator checkbox plus
  defence in depth — never as two human actions.
- The final-screen confirmation and its wording.
- The fee ceilings (25 sat/vB, 10,000 sats) and the fee policy.
- Broadcast and scan safety rules, the pending-payment pause, the
  dual-explorer mainnet outpoint check.
- `network_settings.py`'s stored format and `verify_esplora`'s genesis and
  Mutinynet checkpoint checks. The `{"main", "testnet4"}` requirement in
  `load_servers()` stays: the app must keep validating every network's saved
  URLs even when only Bitcoin is reachable from the main screen.
- The BIP48 change policy and the `CHANGE-ADDRESS-REVIEW.md` trust boundary.
- F2, F3, F5, F6.
- Repository history. No rewriting, no tag changes.

## Version and release policy

The owner directed **0.6.0**, and the version moved to **0.6.1** before publication (see the amendment at the end). The reasoning, recorded:

- `AGENTS.md` requires a new version for any transaction-logic change. This
  release has none, so the minimum bar would be a patch. The owner chose a
  **minor** version instead, which is correct signalling: the app's opening
  screen and default network genuinely change for the first time since 0.5.0,
  and a patch number would understate it.
- Because the engine is byte-identical to 0.5.1, the release notes and
  `RELEASE-HISTORY.md` entry must state plainly that **the transaction and
  signing engine is unchanged from 0.5.1** — the build that sent real Bitcoin.
  Nothing in this release may be described as new transaction capability.
- `version.py` (`APP_VERSION = "0.6.1"`), user-facing version references,
  `CURRENT-STATUS.md`, `PHASE-HANDOFF.md`, `RELEASE-HISTORY.md` and the
  `releases/` evidence file are bumped together at release time, per the
  existing rule that a version bump, commit and tag are one step.
- Publication stays manual-dispatch through
  `.github/workflows/build-candidate.yml`. Do not build the DMG locally: the
  Mac's Homebrew libusb does not match the reviewed `LIBUSB_SHA256` pin.

## Documentation to write

1. **`docs/index.html`** (public site, what a stranger reads first): a short,
   honest section — developer mode exists; it opens Mutinynet and Testnet4;
   Mutinynet is the faster default practice network; it is a good place for a
   developer to try a wallet file end-to-end. Framed as a test bench that is
   *not the primary purpose of the app*, in the owner's words. Still no
   "approved"/"verified" language, and still no claim that testing substitutes
   for the operator's own review on the device.
2. **`README.md`**: how to reach developer mode, what it changes, what it does
   not do (cannot fund a practice wallet, cannot recover a wrong-network
   payment), and that it is session-only.
3. **The plain-language operator guide** (an open Phase 5 item): the trustee
   never sees the gate. The guide should say so, and should carry the honest
   limit that a practice send does not by itself prove the change-address
   behaviour of a given firmware.
4. **`CHANGE-ADDRESS-REVIEW.md`**: unchanged in substance; the change-address
   firmware-gap note stays accurate and untouched.

## Test plan

Existing tests that **will fail and must be rewritten**:

- `tests/ui_send_mode.cjs:38-40` asserts
  `<input type="radio" id="chain-mutinynet" name="chain" value="mutinynet" checked>`
  is present, with the message *"Mutinynet should be the default network"*. The
  `checked` attribute moves to Bitcoin and the message must be rewritten.
- `tests/ui_send_mode.cjs:91` asserts `role="radiogroup"` is on the main screen,
  and `tests/ui_send_mode.cjs:93-97` asserts each of `chain-mutinynet`,
  `chain-testnet4` and `chain-main` is on the main screen. All three moved
  behind the gate in the first draft; from 0.6.1 the panel holds the two practice
  networks and the mainnet card is removed (see the amendment at the end).
- `tests/ui_send_mode.cjs:98` iterates `['mutinynet', 'testnet4', 'main']` to
  exercise each selected chain; that loop must set its chain inside developer
  mode rather than relying on a pre-checked radio.

New or updated coverage:

- A DOM test asserting **no** chain-choice control is reachable before
  developer mode is entered, and that the network badge still states the active
  chain.
- A DOM test for the gate: the dialog appears, Cancel leaves the app on Bitcoin,
  confirm switches to Mutinynet with the green frame active.
- A DOM test asserting **frame and badge can never disagree** across all three
  networks in both themes.
- A DOM test or unit test asserting a prepared payment disables the gate, and
  that the transition cannot silently change the chain of a prepared payment.
- Full regression: `.venv/bin/python -m unittest discover -s tests` (currently
  `Ran 238 tests` / `OK`) plus all eight `tests/ui_*.cjs` DOM tests, run clean
  before the branch is offered for review.

## Deliberate non-goals

- No new persistence of the selected network, ever, without a fresh decision
  recorded here.
- No removal of testnet support, no deprecation language, no claim that it was
  rolled back.
- No colour literals outside the token blocks in `ui.html`; `--frame` already
  exists and `tests/test_palette.py` must stay green.
- No theme change. The frame is decoration and must remain unable to break the
  app.

## Amendment — 0.6.1: developer mode is the practice networks, and only those

After installing and opening the 0.6.0 candidate, the owner directed (m01190,
verbatim): "Live Bitcoin does not belong in the developer mode, remove it Only
the test nets. make 1.6.1" — meaning version 0.6.1. The defect he saw: inside
developer mode the panel offered a third card, **Bitcoin LIVE**, so a window
whose own note read "practice coins only" could sit on mainnet with a green
frame, and choosing that card returned the app to live Bitcoin without closing
the gate. The frame and the badge would then have disagreed with the mode, which
is exactly what the seventh decision above forbids.

What changed, and nothing else:

- The mainnet card is removed from `ui.html`. The panel inside developer mode
  offers Mutinynet and Testnet4 only, so "practice network" is the whole of the
  choice.
- The way back to live Bitcoin is the gate button, which already read "Return to
  Bitcoin". The gate's own confirmation still switches to Mutinynet.
- `setChain("main")` is refused while developer mode is open, so a stale card, a
  restored selection or any future caller cannot leave the app on mainnet with
  the practice frame and badge. `leaveDeveloperMode()` closes the gate first, so
  the ordinary way home is unaffected.
- The step-1 note no longer says "you are on mainnet" while the gate is open; it
  names the practice network actually in force.
- `tests/ui_developer_mode.cjs` pins all of this (no mainnet card, a scripted
  mainnet selection refused, frame/badge/live banner staying on the practice
  side) and `tests/ui_send_mode.cjs` pins that live Bitcoin is not a card at all
  and that mainnet remains selectable once the gate is closed.
- The version moved to 0.6.1 and the 0.6.0 candidate is superseded. No 0.6.0
  artifact was published, so there is no published build to correct and no need
  to reach the change through a patch above 0.6.0.

Nothing about the transaction, signing or broadcast path changed, this amendment
does not widen the scope above, and it does not shorten the out-of-scope list.
