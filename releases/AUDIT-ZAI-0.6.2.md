# Z.ai Security Audit — v0.6.2

**Audited software:** Bitcoin Easy Signer v0.6.2, a Mac application that helps a
non-technical person (an executor, trustee, or attorney) make a payment from an
existing 2-of-3 multisig Bitcoin wallet using the wallet's BSMS definition file,
hardware signing devices, and public blockchain explorers.

| | |
|---|---|
| **Exact version examined** | Tag `v0.6.2`, commit `7b4db8548df2132ee031153725c45391c0f3103f`, published 2026-10-02 |
| **Auditor** | Z.ai (GLM-5.3, via ZCode), 2026-10-02, working to a written audit framework; assisted by three independent audit sub-agents and a separate verification pass |
| **Method** | Full read of every line of the application's own code; line-by-line review of the inherited libraries it depends on (embit 0.8.0, Bitcoin Core HWI 3.2.0, the bundled libusb); inspection of the build, signing, notarization, and release pipeline; independent re-verification of the published download's hashes, code signature, and Apple notarization |
| **Verification** | The application's own 240 automated tests plus 9 interface tests were re-run and pass; the auditor's own hostile-input tests (tampered device responses, malicious explorer data, forged signatures) were all refused by the application |

---

## What a reader needs to know first

Bitcoin Easy Signer never holds the wallet's keys. It cannot: it has no code path
that reads a seed phrase, a private key, or a device PIN anywhere — this was
verified by tracing every input the software accepts, not by taking the
documentation's word. Every payment must be physically approved on the screens of
the number of hardware signing devices the wallet's definition file requires —
two of three for the wallets this software is built for — and the software
cryptographically checks that what the devices signed is exactly what the
operator reviewed on screen before anything is sent.

**This audit is evidence about this one version, examined on this date. It is not
a guarantee, and it does not make any future payment safe.** What it does
establish is below.

## The four questions that matter

**1. Could this software send bitcoin somewhere the operator did not approve?**
**No — no such path was found.** A payment can only leave the machine after: the
operator checks a box confirming the exact destination, amount, fee and change
shown on a review screen; the transaction ID they confirm is checked against the
one built; every output of the final transaction is re-compared field-by-field
against that review; the coins being spent are re-checked as unspent against two
independent public sources on mainnet; and the network's answer is checked
against the reviewed transaction ID. Every input is proven to belong to the
wallet before it can be used: the software fetches each coin's original
transaction and verifies its identifier, value, and ownership script from
scratch. The audit attempted to break this chain with hostile data at every
stage; every attempt was refused.

**2. Could this software expose a seed phrase, private key, or device PIN?**
**No — no such path was found.** Verified by enumeration of every code path that reads wallet files,
device responses, or operator input. The wallet-file parser actively rejects any
file containing private key material. A Blockstream Jade's PIN is typed on the
device itself and never reaches the computer in any form (confirmed down to the
device-communication library). The only things the software ever writes to disk
are an unsigned transaction file, a fixed-vocabulary troubleshooting report, and
explorer web addresses.

**3. Could a remote party, a software dependency, or another program on the
computer change a transaction without the operator seeing it?**
**No — not on any path this software actually executes.** This question was
pursued hardest, including inside the inherited libraries. Two defects of exactly
this kind were found *in the libraries* (detailed below): embit's off-the-shelf
"finalize" routine accepts garbage signatures, and embit rewrites certain
transaction fields. Both were traced to dead ends: Bitcoin Easy Signer does not
use embit's finalizer — it has its own, which verifies every signature
cryptographically before assembling the final transaction — and the field
rewrite cannot occur in transactions this app builds. The remaining honest
caveat is inherent to using any off-the-shelf cryptography: if the underlying
mathematics library itself were secretly backdoored, no application-level check
could detect it. The defenses against that are the hardware devices' independent
screens and the locked, hash-verified dependency chain — and the audit verified
those devices' role cannot be bypassed from this software.

**4. What should be fixed first?**
One gap in the build pipeline (see below): a single support package is installed
in the release build without the cryptographic hash check that every other
dependency has — in the same build job that holds the company's signing
certificate. A one-line fix. It does not affect the version already published,
which was verified intact.

## What the audit found (all High and Medium findings listed; lower-severity items summarized)

No Critical findings — nothing that can move funds, expose keys, or broadcast
without review. The findings below are real and are reported at their true
severity. Most concern either the *publishing pipeline* (how future versions get
built and signed) or *latent library defects this application does not reach*;
the remainder are smaller control and availability gaps listed below — none lets
a payment leave the machine unapproved, and none provides a way to steal bitcoin
from a user of v0.6.2.

**The publishing pipeline (fix before the next release):**

- **HIGH — one unhashed install beside the signing certificate.** In the
  GitHub build workflow, `pyyaml` is installed without the hash verification
  every shipped dependency has, after the Developer ID certificate has been
  unlocked on the build machine. A compromise of the PyPI package repository at
  that moment could plant code in a future *signed and notarized* release. The
  already-published v0.6.2 is unaffected (its contents verify cleanly).
- **MEDIUM — the signing secrets stay available to the whole build job**, and
  the fallback that fetches the USB library via Homebrew runs unverified code in
  that same job; **MEDIUM — the release step never re-checks the published
  files' hashes against the published checksum list**, and its "never rebuild a
  version" guard tests for an existing *release*, not an existing *tag*. Each
  widens the blast radius of the first item or weakens a stated control; none is
  independently exploitable.

**The bundled USB library (control does not mean what it says):**

- **MEDIUM — the "digest-pinned libusb" guarantee cannot be checked on the
  shipped product.** The published binary embeds a re-signed copy whose hash
  necessarily differs from the pinned value (the app's own signature is applied
  during bundling), and the software bill of materials records the pre-signing
  hash, so an independent verifier comparing them sees an unexplained mismatch.
  **MEDIUM — on Macs with Homebrew installed, the audit's analysis shows the
  device software loads Homebrew's copy of the USB library instead of the
  bundled one** (a file-name mismatch defeats the intended loading order; the
  shipped binary was not executed during the audit, so this was established by
  code analysis and a loading experiment on the identical library code).
  Exploiting either requires an
  attacker already running as the user — at which point no desktop application
  could resist — but the documented control should either hold or be restated.

**Latent defects in the inherited embit library (verified unreachable or contained here):**

- embit's stock finalizer performs **no signature verification** (HIGH as a
  library; this app does not use it — it has its own verifying finalizer).
- embit **silently rewrites two transaction fields** when they hold a value of
  zero (open upstream issue; unreachable here because the app hard-codes
  different values), and its parser **accepts some truncated input** instead of
  rejecting it (contained here: every downstream check re-derives values
  independently).
- embit 0.8.0 predates that library's own 2026 security hardening releases and
  ships prebuilt cryptography binaries it later removed under a "Security"
  label. **Recommendation: schedule a reviewed upgrade.** The audit validated
  the shipped version's behavior against Bitcoin's official test vectors (all
  exact matches).

**Smaller items:** the app does not update itself, so users must re-download
deliberately; the software bill of materials omits the bundled Python runtime
itself; the source archive contains its own pre-publication "not published yet"
stamps; device identity is verified when devices are *scanned* but not re-checked
at the instant of signing (what a swapped device returns still cannot pass the
signature verification, so the bound is cryptographic, not procedural).

## What this audit did not do

No physical hardware device was attached; device-screen behavior is taken from
the project's recorded hardware evidence. No transaction was created, signed, or
broadcast on any network, and no live explorer was contacted by the auditor. The
guts of GitHub's and Apple's build/signing infrastructure were not (and cannot
be) audited; the published artifact's validity rests on checks that *were*
performed: every published hash recomputed and matching, the Developer ID
signature and Apple notarization verified as intact on the downloaded file, and
every file the source archive shares with the tagged source compared
byte-for-byte (identical, with three documented packaging differences).

**Verified intact:** all three published files' SHA-256 hashes; Developer ID
"Bitseeker LLC (B8G5L7M8TB)" signature with hardened runtime; Apple notarization
ticket valid and stapled; Gatekeeper acceptance; all four GitHub build actions
pinned to exact commits; every shipped Python dependency installed under
hash-lock; tag, commit, and release records mutually consistent. Previously
recorded project issues F2–F6 were re-checked and are correctly described, with
the 0.6.2 fix (F3) confirmed in code.

---

*Audit performed 2026-10-02 by Z.ai (GLM-5.3) on the public repository and
published artifacts only. No wallet material, addresses, or transaction
identifiers appear in this report. An audit is not a certification of safety;
it is dated evidence about one revision, and its coverage limits are stated
above.*
