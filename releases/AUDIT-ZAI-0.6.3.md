# Z.ai Security Audit — v0.6.3 — The Color Team Report

| | |
|---|---|
| **Version examined** | Tag `v0.6.3`, commit `f19bc460a2cb64590e8e37268b5be1df1a1f84b0`, published 2 October 2026 |
| **Auditor** | Z.ai (GLM-5.3, via ZCode) — a five-agent panel plus a referee, each with a written charter locked **before** the build was examined |
| **Prior audit** | v0.6.2 (2 October 2026, earlier that day): 25 findings, no critical — this audit's first job was verifying every one of them fixed |
| **Verification** | All release artifact hashes recomputed and matching; code signature, Apple notarization and stapling verified on the published download; 253 automated tests + 9 interface tests re-run at the audited revision — all pass; the owner completed a physical two-of-three hardware payment on a practice network as acceptance evidence |

## The grade: 🟡 Yellow — one documented step from Green

**All five Green conditions were met except one clause.** There are no critical or
high findings; every one of the 25 prior findings is verified fixed (each pinned by a
regression test that fails if the fix is reverted); the security-critical core — the
signature-verification and transport modules — is byte-identical to the previously
audited version, with the transaction constants (version 2, replaceable sequence)
unchanged; and the fresh attack wave found no breach. One open Medium finding holds
the grade back. The locked rules define Green by five conditions and Yellow by "open
medium findings beyond the owner's written acceptance"; the referee ruled the text
must be read so its Yellow clause can ever apply — so an open Medium that the owner
has not accepted in writing holds the grade at Yellow, whatever the other five
conditions say. It is a process finding, not a code defect:

**v0.6.3 was published through the project's documented manual procedure rather than
through the build pipeline's automated publish gates** — the release appeared eleven
minutes after the non-publishing candidate build finished, so the machine-enforced
checks (tag guard, re-hash-before-publish, unsigned-build refusal) never executed for
the publication event itself. The panel verified every mitigation: the published files
are byte-identical to the checksums the candidate run produced, the tag points at the
exact audited commit, the release notes say plainly what happened, and the procedure
is written down. But a stated gate that did not run is exactly what a supply-chain
audit exists to report — and the grade rules were locked before the audit, so they
were applied as written, not as hoped.

**The path to Green is a single step, then a re-run of the panel:** either publish one
future release through the automated gates (demonstrating the machine-enforced path
end-to-end), or record a dated owner acceptance of the manual path as a documented
residual risk. Nothing else stands between this audit's evidence and a Green grade.

## The four questions that matter

**1. Could this software send bitcoin somewhere the operator did not approve?**
**No — no such path was found.** A dedicated attacker-agent, deliberately kept ignorant
of all prior audit conclusions, attacked every change made since v0.6.2 and every
classic surface: crafted device paths, race conditions on the payment review,
counterfeit-device identity spoofing, hostile explorer data, CI bypass paths, supply
chain substitution. Every attack was refused, fail-closed.

**2. Could it expose a seed phrase, private key, or device PIN?**
**No.** The application still has no code path that reads, stores, or transmits key
material of any kind — re-verified against the changed code.

**3. Could a remote party, a dependency, or a local process alter a transaction
without the operator seeing it?** **No — not on any path this software executes.**
The deepest new risk this release took was vendoring its own cryptography library;
the panel proved the vendored build is the upstream library plus exactly two declared
lines (a version label and a one-line correctness fix the upstream project has not yet
merged), validated against Bitcoin's official test vectors, byte-exact end to end.
The application's own verify-then-finalize remains the only finalizer in use.

**4. What should be done first?** Publish the next release through the automated
gates — it is the one item between this report and a Green grade.

## The prior audit's findings: all fixed

All 22 actionable findings from the v0.6.2 audit are verified fixed at this commit,
each with file-and-line evidence and a regression test that would fail if the fix
were reverted. The referee independently re-derived the six most safety-critical
rows — the hash-pinned install order, the step-local signing secrets, the publish
gates, the dual-named USB library, the sign-time device binding, and the parser
error handling — and found each exactly as claimed. Three informational findings
required no action; one optional enhancement
(recording a cryptographic attestation on releases) remains open by choice. The
headline repairs, all verified in the shipped product: the release pipeline now
installs every dependency hash-verified *before* any signing credential exists; the
USB library is vendored, dual-named, loaded deterministically (proven on a real
Homebrew-equipped Mac with the shipped binary's own self-check), and its shipped
digests are recorded in the bill of materials; signer identity is now re-verified at
the exact moment of signing, not just when devices are scanned; and the cryptography
library's known defects (including one the upstream project still has not fixed) are
repaired in a vendored build whose every byte is accounted for.

## The panel

**🔴 Red — the attacker. No breach found.** Attacked every changed surface plus the
classics; every attempt refused. Residuals: a physical device-swap window measured in
seconds, bounded to denial-of-service — a swapped device can consume an approval
attempt but cannot produce a signature that survives verification.

**🔵 Blue — the defender. Defenses hold.** All nine stated security controls verified
end-to-end in code and pinned by tests; all 25 prior findings tracked to their fixes.
Gaps: three refusal branches lack their own regression tests (all verified fail-closed
by inspection) — coverage debt, not defects.

**🟠 Orange — the cryptographer. Cryptography sound as used.** The vendored library is
upstream at commit `2b375a` plus exactly two declared lines; all BIP test vectors pass
byte-exact (all six signature-hash modes); the library's own 121-test suite passes
against the vendored build; the provenance chain from upstream commit to installed
package is hash-verified with no unexplained bytes. Note for the future: the project
now carries a private, spec-correct patch its upstream has not merged — every future
library update must re-audit that divergence.

**🟤 Copper — the hardware specialist. Transport sound.** Both USB library names ship
inside the signed binary; loading is deterministic and fail-closed; provenance traces
byte-exact to the official libusb 1.0.30 release; the new sign-time device binding is
correctly implemented and lock-consistent. One supply-chain observation: the vendored
USB *binary's* trust anchors all live in the same repository — an honest trade-off a
future release could close by rebuilding from the vendored official source.

**🟡 Amber — the supply-chain inspector. Chain holds** — every pipeline claim in the
remediation record verified with evidence — **with one finding:** the manual
publication (above). The published source archive is byte-identical to the tagged
tree, all 117 files, and contains nothing that should not be public.

**⚪ White — the referee.** Re-derived every load-bearing claim personally — all
verified; three minor citation drifts in the specialists' reports were corrected
(the parser catch is at wallet_service.py:848, the signer-binding initialization at
gui.py:405, and the publication time is carried by the release's asset timestamps —
all at commit f19bc460). Merged the panel's findings into the final
numbered ledger (BESA-26…44), calibrated severities, and applied the locked grade
rules mechanically, in neither direction. **Publication approved**, with the facts
above mandatory.

## What this audit did not do

No panel agent attached a hardware device — the owner's physical practice-network
payment (two vendors, both signatures verified by the app, broadcast accepted) is
taken as reported evidence, recorded in the release records without wallet details.
No transaction was created or broadcast by the panel on any network. The automated
publish workflow has never executed a publication for any release — that is the
substance of the grade's one finding. "No finding" means "none found within this
coverage," not "none exist."

## Appendix — findings ledger (for auditors and agents)

Prior-cycle findings BESA-01…25: see the v0.6.2 report; **status at this commit: all
actionable findings fixed (BESA-20's optional attestation remedy open by choice;
BESA-23/24/25 informational, no action required).** Final consolidated new findings
(numbering fixed by the referee after the specialists' independent counts collided):

| ID | Severity | Finding (one line) |
|---|---|---|
| BESA-33 | Medium | v0.6.3 published via the documented manual path; automated publish gates did not execute for the publication event (bytes verified identical to the candidate; disclosed; conversion path defined) |
| BESA-26 | Low | Physical device swap in the verify→sign window (seconds) receives the reviewed PSBT; bounded to disclosure/DoS — no forged signature can survive verification |
| BESA-27 | Low | Three /api/sign refusal branches lack regression pins (no-binding, stale-binding, verify-failure wiring) — fail-closed by inspection |
| BESA-28 | Low | Broadcast returned-txid-mismatch branch untested directly (gui.py:942-946 @ f19bc460) |
| BESA-29 | Low | hwi ships disable-library-validation + onefile extraction surface; the entitlement may now be droppable (all embedded binaries team-sign); stale build comment |
| BESA-30 | Low | Vendored libusb binary's trust anchors are repo-circular (source correspondence hash-verified but never rebuilt) |
| BESA-31 | Low | SBOM embit entry carries no hash; its purl is symbolic (local build) — authenticate via the hash-locked wheel |
| BESA-32 | Low | Seconds-wide tag-check/publish TOCTOU (needs concurrent push access) |
| BESA-34…44 | Info | Hygiene and documentation notes, each bounded: stale binding cleanup, CI argv secrets on ephemeral runners, bundled-library check lives in the preflight, inherited secp256k1 loader (blocked by hardened runtime), the private crypto-patch maintenance obligation, unreachable Liquid-code residual, library-layer address quirks (neutralized by the app), public-data device binding (inherent), prepublication stamps (documented), dev-doc install hints, candidate-evidence timing (resolved on main immediately after the tag) |

---

*Audit performed 2 October 2026 by Z.ai on the public repository and published
artifacts only. The grade rules were locked in writing before the audit began and
applied as written. No wallet material, addresses, or transaction identifiers appear
in this report. An audit is not a certification of safety; it is dated evidence about
one revision, and its coverage limits are stated above.*
