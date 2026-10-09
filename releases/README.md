> **Audit reset:** Historical audit documents referenced below are preserved in the archive branch and Git history, but removed from the active tree. See [the reset explanation](../AUDIT-RESET-2026-10-09.md). The historical links below may not resolve on this branch.

# Release records

This folder holds the long-form evidence record for each version: the patch
records, the plans a release was built against, the independent audits, and the
security review. They live here rather than in the repository root so the root
holds only the living documents.

[`../RELEASE-HISTORY.md`](../RELEASE-HISTORY.md) is the index. Its version table
links each version to the record below, and its prose sections quote them.

## Naming

| Prefix | What it is |
| --- | --- |
| `PATCH-<version>.md` | The evidence record for one release: what changed, what was proven, what was corrected afterwards |
| `PLAN-<version>.md` | The plan a release was built against |
| `SCOPE-<version>.md` | The scope a release was built against, as the owner signed it off |
| `AUDIT-<who-or-when>.md` | An independent audit of the code as it stood at that commit |
| `SECURITY-REVIEW-<version>.md` | A security review and its remediation |
| `MUTINYNET-<version>.md` | A signet-network walkthrough record |

## What is in here

| Record | Version | What it covers |
| --- | --- | --- |
| [`AUDIT-BASELINE-0.1.27.md`](AUDIT-BASELINE-0.1.27.md) | 0.1.x | Baseline audit of the Phase 1–4 work |
| [`SECURITY-REVIEW-0.2.0.md`](SECURITY-REVIEW-0.2.0.md) | 0.2.0 | Hot-item security fixes; hardware signing was broken in this release |
| [`PATCH-0.2.1.md`](PATCH-0.2.1.md) | 0.2.1 | HWI field-order repair; first confirmed Testnet4 payment |
| [`PATCH-0.2.2.md`](PATCH-0.2.2.md) | 0.2.2 | One-payment-at-a-time confirmation wait |
| [`PATCH-0.3.0.md`](PATCH-0.3.0.md) · [`PLAN-0.3.0.md`](PLAN-0.3.0.md) · [`MUTINYNET-0.3.0.md`](MUTINYNET-0.3.0.md) | 0.3.0 | Warm safety work, Mutinynet, stale-screen fix |
| [`PATCH-0.3.1.md`](PATCH-0.3.1.md) | 0.3.1 | Send All is never preselected; Mutinynet becomes the default network |
| [`PATCH-0.3.2.md`](PATCH-0.3.2.md) | 0.3.2 | One-file BIP48 custom sends from a Nunchuk BSMS |
| [`PATCH-0.4.0.md`](PATCH-0.4.0.md) | 0.4.0 | Visual refresh; session-only payment receipt |
| [`PATCH-0.4.1.md`](PATCH-0.4.1.md) | 0.4.1 | Signature-only signer-response import; longer signing window |
| [`PATCH-0.4.2.md`](PATCH-0.4.2.md) | 0.4.2 | Three-minute device discovery and authorization waits |
| [`PLAN-0.4.4.md`](PLAN-0.4.4.md) · [`AUDIT-DEEPSEEK-0.4.3.md`](AUDIT-DEEPSEEK-0.4.3.md) · [`AUDIT-ZAI-0.4.3.md`](AUDIT-ZAI-0.4.3.md) | 0.4.4 | Audit remediation: tests for the guards that had none, three fail-closed gaps, MIT licence and third-party notices |
| [`PATCH-0.4.6.md`](PATCH-0.4.6.md) | 0.4.6 | Signature checklist after the first device signature |
| [`PATCH-0.4.14.md`](PATCH-0.4.14.md) | 0.4.14 | Follow the BSMS quorum for wallets with up to three hardware keys |
| [`PATCH-0.4.15.md`](PATCH-0.4.15.md) | 0.4.15 | Fix signed HWI/libusb loading; OneKey Classic 1S support; a cleared, unbroadcast mainnet dry run |
| [`PATCH-0.5.0.md`](PATCH-0.5.0.md) | 0.5.0 | Mainnet broadcast behind explicit final-screen and backend opt-ins; made the first live mainnet payment |
| [`PATCH-0.5.1.md`](PATCH-0.5.1.md) | 0.5.1 | First published mainnet-broadcast release; publishes the 0.5.0 engine unchanged and corrects the change-address guidance |
| [`PATCH-0.6.2.md`](PATCH-0.6.2.md) | 0.6.2 | **Published 2026-10-02 as `v0.6.2`.** Internal state fix: retiring a review also retires the network it was bound to, so a later payment cannot inherit the mainnet opt-in from an earlier one. No user-visible behaviour change and the engine is unchanged from 0.5.1 |
| [`PATCH-0.6.1.md`](PATCH-0.6.1.md) · [`SCOPE-0.6.1.md`](SCOPE-0.6.1.md) | 0.6.1 | **Published 2026-10-02 as `v0.6.1`.** Interface only: the app opens on mainnet and the practice networks move behind an "Enter Developer Mode" gate that offers Mutinynet and Testnet4 only; the engine is unchanged from 0.5.1. The 0.6.0 candidate that first carried the gate is superseded, so no 0.6.0 tag or release exists |

## These are historical records

Every file here describes the repository as it stood at the time it was written.
They are deliberately **not** rewritten when the code, the layout, or the policy
changes — a record that gets edited to match the present is no longer evidence.

So a file here may say something that is no longer true. In particular, records
written before 0.5.0 say that mainnet broadcast is refused in code, which was
correct when they were written and is not correct now.

For what the app does today, read the code and the tests. For current status,
read [`../CURRENT-STATUS.md`](../CURRENT-STATUS.md) and
[`../PHASE-HANDOFF.md`](../PHASE-HANDOFF.md). Where a historical description and
the current source disagree, the source and its tests win.

## Adding a record

Name the file `PATCH-<version>.md` for the release it belongs to, add it to the
version table in [`../RELEASE-HISTORY.md`](../RELEASE-HISTORY.md), and add a row
to the table above. [`../scripts/build-source.sh`](../scripts/build-source.sh)
copies every `releases/*.md` into the source archive and fails the build if one
is missing, so a new record ships automatically.
