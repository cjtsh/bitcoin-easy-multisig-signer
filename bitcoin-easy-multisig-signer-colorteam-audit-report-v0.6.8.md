# ZCode Color Team Security Audit — Bitcoin Easy Signer 0.6.8 (cycle 5)

| | |
|---|---|
| **Version examined** | Commit `bc92f054822008510249e743a60033009dc4995a` on `main` — the 0.6.8 audit-remediation commit. **Untagged and unpublished by design**: per the signed plan, the cycle-5 grade comes before any candidate-promotion, hardware walkthrough, or publication. Live release/tag lists verified: latest published is v0.6.7 |
| **Assets declared** | (1) the operator's Bitcoin — mainnet and practice-network funds; (2) signing and CI credentials and the release workflow; (3) the reviewed-transaction integrity chain; (4) release artifact integrity; (5) wallet privacy. All five mission-critical; the ranking orders severity, not attention |
| **Auditor** | A five-specialist Color Team panel plus a referee (framework `cjtsh/ai-color-team-audit-framework` v1.3.2, definitions v2.4); asset declaration, charters and grade rules locked in writing **before** the build was examined |
| **Surveyor** | Harness `Kimi Code desktop app` · session `not exposed by the harness` · model `not exposed by the harness` — declared in the signed plan §0 |
| **Auditor identity** | Harness `ZCode desktop app 3.14.4` · session `not exposed by the harness` · model `zai-api/GLM-5.3` (declared by the harness system prompt, not verified) |
| **Independence** | Surveyor and auditor ran in different harnesses as declared by the operator: **cannot be determined mechanically** — both session identifiers read `not exposed by the harness`; independence rests on the operator's declaration; declared model names are declarations, never verifications |
| **Cycle** | `v0.6.8` (cycle 5) — this file is `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.8.md` |
| **Prior audit** | Cycle 4: `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.7.md`, SHA-256 `340495e93a46cface603291f88671f60b05198768c46f0c4b91ffe980f0e7ff0` (re-verified byte-identical this cycle), graded ⛔ **BLOCKED** |
| **Verification** | Full suite at the target re-run by the lead, all five lanes, and the referee (580 tests OK, zero skips, before and after every break campaign); every load-bearing claim re-derived personally by the referee **and the two heaviest independently re-derived again by the lead**; CT-97 platform state verified live read-only via `gh api` (repository secret list empty; `release-signing` and `apple-signing` environments `main`-only, no human gates, exact documented secret sets); the repo's own `check-release-credentials.sh` prints `ok` live; candidate run 37783584533 verified (7/7 jobs, publish-refusal path, nothing published) |
| **Scope lock** | Plan `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md` (signed **Bitseeker LLC, 2026-10-08**, commit `5d826a1`; an earlier 2026-10-07 signature was voided by three target moves and re-signed before this audit started), SHA-256 `4f15a68013ef9e409719f8eb05ecb7f44f4fea2743a127e58c97f4454af4ed19` before the first specialist ran and identical at the end — **equal: the scope never moved.** The signed plan was public on `origin/main` (`5d826a1`) before dispatch; the lock file is `bitcoin-easy-multisig-signer-colorteam-audit-lock-v0.6.8.md` |

---

## The grade: ⛔ BLOCKED — three lanes proved their failure states, and the cycle-4 fixes closed their documented vectors but not their classes

This cycle audited the 0.6.8 remediation **before publication** (grade-first order — the
right order, and it earned its keep). The honest headline has two halves:

**What genuinely improved.** Every fix shipped in 0.6.8 closed the exact vector its
finding named — verified by 33 of 34 break-and-watch tripwires going red for their own
assertions: the CT-72 gate refuses identical-serialization duplicate keys; the CT-90
check no longer executes the package it inspects and refuses the cycle-4 attack; CT-73's
sweep now refuses the `gh api`/action evasions of cycle 4; CT-77…80's guard exits are
branch-pinned against deletion AND absorption; the CT-97 credential move to `main`-only
environments is real, pinned, and verified live; and the money path — re-derived in full
— held under every attack, with the signature math again proven against BIP-143's
published vectors and the message digest against bitcoinjs's published fixtures.

**What did not hold.** Five lanes, five fresh examinations — and the two grade-setting
classes of cycle 4 remain open through variants, each demonstrated end-to-end and
re-derived independently:

1. **CT-72 (High, open — the variant).** The new gate compares base58 *spellings* of
   the signer keys, not the keys. The **same key** re-serialized (`xpub` alongside
   `tpub`, or any version variant) under two origin fingerprints still parses as an
   honest "2-of-2"/"2-of-3", still displays distinct cosigner cards, and **one device
   approval still finalizes it** — reproduced at the app's own HTTP boundary
   (`{"signatures": 2, "threshold": 2, "complete": true}` from a single-key device) by
   Red, confirmed from the logic side by Orange (LOGIC WRONG), reproduced end-to-end by
   the referee, and re-derived at parse level by the lead. The final witness carries the
   same signature twice.
2. **CT-90 (Medium, open — three new roads).** The check now locates files without
   executing them — but it pins only 2 of the ~20+ hwilib files that actually execute
   (a poisoned sibling module ran with pins green), a `.pth` startup hook **survives the
   `-I -P` scrubbed child** and can serve different code to the helper than was hashed
   (the check calls `PathFinder.find_spec` directly, bypassing the hostile meta-path the
   helper honors), and a deterministic check→use swap (TOCTOU) passes full verification
   then runs a trojan. All three confirmed in the referee's labs. Source mode only; the
   frozen bundle's chain and the key-proof money gates held everywhere they were
   attacked.
3. **CT-73 (Medium, open — round three).** The sweep's read-only arm is satisfiable by
   a **comment** and its write-grant regex misses spaced `contents : write`; a fixture
   workflow carrying a real GITHUB_TOKEN write grant passes the gate with `ok`. Plus
   CT-92's link refusal is symlink-only — a **hardlink** at the bundled-library name
   loads attacker bytes (calibrated Low); and CT-97's watch-net is a fixed five-name
   list that cannot see `MAC_NOTARY_KEY_P8_BASE64`, which the workflow itself names
   (today unset — conditional, Medium).

**Grade arithmetic (computed, not chosen):** Red BREACH DEMONSTRATED, Orange LOGIC
WRONG, and Copper EDGE TRUST BROKEN each independently force ⛔ under ruling 4 — no
severity calibration, no weighing against clean lanes. The open High (CT-72 variant)
forces ⛔ on a fourth ground under the framework rubric. Amber's CHAIN UNVERIFIED and
Blue's unpinned controls cap at CONDITIONAL (ruling 5) — moot under the floor. CLEARED
is unreachable on at least four grounds.

**Path out of BLOCKED:** compare key *material* (pubkey + chain code) and refuse
duplicate pubkeys in the compiled witness script as an independent second gate (CT-72);
whole-tree hashing or dist-info RECORD verification, a meta-path-aware check child, and
verify-at-execution for the TOCTOU (CT-90); parse YAML permissions instead of lexical
matching (CT-73); refuse non-regular files at the bundled-library name (CT-92); derive
the watched credential-name set from the workflow text (CT-97); then a new cycle.

## The four questions that matter

1. **Could this software sign or broadcast a transaction the operator did not review
   and approve?** — **The reviewed-transaction chain held under every attack** (mutated
   signer updates merge to the reviewed bytes exactly; foreign/corrupt signatures
   refused; concurrent submissions refused; the backend mainnet gate re-broken red).
   The open danger is the **wallet-definition deception** (CT-72 variant): a crafted
   file shows a false quorum while one approval spends. Until fixed, the operator's
   protection is unchanged: only open wallet files received through trusted delivery.
2. **Could it leak xpubs, addresses, transaction IDs, or credentials?** — No path in
   the app-as-shipped: privacy surface re-attacked and clean; credential values now
   live in `main`-only environments (verified live), with one name outside the watch
   net (CT-97 variant, unset today). The source-mode helper check remains the leak
   surface for developer machines (CT-90 variants).
3. **Could a remote party, a dependency, or a local process act invisibly?** — The
   loopback server now answers every malformed token with a clean 403 (CT-74 fixed and
   pinned), feeds are token-gated (CT-75 fixed). The invisible actors found are
   process-level: the publish sweep blesses evasions it cannot parse (CT-73), and
   several pins still cannot fail in every direction (CT-100 omission, CT-98
   release-job body — referred items).
4. **What should be fixed first?** — CT-72's key-material comparison (closes the only
   open High), then CT-90's whole-tree verification, then the sweep's YAML parsing,
   then the name-derived credential net. The private work-orders file carries each as
   an executable order.

## The prior audit's findings: all 104 accounted for — every fix closed its documented vector; five classes stay open

Cycle 4's ledger CT-01…CT-104 was enumerated from the prior report (hash re-verified)
and every ID accounted for. CT-01…CT-71 carry their cycle-4 dispositions (engine files
byte-identical v0.6.7→0.6.8; acceptance note re-read; CT-54/CT-59 open dated deferrals,
hard expiry 2027-10-07). For CT-72…CT-104: **verified fixed** — CT-74, 75, 76, 77, 78,
79, 80, 81, 83, 84, 85, 86, 91 (named vector), 98 (named vector), 99, 101, 103, 104 ·
**partially fixed — class open with new evidence attached:** CT-72 (xpub/tpub variant),
CT-73 (comment-arm + spaced-colon + github-script evasions), CT-90 (sibling + `.pth` +
TOCTOU), CT-92 (hardlink), CT-97 (sixth credential name), CT-102 (both directions of
the lexical class) · documented residuals unchanged: CT-87, CT-88, CT-89, CT-93, CT-94,
CT-95, CT-96 (extended by CT-112). None dropped, none closed by silence.

## The panel

**🔴 Red — BREACH DEMONSTRATED (assets 1, 3).** The CT-72 variant bypass driven
end-to-end through the app's own engine and HTTP boundary (one device sign → complete →
finalize; witness = same signature twice); the CT-90 check bypassed both ways
(partial-file pins; `.pth` finder surviving `-I`); the sweep evaded a third time
(github-script + `$GITHUB_API_URL` + read-all comment). The full loopback battery,
concurrency interleavings, hostile devices, lying explorers, and credential scripts:
nothing found. 8 findings (1 Critical filed; calibrated High by the referee — dissent
recorded).

**🔵 Blue — DEFENSES HOLD WITH GAPS.** Money path fully re-derived at this revision
(every gate broken red, restored green; the engine-two-refuse-only-places claim
confirmed from the diff). Three test-5 gaps: the CT-97 watch net's five-name
vocabulary (B-1/Medium), the broadcast identity clause that cannot fail (B-2), and the
inner token-cleaner layer unpinned (B-3).

**🟠 Orange — LOGIC WRONG (1 wrong, 13 proven, 0 unproven).** The wrong one is the
duplicate-key invariant, violated by the serialization variant (full money path
completed with one signature). The proven set is stronger than ever: BIP-143 both
published digests matched by execution against the fetched BIP text; the message
digest matched to bitcoinjs's published fixtures; external-vector pins verified against
published sources. Dependency locks byte-identical; vendored embit delta exactly the
two documented edits.

**🟤 Copper — EDGE TRUST BROKEN (E2, E3).** E2's reworked identity chain broken three
ways (sibling module, `.pth` hook, check→spawn race) with the PSBT captured in
demonstrations; E3's loader fed attacker bytes via hardlink (symlink control correctly
refused). E1 devices, E4 bridge, E5 Esplora, E6 BSMS: HOLDS under runtime batteries.
E7 (frozen bundle runtime) UNPROVEN — no build exists to run. 8 findings; all writes
confined to the disposable copy this cycle.

**🟡 Amber — CHAIN UNVERIFIED.** Nothing published for 0.6.8 by design, so *matched*
(artifact bytes vs published bytes) is unestablishable this cycle and honestly labeled
UNVERIFIED. Everything checkable, checked: five action SHAs resolve to public tags;
dependency digests match PyPI; all vendored pins match; CT-97's platform half verified
live (secrets empty; environments `main`-only, gate-free, exact sets); the candidate
run verified non-publishing. Weakest links: the sweep's two lexical arms (A-1/High
filed; the strongest arm needs no PAT), the sixth credential name, and two argv leaks
in the provisioning path that contradict its stdin-only claim (CT-107).

**⚪ White — PUBLISH.** 15/15 load-bearing claims CONFIRMED (0 corrected, 0
unverifiable); 33/34 tripwires red; 104/104 prior IDs round-tripped; grade computed
with the arithmetic shown; scope hash equal start/end; four severity dissents recorded
(grade unaffected); two REFERRED-TO-LANE items carried as open pin-coverage gaps.

### The lead's verification layer (disclosure)

The referee ran as a separate-context sub-agent and personally re-derived every
load-bearing claim, including end-to-end reproductions of the CT-72 variant at the
app's HTTP boundary and all three CT-90 roads. The lead then independently re-derived
the two heaviest claims in separate work: the xpub/tpub variant at the parse level
(`distinct spellings=2, distinct key material=1`, threshold=2 accepted; the
identical-serialization control correctly refused) and the sweep's combined
spaced-colon + comment arm on a purpose-built fixture (`ok`, exit 0, with a real write
grant present). Both confirmations matched the referee's record. One process note: an
initial too-naive lead fixture (silence-is-an-offender caught everything) failed to
reproduce the sweep bypass and was rebuilt to the lane's exact shape before confirming
— recorded so the transcript stays honest.

## What this audit did not do

- **Nothing published for 0.6.8 exists** — release-artifact matching (published bytes ==
  candidate bytes) is UNVERIFIED this cycle by design and must be re-run at publication
  time.
- **No physical hardware wallet** and **no frozen macOS/Windows build** on the audit
  machine: device trust proven to the subprocess/JSON pipe; CT-92/E3 re-derived on a
  fake `_MEIPASS` layout with the real prelude; CT-105's Windows half is code-read
  only; E7 is unproven (coverage, not a clean bill). Any claim that a real device
  would warn about a duplicated-key policy is a named missing hop.
- **Dependency internals not read** (identity-verified only); the independent component
  audit remains outstanding. The two hwilib pin files were verified against the
  published PyPI wheel this cycle.
- **Process notes:** the pre-grade candidate run 37783584533 preceded the panel grade,
  inverting the plan's grade→candidate order (published nothing); one lane initially
  misdirected its baseline via a stale prior-cycle `/tmp` copy (caught by the test
  count, recreated); the lead's first sweep fixture was too naive and was rebuilt.
- Lane samplings are disclosed per lane and consolidated by the referee (Blue's
  unbroken long tail, Orange's carried byte-identity invariants, Amber's sampled
  dependency closure, Red's suite-backed privacy bill).
- Best-effort, not a guarantee: "nothing found" means "none found within this
  coverage"; an audit is evidence about one revision on one day.

---

# Bitcoin Easy Signer 0.6.8 — Plain-English Safety Review

**Bitcoin Easy Signer 0.6.8 (unreleased) · 2026-10-08 · reviewed by the Color Team panel (five specialist examiners plus a referee), framework v1.3.2**

## ⛔ VERDICT: BLOCKED — do not publish this version yet; one high-priority fix and several hardening fixes remain

This review was written for the person this software is actually for: a lawyer,
trustee, accountant or spouse settling an estate that includes Bitcoin. Every statement
traces to the technical report above, produced under rules locked before anyone looked
at the code. This cycle ran **before** the version was published — exactly the right
order — and the grade is doing its job.

## The questions that matter

**Can this app steal the money?**
As before: **no path was found to make it send Bitcoin somewhere you didn't approve.**
Every attack on the reviewed-transaction chain was again refused, and the math checks
out against Bitcoin's official test vectors. The serious finding is a familiar one in a
new costume: last cycle's "fake 2-of-2" trick was fixed — the fix works for the exact
case the audit showed — but the same trick with the key **written in a different but
equivalent spelling** (like writing a bank account number in two valid formats) still
slips past the new check. The screen still shows a false "2-of-N," one device still
suffices. Your protection is unchanged and simple: **only open wallet files from
someone you trust, through a channel you trust.**

**Could it leak the family's wallet privacy?**
Not through the app as it would ship. The signing credentials were moved somewhere old
copies of the release machinery cannot reach (verified against GitHub's live settings).
The remaining leak paths are on developers' own machines (the helper-identity check can
still be fooled in three new ways) — real, worth fixing, not in your installed app.

**Could someone act invisibly?**
The biggest invisibility item is the release gatekeeper: the script that refuses "a
second way to publish" can still be fooled by formatting tricks — a pushed branch could
carry publishing power while the gate says all-clear. Nothing like that exists in the
repository today (verified); the gate just can't see it if it appears.

**What does BLOCKED mean — and not mean?**
It means: under rules fixed in advance, this unreleased version is not ready to ship.
It does not mean the published 0.6.7 app became unsafe, and it does not mean the fixes
were fake — every documented fix verifiably works; the audit found **variants** of the
same tricks that the fixes don't yet stop. That is exactly what this grade-first order
is for: nothing was published, so nothing needs recalling.

## How this review was done

Five independent examiners with one job each, blind to each other; a sixth agent that
re-derived every claim the verdict rests on and computed the grade from locked rules;
and the two heaviest findings verified a third time by the lead auditor. Nothing is
published for 0.6.8 until a future cycle grades it CLEARED and the owner completes the
hardware walkthrough.

## The review team

| Examiner | Their one job | In this review |
|---|---|---|
| 🔴 RED · The attacker | Steal, alter, or act as the owner by any path | The false-quorum trick returned through a different key spelling; two ways past the developer-mode helper check; a third way past the publish gate (on a test copy) |
| 🔵 BLUE · The defender | Prove every protection holds and has a working alarm | All protections hold; every documented fix re-verified with its alarm rung; three alarm gaps |
| 🟠 ORANGE · The logic specialist | Check the money math against the public standards | One invariant violated (the same false-quorum variant); everything else — including the official signature vectors — proven |
| 🟤 COPPER · The edge specialist | Assume every device, server, and file is hostile | The developer-mode helper identity broken three ways; the bundled-library check fooled by hardlinks; the other five edges held |
| 🟡 AMBER · The supply inspector | Verify how the software is born | Everything checkable, checked and clean; the final "published bytes" check must wait until publication; the publish gate fooled by formatting |
| ⚪ WHITE · The referee | Trust nobody; re-derive everything; compute the grade | Every load-bearing claim confirmed, some three times over; grade computed, not chosen; verdict: publish this report with the BLOCKED grade |

## The audit trail

**Read this first:** across five audits, no way has ever been found to make this app
send the owner's Bitcoin somewhere unreviewed — including this one. The items below are
a deceptive wallet-file display, developer-machine tooling, and release-process
guardrails.

| How serious | What it was, and what happened | Evidence |
|---|---|---|
| **DANGER SIGN (fix before release)** | The "fake 2-of-2" fix checks how the key is *spelled*, not the key itself — the same key in a second valid spelling still displays a false quorum and one approval still spends. Fix: compare the actual key bytes; refuse duplicates in the compiled script too. | CT-72 |
| **IMPORTANT TO FIX** | The developer-mode helper check pins 2 of ~20 files that run, misses startup hooks that survive its quarantine, and can be raced between check and use; the publish gate can be fooled by a spaced colon or a comment; one credential name sits outside the new watch net; the Windows helper's identity is self-asserted. | CT-90 · CT-73 · CT-97 · CT-105 |
| **MINOR IMPROVEMENT** | Hardlink bypass of the library check; two alarm gaps; argv leaks in the recovery script; a lying-but-consistent explorer can drive PSBT preparation (never broadcast); CI never runs the helper check's real accept path. | CT-92 · CT-108/109 · CT-107 · CT-111 · CT-112 |
| **HOUSEKEEPING** | Documentation wording (environment claim, "exactly two places," a misleading test pairing); comment-blind matcher notes; the two deferrals unchanged (review dates 2027-10-07). | CT-106 · CT-116 · CT-115 · CT-113/114 · CT-54/59 |

## What this review does not cover

Version-locked to the unrevised 0.6.8 commit. No physical hardware wallet, no frozen
build was run, dependency internals were identity-checked not read, and the final
published-bytes check happens at release time. AI-panel diligence complements, never
replaces, a qualified human firm. "Nothing found" means "within this coverage."

## Check our homework

| Artifact | Where |
|---|---|
| This report (technical + safety review + ledger) | `bitcoin-easy-multisig-signer-colorteam-audit-report-v0.6.8.md` (this file) |
| Cycle history | `bitcoin-easy-multisig-signer-colorteam-audit-index.md` |
| The signed audit plan + scope lock | `bitcoin-easy-multisig-signer-colorteam-audit-plan-v0.6.8.md` · `…-lock-v0.6.8.md` |
| The method | `cjtsh/ai-color-team-audit-framework` (v1.3.2) |

---

## Appendix — findings ledger

**Open totals at cycle-5 close: 0 Critical · 1 High · 4 Medium · 10 Low · 5 Info.**

### Prior-cycle findings (CT-01…CT-104) — all accounted for

Carried from cycles 1–4 with unchanged dispositions: CT-01, CT-02…CT-21 (except as
noted), CT-24, CT-25, CT-26…CT-34, CT-35…CT-47 (fixed / observation / positive /
accepted per cycle-4), CT-48, CT-50, CT-51, CT-53, CT-55, CT-56, CT-57, CT-60, CT-62,
CT-71 · **open dated deferrals (hard expiry 2027-10-07): CT-54, CT-59** · CT-49
(fixed; residual = CT-90), CT-52 (fixed; residual = CT-77…80, now fixed), CT-58 (fixed
for its vector; the check→spawn window is CT-90(c)).

Cycle-5 rulings on CT-72…CT-104: **verified fixed** — CT-74, CT-75, CT-76, CT-77,
CT-78, CT-79, CT-80, CT-81, CT-83, CT-84, CT-85, CT-86, CT-91 (named vector), CT-98
(named vector), CT-99, CT-101, CT-103, CT-104 · **partially fixed — class open:**
CT-72 (High), CT-73 (Medium), CT-90 (Medium), CT-92 (Low), CT-97 (Medium), CT-102
(Info residual) · **documented residuals unchanged:** CT-87, CT-88, CT-89, CT-93,
CT-94, CT-95, CT-96 (extended by CT-112) · CT-82 closed (positive observation).

### New findings this cycle (referee-numbered; locations @ bc92f05)

| ID | Lane | Sev | Location | Claim |
|---|---|---|---|---|
| CT-105 | Copper | **Medium** | scripts/build-windows.ps1:230-247; probe.py:455-458 | Windows helper identity self-asserted (unsigned `hwi.exe` + co-located sidecar, user-writable); the docstring's "inside the signed bundle" is macOS-only truth |
| CT-106 | Amber | Low | build-candidate.yml:714-719 | Workflow comment overclaims "a candidate never enters this environment" (deployments exist in run 37783584533); the real control (secret use gated by `if:`) holds |
| CT-107 | Amber | Low | provision-release-credentials.sh:12-13,157; build-candidate.yml:302-303 | The stdin-only argv claim contradicted twice (`security export -P`, `notarytool --password`); bounded `ps` windows |
| CT-108 | Blue | Low | gui.py:1054 | Broadcast identity clause cannot fail any test (removed → 31 send-flow tests green) |
| CT-109 | Blue | Low | gui.py:396 | `_clean_token` drop-don't-escape layer has no pin of its own |
| CT-110 | Red | Low | build-candidate.yml:131,235,320 | `needs.version.outputs.version` interpolated unquoted into run scripts — CT-98 class for repo content; missing hop (push access) out of scope by the plan |
| CT-111 | Copper | Low | network_settings.py:118-145 | A fully self-consistent lying explorer yields a preparable PSBT over phantom funds (broadcast fails closed; mainnet needs two agreeing liars) |
| CT-112 | Copper | Low | requirements*.lock; tests/test_hardening_pins.py:434-453 | The payload check's real accept path never runs in CI (hwi absent; fixtures patch out `-I -P`) — extends CT-96 |
| CT-113 | Copper | Info | gui.py:594-619 | GET routes check Host+token but not Origin; no wallet data exposed; document |
| CT-114 | Copper | Info | probe.py:97 | Double BOM tolerated (`lstrip("\ufeff")` strips all); cosmetic |
| CT-115 | Blue | Info | releases/PATCH-0.6.8.md CT-72 row | The closing-evidence pairing names the fingerprint test as if it pinned the key gate — both pins genuine, the pairing misleading |
| CT-116 | Orange | Info | PATCH-0.6.8.md:21-23 | "Engine changed in exactly two places" is scope-true but imprecise (also CT-91 re-hash, `-I -P` argv, CT-74/75 gates) |

**Severity dissents recorded (grade unaffected):** CT-72 variant filed Critical by Red /
High by Orange — calibrated **High**; CT-90 variants filed High — calibrated **Medium**;
CT-92 hardlink filed Medium — calibrated **Low**; Blue's C8 five-test row vs the merged
CT-90 evidence — recorded, sub-verdict unchanged.

**REFERRED-TO-LANE items (open pin-coverage gaps, carried per the referee's
no-origination rule):** CT-100 omission direction — dropping a name from
`TOOLCHAIN_PROBES` leaves the SBOM pin green (the pin iterates the list it should
guard) → Blue/Amber; CT-98 release-job body — the `assertNotIn("${{")` pin covers only
the version-job guard while the release job's run block also consumes
`CANDIDATE_RUN_ID` unpinned → Blue.

---

*Audit date 2026-10-08. Performed on the public repository at the audited commit only;
the grade rules were locked before the audit began and applied as written; no wallet
material, secret, or credential appears in this report; every key, address, and PSBT in
the evidence is synthetic; an audit is evidence about one revision on one day — not a
certification of safety; coverage limits stated above. The referee's full record
(re-derivation table, tripwire transcript, round-trip ledger, PoC drivers) is preserved
with the audit artifacts; the lanes' reports are preserved unedited alongside it.*
