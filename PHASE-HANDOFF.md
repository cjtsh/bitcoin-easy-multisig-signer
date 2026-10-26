# Current handoff — Bitcoin Easy Signer

**Source revision 0.7.1 is the Color Team cycle-7 build-process
remediation of the `v0.7.0` tree.** Every finding the cycle's plan
schedules has exactly one row in `releases/PATCH-0.7.1.md` with a
severity and a closing test the build loads; the loopback server's
retired-connection guard is pinned by a test that goes red when the
guard is removed; the control inventory now parses the GitHub workflow
files, so the retired-publisher pagination guard and the notarisation
and checksum-signing credential guards are tracked rows with executable
pins; the busy-slot docstring says what the slot actually requires; and
the terms of use in `DISCLAIMER.md` incorporate the Bitseeker LLC
standard legal framework published at
[cjtsh/software-disclaimer](https://github.com/cjtsh/software-disclaimer).
The release is built and published from `main` through the
unified pipeline; until its promote run lands, the newest published tag
remains
[`v0.7.0`](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.7.0).
The engine is unchanged from 0.7.0,
which was the cycle-6 build-process remediation of the `v0.6.9` tree. The out-of-gate `v0.6.5-windows-x64` release was deleted
(CT-27), and cycle 3 then found the root cause of it: the per-platform
publish workflows were never deleted (CT-48). They are now gone from
every branch. Owner-reported acceptance of the Windows console fix and
of the Linux AppImage remains in this file's history and in `releases/`;
those port builds are superseded by the unified pipeline.

## Current stop point — source revision 0.7.1 is the release this tree publishes; v0.7.0 is the newest published tag

The **published set** is whatever the
[Releases page](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases)
and `RELEASE-HISTORY.md` carry; read one of those rather than trusting a
hardcoded number here. As of 2026-10-16 that is [v0.7.0](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases/tag/v0.7.0), published 2026-10-16T06:15:36Z as tag `v0.7.0` on commit `4fe8f2955e29cae6838e2ba0b8029c9abae9fdeb` by successful candidate run [38854414566](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/38854414566) and promote run [38857329074](https://github.com/cjtsh/bitcoin-easy-multisig-signer/actions/runs/38857329074). The release page carries macOS, Windows, Linux, the source archive, one `SHA256SUMS` with `SHA256SUMS.asc`, and `BUILD-SBOM*.json`. Version 0.6.7 is the Color Team cycle-3 build-process remediation: one publish path with the retired per-platform workflows deleted from every branch, the HWI helper identified by bytes rather than by its own version string, the interpreter pinned to a full patch, the lock-writer hash-locked, the source tarball able to rebuild a signed Mac app, and the broadcaster verified at use on every network. Version 0.7.1, the source revision this tree publishes, is the Color Team cycle-7 build-process remediation of the `v0.7.0` tree: every finding the cycle's plan schedules has one ledger row with a closing test the build loads; the retired-connection guard in the loopback server is pinned by a test that goes red when the guard is removed; the control inventory now parses the GitHub workflow files, so the retired-publisher pagination guard and the notarisation and checksum-signing credential guards are tracked rows with executable pins; the busy-slot docstring says what the slot actually requires; and the terms of use incorporate the Bitseeker LLC standard legal framework. Version 0.7.0 was the Color Team cycle-6 build-process remediation of the `v0.6.9` tree: every finding the cycle's plan schedules has one ledger row with a closing test the build loads; the value and script limbs of the build-time prevout match are pinned by tests that fail when their own limb is removed; the loopback server retires its oldest idle connection rather than refusing the operator's window at the connection ceiling; `CONTROLS.md` gains rows `CM-27`…`CM-32` and a widened claim-phrase net; the retired-publisher guard refuses when the platform reports more registrations than the one page it reads; and the Windows startup dialog shows the same bounded record as the log. Version 0.6.9 was the cycle-5 build-process remediation of the `v0.6.8` tree: every finding that cycle's plan scheduled had one ledger row with a closing test the build loads, every `CONTROLS.md` citation is content-bound to a marker inside the range it cites, and the launcher installs the device library from a checked lock. Version 0.6.8 was the cycle-4 build-process remediation of the `v0.6.7` tree, which introduced the checked audit ledger and the parsed `CONTROLS.md` inventory. The wallet, transaction, signing and broadcast engine is unchanged. Owner practice-network hardware walkthrough passed on candidate 37644267740 before promotion. No independent human end-to-end security review is recorded; nothing here is a certification or a guarantee. Mainnet still requires the final-screen checkbox and backend opt-in; the 25 sat/vB and 10,000-sat fee ceilings remain.

**The cycle-3 panel rerun already ran and graded ⛔ BLOCKED** on the
`v0.6.6` tree — not on the app. Red found no breach; Orange recorded its
first LOGIC PROVEN (21/21); Amber verified the supply chain end to end.
The grade was set by **CT-48 (High)** on the build process: the retired
per-platform publish workflows were still live on `windows-port` and
`linux-port` and one had published an unsigned manifest, while
`build-candidate.yml`'s header claimed no second path existed. The report,
plan, lock and index for that cycle are no longer in `main`; they remain in the
`v0.6.6` tag tree.

**0.6.7 is done and published.** The cycle-3 findings are answered in
code and in the dated acceptance note (`releases/PATCH-0.6.7.md` is the
evidence record). The owner installed the candidate DMG and accepted a
practice-network payment on hardware; `publish=true` then promoted the
same candidate bytes from the same commit. The cycle-3 audit plan was carried
forward against tag `v0.6.7` and signed Bitseeker LLC on 2026-10-07
(`bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.7.md`, now in the
`v0.6.7` tag tree only). It is **not** an input to the current audit. The owner
directed a fresh, unbiased baseline on 2026-10-11, and the repository root now
carries `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.7.1.md` for the
published `v0.7.1` revision, signed Bitseeker LLC on 26 Oct 2026. That cycle is a
follow-up in the `v0.6.8` lineage: the `v0.7.0` plan, lock, report and public
security statement are its inputs — moved unedited into `audit-history/` with
the `v0.6.8` and `v0.6.9` records — and the scope of the `v0.6.8` baseline is
carried forward unchanged. Plans,
locks, reports and grades of the earlier cycles may not be cited by the panel.
Treat the older plans and the reports they cite as history, never as a current
clearance — see the `v0.6.8` plan's §6, *The legacy audit artifacts inside the
audited tree*.

The owner supplied two BSMS exports of the **same practice wallet**, one from Sparrow and one from Nunchuk. A read-only comparison found identical cosigner keys/origins, first receive address, and receive/change scripts at indices 0–19. Sparrow declares both paths; Nunchuk leaves them unstated and the app uses a strictly gated BIP48 standard inference. `CHANGE-ADDRESS-REVIEW.md` records the limits. These test-wallet exports do not establish the policy of a different live mainnet wallet. No wallet identifiers or files were committed.

**Next Phase 5 gates:** the plain-language operator guide and website manual are published. Still open are an owner-led nontechnical walkthrough, a tested device/firmware matrix, and an independent end-to-end security review. The app never broadcasts automatically. The fee cap remains conservative; a quote above 25 sat/vB blocks preparation. There is no in-app fee replacement; transactions signal RBF and a compatible external wallet may be able to replace a stuck payment. Do not ask the recovery operator for a second wallet file, a Nunchuk database, seed words, or path decisions.

## 0.4.1 accepted on Ledger and Jade; 0.4.3 change-path correction published

The owner's 0.4.0 Jade attempt was rejected twice after transaction preparation. The diagnostic report identifies the signer-response boundary but omits the changed PSBT field. The same signing engine shipped in 0.3.2, which the owner reported worked on Jade; the precise device-side difference is unknown. Ledger then asked for two review rounds; a failed request about 46 seconds after its check is consistent with the old 45-second HWI limit. A later attempt showed HWI “open failed,” before a signature response; its specific device-connection cause is unknown. `releases/PATCH-0.4.1.md` documents the correction: retain the reviewed PSBT and import only signatures that verify against it, allow ten minutes for signing only, and give targeted Ledger reconnect guidance. The owner then reported an installed 0.4.1 Ledger + Jade Mutinynet payment; the privacy-limited report recorded two verified signer responses, verified finalization and accepted broadcast, and Mutinynet subsequently reported confirmation. The owner also found Jade PIN entry during discovery can exceed one minute; 0.4.2 gives discovery and matched-device xpub checks three minutes. That wait change is not yet physically tested. **At that historical release point, mainnet broadcast was disabled; it was enabled from 0.5.0 and published in 0.5.1 behind explicit confirmation and a backend opt-in.**

**Start here for any agent or independent reviewer.** Read `AGENTS.md`, then this file, `RELEASE-HISTORY.md`, `CHANGE-ADDRESS-REVIEW.md`, and the current code. The release-history entries link each version's full evidence record (`releases/PATCH-*.md`, `releases/MUTINYNET-0.3.0.md`, `releases/SECURITY-REVIEW-0.2.0.md`). `PROJECT-HISTORY.md` and the older phase text in `ROADMAP.md` are historical evidence, not current capability claims.

## Status and version policy

The published set is whatever the
[Releases page](https://github.com/cjtsh/bitcoin-easy-multisig-signer/releases)
and `RELEASE-HISTORY.md` carry — **do not restate a "latest published
build is X" here**, because that sentence is exactly what CT-71 filed and
it goes stale the moment `version.py` moves again. As of 2026-10-11 the
newest published tag is `v0.6.9`, promoted through the automated workflow
from the exact successful signed candidate. The AI-generated Z.ai v0.6.4
report assigned Green under its published rubric, and the v0.6.3 report carried
Yellow. Both are history about those revisions and are **not** inputs to the
current audit (the owner's independence condition, reproduced in the `v0.7.0`
plan §6), and neither was a certification. No independent human end-to-end
review is recorded.
Version 0.6.7 is build-process remediation and adds no payment
capability. Version 0.5.0 was the unpublished mainnet-broadcast candidate
whose engine 0.5.1 published. The app supports multisig quorums with at
most three keys. The full published version-by-version record — including
the 0.2.0 hardware-signing failure ("do not use"), the 0.2.1 field-order
correction, the 0.3.x Mutinynet and one-file BSMS work, the 0.4.1
physical payment, and later interface and notarization work — lives in
`RELEASE-HISTORY.md`. Mainnet broadcast requires explicit final-screen
consent plus a backend opt-in; one earlier mainnet transaction by this
app has been confirmed on chain.

Use a new patch version for any correction to a published build. The owner prefers milestone-based Mac installs after extensive automation rather than repeated installs for small revisions. The installed 0.2.1 app showed a new unsigned review above the previous payment's signing/final screen; **never broadcast from such a mixed screen — close the old app before installing a newer release.** The UI regression tests cover that reset. Since 0.6.1 the app **opens on Bitcoin mainnet**, and Mutinynet and Testnet4 are reached only through the "Enter Developer Mode" gate on the opening screen; the gate's panel offers those two practice networks alone, live Bitcoin being what its own "Return to Bitcoin" button goes back to. Mutinynet is the default practice network once the gate is open, and Testnet4 remains available for an existing practice wallet. The selected network stays in memory for the session, so a practice network cannot outlive a restart.

## Product goal

The user is a spouse, lawyer, accountant, or estate planner with little Bitcoin knowledge, recovering from an existing multisig wallet defined by one BSMS file. The current local candidate accepts any valid quorum with two or three total keys; the wallet file supplies the threshold. Keep the screen's decisions plain. Put descriptor and key technicalities in automatic checks or optional wallet details. Never ask this person to certify a derivation path or inspect a PSBT to make the tool work. They must still compare the payment on each hardware device and confirm the final transaction.

## Current behavior and safety boundaries

1. One engine in `wallet_service.py` and `signing.py` serves Testnet4, Mutinynet and mainnet. `network_config.py` selects BIP48 coin type, address prefix, genesis/checkpoint hashes and Esplora endpoint. `gui.py` applies network-specific safety rules; mainnet broadcast requires final-screen consent and the backend opt-in.
2. A partial send uses a two-branch descriptor, a BSMS `/**` template with `/0/*,/1/*` restrictions, an explicit restrictions line, or the strict BIP48 standard fallback described in `releases/PATCH-0.3.2.md`. `No path restrictions` does not *declare* change; the standard fallback is labelled as derived. Nunchuk's BSMS importer itself defaults an unspecified signer branch pair to `{0,1}`. Custom historical branch indices can be lost in Nunchuk's ordinary BSMS export; such layouts are outside this fallback. Unsupported files remain explicit no-change Send All only. The scan can still miss funds outside its gap/range.
3. `build_unsigned_psbt` checks each chosen previous transaction's txid, value and derived script. It stores a reviewed recipient, amount, fee, change and txid in local session state. In 0.4.1, `accept_signature_update` copies only device signatures into a clone of the reviewed PSBT, verifies them over BIP143 SIGHASH_ALL against the original transaction and discards signer-returned metadata. A different unsigned transaction or removed prior signature fails. `finalize_multisig` repeats signature and witness/prevout checks. Finalization and broadcast compare every final output and fee against the reviewed state. Broadcast holds the session lock through submission so a concurrent refresh cannot change the payment mid-submit.
4. The final screen shows network, full destination, amount, change address/amount, absolute fee, effective fee rate, signer numbers and txid together. A distinct confirmation submits on every network. Mainnet's checkbox states that it sends real Bitcoin; the backend requires a mainnet-specific opt-in as well. A new review clears the entire old signing/final section before preparation begins. In 0.4.0, the confirmed-payment explorer link remains as a receipt in the current browser session; pending and confirmed status still come from the blockchain scan.
5. Diagnostics are opt-in. The UI button saves `bitcoin-easy-signer-diagnostics-0.3.0.json` (or a numbered variant) to Downloads, mode 0600. Events use fixed stage/outcome codes and timestamps only. No addresses, xpubs, fingerprints, PSBTs, raw transactions, amounts, device paths, or exception messages enter this file. Agents may request it after a failed owner walkthrough; never request wallet material.

## Reviewer checklist

- Challenge the BSMS branch logic, especially exports whose descriptor and restrictions disagree. Confirm the strict BIP48 fallback applies only to standard sorted 2-of-3 origins and the checked first receive address; nonstandard layouts must not construct a change output.
- Challenge signer response binding. A different unsigned transaction, removed prior signature, bad DER/ECDSA signature, or non-ALL sighash must fail. Device-returned prevout/script/derivation/global xpub/output metadata must never enter the stored payment, even if Jade rewrites it. Reordered PSBT fields must pass. Confirm legitimate HWI responses from **each** supported physical model; the 0.4.0 Jade rejection and 0.4.1 correction need a new physical walkthrough.
- Verify the final review screen against the exact finalized transaction. Check no stale API request can alter a broadcast in flight. Mainnet broadcast must fail without the mainnet-specific opt-in at both the route and transport-helper levels.
- Verify the diagnostic report's privacy by inspecting the saved file. Check build locks, mandatory `LIBUSB_SHA256`, CycloneDX `BUILD-SBOM.json`, signed bundle structure, test archive, source/DMG hashes and immutable tag.
- Distinguish unit/integration results from a real device walkthrough. A passing test suite cannot establish firmware display behavior.

## Build and owner test

Follow `RELEASE-PROCESS.md` for every agent and build. Use Python 3.12; run `python -m unittest discover -s tests -q`, the Node UI regression, Bash syntax checks, source archive tests, and packaged Mac self-checks. The GitHub workflow is manual dispatch only and defaults to a nonpublishing candidate. It installs hash-locked dependencies before loading Apple credentials, verifies the vendored libusb digest, builds the Apple Silicon DMG, verifies the extracted bundle, inventories shipped components in `BUILD-SBOM.json`, and writes `SHA256SUMS`. Public release follows owner hardware acceptance and uses the same verified DMG bytes. Per-release runs, commits, hashes and owner gates are recorded in the `releases/PATCH-*.md` evidence files indexed by `RELEASE-HISTORY.md`.

The controlled 0.2.1 Testnet4 payment signed with two devices, was accepted by the broadcaster and later confirmed. The owner began another payment and discovered the stale signing/final-panel bug; no new Trezor signature or second payment result was reported for that older build. With 0.3.2, the owner reports two successful Mutinynet sends from the **existing BSMS alone**. The second proceeded without reloading the app. The first displayed an explorer view/link; the second did not and reportedly validated almost immediately. Current UI hides the pending explorer link once confirmation is observed, which may explain the visual difference. Record a persistent receipt/link as a 0.4.0 UI improvement; do not request a third payment solely for this. If future device signing fails, request only the diagnostic report and a plain-language description of its screen. Do not request signed bytes or keys.

## Remaining Phase 5 dependencies

Current UTXO checks still depend on public explorers (dual-source on mainnet, single-source recheck on practice networks), and fee replacement remains outside this app. Mainnet broadcast requires final-screen consent plus the backend opt-in; the 0.4.15 dry run is complete and one live mainnet payment on the published engine has been confirmed on chain. The plain-language operator guide and website manual are published. An owner-led nontechnical walkthrough, tested device/firmware matrix, and independent security review remain open; see `ROADMAP.md` Phase 5.

## Developer ID signing and notarization — complete

Version 0.4.12 was the first Developer ID-signed and Apple-notarized release. Version 0.4.13 corrected the staple order: the app is stapled before the DMG is built, then the finished image is mounted and the app copy inside is validated. See `RELEASE-HISTORY.md` for the release evidence and artifact checks.

`scripts/build-macos.sh` with `RELEASE=1` signs nested Mach-O files (including bundled `hwi`) with the hardened runtime, seals the `.app`, submits to Apple, staples, validates, and checks Gatekeeper acceptance. `scripts/notary-args.sh` refuses partial or ambiguous credential configuration. The workflow exposes notarization as an explicit dispatch input:

```
gh workflow run build-candidate.yml --ref main -f notarize=true
```

With `notarize` off, a run produces an `-UNSIGNED-TEST.dmg`. With it on, the run **fails closed** unless the signing and notarization credentials are present; it cannot quietly produce an ad-hoc-signed image under a notarized release path. Keep credential values in GitHub Actions secrets/variables or the local keychain, never in this repository or a chat. The separate Apple Developer instructions document is the canonical setup reference.

Do not assess the DMG itself with `spctl`: a disk image is not executable code. Validate both staples and assess the app, including the copy mounted from the finished DMG. The build performs these checks. Keep release notes factual and version-specific; do not reuse claims that applied only to an earlier wallet export or build.
