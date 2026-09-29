# Roadmap and agent handoff

**Current build:** **v0.1.26**, 28 September 2026, on the `phase2-transaction-builder`
branch. It prepares and reviews an **unsigned** transaction and performs read-only
hardware signer recognition. **It does not sign, and it does not broadcast.**

## Status at a glance

- [x] **Phase 1 — framework and balance view.** Complete and owner-approved. One
  Python wallet/PSBT engine, one local HTML interface, an Apple Silicon WebKit
  wrapper, balance in BTC with satoshis and an approximate USD line.
- [x] **Phase 2 — send eligibility explained and unblocked.** Complete. The owner's
  receive-only `/*` export now reaches the send form. The app resolves the wallet's
  usual change addresses itself rather than asking the owner to confirm a detail
  they have no way to check, and reports whether the wallet's own history supports
  them.
- [x] **Phase 3 — prepare, review and save an unsigned transaction.** **Complete:
  acceptance gate passed.** Exercised by the owner on Apple Silicon: destination and amount,
  or Send All with the fee deducted; live fee tiers with a visible selected state;
  size and fee computed from the inputs actually selected; the change address shown
  in the review; the final transaction id and a public explorer link; a
  small-test-payment recommendation; and the `.psbt` saved to the Downloads folder.
  Two usability bugs found in live use — no confirmation of the chosen fee tier,
  and no sign of progress during a slow scan — were fixed in v0.1.14. Step 3, a
  pre-flight check of the hardware wallets, was added in v0.1.15 so a missing or
  mismatched device is discovered before a payment is built.
  **Gate passed on real hardware (28 Sep):** with the owner's own wallet open, the
  app reported *"Trezor Safe 3: signer 2 of 3 public xpub matched (not a signing
  test)"*, and the xpub it verified was confirmed byte-identical to the cosigner
  declared in the BSMS file. The change address it proposed
  (`...qdvr9fn`, index `/1/1` because `/1/0` was already used) was independently
  re-derived from Sparrow's own descriptor and matched. It previously enumerated a
  Ledger Nano S Plus and correctly rejected it as a non-member device.
- [x] **Phase 4 — signing and broadcast (testnet4).** Implemented at the owner's
  request. The app asks each device to sign, finalises when the threshold is met,
  re-displays the finalised transaction, and broadcasts to Testnet4 after an explicit
  confirmation of that exact transaction id. **Broadcasting real Bitcoin is refused
  outright** and stays refused until a full testnet send has been completed. What
  remains is the owner's first live testnet send with two of the three devices.

**Progress note.** The phases were fixed in sequence on this branch: the transaction
journey was unreachable (v0.1.10); the bundled trust store was never actually used,
so HTTPS depended on the host machine; the save button produced no file; the wallet
card asked the owner to answer an unanswerable question; the fee buttons confirmed
nothing; and a slow scan looked like a dead app. Each is fixed and covered by tests.
Redirect following was removed from outbound HTTP, the local access token is no
longer disclosed in an unauthenticated response, and the high-value confirmation no
longer depends on a remote price feed.
**How to hand this to another agent:** Say “Implement Phase 2 of `ROADMAP.md`,” then Phase 3, then Phase 4. Read the repository's `README.md`, `replit.md`, and this document first. Each phase has a goal, affected areas, constraints, acceptance checks, and a handoff record. Do not treat the next phase as approved just because the previous one is done. Complete phases in order: the balance view must lead to a clearly explained send-eligibility state before transaction preparation can be completed; an independently checked unsigned transaction is needed before a signer or broadcaster can be connected. The app now walks the user through four numbered steps — open the wallet, see the balance, **check the hardware wallets**, prepare the send — so a device problem is found before a payment is built, not at its last step.

## Phase 1 — Current checkpoint: framework and balance view

**Status: complete.**

The repository has one Python wallet/PSBT engine and one local HTML interface for Testnet4 and mainnet, selected by network configuration. The Apple Silicon wrapper embeds Python and displays that interface in a native WebKit window; the source archive is separately usable with Python. The app reads an existing BSMS wallet definition, checks network and reference-address consistency, derives supported public addresses, and asks a selected Esplora explorer about balances and UTXOs. The balance view displays BTC to eight decimal places, sats beside it, and an approximate mainnet BTC/USD comparison beneath BTC. The whole-BTC portion is not capped at one digit. The user has approved this balance presentation.

Implemented code also includes a re-scan request, locally saved advanced Esplora endpoint settings, transaction inputs, fee guidance, PSBT creation, a transaction-review panel, and saving an unsigned `.psbt` into the user's Downloads folder (new filename each time, never replacing an existing file). There are automated tests using synthetic wallet/explorer data and an Apple Silicon CI build with bundle/network self-checks. The v0.1.6 release build passed those checks. **Those checks are not evidence that the full click-through journey works with the user's actual wallet on the Mac.**

The user says **Refresh balance appears to work**; do not list refresh as a reported defect. v0.1.8 does not include the current transaction workflow. v0.1.9 adds three live fee tiers, a UTXO-count fee preview with dollar equivalent, a high-dollar confirmation, transaction review, and HWI-backed signer recognition. Testnet4 and physical signer use remain to be tested on the owner's Mac. Signer recognition is not signing; the app cannot sign or broadcast, and the broadcaster URL remains future-use only.

| Capability | Evidence | Not yet proven / gap |
| --- | --- | --- |
| Open a BSMS definition and display balance | Owner uses it on Apple Silicon; wallet, balance and change-address handling all reach the screen; parsing, rejection and scan-coverage tests exist. | Formal error-path walkthrough by the owner. |
| Prepare an unsigned transaction | Owner reached the send form, fee selection, review and save on the Mac; the engine is verified independently by signing a synthetic PSBT and measuring it (305 vB actual against 307 estimated; effective 5.033 sat/vB against a requested 5). | Recognition of a physical hardware signer (recognition is not signing). |
| Recognize hardware signers | HWI-backed recognition matches a connected device's public key to a BSMS signer; the packaged app passes its headless checks. | Never run against a physical device. Recognition is not signing. |
| Sign and broadcast | Not implemented, by design. | Phase 4, and only after explicit owner authorisation. |

### Rules that apply to every subsequent phase

1. Keep this a **local, existing-wallet** app. No seed words, private-key entry, hosted wallet upload, silent background signing, or wallet creation. Do not commit BSMS exports, xpubs, wallet addresses, PSBTs, settings, credentials, or user test artifacts. Redact sensitive values from issues, logs, screenshots, CI artifacts, and handoff notes.
2. Use Testnet4 for live development/validation unless the owner explicitly authorizes a specific mainnet operation. A `tb1` address alone does not establish whether the wallet is Testnet4 versus another test chain. Never silently switch networks or explorers. A failed custom endpoint must not fall back to a public endpoint without the user's knowledge.
-3. A BSMS export with only a proven receiving path is **view-only**. Do not guess `/1/*` change, fabricate descriptor paths, treat missing coverage as zero balance, or call a gap-limited scan a complete wallet sweep. Confirmed outputs found by *this scan* are not necessarily every output owned by the wallet. **Amended in v0.1.13 (owner decision):** for a wallet whose receive path the reference address proves, the app now *resolves* the wallet's usual `/1/*` change addresses rather than gating on a declaration, because the previous design asked a non-technical owner to assert something they could not check. The change address stays visible in the review, the scan reports whether the wallet's own history supports it, and a test payment is recommended when it is unconfirmed.
4. Make consequential failures visible: disabled controls need a reason and next action; a scan or PSBT error must not look like success. Keep recipient, selected network, change, total debited, and fee review explicit. Do not relax fee/coverage guards just to make a button clickable.
5. Change only the phase's agreed behavior. Preserve the approved BTC/sats/USD balance layout and existing adjacent controls unless they are directly necessary to fix that phase. Record any scope decision that needs owner input instead of improvising it.
6. Synthetic fixtures prove code paths, **not** that the user's wallet, Mac window, real explorer, hardware signer, or final transaction works. Live validation with the actual Testnet4 BSMS requires explicit permission; keep wallet-derived material local and out of source control.

## Phase 2 — Explain and unblock transaction eligibility on the Mac

**Status: complete — acceptance gate passed on the owner's Mac.** The owner's own
receive-only `/*` wallet hit the gate, was explained plainly, and reached the send
form. The declaration checkbox this phase originally introduced was removed in
v0.1.13 by owner decision (see rule 3), because it asked a non-technical owner to
assert something they could not check. The app now resolves the wallet's usual
change addresses itself, reports whether the wallet's own history supports them, and
keeps the change address visible in the review.

*Evidence:* the owner imported their real wallet in the shipped Apple Silicon app,
saw the blockage and its explanation, and reached the send form; screenshots
confirmed the wallet card, the balance and the send step. Synthetic and
loopback-API tests cover the eligibility logic, and page tests forbid descriptor
jargon and the return of the confirmation checkbox on the main screen.

**Goal:** After a working Testnet4 balance scan, determine why the user cannot use Prepare send. If the wallet is view-only, show the specific reason and requirements; if a verified spend-capable wallet meets all gates, make the send form available. Preserve the currently working refresh behavior. This is the immediate next assignment. **Do not add signing or broadcasting in this phase.**

**Start here in the code:** `ui.html` (send-card visibility, disabled-button states, fee guidance, and status messages); `gui.py` (`/api/import`, `/api/scan`, `/api/status`, fee and preparation endpoints); `wallet_service.py` (wallet layout, scan, and spend eligibility); `desktop.py` (native WebKit/file bridge); `tests/test_gui.py` and `tests/test_wallet_service.py`. `README.md` documents current limits. Diagnose the reported send blockage against the released v0.1.6 app before changing code.

**Work to do**

1. On Apple Silicon, observe the state after a successful Testnet4 import and balance scan. Confirm Refresh still works as a baseline; do not spend this milestone redesigning it. Record whether the send form is hidden, Prepare send is disabled, or a warning is present, and what each control says. Check the native window, not just a Python test or browser-only mock.
2. Trace spend eligibility end-to-end: `wallet_summary`/`can_prepare` → scan `coverage_limited` and `utxo_consistent` → `showWallet`/`showBalance` send-card visibility → fee-quote gating in `renderFeeGuidance`. Identify the actual reason the user's current wallet stops at the balance; do not guess that Refresh failed.
3. Determine whether the BSMS definition proves both receiving and change paths for the supported 2-of-3 wallet. A receive-only export is intentionally view-only. State what verified input is missing, if any, instead of inferring a path or removing the safety guard.
4. Make the reason for an unavailable send form or disabled Prepare button visible and actionable in the existing interface. Distinguish missing wallet-path evidence, partial scan, inconsistent UTXOs, no confirmed outputs, and unavailable/out-of-bounds fee quotes. A non-spendable wallet should not look like a broken click; a valid one should not remain hidden without an explanation.
5. With a controlled spend-capable Testnet4 definition, verify the send form becomes accessible after a valid scan and fee quote. Check negative cases and network/session changes without altering the advanced network settings or the working balance layout. Do not quietly relax fee policy, change servers, or enable a send after a failed scan.
6. Add focused regression tests for the actual send-eligibility issue and exercise the updated Apple Silicon app. Use synthetic fixtures for deterministic cases; a claim about the user's particular wallet requires explicit permission to inspect its Testnet4 BSMS through the real import/scan path without retaining wallet material.

**Acceptance gate:** Refresh still works as before. On an Apple Silicon Mac, a view-only or otherwise ineligible wallet clearly explains why Prepare send is unavailable; a controlled verified wallet with consistent confirmed outputs and acceptable fee guidance reaches the send form. The observed send blockage is diagnosed and resolved or correctly explained with a real Mac interaction, not just successful CI. A failed scan never authorizes a send. Actual PSBT creation and save are Phase 3.

**Handoff to Phase 3:** Record build/version, the exact Mac steps and outcomes, supported BSMS shape and observed path-eligibility state (without xpubs or addresses), explorer/network used, test results, known gaps, and whether the owner authorized a real Testnet4 wallet check. Update this phase's status only after its acceptance gate passes.

## Phase 3 — Produce and independently verify a Testnet4 unsigned transaction

**Status: complete — all acceptance evidence obtained.**

*Evidence:* the owner reached the send step, chose a fee tier, prepared and reviewed
a transaction, and reports the journey working in v0.1.13/v0.1.14. The engine is
verified independently of its own tests by building a transaction, signing it with
2 of 3 synthetic keys, finalizing it and measuring it. 96 automated tests pass,
including a loopback frontend-to-API journey and a headless check that the packaged
binary can write a PSBT.

*Fixed after live use:* the fee-speed buttons confirmed nothing (`aria-pressed` was
set on two buttons and had no CSS; selection was inferred by comparing rate values,
which cannot distinguish tiers that round to the same whole sat/vB — the owner's
live quote was 1 / 2 / 2), and a slow scan looked like a dead app.

*Independently verified:* a PSBT saved from the owner's real wallet was decoded by
  two independent implementations that agreed on every material value, and the change
  output was rebuilt from its declared keys and matched the wallet's own change
  branch. See the verification record below. *Hardware recognition:* **proven.** The shipped
  app enumerated a Ledger Nano S Plus and correctly rejected it as a non-member, then
  matched a Trezor Safe 3 to signer 2 of 3 on the owner's real wallet, with the
  verified xpub confirmed byte-identical to the BSMS cosigner.

**Goal:** With verified 2-of-3 receive/change paths and a consistent confirmed scan, the user can prepare and review a partial or Send All transaction, see live slow/medium/fast fee choices with sats and USD estimates, catch a high-dollar amount, save an unsigned PSBT, then reach an HWI device-recognition screen that identifies matching signers. The v0.1.9 Mac app must be ready for physical keys to be plugged in for this recognition check. **Do not sign or broadcast.**

**Start here in the code:** `wallet_service.py` (`wallet_layout`, `scan_wallet`, `build_unsigned_psbt`); `gui.py` (`/api/prepare`, cached scan/fee binding); `ui.html` (send form, fee guidance, review, download); `desktop.py` (`save_psbt`); `tests/test_wallet_service.py`, `tests/test_gui.py`, and `tests/test_desktop.py`. The existing tests prove important synthetic cases, but the owner has not been able to complete this journey on the Mac.

**Work to do**

1. Accept a BIP 129 descriptor template only with the explicit `/0/*,/1/*` restrictions. Expand both paths, verify the reference address against the receive path, and confirm identical policy and signer keys. The currently documented sample `/*` export is receive-only/view-only; never infer a change branch from it or weaken `can_prepare`. This support is implemented in the v0.1.8 candidate and covered by synthetic tests; a test-wallet Mac walkthrough is still pending.
2. Starting from the Phase 2 working scan, check that the send form becomes visible only when the policy, descriptor paths, coverage, UTXO consistency, confirmed outputs, and network make it safe. Provide a specific visible explanation for each blocked condition. An incomplete gap scan must not produce a misleading “entire wallet” claim.
3. Show live slow/hour, medium/half-hour, and fast/fastest mainnet sat/vB guidance; round the selected rate up to a whole sat/vB and prepopulate the rate field. Label that fee data is a mainnet reference in Testnet4 mode. Keep fee caps and minimum-rate checks.
4. Confirm correct destination network, amount parsing to whole sats, sufficient confirmed funds, input selection, previously verified transaction outputs, change ownership, dust handling, fee bounds, and send-all fee deduction. Ensure stale scans or changed settings invalidate a pending review. Keep backend validation authoritative even if frontend fields are enabled.
5. Show recipient, exact amount in BTC/sats and indicative USD, selected fee rate, estimated vbytes, fee in sats and USD, total deducted, change, and the scan-coverage caveat before enabling the next step. Require transaction and fee review acknowledgements. For a mainnet amount worth $10,000 or more, require a separate high-value confirmation; enforce it in the backend too.
6. Save the `.psbt` where the user can actually find it. **Amended in v0.1.12:** the
native Mac dialog could return nothing while reporting no error, and WKWebView
ignores browser downloads, so the button appeared to do nothing at all. Saving now
uses the same local API every other action uses, writes a new file into the
Downloads folder, and names the full path on screen; an existing file is never
replaced. **Done:** a PSBT saved from the owner's real wallet was independently
   decoded and agreed with the review on every material value — see the verification
   record below. The next screen bundles HWI 3.2.0, prompts the user to connect and
   unlock hardware wallets on-device, enumerates devices, and verifies each available
   xpub against a public BSMS signer key. It states clearly that this does not sign
   and is not a test of transaction approval.
7. Extend tests for both accepted and rejected cases, including a real frontend-to-local-API path in the packaged Mac app, backend policy refusals, offline/malformed explorer responses, wrong-network destination, and a save cancellation. Recheck the approved balance view and refresh flow for regressions.

**Acceptance gate:** The v0.1.9 Mac build completes **import → fresh scan → yes/no → partial or Send All → live fee/amount/fee-dollar review → high-value confirmation where applicable → PSBT save → signer-recognition page**. HWI launches from the packaged app, and an independent decoder agrees with the transaction review. With the owner's devices available, at least one intended signer is recognized as matching its BSMS key. Unsupported, incomplete, stale, wrong-network, unaffordable, or excessive-fee cases fail visibly. No Bitcoin is signed or transmitted.

**Handoff to Phase 4:** Record supported descriptor/export format, deterministic fixtures, independent PSBT verification, fee policy, HWI/device recognition results, and Mac steps without wallet data. Actual signing and broadcast remain a separately approved later phase.

### Verification record: a real PSBT, decoded independently

The owner saved an unsigned `.psbt` from the app and it was decoded without trusting
the app's own report. Two independent implementations were used — a hand-written
BIP174 and raw-transaction parser that uses no Bitcoin library at all, and a
different library — and they agreed on every material value: the transaction id, the
input and output counts, every amount, and the fee.

Beyond agreeing, the things that matter were checked directly from the bytes:

- **Each input's `witness_utxo` really is this wallet's multisig script**, by
  recomputing the P2WSH from the `witness_script` carried in the PSBT.
- **The change output was rebuilt from its own declared keys** using plain SHA-256,
  and it reproduced the output script exactly. The change output's declared cosigner
  fingerprints are the same three as the spent input's, and its derivation path is
  the wallet's **change branch** while the input's is the **receive branch** — so the
  change demonstrably returns to this wallet's own change addresses, which is the
  claim the app makes and the one that could cost money if wrong.
- **The fee equals the reviewed rate times the reviewed size exactly**, so the
  on-screen estimate and the file agree.
- **No partial signatures are present**: the file is genuinely unsigned.
- The destination output is a single payment to an address that is not the wallet's.

No wallet material — addresses, keys, fingerprints, amounts or transaction id — is
recorded here, and the PSBT was not committed. A third library was attempted for a
further cross-check and could not load in this environment; that limitation is
stated rather than glossed.

## Phase 4 — Decide the signing boundary, complete the send, and review the whole tool

**Status: the owner has asked to begin it (28 September).** The read-only recognition
screen exists from Phase 3; signing and broadcast do not. Phase 4 begins with the
owner's answers to the decisions below, then implementation on **testnet4 only**,
with mainnet broadcast gated behind a separate explicit opt-in after a complete
testnet cycle.

**Decisions this phase needs from the owner**

1. Does the app sign **and** broadcast, or sign only and hand over a signed
   transaction for another wallet to broadcast? (Recommendation: both, because the
   intended user should not have to leave the tool.)
2. Confirm the safety interlocks: the finalised transaction is decoded and shown for
   confirmation before broadcast; a changed transaction id aborts; mainnet broadcast
   stays disabled until deliberately switched on; nothing is ever broadcast
   automatically.
3. Which devices must be supported first, and in what order the signatures are
   collected.

**Goal:** Move from a proven unsigned Testnet4 PSBT to an **owner-approved** end-to-end Testnet4 prototype: hardware signers review and sign, the app verifies the finalized payment, and only an explicit user action submits it. Then run an independent full-tool review. This is **future scope**, not existing functionality. `replit.md` currently says no signing or broadcasting; do not implement this phase until the owner explicitly approves changing that boundary, the supported devices, and the intended send workflow. If the owner instead chooses external signing/broadcast, document and validate that handoff as the agreed prototype endpoint; do not claim the app itself sends Bitcoin.

**Start here in the code:** the completed Phase 3 handoff; `probe.py` (read-only HWI device proof); `wallet_service.py` (wallet policy and PSBT); `gui.py` and `ui.html` (local session and review); `desktop.py` and `scripts/build-macos.sh` (packaging). Treat the current “Connect signers (not available yet)” UI and stored broadcaster URL as placeholders, **not** working integrations.

**Work to do after explicit scope approval**

1. Write down the supported hardware models/firmware, HWI version and binary verification, Testnet4 support, signer fingerprint/policy matching, threshold requirements, Mac permissions, and failure/cancellation behavior. Confirm at least two compatible signers can independently display and approve the exact destination, amount, fee, network, and change. No seed/PIN collection, arbitrary command execution, or silent hardware action.
2. Design a session-bound PSBT signing flow that refuses a different wallet, changed scan or review, wrong network, unexpected outputs, or signatures from the wrong policy. Start with emulators/test devices, then test the supported physical signers. Verify the resulting partial signatures and threshold; preserve an offline/export path when a device is unavailable.
3. Before finalization/broadcast, independently recompute inputs, outputs, change ownership, total debited, effective final fee and fee rate, and transaction ID from the **final signed transaction**, not merely the estimated unsigned review. If any signer display or independently computed result disagrees, stop without sending.
4. Permit broadcast only after a second, explicit confirmation of the final transaction and destination. Validate the chosen Testnet4 broadcaster's network; never use a saved broadcaster URL merely because it exists. Show submission response/txid and independently check the result; handle refusal, timeout, duplicate submission, and unknown status without reporting success or trying a different server silently. No automatic mainnet broadcast or real-funds trial.
5. Run a **separate full-tool review** after functional tests: threat model and privacy of wallet/address/device data; descriptor and BIP48 correctness; scan-gap/UTXO provenance; fee and transaction invariants; malicious or stale explorer/broadcaster responses; wrong-network handling; race/session invalidation; dependency and bundled-binary provenance; file permissions; signer-display agreement; accessibility and understandable failure states. Ask an independent reviewer to challenge the assumptions, not just rerun happy-path tests.
6. Demonstrate on an Apple Silicon Mac using controlled Testnet4 funds: open → refresh → prepare → independently review PSBT → obtain required hardware approvals → verify finalized transaction → explicitly broadcast → confirm txid/result. Also test cancellation and failure at each boundary, then recheck mainnet **view-only** behavior without querying a real mainnet wallet absent fresh permission.

**Acceptance gate:** The owner-approved prototype endpoint is completed with evidence from the actual Mac and Testnet4 signers, and the independent review has no unresolved high-risk correctness or key-handling findings. The README accurately distinguishes implemented capabilities from future ones. A mainnet sending release, signed/notarized Mac distribution, and broad wallet/device support are **separate decisions**, not consequences of a passing Testnet4 demo.

**Final handoff:** Provide the supported wallet/signers/network matrix, reproducible non-sensitive test procedure, reviewed source and release identifiers, security findings and dispositions, manual Mac results, remaining limitations, and a precise list of operations still prohibited. If there is no owner approval for signing/broadcast, close this phase as *not authorized*, not *complete*.

## Delivery discipline for any agent working from this roadmap

- **Documentation-only pushes must not republish.** The workflow ignores changes that
  touch only Markdown, and a docs-only commit can carry `[skip ci]`, so a released
  version keeps exactly the artifacts it was verified with.
- **A device check with no transaction is legitimate; a check inside a send must
  belong to the review.** Step 3 lets an owner confirm their signers work before
  building anything, which needs no transaction and says so in its reply. The check
  at the end of a send must still match the review on screen, and any future signing
  endpoint must *require* that review rather than merely allow it.
- **One version per published build.** Never rebuild a released tag in place: v0.1.11's assets were replaced five times, so a filename and a tag no longer identified their contents. Bump `version.py` for every build that is published; it is the single place the version lives, and the workflow derives the tag, the artifact names and the release title from it.
- Make one phase's scoped changes at a time. Before editing, compare this roadmap with the actual code and the latest release; the document can become stale. State any assumptions or blocker rather than inventing wallet paths, policy, or a successful click flow.
- Add focused tests for each fixed failure and run `python -m unittest discover -s tests -q`; validate inline JavaScript syntax and inspect runtime errors when changing `ui.html`. For Mac changes, build on Apple Silicon and perform a **manual native-window** walkthrough. Record which checks used synthetic data and which used real Testnet4 services/devices.
- Keep `README.md`, `ROADMAP.md`, and user-facing capability claims consistent with observed behavior. An automated build self-check is not a substitute for native file-picker, refresh, review, save, signer, or broadcast testing.
- For a requested test release, build matching-version source and Apple Silicon DMG artifacts, verify both before publishing, keep `main` current with the released source, and remove superseded temporary candidate branches only after confirming their commits are on `main` and they have no open pull requests. Preserve release tags and download assets.
- End each phase with a short handoff: **what changed; why; how to reproduce; tests and manual evidence; remaining risks/blockers; exact next phase entry point**. Do not mark an acceptance gate passed without its stated evidence.
