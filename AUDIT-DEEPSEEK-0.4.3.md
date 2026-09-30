# Bitcoin Easier Signer — Independent Code Audit (DeepSeek)

**Audit target:** [`cjtsh/bitcoin-easy-multisig-signer`](https://github.com/cjtsh/bitcoin-easy-multisig-signer), branch `main` at commit `7d622ef` (`Merge pull request #21 …docs/consolidate-status-and-history`), source version `0.4.3` (`version.py`). This is two docs-only commits ahead of the revision audited by the prior Z.ai review (`e8472a2`); **no source file differs from that review's target**.

**Independently executed during this audit**

| Action | Result |
|---|---|
| Full test suite, Python 3.12, hash-verified `embit==0.8.0` | **172 tests, 0 failures** (~38 s) |
| Same suite following `README.md:46-52` verbatim | **8 skips** — the whole `test_workflow_config` CI-lint module, reason `PyYAML not installed` (see §2 N-5) |
| **Mutation testing** on untracked copies: guards deleted, suite re-run | **The mainnet broadcast lock and three other guards are not covered** — deleting them breaks no test (see §2 H-3) |
| Isolated single-test re-run (see §5, test-isolation finding) | Confirmed a test-isolation defect, not a code defect |
| Numerical re-derivation of `signing.virtual_size` against embit's own non-witness serialization | **Exact match** on 6 constructed transactions |
| Numerical test of the fee estimator across 1–10 inputs × 70–73-byte signatures | **Never underestimates** (worst case delta `0`) |
| Quantification of the fee-ceiling input limits | New quantified finding (W-1, §1) |
| Read-only scan of the packaging path (`Start Easy Multisig.command`, build scripts, SBOM, licences) | Two new findings (§2 W-2, W-3) |
| Adversarial DOM-sink enumeration of `ui.html` | Zero injection sinks |
| **Adversarial red-team** of the transaction/signing pipeline — six scripted attack classes, ~100 hostile cases executed | **No fund-loss path found.** Every non-`ALL` sighash variant, high-S, bit-flipped DER, outsider/aliased/cross-input signature, threshold tamper, prevout/script swap and removed prior signature was refused; a fully signed **mainnet** transaction is refused at `/api/broadcast` with HTTP 400. See Appendix |

**Not performed:** no hardware device was connected; no transaction was signed with real keys or broadcast to any network; no owner wallet file or DMG was inspected; and no wallet identifiers were handled. Signing, finalization and broadcast paths were exercised only against synthetic fixtures, fake explorers and a recording broadcaster. Dependency installation and a few HTTPS requests to public explorers were the only network activity.

**A note on method.** I treated the prior Z.ai review as a hypothesis to re-test rather than as ground truth. Two of my own candidate findings were **falsified** and are *not* reported: (a) an "uppercase bech32 address is accepted at review but rejected at finalisation" bug — embit rejects uppercase addresses outright, so the address is refused cleanly at prepare time; (b) an apparent `virtual_size` mismatch — that was a bug in my own throw-away parser, and `signing.virtual_size` is correct. One test failure I initially observed was traced to my own filesystem sandbox and is reported below as a **test-isolation** defect, not as a code defect. Findings that survived are marked as independently reproduced where I verified them, and as *new* where they are absent from the prior review.

---

## 1. Safety of operation — can this tool construct a bad transaction and lose Bitcoin?

### Findings

#### Hot

- **H-1 — No defect found that can produce a malformed, mis-valued, or mis-directed transaction inside the supported scope.** This is a negative result, but it is a *tested* negative result, so the argument matters. The chain is closed at every joint:
  - **Inputs provably belong to this wallet.** Each selected outpoint's full previous transaction is fetched and parsed, and the input is rejected unless `previous.txid() == utxo.txid`, `prevout.value == utxo.value`, and `prevout.script_pubkey == derived.script_pubkey()` (`wallet_service.py:812-821`). A hostile explorer cannot fabricate a spendable output; it can only refuse service.
  - **The fee is exact, not estimated.** One selection function (`_select_inputs`, `wallet_service.py:595-626`) feeds both the live preview (`:669`) and the builder (`:756`), so they cannot disagree about which coins are spent. The build aborts unless `packet.fee() == fee` (`wallet_service.py:836-837`). **I verified independently** that the size estimator is conservative and never underestimates: across 1–10 inputs and 70–73-byte signatures, estimated vbytes ≥ actual vbytes in every case (worst case equality at the maximum 73-byte signature the estimator assumes). The effective sat/vB can therefore only drift *above* the requested rate, never below.
  - **I verified `virtual_size` is exactly BIP141-correct** by rebuilding the same transactions with embit's own non-witness serialization and comparing weights; 6/6 exact matches (`signing.py:159-175`).
  - **Change can neither vanish nor fall under dust.** A partial send requires `total ≥ amount + fee + 546` before building (`wallet_service.py:770-771`), so change is always ≥ dust; Send All must equal the whole scanned confirmed balance and emits exactly one output (`:760-769`).
  - **What is reviewed is what is signed and broadcast.** SegWit keeps signatures out of the txid, so the txid is computed before signing and re-verified at finalisation (`signing.py:254-258`), compared field-by-field against the immutable reviewed snapshot (`gui.py:777-790`), and the operator must echo the txid before submit (`gui.py:806-809`).
  - **A signature that does not verify cannot be counted.** Every counted signature is DER-parsed, restricted to `SIGHASH_ALL`, and ECDSA-verified against the BIP143 digest of *this* transaction with the verified prevout value and witness script (`signing.py:75-114`).
  - **Coins are re-checked as unspent immediately before preparation and again immediately before submit** (`gui.py:1003`, `:826`), with dual-source and tip-agreement on mainnet (`gui.py:209-226`).
  - **Mainnet broadcast is refused in code**, not merely in the UI (`gui.py:799-803`), with a UI backstop that hides the control entirely.
  - **Independently red-teamed, and it held.** A separate adversarial pass ran roughly 100 hostile cases across six scripted attack classes and found **no fund-loss path**: all six non-`ALL` sighash variants, a high-S signature, a bit-flipped DER signature, an outsider-key signature, an aliased signature and a cross-input transplant were refused; mutating a scanner UTXO value was caught by the prevout binding; device metadata rewrites (a raised output value, an altered `witness_utxo`, a changed input outpoint) were **silently discarded rather than honoured**; and a complete mainnet `import → scan → prepare → sign → finalize` chain returned **HTTP 400** at broadcast. The pass also closed a hypothesis I had raised: the `if expected_txid:` guard in `finalize_multisig` (`signing.py:254`) is **unreachable-by-design**, because `PreparedPayment.create` refuses a missing, empty or `None` txid (`gui.py:257-258`). Key exposure was audited by reading rather than by this pass (Appendix row 25).

- **H-2 — The BIP48 change inference for an unrestricted BSMS is the one real-money decision that has never been exercised against the live mainnet wallet.** For a Nunchuk-style export (`No path restrictions`, bare `/*`), change is derived as `/1/*` from the same three xpubs under a genuinely strict guard: sorted native-SegWit 2-of-3, three identical four-level BIP48 account origins with hardened account level, and a first receive address that must reproduce `receive.derive(0)` (`wallet_service.py:290-300`, `:307`, `:318-334`). I reviewed this logic closely and consider it well built and correctly fail-closed. The residual risk is not a code defect: if the *source* wallet used custom branch indices, the change output lands on addresses that wallet will not auto-discover. Funds remain spendable by the same three seeds via descriptor import, so this is a *visibility* failure, not permanent loss — but for the non-technical executor this tool is built for, "money the tool put somewhere the tool can no longer see" is precisely the failure mode the project exists to prevent. The project documents this honestly (`CHANGE-ADDRESS-REVIEW.md:25-27`) and correctly lists it as the first Phase 5 gate.

- **H-3 — The entire mainnet path is unexercised.** `README.md:3` and `PHASE-HANDOFF.md:19` state plainly that no mainnet transaction has ever been prepared, signed, or broadcast by this app. Everything mainnet-specific — the high-value confirmation (`gui.py:964-987`), the dual-source outpoint check (`network_config.py:57`), the BIP48 coin-type `0'` path, and the dry-run flow itself — has zero execution history. This is the correct thing for the project to be honest about, and it is also exactly why it cannot be graded as production-ready.

#### Warm

- **W-1 — *(new, quantified)* The 10,000-sat fee ceiling binds far earlier than the documentation implies, and there is no override — so a many-UTXO wallet cannot be recovered at all.** The ceiling is absolute (`wallet_service.py:38`, `:51-55`, `:764-766`) and the rate is capped at 25 sat/vB (`gui.py:959-963`). Because a 2-of-3 P2WSH input costs ~104 vB, the ceiling caps the spendable input count:

  | Requested rate | Maximum inputs before the build is refused | Fee at the cap |
  |---|---|---|
  | 1 sat/vB | 94 | 9,955 sats |
  | 2 sat/vB | 46 | 9,830 sats |
  | 5 sat/vB | 18 | 9,875 sats |
  | 10 sat/vB | **8** | 9,250 sats |
  | 20 sat/vB | 3 | 8,000 sats |
  | 25 sat/vB | 3 | 10,000 sats |

  An estate wallet with, say, 12 UTXOs is therefore unrecoverable at 10 sat/vB: partial send is refused by the ceiling, and **Send All is refused by the same ceiling** (`:764-766`). The tool's entire reason for existing is availability at an unpredictable future moment; this is the sharpest expression of the project's own acknowledged "fee policy" gap. This is a *liveness* failure, not a fund-loss one — the money is not at risk, but the mission can fail with no way forward inside the app.

- **W-2 — *(new)* A broadcast HTTP 5xx is reported to the operator as a definitive network refusal, when it is an unknown outcome.** `broadcast_transaction` converts *every* `HTTPError`, including `500/502/503/504`, into `WalletError("The network refused this transaction: …")` (`wallet_service.py:89-97`), while only transport-level failures (`URLError`, timeout, `OSError`) raise `BroadcastOutcomeUnknown` (`:98-102`). A reverse proxy that returns 502/504 after the node already accepted and relayed the transaction is the classic case. This directly contradicts the project's own invariant that an indeterminate submission is outcome-unknown and must never be blind-retried (`AGENTS.md:26`). The blast radius is bounded and I want to be precise about why: a retry re-submits the byte-identical transaction (same txid), so re-broadcast is idempotent; and a genuinely *different* replacement spend is still blocked by the pre-broadcast outspend re-check (`gui.py:826`). The real costs are a false statement shown to the operator and the fact that the pending-payment pause (`gui.py:843-845`) is not armed. Severity: warm, not hot.

- **W-3 — Explorer dependence is structural and honestly bounded, but practice networks have only a same-operator recheck.** Balances, UTXO sets, fee quotes and broadcast all depend on public Esplora instances. Mitigations verified: genesis and Mutinynet block-1 checkpoint pinning (`network_settings.py:108-135`, `network_config.py:43`), strict typed schema validation with size caps (`wallet_service.py:111-158`, `:435-455`, `:517-528`), UTXO/total reconciliation (`:458-473`), and unspent re-checks before prepare and broadcast (`gui.py:1003`, `:826`). Mainnet uses an independently operated second Esplora with a ≤2-block tip agreement; Testnet4 and Mutinynet do not (`network_config.py:57-58`). This is a stated limitation, not an oversight, and the realistic worst case is a refused payment rather than a bad one.

- **W-4 — A fee-quote outage is fatal, with no runbook fallback.** Preparation hard-requires a live quote (`gui.py:942-950`), and the 25 sat/vB refusal (`:959-963`) triggers exactly when a busy mempool would need more. For an estate-recovery tool whose value is availability at an arbitrary future date, this is the operational weak spot the project itself identifies as an open Phase 5 decision.

- **W-5 — "Send All" means "all found by this scan", and the operator is not asked to acknowledge it specifically.** The 20-address gap and 100-index cap are real (`wallet_service.py:35-36`) and the copy is honest ("Send all confirmed Bitcoin found by this scan"), but the number 20 never appears in the UI, the 100-cap only appears when tripped, and passing the gate requires only the *generic* review acknowledgement whose wording emphasises destination, amount, fee and change — not "this is everything the scan found" (independently confirmed against `ui.html:349-350`, `:418-419`, `:1174`).

- **W-6 — *(new)* The mainnet broadcast refusal is a single-layer guard, and the engine beneath it will still post to a mainnet endpoint.** `gui.py:799-803` is the only place mainnet is refused. `wallet_service.broadcast_transaction(raw, chain="main")` performs an outbound submission to the configured mainnet broadcaster with no further check — verified directly by the red-team, which observed the request leave the process. This is consistent with the documented architecture (`gui.py` owns the network gates), but it means the product's headline guarantee rests on one call site inside a 1,057-line file that, as §2 H-3 shows, has no effective test. Any future CLI, additional endpoint or refactor that calls the engine directly would bypass mainnet refusal silently. Defence-in-depth belongs at the engine boundary too.

#### Nice to have

- **N-1 — Preview/builder fee-cap asymmetry (confirmed, and confirmed untested).** `estimate_fee_preview` applies the 10,000-sat ceiling only for Send All (`wallet_service.py:677-681`), whereas the builder applies `check_fee_safety` unconditionally (`:772`). A partial-send preview can therefore display a fee the builder will then refuse. It fails in the safe direction, but it is a real inconsistency. I checked coverage: the only test touching the ceiling is `tests/test_wallet_service.py:277`, and it exercises the **Send All** path only — the partial-send preview/builder asymmetry has no test.
- **N-2 — Effective rate drift.** Because the estimator assumes maximum-length signatures, the finalised effective sat/vB is slightly above the requested rate (~1%). The absolute fee is what was reviewed, and it is disclosed at finalisation (`gui.py:774`). Acceptable.
- **N-3 — A second device response arriving for an already-replaced payment is refused** (`gui.py:735-738`). Fails safe; only mildly confusing.
- **N-4 — Change-index selection can reuse an index the scan did not observe** (`wallet_service.py:777-783`). Privacy-only, since address reuse cannot lose funds.

### Recommendations to fix

**Hot**
1. **Before any partial mainnet send, independently establish the live wallet's change policy.** Derive the first *unused* change address and its full script and derivation in the originating wallet (or read it off a signer screen) and compare it with what the app derives. Record the *shape* of the proof in the repo, never the wallet data. If it cannot be established, keep that wallet on explicit Send All or a declared-change export. **Do not soften the strict-BIP48 guard to make this easier** — wallets outside it must stay fail-closed.
2. **Treat the mainnet dry run as the release gate it is:** prepare → two-device sign → finalise in memory → independently decode and verify witness scripts, outputs, change, fee and txid → **discard, never broadcast**. The code needs no change for this (`gui.py:799-803` is the only mainnet-specific refusal), which is itself evidence the gate was designed rather than bolted on.
3. **Do not attempt the "live Bitcoin network test" on this build as shipped.** `README.md:3` and the release notes are explicit that mainnet broadcast is refused in code; a live mainnet send requires a deliberate code change, a fee-policy decision and a new release, behind a per-transaction opt-in. Plan Phase 5 as *dry run first*, with the live send as a separate, explicitly authorised milestone.

**Warm**
4. **Resolve the fee ceiling and cap deliberately before mainnet** (W-1, W-4): either a bounded high-fee override behind a fresh, explicit high-fee review — with a stubbed busy-mempool quote test — or a plain-language referral to an established wallet when the cap binds. Also publish the input-count limit the ceiling implies, since at 10 sat/vB it is only 8 inputs. Consider making the ceiling *proportional* (a percentage of the amount) rather than an absolute 10,000 sats, which is what currently bites a many-UTXO estate wallet.
5. **Classify broadcast HTTP 5xx as `BroadcastOutcomeUnknown`, not as a refusal** (W-2): keep a definite refusal for 4xx responses that carry a node rejection reason, and treat 5xx as indeterminate so the pending-payment pause engages and the operator is told the truth.
6. **Add a second, independently operated outpoint source for Testnet4/Mutinynet** (W-3), and consider a `testmempoolaccept`-style acceptance pre-check before presenting broadcast as ready. Mainnet's dual-source check is the standard; make practice networks match as soon as a reliable second service exists.
7. **Define a fee-outage policy for urgent recovery** (W-4), e.g. a manually entered rate behind an explicit "no live reference" acknowledgement, so a third-party API outage cannot lock out a time-sensitive recovery.
8. **Add a second mainnet guard at the engine boundary** (W-6): have `broadcast_transaction` refuse a mainnet chain unless the caller supplies an explicit, short-lived broadcast authorisation bound to the prepared txid, so the headline guarantee no longer depends on a single call site in `gui.py`.

**Nice to have**
9. Apply the 10,000-sat ceiling inside `estimate_fee_preview` for partial sends so the preview can never show a fee the builder refuses (N-1), and add the missing test.
10. Add a Send-All-specific acknowledgement ("the scan stops looking after 20 unused addresses; this empties only what was found") rather than relying on the generic review checkbox (W-5).
11. Surface the 20-address gap number in the coverage copy rather than only "standard gap scan".

---

## 2. Safety of code & keys — could keys be stolen or the signing process subverted?

### Findings

#### Hot

- **H-1 — No hot finding. There is no seed, PIN, or private-key code path anywhere in this repository, and I verified every input surface.** The BSMS parser rejects private keys outright (`probe.py:157`), there is no key-generation code, HWI is the only device channel, and the app's interface to it is a **no-shell subprocess with the signing PSBT passed on stdin, never argv** (`probe.py:234-289`; `signature` sent as `"signtx " + psbt_base64` on stdin at `:284`), with bounded timeouts (180 s discovery/xpub, 600 s signing) and **no automatic retries**. Keys cannot be stolen *by this app* because the app never possesses them.

- **H-2 — The signer-response boundary is the strongest single piece of engineering in the project, and it has a stronger consequence than the prior review stated: even a fully malicious HWI cannot redirect funds.** `accept_signature_update` (`signing.py:117-145`) clones the app's own reviewed PSBT, imports **only** partial signatures from the device response, requires the unsigned transaction bytes to be identical, requires prior signatures to survive, then cryptographically verifies everything. Device-returned global/input/output metadata — the classic channel for a hostile signer to rewrite a payment — is structurally incapable of entering prepared state, and this is directly regression-tested with real cryptography: metadata injection, a changed `witness_utxo.value`, a nulled `witness_script`, added `unknown` fields, a changed output value, a corrupted signature, and PSBT field reordering are each pinned by `tests/test_signing.py:181-241`. The consequence I want to highlight: because returned signatures must verify against the **app's** transaction, a compromised or substituted `hwi` binary can only fail or deny service — it cannot obtain a signature the app will accept for a different payment. I verified `tests/test_signing.py` uses real derived keys and real ECDSA verification, not mocks.

- **H-3 — *(new)* The mainnet broadcast refusal — the product's headline safety guarantee — has no test that actually reaches it, and neither do two signature guards nor the security headers.** I did not find this by reading; it was found by **mutation** (deleting a guard from a scratch copy and re-running the suite), and it is the most important *code-safety* finding in this audit:
  - `tests/test_send_flow.py:307` (`test_broadcasting_real_bitcoin_is_not_enabled`) sets `app.chain = "main"` while the prepared payment's own chain is `testnet4`, so `_current_prepared` raises *"The wallet or balance changed"* (`gui.py:695-697`) **before** the real refusal at `gui.py:799-803` is ever reached — and that earlier message is exactly the string the test asserts (`:321`). **Deleting `gui.py:795-803` leaves the test passing.** The lock is correct in the code today (I traced it independently, and it is the linchpin of every "mainnet broadcast is refused" claim in the documentation), but nothing in the suite would notice if a Phase 5 edit removed or weakened it. That matters more than usual here, because Phase 5 is precisely the change that will touch broadcast code. The test's own docstring makes this worse: it asserts the lock "is checked against the open wallet's network **before anything else**" (`tests/test_send_flow.py:308-310`) — the opposite of what the code does, since `_current_prepared` runs first. The test documents an ordering the implementation does not have, and passes for the wrong reason. I verified the ordering (`gui.py:793-794` executes before `:800-803`) and the docstring directly.
  - Deleting `signing.py:102` (the `SIGHASH_ALL` / unexpected-signature guard) and `signing.py:131-133` (the removed-or-changed-prior-signature guard) **also breaks no test**; searching `tests/` for their message strings returns zero hits.
  - Deleting the entire CSP and security-header block (`gui.py:413-418`) **also breaks no test** — no assertion anywhere names `Content-Security-Policy`, `nosniff`, or `Referrer-Policy`.

  Two of these three guards protect exactly the property this audit was asked to test — that a device response cannot substitute, weaken or remove a signature — and the third protects the local API. Their logic is correct; their *regression protection* is absent.

#### Warm

- **W-1 — The local API trust boundary is "same user on this machine", and it is well defended at exactly that boundary.** Loopback-only bind on an ephemeral port (`gui.py:1040`), `Host`-header check (`:426-429`), `Origin` check plus `hmac.compare_digest` token comparison on every write (`:488-497`), token carried only in the URL fragment and never echoed into the unauthenticated page response (`:67-74`, `:436-444`), no request logging (`:402-404`), and `no-store`/`nosniff`/`no-referrer`/CSP headers (`:406-419`). Independently confirmed: `ui.html` contains **zero** `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write`/`eval`/`new Function`/`srcdoc`/`javascript:` sinks and no inline event-handler attributes; every wallet/device/error string is written with `textContent`. Residual: any code already running as the same user could talk to HWI itself — inherent to desktop signing, and correctly documented as accepted.

- **W-2 — *(new)* The double-click launcher installs an unhashed dependency and does not verify its version — contradicting the project's own supply-chain invariant.** `Start Easy Multisig.command:17-19` installs from `requirements.txt`, which is a bare `embit==0.8.0` with **no hashes**, rather than from `requirements.lock`, which carries the SHA-256. The guard is only `import embit`, not a version check, so any importable `embit` satisfies it. This is the easy path a non-technical user follows from the source archive, and it sits directly against `AGENTS.md:36` ("Dependency locks are hash-verified") and `README.md:46-54` (which correctly documents `--require-hashes -r requirements.lock`). **Scope, stated precisely:** the packaged DMG is unaffected, because PyInstaller bundles the environment at build time from `requirements-desktop.lock`. The prior review's claim that "the source lock's single hash is complete because `embit` is the only runtime dependency" is true of the lock *file* but misses that the shipped launcher does not use it.

- **W-3 — *(new)* No `LICENSE` and no third-party notices, although the DMG redistributes LGPL-2.1-or-later libusb.** The repository contains no `LICENSE`, `COPYING`, `NOTICE`, or third-party-notices file (`find` over the tree excluding `.git` returns nothing), and `scripts/build-macos.sh:53` bundles only `ui.html` and certifi data (`--add-data "ui.html:." --collect-data certifi`) with no licence text. `brew info libusb` reports **`LGPL-2.1-or-later`** for the pinned `libusb 1.0.30` recorded in the SBOM (`scripts/build-sbom.py:47-50`), and the SBOM carries no `license` field for any component. LGPL-2.1 carries notice and relinking obligations on redistribution. Separately, with no licence of its own the public repository is "all rights reserved" by default, which sits awkwardly beside a curated "source archive" that invites third-party review and use.

- **W-4 — The DMG is ad-hoc signed and unnotarized, so artifact integrity is strong but publisher attribution is missing.** `SHA256SUMS` is published in the same channel as the DMG, so it detects transfer corruption, not publisher impersonation; recipients must right-click → Open. The project holds this correctly as a Phase 5 dependency (`README.md:24`).

- **W-5 — *(new)* `_hwi_path` falls back to a `PATH` lookup even in a frozen build.** `probe.py:193-201` prefers the bundled `hwi` beside `sys.executable`, but if it is absent it falls through to `shutil.which("hwi")`. In a packaged app a missing bundled binary should be a hard error, not a silent PATH search that could execute a substituted `hwi`. Bounded by H-2 (it cannot redirect funds), so this is a hardening item, not a fund-safety one.

- **W-6 — The signing TCB is inherited, not audited.** `embit 0.8.0`, `HWI 3.2.0`, `pywebview`, `PyInstaller` and `libusb` are canonical, pin-and-hash-verified choices, but no one in this project's records has audited embit's PSBT/ECDSA internals or HWI's transports, and a build-time compromise of any of them defeats every app-level safeguard. This is the standard residual risk of composing rather than writing from scratch.

- **W-7 — A signed but unbroadcast mainnet transaction is itself spend authority.** During the dry run the finalised bytes live in process memory and can be saved deliberately. Python cannot guarantee memory erasure; the project's guidance (tiny self-owned amount, short session, keep the bytes private) is correct.

- **W-8 — *(new)* `brew install libusb` runs *before* the digest gate.** `.github/workflows/build-candidate.yml:73` installs the unpinned Homebrew formula — executing whatever install code it carries — and only afterwards verifies `libusb-1.0.0.dylib` against `LIBUSB_SHA256` (`:74-84`). The digest gate correctly protects the *bundled* library and correctly fails closed on a mismatch, but the unverified install step happens first. Verifying before installing, or vendoring the dylib, would be stronger.
- **W-9 — *(new)* CI never exercises the signed or notarized build path.** The `macos` job never sets `RELEASE=1` (`:93`), so `scripts/build-macos.sh:124,174` always produces the ad-hoc-signed `-UNSIGNED-TEST` artifact, and the `MAC_SIGN_IDENTITY` / `MAC_NOTARY_PROFILE` notarization branch (`:24-27`, `:178-180`) is never run. When Developer ID enrolment completes, notarization will land on a code path that has never executed in CI.
- **W-10 — *(new)* The regression suite does not protect the invariants the project states loudest.** See H-3. In addition to the untested guards there, three properties the project documents as guarantees have **no** test at all: refusal of a **removed prior signature**, refusal of a **non-`ALL` sighash type**, and refusal of **under-dust change** (the existing test at `tests/test_change_branch.py:171` covers a sub-dust *recipient amount*, never a change remainder in the 1–545 sat range). The project's own reviewer checklist (`PHASE-HANDOFF.md:35-41`) asks for exactly these.

#### Nice to have

- **N-1 — CSP retains `'unsafe-inline'` for `script-src`** (`gui.py:413-418`), required by the single inline `<script>` block in `ui.html:478-1497`. With no injection sink present this is a missing defence-in-depth layer rather than an exploitable hole.
- **N-2 — *(new)* CI installs one unpinned, unhashed dependency.** `python -m pip install --quiet pyyaml` in the source job (`.github/workflows/build-candidate.yml:38`) — the only dependency in the pipeline without a hash. It does not ship in the artifact, but it executes in CI with the repository checked out.
- **N-3 — `_validate_chain` still carries stale "test-only release" wording and is bypassed by the GUI.** `probe.py:465-472` raises "This test-only release will not probe or fund a mainnet wallet", yet the GUI's `/api/devices` path calls `probe_devices_detailed` directly (`gui.py:676`), so mainnet device probing *is* reachable by design. The CLI-only guard reads as a contradiction in a 0.4.3 that supports mainnet preparation and signing.
- **N-4 — *(new)* Latent case-sensitivity bug in the SBOM step.** `scripts/build-sbom.py:33` requires a *lowercase* 64-hex digest, but CI passes `vars.LIBUSB_SHA256` through raw (`:133`) while only the earlier build step lowercases it (`:83`). An uppercase repository variable would fail the SBOM step *after* a successful build and tests had already passed.
- **N-5 — *(new)* The documented test command does not reproduce CI.** `README.md:46-52` omits the `pip install pyyaml` that CI performs (`build-candidate.yml:38`), so anyone following the README sees **8 silent skips** covering the entire workflow-lint module. A skipped module is invisible; an unpinned CI-only dependency is the cause.

### Recommendations to fix

**Hot**
1. **Complete Developer ID signing and notarization, with a reverse-DNS `CFBundleIdentifier`, before the DMG is placed in front of the spouse/lawyer/accountant it is meant for.** Until then keep the right-click → Open instruction and the `UNSIGNED-TEST` artifact naming so nobody mistakes the current build for a verified publisher release.
2. **Add tests that actually reach the mainnet broadcast lock and the three unprotected guards** (H-3, W-10) *before* Phase 5 touches broadcast code. Concretely: prepare a payment whose `PreparedPayment.chain` is genuinely `"main"` and assert the refusal at `gui.py:799-803`; assert rejection of a removed prior signature, a non-`ALL` sighash, and an under-dust change remainder; and assert the security headers exist. Mutation-test each so a deleted guard fails the suite.

**Warm**
3. **Fix the launcher to use the hash-pinned lock and to check the version** (W-2): install `--require-hashes -r requirements.lock`, and replace `import embit` with a version assertion. This is a one-line-class change that closes a real supply-chain gap and removes a contradiction with `AGENTS.md`.
4. **Add a `LICENSE` and a `THIRD-PARTY-NOTICES` file, and bundle the notices into the DMG** (W-3) — minimally libusb's LGPL-2.1 text and PyInstaller's exception notice, plus licence identifiers in the SBOM. Decide and state the project's own licence.
5. **Externalize the inline JavaScript into a bundled `.js` file and tighten CSP to drop `'unsafe-inline'` for `script-src`** (N-1); a per-session nonce is even better. Pure hardening, no behaviour change.
6. **Make a missing bundled `hwi` a hard failure in frozen builds** (W-5) rather than falling back to `PATH`.
7. **Document the device/firmware matrix actually exercised** — Jade, Trezor Safe 3, Ledger Nano S Plus on the recorded versions — as a reviewed reference, so a future device-family addition is a decision rather than an accident. No firmware version is documented anywhere today.
8. **Reorder the build job so nothing executes before it is verified, and exercise the notarization path in CI** (W-8, W-9): verify or vendor the libusb dylib before `brew install`, and add a scheduled or opt-in job that builds with `RELEASE=1` so the signing/notarization branch is not first run on a real release.

**Nice to have**
9. **For the mainnet dry run, add a one-click "clear signed transaction from this session" control** (W-7) so the finalized bytes' lifetime in app state is operator-visible and deliberately ended.
10. **Pin or hash `pyyaml` in CI, and add it to the documented test command** (N-2, N-5), or parse YAML without a third-party dependency.
11. **Fix or remove the stale `_validate_chain` wording** (N-3) so the CLI and GUI tell one consistent story about mainnet, and normalize the libusb digest case before the SBOM step (N-4).
12. **When Python/HWI are upgraded, regenerate both lock files and re-pin all Actions in the same change**, and add a scheduled quarterly dependency review so the pins do not silently age.

---

## 3. Efficiency of design — is this best of breed? What would a third party say?

### Findings

#### Hot

- **H-1 — Verdict: a third-party reviewer would call this a genuinely impressive, purpose-built tool — "wow, this is careful" — with reservations about documentation currency and unfinished distribution, not about engineering.** The specifics that earn that verdict:
  - **One engine, three networks, no forks.** `wallet_service.py` + `signing.py` serve Testnet4, Mutinynet and mainnet behind a *data-only* network profile (`network_config.py`); there is no network-specific transaction code path to drift. The rule is stated (`AGENTS.md:13`), enforced, and tested.
  - **State-machine discipline around the payment.** The frozen `PreparedPayment` binds wallet identity, chain, scan generation, review id, txid, review values and selected outpoints through every transition (`gui.py:234-271`); staleness is caught by generation *and* object identity (`:698-700`, `:736`, `:814`); broadcast holds the session lock through submission so no concurrent refresh can alter an in-flight payment (`:810-816`). The 0.2.1 stale-screen bug class has a DOM regression test pinning it shut.
  - **The off-the-shelf selection is correct, not lazy.** embit (small, purpose-built descriptors/PSBT), Bitcoin Core HWI (the reference device implementation), Esplora's standard API, `pywebview` + PyInstaller for a native Mac shell, stdlib `http.server` for the loopback API. No framework, no blockchain-as-a-service, and — decisively — **no key-handling code written here**.
  - **Documentation as an engineering artifact.** Phase records with acceptance gates, per-release evidence with run URLs and SHA-256s, honest separation of owner-reported from independently verified evidence, superseded statements marked rather than deleted, and an agent guide whose invariants match the code (I checked several; they do).
  - **Test quality is adversarial, not decorative.** 172 tests covering corrupted signatures, metadata-rewrite attacks, txid swaps, unknown-outcome broadcast locks, concurrent import during broadcast, spent-outpoint refusal, mainnet refusal, and Node UI state regressions; CI re-runs the suite on the extracted source archive. I ran it: green.

#### Warm

- **W-1 — `gui.py` concentrates too much.** HTTP plumbing, session state, fee and price reference fetching, settings, and the entire prepare/sign/finalize/broadcast orchestration live in one 1,057-line file. It is organized and heavily guarded, but the payment lifecycle is the security-critical core, and it currently cannot be read — or reviewed — in isolation.
- **W-2 — *(new, sharpened)* Documentation volume has hardened into demonstrable internal contradiction, not merely sprawl.** The prior review called this a navigation problem; it is stronger than that. Concrete, checkable contradictions between documents that describe the *current* product:
  - `ROADMAP.md` contradicts itself: `:5` states v0.4.3 is current with Phases 1–4 complete, while `:20` labels v0.1.27 the "Previous build", `:225` says Phase 4 has only been *asked to begin*, and `:243` declares signing and broadcast "**future scope, not existing functionality**" and instructs agents not to implement the phase — while that same line notes "`replit.md` currently says no signing or broadcasting", i.e. a drift notice sitting inside a document that is itself stale.
  - `DISCLAIMER.md:10` still frames **0.2.0** as the version that "can ask hardware devices to sign and can broadcast to Testnet4", and never mentions Mutinynet.
  - `replit.md:5` says the tool "serves Testnet4 and mainnet" and "broadcasts only to Testnet4" — stale since 0.3.0 — and `:7` still calls "0.2.0 … the hot-audit-fix milestone".
  - `PROJECT-HISTORY.md:159` says "**No Apple Silicon window walkthrough**" and `:167` says "No hardware signer… signing and broadcast remain unimplemented by design" — both long superseded.
  - `PATCH-0.2.1.md:23` says acceptance "remains pending until… the transaction confirms", while `RELEASE-HISTORY.md:56-58` records it as confirmed.
  - `README.md:36` labels the device table "Hardware tested before 0.2.0", understating the 0.3.2/0.4.1 evidence it elsewhere cites.

  Note that commit `61371d5`, titled *"docs: consolidate release history, trim stacked status notices"*, landed immediately before this audit and **did not fix these**; the contradiction is live on `main` today.

#### Nice to have

- **N-1 — Scanning is slow and chatty by design.** Up to ~200 address queries per scan with 2 workers in sequential 10-address chunks (`wallet_service.py:492-507`). Bounded, consented, and honest — but a wallet with deep history will feel sluggish, and every scanned address is disclosed to the explorer.
- **N-2 — `ui.html` is a 1,499-line monolith** mixing structure, styling and logic, which also blocks the CSP tightening above.
- **N-3 — No plain-language architecture / threat-model page** for a third-party reviewer, even though `AGENTS.md`'s invariant list is already most of the content.
- **N-4 — *(new)* The release workflow exists twice, byte-for-byte.** `.github/workflows/build-candidate.yml` and `ci/build-candidate.yml` are identical, and the source archive copies the latter (`scripts/build-source.sh:44-51`). Keeping two copies in sync is a manual burden enforced only by a test.
- **N-5 — *(new)* The source archive omits `RELEASE-HISTORY.md`, which its own README tells reviewers to read.** `scripts/build-source.sh:20-26` copies an explicit allow-list of 21 root documents, and `RELEASE-HISTORY.md` is not among them — I diffed the list against the root `*.md` set and it is the only document missing. But `README.md:3` points to it as "the version-by-version record of changes, corrections and evidence", and `AGENTS.md:7` instructs any reviewer to read it third. So the shipped source tarball contains a README that links to a file the tarball does not contain — and it was the doc-consolidation commit `61371d5` that made `RELEASE-HISTORY.md` the canonical version record without adding it to the archive.

### Recommendations to fix

**Hot**
1. **Keep the one-engine rule absolute through Phase 5.** Resist any pressure to add a "mainnet-special" path, endpoint or flag beyond the deliberate per-transaction broadcast opt-in already specified in the roadmap.

**Warm**
2. **Extract the payment lifecycle from `gui.py` into its own module** (W-1) — `PreparedPayment` transitions and the sign/finalize/broadcast gating, with the invariants as docstrings and a dedicated test file — leaving `gui.py` as HTTP/session plumbing. This is the single highest-leverage refactor for third-party reviewability.
3. **Consolidate the document set** (W-2): one short `CURRENT-STATUS.md` (version, what is proven, what is next, links), `README.md` trimmed to capabilities + install, a single `CHANGELOG.md` carrying per-release corrections, and everything else explicitly marked archive. Critically, **fix the six concrete contradictions above in the same change** — a reviewer who finds `ROADMAP.md` claiming signing is "future scope" has to distrust the rest of the set.

**Nice to have**
4. Increase scan parallelism modestly (4–8 workers) with the same gap logic, show per-branch progress, and consider incremental re-scans from the last used index within a session (N-1).
5. Split `ui.html` into HTML/CSS/JS assets (N-2), which also unblocks the CSP fix, and add a plain-language threat-model page (N-3).
6. Make the workflow canonical in one location and have the archive copy it at build time (N-4).

---

## 4. Grade

### Findings

#### Hot

- **Overall: 7.5 / 10**, with a wide split that matters more than the average:
  - **8.5 / 10 as a scoped 2-of-3 native-SegWit practice-network recovery tool and mainnet-dry-run candidate.**
  - **4 / 10 as a tool to hand to the non-technical executor for real Bitcoin today.**

  The prior Z.ai review graded 8/10 scoped and 5/10 for unattended mainnet use. I land close on the scoped number and **one point lower** on the mainnet/executor number, for three reasons I verified independently: the shipped launcher installs an unhashed dependency and contradicts the project's own supply-chain invariant (§2 W-2); the DMG redistributes LGPL-2.1-or-later libusb with no licence or notices and the repo has no licence at all (§2 W-3); and the 10,000-sat ceiling makes a many-UTXO wallet unrecoverable with no in-app escape (§1 W-1). None of these is a fund-loss defect — that is why the scoped grade stays high — but each directly degrades the intended-user story.

#### Warm

- **Subscores (out of 10, my own assessment):**

  | Dimension | Score | Basis |
  |---|---|---|
  | Transaction correctness within declared scope | **9** | No fund-loss path found; fee exact and conservative (verified numerically); review→finalize→broadcast binding intact; adversarially tested |
  | Key and secret safety | **9** | No key path in-app; PSBT on stdin; signature-only import defeats even a malicious HWI; no XSS sinks; loopback boundary solid |
  | Design and architecture | **8** | Right engine count, right components, real state-machine discipline; `gui.py` concentration is the visible cost |
  | Usability for the intended non-technical user | **7** | Plain language, accessible, visible gates, honest failure text; but unnotarized install, no operator guide, mainnet-USD scares on worthless practice coins, gap-of-20 not surfaced |
  | Testing and evidence | **7** | Genuinely adversarial suite with real cryptography, archive-level CI re-run, recorded physical evidence — but mutation testing shows the mainnet broadcast lock has no effective test and three further guards are unprotected (§2 H-3, W-10); practice networks single-source; no mainnet dry run |
  | Distribution and release readiness | **4** | Hashes, SBOM, immutable releases, mandatory libusb digest — but unsigned, unnotarized, no licence, unhashed launcher install |
  | Documentation currency | **6** | Content is unusually good; currency is not — six live contradictions on `main` |

- **Why not higher.** Not one of the remaining blockers is a discovered defect. They are unpassed gates — no mainnet dry run, no live-wallet change-policy proof, an unresolved fee policy, an unnotarized DMG — plus the three distribution/compliance items above. A tool whose whole purpose is to be usable years from now, by someone who is not a Bitcoiner, during what is probably a difficult week, cannot be scored as production-ready while its install path needs a Gatekeeper bypass and its operator guide does not exist.

#### Nice to have

- **Why not lower.** The security thinking here is better than most audited production wallets. The signature-only import boundary, verified-prevout binding, fail-closed BSMS parsing, outcome-unknown handling, and the refusal to invent a change path are exactly the controls a from-scratch wallet should have and frequently does not. The project's own documentation of its limits does more for trust than most marketing.

- **Third-party impression.** Expect: *"This thing is careful — the guardrails are real, and it documents its own limitations."* Followed immediately by: *"Which document is current?"* and *"It isn't notarized, so I can't attribute the download."*

### Recommendations to fix

**Hot**
1. **Treat the Phase 5 sequence as the grading rubric it already is**, in order: (1) live-wallet change-policy verification; (2) mainnet dry run with independent decode; (3) fee-policy decision; (4) Developer ID + notarization. Then, only on explicit owner authorization, the deliberate per-transaction mainnet opt-in. Each closed gate moves the mainnet score; nothing else will.
2. **Close the three distribution/compliance items in one release** (unhashed launcher install, missing licence/notices, missing notarization). These are cheap relative to their effect on the executor-facing grade.

**Warm**
3. **Commission at least one external review of the two inherited critical components** — embit's PSBT/ECDSA paths and HWI's transports — or pin them to releases that have one, and record the provenance decision in the repo.
4. **Re-grade after the dry run and a notarized release.** A 9/10 as a scoped 2-of-3 recovery tool is a realistic ceiling, with the last point reserved for practice-network independence checks, the operator guide, and time passing without incident.

**Nice to have**
5. Publish a short "known limits and open gates" table at the top of `CURRENT-STATUS.md` so the grade-relevant gaps are the first thing a reviewer sees rather than something they must assemble from six documents.

---

## 5. Improvements

### Findings

#### Hot

- **Phase 5 is correctly sequenced; the risk is skipping steps, not missing them.** The code needs no change for the dry run (`gui.py:799-803` is the only mainnet-specific refusal), which is itself evidence that the gate was designed rather than retrofitted. The improvements that matter most are therefore procedural, in this order: change-policy proof for the live wallet → dry run with independent verification → fee decision → notarization → deliberate opt-in.

#### Warm

- ***(new)* The single most likely source of a confusing false failure is an environment-dependent test.** `tests/test_gui_integration.py` patches `load_servers` (`:79`) but **not** `save_servers`/`settings_path`. `test_stale_explorer_settings_invalidate_a_review` (`:338-349`) therefore drives `/api/settings` with `action="reset"`, which writes to the **real** `~/Library/Application Support/Easy Bitcoin Multisig/settings.json`. Two consequences I verified: (a) running the suite silently **resets a developer's own saved explorer/broadcaster settings to defaults**; (b) in any environment where `$HOME` is not writable — a read-only container, a hardened CI runner, or a sandboxed reviewer such as this audit — the suite reports a **failure** that is not a code defect. I confirmed the diagnosis: with `settings_path` redirected to a temp directory, that test passes and the full suite is 172/172 green. Note also that four other test modules (`test_desktop.py:26`, `test_gui.py:37`, `test_network_settings.py:22`, `test_send_flow.py:44`) *do* isolate this path, so this is an inconsistency rather than a house style.

- **Operator-facing deliverables still lag the engine.** The plain-language one-page guide (devices, a test payment, what a missing device looks like, "not finished until confirmed", what to do when stuck) is planned but unwritten. For the tool's actual user it is worth as much as any code gate.

- **The stuck-payment story is thin.** RBF is signalled (`wallet_service.py:796-798`) but there is no bump flow and the guidance points back to the originating wallet; a fee-bump runbook — or a minimal bounded bump feature — belongs on the Phase 5 list.

- **Dependency freshness has no owner.** HWI 3.2.0 caps Python below 3.13 (`AGENTS.md:36`) and pins the device-support surface to mid-2025-era firmware; `embit 0.8.0` likewise. Fine today; a deliberate upgrade review should be scheduled rather than discovered.

- ***(new)* The README's documented test command silently skips a whole module, and the archive build ships a hardcoded file list that is already demonstrably wrong.** Following `README.md:46-52` verbatim yields **8 skips** — the entire `test_workflow_config` CI-lint module, reason `PyYAML not installed` — because CI installs `pyyaml` (`build-candidate.yml:38`) but the README does not. A skipped module is worse than a failing one, because nothing signals it. Separately, `scripts/build-source.sh:20-26` copies an explicit document list, and it has already drifted: **`RELEASE-HISTORY.md` is missing** from the shipped archive even though the archive's own README and `AGENTS.md:7` direct reviewers to it (§3 N-5). The existing "every root module must ship" loop (`:31-40`) guards `*.py` but not documents; extend the same assertion to root `*.md`, and add `RELEASE-HISTORY.md` and both 0.4.3 audits.

- ***(new)* The suite does not protect the invariants the project states most loudly.** Mutation testing (§2 H-3) showed that deleting the mainnet broadcast refusal, the sighash-type guard, the removed-prior-signature guard, or the CSP/security-header block breaks **no test**, and three documented guarantees have no test at all (removed prior signature, non-`ALL` sighash, under-dust change). This is the cheapest high-value hardening available before Phase 5, and it protects precisely the code that is about to be edited.

- ***(new)* Three defects in the release gate's ordering and coverage.** `brew install libusb` executes before the digest gate (§2 W-8); the `macos` job never sets `RELEASE=1`, so the signed/notarized path is never exercised in CI and will be first run on a real release (§2 W-9); and the SBOM step's lowercase-hex requirement (§2 N-4) is a latent failure that would surface *after* a successful build and test run.

#### Nice to have

- **Product surface:** fee-preview cap parity, second-source practice-network checks, scan speed/progress, doc consolidation, asset split, device/firmware matrix page, session "clear signed bytes" control, quarterly dependency/pin review.

### Recommendations to fix

**Hot — first**
1. **Verify the live wallet's change policy independently before any partial mainnet send.** Derive the first *unused* change address plus its full script and derivation in the originating wallet (or read it on a signer screen) and compare against what the app derives. Record the proof's *shape only*, per the standing no-wallet-data rule. If it cannot be established, keep that wallet on Send All or a declared-change export, and keep wallets outside the strict-BIP48 guard fail-closed.

**Hot — second**
2. **Run the Phase 5 dry run exactly as gated:** import the real BSMS, verify the change policy, prepare a small payment to an owner-controlled destination, obtain two device approvals, then independently decode and verify the finalised transaction (per-input witness against the wallet's own witness script; outputs, change address, change amount and fee against the review; txid before = txid after). Keep the bytes private. **Do not broadcast.** Then make the fee decision (bounded high-fee override with fresh explicit review, or documented referral) and land Developer ID + notarization with a reverse-DNS bundle identifier.

**Hot — third**
3. **Only on explicit owner instruction, implement the mainnet broadcast opt-in as specified:** per-transaction, visible, naming mainnet, default-refused, txid-bound, with tests proving broadcast remains impossible without it — including cancellation, stale-state, duplicate-submission, timeout and unknown-outcome paths.

**Warm**
4. **Fix the four verified correctness/isolation issues from this audit, in this order:**
   - **(a)** `Start Easy Multisig.command`: install with `--require-hashes -r requirements.lock` and assert the `embit` version (§2 W-2). One-line-class; closes a real supply-chain gap and a contradiction with `AGENTS.md`.
   - **(b)** Broadcast HTTP 5xx must raise `BroadcastOutcomeUnknown`, not "the network refused" (§1 W-2). Add a test for a 502 after acceptance.
   - **(c)** Isolate `settings_path`/`save_servers` in `tests/test_gui_integration.py` so the suite stops writing to the real user settings file and stops failing in read-only environments (W-1). Add a regression assertion that no test writes outside its temp directory.
   - **(d)** Apply the 10,000-sat ceiling inside `estimate_fee_preview` for partial sends, and add the missing test (§1 N-1).
   - **(e)** Add the missing regression tests for the guards mutation testing found unprotected (§2 H-3, W-10) — the highest-value item on this list — and fix the README/CI `pyyaml` mismatch so the documented command reproduces CI (§2 N-5).
   - **(f)** Verify or vendor libusb before `brew install`, and add a CI job that exercises `RELEASE=1` (§2 W-8, W-9).
5. **Add `LICENSE` and `THIRD-PARTY-NOTICES`, bundle the notices into the DMG, and add licence identifiers to the SBOM** (§2 W-3).
6. **Write the one-page operator guide and a stuck-payment runbook**, add the supported wallet/export/device/firmware matrix, and schedule the quarterly dependency/pin review covering HWI, embit, certifi, Actions pins and the libusb digest.
7. **Make a missing bundled `hwi` a hard failure in frozen builds** rather than a `PATH` fallback (§2 W-5), and pin or remove the CI-only unhashed `pyyaml` (§2 N-2).

**Nice to have**
8. **Publish the fee ceiling's practical consequence** — at 10 sat/vB it is 8 inputs — and consider a proportional ceiling rather than an absolute 10,000 sats, since that is what currently blocks a many-UTXO estate wallet (§1 W-1).
9. The remaining polish: `gui.py` payment-lifecycle extraction, doc consolidation **including the six live contradictions**, `ui.html` asset split with strict CSP, faster and progressive scans, a Send-All-specific acknowledgement, the gap-of-20 surfaced numerically, and a session control to clear signed bytes. None of these should delay the Phase 5 sequence; all of them make the tool read, to a third party, like what it already is.

---

## Appendix — Verification log

Everything below was executed against a clean clone of `main` at `7d622ef` in Python 3.12.14 with `embit 0.8.0` installed from the hash-pinned source lock.

| # | Check | Result |
|---|---|---|
| 1 | `python -m unittest discover -s tests -q` (settings path writable, `pyyaml` present) | **172 tests, 0 failures, 0 errors, 0 skips** in 37.7 s |
| 1b | Same suite following `README.md:46-52` verbatim (no `pyyaml`) | 172 run, **8 skips** — the entire `test_workflow_config` module, reason `PyYAML not installed` |
| 1c | `node tests/ui_state_reuse.cjs` and `node tests/ui_send_mode.cjs` (node v25.8.0) | Both pass, exit 0 |
| 2 | Same suite with the ambient `$HOME` unwritable (this sandbox) | 1 failure in `test_stale_explorer_settings_invalidate_a_review` → traced to the real settings-file write, **not** a code defect; now the §5 test-isolation finding |
| 3 | `signing.virtual_size` vs embit's own non-witness serialization, 6 constructed segwit transactions | **6/6 exact** → `virtual_size` is BIP141-correct |
| 4 | `_estimated_signed_vbytes` vs authoritative vsize, inputs 1/2/3/5/10 × signatures 70/71/72/73 B | **Estimated ≥ actual in all 20 cases**, worst-case delta `0` at the assumed 73-byte signature → the estimator never underestimates |
| 5 | Uppercase and mixed-case bech32 destination through embit | Both **rejected** (`Invalid bech32 address`) → my candidate "uppercase accepted at review, rejected at finalisation" bug is **falsified**, not reported |
| 6 | Fee-ceiling input limits derived from the real estimator | 8 inputs at 10 sat/vB, 3 at 25 sat/vB → new finding §1 W-1 |
| 7 | Launcher vs lock files | `Start Easy Multisig.command:19` uses `requirements.txt` (unhashed), guard is `import embit` only → new finding §2 W-2 |
| 8 | Licence/notice inventory over the tree (excluding `.git`) | **No `LICENSE`/`NOTICE`/`COPYING`/third-party file**; `brew info libusb` → `LGPL-2.1-or-later`; build bundles no licence text → new finding §2 W-3 |
| 9 | `MAX_ESTIMATED_FEE_SATS` coverage in tests | Only the **Send All** path is tested (`tests/test_wallet_service.py:277`); the preview/builder asymmetry is untested → §1 N-1 |
| 10 | `ui.html` DOM-sink enumeration | **Zero** `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write`/`eval`/`new Function`/`srcdoc`/`javascript:`/inline handlers |
| 11 | Workflow trigger and publish gating | `workflow_dispatch` only; Actions SHA-pinned; Python 3.12 pinned; tests before build; `LIBUSB_SHA256` mandatory; release refuses an existing tag → no push-to-publish path found |
| 12 | `tests/test_signing.py` inspection | Real derived keys, real ECDSA verification, real re-parsing — adversarial, not mocked |
| 13 | Docs cross-read | Six live contradictions identified (§3 W-2) |
| 14 | **Mutation:** delete `gui.py:795-803` (mainnet broadcast refusal) from a scratch copy | `test_broadcasting_real_bitcoin_is_not_enabled` still **passes** → the lock has no effective test (§2 H-3) |
| 15 | **Mutation:** delete `signing.py:102`, `signing.py:131-133`, and the CSP block `gui.py:413-418` | Full suite result unchanged → three guards and the security headers are untested (§2 H-3, W-10) |
| 16 | `requirements-desktop.lock` structural audit | 37 packages, **571 hashes, none missing**, no unpinned/URL/editable entries → `--require-hashes`-compatible |
| 17 | `bash -n` on all four shell scripts, `zsh -n` on the launcher, `node --check` on both UI tests | All clean; no `eval`, unquoted variables, `curl \| bash`, or TLS disabling found |
| 18 | CI ordering and coverage review | `brew install` before the digest gate; `RELEASE=1` never set in CI; SBOM lowercase-hex mismatch → §2 W-8, W-9, N-4 |
| 19 | Red-team: **fee/value integrity** — 26 hostile `fee_rate`/`amount`/`send_all` combinations, plus scanner-value mutation | All refused or invariants held (`reported fee == packet.fee()`, no outputs > inputs, change never under dust); scanner-value tampering caught by the prevout binding |
| 20 | Red-team: **change redirection** — 15 descriptor/restriction layouts, including bare `/*` at `xpub/0`, `<0;1>/*`, `/**`, `/0/*,/1/*`, mixed suffixes, duplicated xpubs and fingerprints, differing per-key origins, and all-`/1/*` | Every non-standard layout failed closed; no case produced a change output outside the wallet's declared or inferred change branch, and the built change address always equalled the reviewed one |
| 21 | Red-team: **signature forgery** — outsider key, high-S, six non-`ALL` sighash variants, bit-flipped DER, aliased signature, removed prior signature, 1-of-3 threshold tamper, prevout/script swap, cross-input transplant | **All refused**; metadata-rewrite attempts were discarded, not honoured |
| 22 | Red-team: **mainnet reachability** — full mainnet import → scan → prepare → sign → finalize, then broadcast | **HTTP 400**, *"Broadcasting real Bitcoin is not enabled in this build"* — refused at the API. The low-level `wallet_service.broadcast_transaction(chain="main")` *does* POST, showing the guard is single-layer (§1 W-6) |
| 23 | Red-team: **TOCTOU** — stale preparation, replayed `preparation_id`, scan-generation bump, concurrent import during broadcast | All refused; the broadcast lock held and the import could not displace the in-flight payment |
| 24 | Red-team: **falsy `expected_txid`** — `PreparedPayment.create` with missing, empty and `None` txid | All refused (*"The reviewed transaction ID is inconsistent"*) → the `if expected_txid:` branch in `finalize_multisig` is unreachable by design, closing a hypothesis I had raised |
| 25 | **By reading, not by the red-team pass:** key exposure — every outbound URL path built in `wallet_service`, every HWI argv, and the saved PSBT/diagnostic files | No xpub, descriptor, seed or private key reaches an explorer, a log, an argv or the diagnostic report; the signing PSBT travels only on stdin |

**No file in the audited repository was modified.** Scratch scripts used for checks 1–6 were written outside the clone; `git status` in the clone is clean at `7d622ef`.
