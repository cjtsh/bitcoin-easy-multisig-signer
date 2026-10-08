# ZCode Color Team Security Audit — Bitcoin Easy Signer 0.6.7 — Cycle 4

| | |
|---|---|
| **Version examined** | Tag `v0.6.7`, commit `81f58ec0dd8c8afa8dcc2c1f69c10057e62dfe7b`, published 2026-10-07T17:10:37Z |
| **Assets declared** | (1) the operator's Bitcoin — mainnet and practice-network funds; (2) signing and CI credentials and the release workflow ("loss of credentials is the same thing as loss of funds"); (3) the reviewed-transaction integrity chain (frozen `PreparedPayment` → PSBT → verified signer responses → final transaction); (4) release artifact integrity — the published DMG and SBOM; (5) wallet privacy — xpubs, addresses, BSMS contents, txids, device identities. All five mission-critical; the ranking orders severity, not attention |
| **Auditor** | A five-specialist Color Team panel plus a referee (framework `cjtsh/ai-color-team-audit-framework` v1.3.2, definitions v2.4); asset declaration, charters and grade rules locked in writing **before** the build was examined |
| **Surveyor** | Harness `Kimi Code desktop app` · session `not exposed by the harness` · model `not exposed by the harness` — declared in the signed plan §0 |
| **Auditor identity** | Harness `ZCode desktop app 3.14.4` · session `not exposed by the harness` (environment inspected; only app version and build commit present) · model `zai-api/GLM-5.3` (declared by the harness system prompt, not verified) |
| **Independence** | Surveyor and auditor ran in different harnesses as declared by the operator: **cannot be determined mechanically** — both session identifiers read `not exposed by the harness`, so independence rests on the operator's declaration; declared model names are declarations, never verifications |
| **Cycle** | `v0.6.7` (cycle 4) — this file is `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md` |
| **Prior audit** | Cycle 3: `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.6.md`, SHA-256 `e1623a984dc0f189f87dd0fd142409ba77b6b7f3fb1f032be0ad9d029cf39e68`, graded ⛔ **BLOCKED** (CT-48 High) |
| **Verification** | Suite re-run at the tag (520 tests OK, zero skips, CI-identical invocation) and after every break; all 10 release assets re-downloaded and re-hashed against `SHA256SUMS` (8/8 + 2 checksum files); `SHA256SUMS.asc` good signature from the committed release key; DMG codesign deep/strict valid, Gatekeeper accepted (Notarized Developer ID, Bitseeker LLC `B8G5L7M8TB`), notarization ticket stapled; Sigstore attestations verified; candidate run 37644267740 and publish run 37655666900 both at head `81f58ec`; every load-bearing claim of every lane personally re-derived by the referee **and independently re-derived again by the lead** (see *The lead's verification layer*) |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.7.md` (signed **Bitseeker LLC, 2026-10-07**), SHA-256 `1328590cc73647990fc02a3b204d7a2719c6816107d2ab3a5c43d65858df7040` before the first specialist ran and the same at the end — **equal: the scope never moved.** The signed plan was public on `origin/main` (`eb549a7`) before the panel was dispatched; the lock file is `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.6.7.md` |

---

## The grade: ⛔ BLOCKED — a lane proved its own failure state: the source-mode hardware-helper identity check can be made to pass while substituted code runs

This cycle audited the v0.6.7 remediation of cycle 3's BLOCKED (CT-48, the live "retired"
publish workflows). **That remediation is real and verified**: every publish-capable
workflow is deleted from every branch (13 on-branch deletion commits re-verified), a
fail-closed sweep gate runs on every dispatch against the live remote, the false "no
second path" comments are corrected, and the money-path engine — which cycle 3 cleared —
is byte-identical between the two tags, with its strongest-ever result: the signature
chain verified from-spec against BIP-143's published vectors, and no breach of the
reviewed-transaction chain was found by any lane.

Two new findings set the grade, each independently sufficient:

1. **CT-90 (Medium, the blocking lane finding).** In **source mode** (running from a
   checkout, not the shipped app), the check that pins the hardware-wallet library by
   hashing its files can be defeated: a substituted library that lies about where its
   files are makes the check hash the *genuine* files while the *attacker's* code runs —
   demonstrated live, with attacker code executing inside the check itself. This is
   Copper's EDGE TRUST BROKEN failure state, and the framework's ruling 4 makes it ⛔
   with no severity calibration and no weighing against clean lanes. The honest scope,
   which the grade does not soften but the reader deserves: the **shipped, signed,
   notarized bundle's identity chain is intact** (frozen-mode byte identity was attacked
   and held), and even a fully poisoned library does not bypass the device key-proof
   gates that guard every payment — the demonstrated loss is the pin's promised
   guarantee, xpub/PSBT exposure (asset 5), and a lying-enumerate surface.
2. **CT-72 (High).** A wallet file that lists the **same key twice with different origin
   fingerprints** is accepted and displayed as an honest "2-of-2" with two cosigner
   cards — while **one** device approval finalizes it. The screen shows a quorum that
   does not exist. Reproduced end-to-end twice (referee and lead, independently). This
   is deception of the operator — the exact class the plan's operator model forbids
   excusing ("the operator should have noticed" is never a defense). It is not a break
   of the reviewed-transaction chain: every payment is still displayed honestly and
   verified against the review. Under the framework's generic rubric an open High also
   forces BLOCKED; under the plan's narrower clause it holds the grade at CONDITIONAL;
   the grade is BLOCKED under every admissible reading.

**Path to CLEARED** (all of): fix CT-72 (parse-time refusal of duplicated key bytes +
hostile fixture test), CT-90 (verify the library by locating files without executing
package code — `PathFinder.find_spec` — and run check and use under the same scrubbed
interpreter; also closes the check→use TOCTOU), the four unpinned release-job guard
exits (CT-77…80) and the unpinned money-path gates (CT-83…85) with break-capable pins,
and the sweep's lexical gaps (CT-73) and tag residual (CT-97); then a new cycle.

## The four questions that matter

1. **Could this software sign or broadcast a transaction the operator did not review and
   approve — altered recipient, amount, fee, or change?** — **No path found.** Every
   mutation attack (recipient swap, change redirection, amount bump, added inputs,
   foreign signatures, SIGHASH_SINGLE, high-S, replayed responses, concurrent
   submission races) was refused at the txid/serialize/witness-script/sighash gates,
   verified independently by Red, Copper, Orange, the referee, and the lead. The wallet
   *definition* can be deceptive (CT-72: a false quorum display) — that is the High
   finding — but the transaction chain from review to broadcast held under every
   attack, including a malicious signing device holding a real wallet key and a lying
   explorer.
2. **Could it leak the unspeakable thing — xpubs, addresses, transaction IDs, or
   credentials?** — **No path found in the shipped app**: diagnostics are
   fixed-vocabulary under hostile input, explorers receive addresses only, request logs
   are silent, no credential value exists anywhere in the repo, artifacts, or logs.
   The one leak path found is CT-90's source-mode defeat, where a poisoned *development*
   environment could see xpubs/PSBTs — not a property of the published app.
3. **Could a remote party, a dependency, or a local process act invisibly?** — The
   loopback server refused every cross-origin, tokenless, and rebinding attack; the
   publish path is a single dispatch-only workflow whose promotion is byte-verified
   (candidate `SHA256SUMS` == published `SHA256SUMS`, same commit, one upload window,
   Sigstore-attested). The invisibility found is in the *development* identity chain
   (CT-90) and the release-gate pins that cannot fail (CT-77…80, CT-83…85): a future
   regression there would be silent — which is why the framework blocks on them.
4. **What should be fixed first?** — CT-72 (one parse-time check + one hostile fixture
   test closes the only High), then CT-90 (locate-without-executing + scrubbed
   interpreter), then the unpinned guard/gate exits (CT-77…80, CT-83…85 — the repo's own
   break-and-watch standard, already written once for 27 other pins), then the sweep's
   lexical matchers (CT-73) and tag residual (CT-97).

## The prior audit's findings: all 71 accounted for — the blocker was fixed and verified

Cycle 3's CT-01…CT-71 ledger was enumerated by the referee from the prior report
(hash re-verified) and every ID accounted for. Headlines:

- **CT-48 (the cycle-3 High): verified fixed.** Publish-capable workflows deleted from
  every branch (13 deletion commits verified on-branch); `scripts/check-publish-paths.sh`
  fails closed on any publish-capable workflow on any non-main ref — including bodies it
  cannot read — and runs as a gate on every dispatch; run clean against the live remote
  by Amber, the referee, and the lead independently; the false header comments
  corrected; guard bodies verified by configuration read and by break-and-watch.
- **CT-49 (helper identity): fixed and pinned in frozen mode** — all eight documented
  break-and-watch rows re-broken red by the referee (planted echo, no sidecar,
  disagreeing sidecars, substring version, PATH lookup, session re-identification,
  payload comparison, sidecar placement) — **with one new residual**: the source-mode
  half of the same control is defeatable (CT-90, the blocking finding).
- **CT-50/51/52/53/55/56/57/58/60/62/71: verified fixed with fail-capable pins** (every
  PATCH-named tripwire re-broken red by the referee; 52 of 53 rows red on the documented
  break — the 53rd is CT-62's message pin, which cannot fail for its named break because
  a code comment satisfies it: W-1 → CT-103).
- **CT-54, CT-59: open dated deferrals**, hard expiry 2027-10-07, triggers named —
  ruling-2 compliant, counted as open in the totals.
- **CT-35, CT-36…42, CT-44, CT-47 (carried cycle-2 Infos) and CT-61, CT-63…70 (cycle-3
  Infos): closed by the dated owner acceptance note** (`releases/OWNER-ACCEPTANCE-2026-10-07.md`,
  Bitseeker LLC, 2026-10-07, itemized with rationale and stated tripwires; ruling-2
  compliant). The note's CT-61 acceptance covers "a BSMS naming an attacker's key is the
  wallet definition" — it does not and cannot cover CT-72's false-quorum display, which
  post-dates it.
- CT-02…CT-34, CT-43, CT-45, CT-46 (fixed in cycles 1–3): carried verified — the engine
  files are byte-identical v0.6.6→v0.6.7 and every pin is green in the 520-test suite
  run eight times during this audit's break-and-watch.

## The panel

**🔴 Red — NO BREACH DEMONSTRATED.** Attacked the whole surface: the loopback API
(auth, drain, races), the BSMS import, malicious signing devices holding real wallet
keys, lying explorers and price feeds, the publish pipeline, and privacy egress.
Everything held except the wallet-definition deception (CT-72) and the sweep's lexical
matchers (CT-73). One hygiene item (CT-74: a non-ASCII token header crashes the refusal
path — no bypass); one procedural note (a single accidental read-only blockstream.info
height query during harness bring-up, no wallet data).

**🔵 Blue — DEFENSES HOLD WITH GAPS.** Inventory of 34 claimed controls from AGENTS.md,
SIGNING.md, RELEASE-PROCESS.md, HWI-DEPENDENCY.md and the asset table; every control
passes present/reachable/effective/fail-closed; 25 money-path/privacy/UI pins and 9
release-path pins demonstrated by Blue's own break-and-watch. Four release-job guard
exits are unpinned — deleting each keeps all 520 tests green (CT-77…80; root cause
CT-81: the guard pin helper cannot see inside multi-step run blocks).

**🟠 Orange — LOGIC UNPROVEN (14/17 proven, 0 wrong).** The signature chain is the
strongest result: a from-spec BIP-143 reimplementation, the embit library, and the
published vectors agree; low-S, sighash, prevout-binding, finalization ordering,
BSMS policy, network identity (Mutinynet checkpoint confirmed live), amount arithmetic
and JS money math all pass 142 independent vector/boundary checks. Three invariants
are unproven only for missing pins (fee-consistency gate, key-proof digest, recipient
round-trip — CT-83/84/85), plus one redundant-anchor pin (CT-86). The vendored embit
delta is exactly the two documented edits; the v0.6.6→v0.6.7 "engine unchanged" claim
verified byte-for-byte.

**🟤 Copper — EDGE TRUST BROKEN (one interface of seven).** Every edge assumed hostile
or broken (lies/dies/stalls/repeats/substituted): devices-over-HWI, the helper identity
chain, the vendored libusb (hashes match all four pins; hardened runtime neutralizes
DYLD insertion — live experiment), the WebKit bridge, Esplora endpoints (live hostile
server), the BSMS file, and the bundle. Six hold with runtime evidence. The seventh —
source-mode helper identity — is broken: the pin check itself executed attacker code
and passed (CT-90). Residuals: within-session swap window (CT-91), extracted-dylib
path-equality (CT-92). **Process disclosure:** Copper's bridge test wrote two synthetic
PSBTs to the real `~/Downloads` and its cleanup deleted a pre-existing
`testnet4-unsigned-2.psbt` (an unsigned practice file from Sep 29; recoverable from the
Oct 5/6 Time Machine local snapshots). No other writes escaped the disposable copies.

**🟡 Amber — CHAIN UNVERIFIED (no link broken).** Every link named, pinned, real, and
matched where the repository allows: 5 actions SHA-pinned and tag-verified; 17/17
sampled lock hashes equal PyPI digests; 7/7 vendored-input pins match; the embit wheel
is byte-identical to its patched source; secrets exist only as names; the promotion is
byte-verified end-to-end (candidate SHA256SUMS == published, same commit, one upload
window, all 10 assets attested); the tarball is file-complete against the tag. Two link
classes cannot be established from the repository and are honestly recorded UNVERIFIED:
hosted-runner/toolchain internals (CT-100: apt/MSVC/Docker float inside pinned labels —
builds are not bit-reproducible) and third-party dependency code not read (Orange's
seam; identity verified instead). Residuals: historical tags freeze dispatchable
publishers gated only by release-existence (CT-97 — all publish-capable tags have
releases today; the one tag without carries no workflow), an expression-injection
surface on `candidate_run_id` requiring dispatch rights (CT-98), an unpinned Docker
proof image (CT-99), the tarball omitting the public signing key (CT-101), and a
comment that trips the sweep's matcher in the false-positive direction only (CT-102).

**⚪ White — PUBLISH.** 18 claim groups re-derived (17 CONFIRMED, 1 CORRECTED —
a grade-neutral prose count in Amber's report), clean bills attacked with the same
energy as findings; 53 PATCH-named tripwires re-broken (52 red, 1 comment-satisfiable →
referred and dispositioned); the prior ledger round-trips 71/71; scope hashes equal;
grade computed with the arithmetic shown: **⛔ BLOCKED, floor set by Copper's proven
failure state (ruling 4); CLEARED unreachable on four independent grounds; the grade
would be ⚠ CONDITIONAL on every ground except ruling 4.** Two referred items (W-1, W-2)
dispositioned by the lead's lane verification (CT-103, CT-104).

### The lead's verification layer (disclosure)

The referee was dispatched as a separate-context sub-agent after the wave. A mid-run
cancellation notice proved misleading: the agent in fact completed, filling the lock's
end-hash row and writing its report at 20:16–20:22Z; the lead, unaware, had begun
executing the referee duties in-session (the cycle-3 precedent) and **independently
re-derived every load-bearing claim** — R-1/CT-72 end-to-end on the repo's own fixture
machinery (parse → scan → prepare → one signature → finalize `(2, 2)`), CT-90 against
the verbatim checker with PyPI-fetched genuine pins, CT-73 on a purpose-built fixture
repo, the four unpinned exits and three unproven gates by seven full-suite break runs,
and a 55-cycle break-and-watch sweep that agreed with the referee's 53-row table row
for row (including the CT-62 comment-satisfiable discovery, independently made on both
sides, and one additional instance of the same class in the sweep's own `cat-file` pin,
folded into CT-103). The two derivations agree on every load-bearing claim and on the
grade. The lock file's process note records the sequence. No lane saw another lane's
output; the referee and the lead-verification saw everything, as provided.

## What this audit did not do

- **No physical hardware wallet** was attached: device-edge trust is proven down to the
  HWI subprocess/JSON pipe by two independent hostile batteries, not the USB transport.
- **Hosted-runner internals and floating toolchain** (runner images, the
  actions/python-versions registry, apt, MSVC, the Docker proof image) are trusted
  infrastructure — CT-100/99; not inspectable from this repository.
- **Dependency internals** (hwi, pywebview, pyinstaller, requests, pyyaml, certifi;
  upstream embit beyond the documented two-edit delta) were identity-verified, not
  code-read — a separate component audit remains outstanding, as prior cycles recorded.
- **No bit-reproducible rebuild** was attempted; artifact "matched" rests on the
  byte-verified candidate→publish promotion, attestations, and hash equality.
- **No workflow was dispatched and nothing was pushed** by the audit (read-only GitHub
  discipline); CT-73's evasion was proven to the sweep on a fixture, and CT-97's tag
  hazard from repository contents and the Actions API only.
- **Windows/Linux runtimes were never executed** here; their pins ran as tests (macOS
  collects 520 tests; other platforms collect 513 by documented design).
- Lane samplings are disclosed in each lane report and consolidated by the referee
  (Blue's unbroken long tail, Orange's INV-17 not executed against a real device,
  Amber's 17-package PyPI sample, Copper's OS-level receipts partially lead-backed).
- Best-effort, not a guarantee: "nothing found" means "none found within this
  coverage," and an audit is evidence about one revision on one day — not a
  certification.

---

# Bitcoin Easy Signer — Plain-English Safety Review

**Bitcoin Easy Signer 0.6.7 · 2026-10-07 · reviewed by the Color Team panel (five specialist examiners plus a referee), framework v1.3.2**

## ⛔ VERDICT: BLOCKED — do not ship the next release until the items below are fixed; the published 0.6.7 app itself remains as safe as this method can show

This review was written for the person this software is actually for: a lawyer, trustee,
accountant or spouse settling an estate that includes Bitcoin. Every statement here is
drawn from — and can be checked against — the full technical report above, produced
under rules locked before anyone looked at the code.

## The questions that matter

**Can this app steal the money — send Bitcoin somewhere I didn't approve?**
No path to that was found, by five independent attackers and two independent verifiers.
Every trick that could change a recipient, amount, fee, or change address between the
screen you read and the transaction that ships was tried — including a fake signing
device that really held the wallet's key and a lying blockchain server — and every one
was refused. The dangerous finding is different: **a crafted wallet file can make the
screen say "2-of-2" when one key alone can spend** (CT-72). If you opened such a file,
you would believe two devices must approve when only one is needed. You can protect
yourself today with one habit: **only open a wallet file you received from someone you
trust, through a channel you trust** — that boundary has always been the design, and
this finding is exactly why it matters.

**Could it leak the family's wallet privacy — addresses, xpubs, transaction IDs?**
Not through the shipped app: diagnostics carry no addresses or keys, blockchain queries
send only what the app is designed to send, and the release files are signed,
notarized, and checksum-verified — all re-verified against the live release page by the
audit itself. The leak found (CT-90) affects only developers running the app from
source code, not the installed app.

**Could someone act invisibly — change behavior without the owner seeing?**
The installed app's defenses held under every invisible-change test. What was found is
silence-in-waiting: several release-process guardrails (CT-77…80) and money-path checks
(CT-83…85) have no alarm attached — if they ever quietly broke, no test would notice.
The project's own standard is that every safety control must have an alarm proven to
ring; these don't yet. That is why the grade is blocked even though nothing is broken
in the shipped app today.

**What does BLOCKED mean — and not mean?**
It means: under rules fixed in advance, this revision cannot be called ship-ready,
because one examiner proved a defense does not hold (the source-mode identity check)
and one High finding (the false-quorum display) is open. It does **not** mean the
published 0.6.7 app was found dangerous to use — no path to moving your funds
unreviewed was found, and the blocking source-mode defect does not exist in the
installed app. It is not a guarantee of anything, it covers exactly this version, and
your own eyes on the final screen still matter.

## How this review was done

Five independent examiners with one job each, none seeing the others' work; a sixth
agent that re-derived every claim the verdict rests on and computed the grade from
locked rules (the lowest score on the team wins); and a final independent re-derivation
of the grade-setting claims by the lead auditor. The grade rules were locked in
writing, hashed, and never moved — verified start and end.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| 🔴 RED · The attacker | Try to steal, alter, or act as the owner by any path | No theft path found; found the false-quorum wallet display (the High) |
| 🔵 BLUE · The defender | Prove every claimed protection actually holds and has a working alarm | All protections hold; 4 release guardrails have no alarm |
| 🟠 ORANGE · The logic specialist | Check the money math against the public Bitcoin standards | Signature math proven against the official test vectors — the strongest result yet; 3 checks lack alarms |
| 🟤 COPPER · The edge specialist | Assume every device, server, and file the app trusts is hostile | 6 of 7 edges held; the developer-mode helper check can be fooled (sets the grade) |
| 🟡 AMBER · The supply inspector | Verify how the software is born — every dependency, build step, signature | Nothing fake reached the release; the build machines themselves remain trusted, not proven |
| ⚪ WHITE · The referee | Trust nobody; re-derive everything, compute the grade, gate the report | Every load-bearing claim confirmed twice; grade computed, not chosen; verdict: publish with this grade |

## The audit trail

**Read this first:** across four audits, no way has ever been found to make this app
send the owner's Bitcoin somewhere unreviewed. The items below are about a deceptive
wallet-file display, developer-mode tooling, and manufacturing discipline — the
guardrails that keep future versions safe.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| **DANGER SIGN (fix before next release)** | A wallet file can show "2-of-2" on screen while one key alone can spend. Not found in the wild; demonstrated by the audit; closed by a one-line refusal plus a test. Until fixed, trust only wallet files from trusted delivery. | CT-72 |
| **DANGER SIGN (fix before next release)** | In developer source-mode, a swapped hardware-wallet library can pass the identity check while running someone else's code. Does not affect the installed, signed app. | CT-90 |
| **IMPORTANT TO FIX** | Four release guardrails and three money-path checks have no alarm that can ring if they break; the publish-path sweep can be evaded by publish commands it doesn't recognize; historical tags remain dispatchable publishers. | CT-77…80 · CT-83…85 · CT-73 · CT-97 |
| **MINOR IMPROVEMENT** | Within-session helper swap window; extracted-library path check; unpinned Docker/toolchain in CI; two deferrals (rebuild libusb from source; stalling-explorer availability) with hard review dates 2027-10-07. | CT-91 · CT-92 · CT-99 · CT-100 · CT-54/59 |
| **HOUSEKEEPING** | Unauthenticated public price/fee endpoints; sweep ref residue; tarball omits the public signing key; two documentation-wording items; and two "alarms" that a code comment can satisfy — the project's own standard says an alarm must fail when its control breaks. | CT-75 · CT-76 · CT-101 · CT-103/104 · CT-102 |

## What this review does not cover

Version-locked to 0.6.7. No physical hardware wallet was attached (device behavior was
proven at the software boundary). The build machines, the Python registry, and
third-party library internals were trusted, not proven — an independent component
review remains outstanding, as in every prior cycle. This AI-panel method complements,
and does not replace, a qualified human security firm. "Nothing found" always means
"nothing found within this coverage."

## Check our homework

| Artifact | Where |
|---|---|
| This report (technical + safety review + full ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md` (this file) |
| Cycle history, one row per audit | `bitcoin-easy-multisig-signer-colorteam-audit-index.md` |
| The signed audit plan + scope lock | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.7.md` · `…-lock-v0.6.7.md` |
| The method, in full | `cjtsh/ai-color-team-audit-framework` (v1.3.2) |

You can read every page of the evidence yourself.

---

## Appendix — findings ledger

**Open totals at v0.6.7: 0 Critical · 1 High · 8 Medium · 14 Low · 13 Info.**

### Prior-cycle findings (CT-01…CT-71) — all accounted for

Verified fixed (carried from cycles 1–3; engine byte-identical v0.6.6→v0.6.7, pins green
in 8× suite runs): CT-02…12, CT-13, CT-14 (re-derived), CT-15, CT-16 (no recurrence
observed), CT-17 (→CT-55), CT-18, CT-19, CT-20 (re-derived), CT-21, CT-24, CT-26
(re-derived), CT-27, CT-28 (re-derived), CT-29, CT-30, CT-31a–d, CT-32, CT-33 (→CT-57),
CT-34 (re-derived), CT-43, CT-45, CT-46 · Closed as observation: CT-22 · Positive
holds: CT-25 · Accounted via decomposition: CT-23 (→ CT-29 + CT-35) · **Verified fixed
this cycle:** CT-48 (the cycle-3 High — sweep clean on the live remote, 13 deletion
commits, guards re-broken red), CT-49 (frozen mode; residual → CT-90), CT-50, CT-51,
CT-52 (residual → CT-77…80), CT-53, CT-55, CT-56, CT-57, CT-58 (residual → CT-91),
CT-60, CT-62 (pin caveat → CT-103), CT-71 · **Open dated deferrals (hard expiry
2027-10-07):** CT-54, CT-59 · **Closed by dated owner acceptance (2026-10-07, ruling 2):**
CT-35, CT-36…42, CT-44, CT-47, CT-61, CT-63…70.

### New findings this cycle (referee-numbered; locations @ 81f58ec)

| ID | Lane | Sev | Location | Claim |
|---|---|---|---|---|
| CT-72 | Red | **High** | probe.py:170; signing.py:276,282-283; ui.html:1462-1464 | Duplicate-xpub BSMS with distinct origin fingerprints parses, displays as honest m-of-n (two cosigner cards, same key bytes), and ONE device approval finalizes it — quorum deception; remedy: dedupe receive keys by key bytes at parse + hostile fixture |
| CT-73 | Red | Medium | scripts/check-publish-paths.sh:49,102-109 | Publish-path sweep is lexical (`contents: write`, `gh release`): `gh api`/REST-upload and `action-gh-release` publishers evade on a fixture; extend matchers + require read-only default token permissions |
| CT-74 | Red | Low | gui.py:638-644 | Non-ASCII `X-Local-Token` header → TypeError before the 403 path; socket dropped, traceback per request; no bypass |
| CT-75 | Red | Info | gui.py:574-577 | Unauthenticated GET /api/price, /api/fees (Host-checked, public data, no CORS read) |
| CT-76 | Red | Info | check-publish-paths.sh:55-59 | `refs/remotes/publish-audit/*` residue after clean runs (self-cleans) |
| CT-77 | Blue | Medium | build-candidate.yml:976 | Candidate `exit 0` (publish=false must not publish) pinned by string order only — deleted → 520 green |
| CT-78 | Blue | Medium | build-candidate.yml:991 | Tag-exists no-overwrite `exit 1` unpinned (the CT-01/v0.1.11 class) |
| CT-79 | Blue | Medium | build-candidate.yml:801 | GPG fail-closed `exit 1` unpinned ("fails closed without this key" rests on it) |
| CT-80 | Blue | Medium | build-candidate.yml:980 | Release-job unsigned/unnotarized refusal `exit 1` unpinned (version-job sibling is body-pinned) |
| CT-81 | Blue | Low | tests/test_workflow_config.py:942-963 | `GuardBodyPins._step_body` structurally blind to guards inside multi-step run blocks — root cause of CT-77…80 |
| CT-82 | Blue | Info | releases/PATCH-0.6.7.md vs tag | PATCH candidate-run narrative corroborated; no discrepancy (positive observation) |
| CT-83 | Orange | Medium | wallet_service.py:868 | Build-time fee-consistency gate unpinned — disabled → 520 green; violates the repo's own tripwire contract |
| CT-84 | Orange | Low | probe.py:569-572 | Key-proof message digest unpinned and unexecuted against an external vector; drift fails closed (availability) |
| CT-85 | Orange | Low | wallet_service.py:767 | Recipient round-trip check unpinned (control verified working against BIP-173/350 vectors) |
| CT-86 | Orange | Low | wallet_service.py:327 | wallet_layout first-receive re-derivation unpinned (redundant with the pinned parse-level anchor today) |
| CT-87 | Orange | Info | gui.py:1198-1201; ui.html:864-869 | Dead disjunct in both large-amount gates (10M term subsumed by 4M; behavior conservative) |
| CT-88 | Orange | Info | probe.py:157 | Threshold-1 quorums accepted by design without import-time emphasis |
| CT-89 | Orange | Info | vendored embit | Raw decoder accepts unknown-HRP bech32; the app-level prefix+round-trip is the only defense (tied to CT-85) |
| CT-90 | Copper | **Medium** | probe.py:311-348 (check), :317 (false comment) | **The blocking finding:** source-mode hwilib payload pin defeated by a `__file__`-lying substituted library — pin check ACCEPTED while attacker code executed inside it; check/use TOCTOU; frozen-mode chain intact; remedy: locate files without executing package code (`PathFinder.find_spec`), run check and use under the same scrubbed interpreter |
| CT-91 | Copper | Low | probe.py:238-249,662 | Within-one-signing-session helper swap window (cache cleared only at session start; documented CT-58 bound) |
| CT-92 | Copper | Low | scripts/hwi_entry.py:18-28,87-99 | Frozen helper extracts to user-writable `_MEI…` dir; libusb checked by path equality only (hardened runtime strips DYLD_*) |
| CT-93 | Copper | Info | probe.py:281-291 | Explicit `--hwi` trusts any self-consistent helper+sidecar pair (operator trust decision) |
| CT-94 | Copper | Info | probe.py:620-676 | No device version identity at the HWI edge by design — possession-based binding is the stronger property |
| CT-95 | Copper | Info | desktop.py:69-82 | Bridge URL pin fails open on unreadable window URL; compensated by payload byte-equality |
| CT-96 | Copper | Info | requirements*.lock; tests/test_hardening_pins.py:338-372 | hwilib absent from the CI requirement set — the payload pin's accept path runs only in desktop builds |
| CT-97 | Amber | Medium | tags v0.1.0…v0.6.3; check-publish-paths.sh:61 | Historical tags freeze dispatchable publishers with today's secrets, gated only by release-existence (all publish-capable tags have releases; the one without carries no workflow); sweep never scans tags |
| CT-98 | Amber | Low | build-candidate.yml:69 | `candidate_run_id` interpolated into a run block before numeric validation (needs dispatch rights; checksums job does it correctly) |
| CT-99 | Amber | Low | build-candidate.yml:673 | CI proof step pulls `ubuntu:24.04` by tag, not digest |
| CT-100 | Amber | Low | build-candidate.yml:568-569; windows-inputs.yml:104-116 | Toolchain floats inside pinned runner labels — non-reproducible builds |
| CT-101 | Amber | Info | scripts/build-source.sh | Source tarball omits `signing-key.asc`, breaking the verification loop for tarball-only verifiers |
| CT-102 | Amber | Info | linux/windows-inputs.yml:24-25 | Comment text trips the sweep's matchers (false-positive direction only) |
| CT-103 | W-1 verified (Blue area) | Low | tests/test_gui.py (LargeAmountMirrorPins); scripts/check-publish-paths.sh:30 vs SweepFailClosedPins | Comment-satisfiable pins: the CT-62 message pin is satisfied by the gui.py:59 comment, and the sweep's `cat-file` pin by its header comment — each stays green for its named code-only regression (demonstrated both ways by referee and lead); assert the live string, not a substring a comment can carry |
| CT-104 | W-2 verified (Amber area) | Info | releases/PATCH-0.6.7.md vs OWNER-ACCEPTANCE note | PATCH says the acceptance note "carries per-item tripwires"; the note states tripwires only for the ones worth stating — documentation-accuracy item; acceptance validity unaffected |

---

*Audit date 2026-10-07/08. Performed on the public repository and published artifacts
only; the grade rules were locked before the audit began and applied as written; no
wallet material, secret, or credential appears in this report; an audit is evidence
about one revision on one day — not a certification of safety; coverage limits stated
above. The referee's full record (re-derivation table, tripwire transcript, round-trip
ledger, grade arithmetic) is preserved with the audit artifacts; the lanes' reports are
preserved unedited alongside it.*
