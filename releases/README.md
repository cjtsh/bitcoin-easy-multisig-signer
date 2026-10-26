# Release records

This folder holds the long-form evidence record for each version: the patch
records, the release notes, the plans a release was built against, owner
acceptance notes, and the security review. They live here rather than in the
repository root so the root holds only the living documents.

[`../RELEASE-HISTORY.md`](../RELEASE-HISTORY.md) is the index. Its version table
links each version to the record below, and its prose sections quote them.

## Naming

| Prefix | What it is |
| --- | --- |
| `PATCH-<version>.md` | The evidence record for one release: what changed, what was proven, what was corrected afterwards |
| `RELEASE-NOTES-<version>.md` | The release announcement text for one version |
| `PLAN-<version>.md` | The plan a release was built against |
| `OWNER-ACCEPTANCE-<date>.md` | The owner's dated hardware-acceptance note for a candidate |
| `BREAK-AND-WATCH-<version>.md` | The tripwire transcripts for one release's audit-technicality fixes: each control broken on a disposable copy, its named test watched to go red, the restore, and the same test watched to go green |
| `<PLATFORM>-<version>-ACCEPTANCE.md` | A platform walkthrough record, e.g. `LINUX-0.6.4-ACCEPTANCE.md` |
| `SECURITY-REVIEW-<version>.md` | A security review and its remediation |
| `MUTINYNET-<version>.md` | A signet-network walkthrough record |
| `platform-state.json` | A dated snapshot of the repository's GitHub platform settings |

## What is in here

| Record | Version | What it covers |
| --- | --- | --- |
| [`SECURITY-REVIEW-0.2.0.md`](SECURITY-REVIEW-0.2.0.md) | 0.2.0 | Hot-item security fixes; hardware signing was broken in this release |
| [`PATCH-0.2.1.md`](PATCH-0.2.1.md) | 0.2.1 | HWI field-order repair; first confirmed Testnet4 payment |
| [`PATCH-0.2.2.md`](PATCH-0.2.2.md) | 0.2.2 | One-payment-at-a-time confirmation wait |
| [`PATCH-0.3.0.md`](PATCH-0.3.0.md) · [`MUTINYNET-0.3.0.md`](MUTINYNET-0.3.0.md) | 0.3.0 | Warm safety work, Mutinynet, stale-screen fix |
| [`PATCH-0.3.1.md`](PATCH-0.3.1.md) | 0.3.1 | Send All is never preselected; Mutinynet becomes the default network |
| [`PATCH-0.3.2.md`](PATCH-0.3.2.md) | 0.3.2 | One-file BIP48 custom sends from a Nunchuk BSMS |
| [`PATCH-0.4.0.md`](PATCH-0.4.0.md) | 0.4.0 | Visual refresh; session-only payment receipt |
| [`PATCH-0.4.1.md`](PATCH-0.4.1.md) | 0.4.1 | Signature-only signer-response import; longer signing window |
| [`PATCH-0.4.2.md`](PATCH-0.4.2.md) | 0.4.2 | Three-minute device discovery and authorization waits |
| [`PATCH-0.4.6.md`](PATCH-0.4.6.md) | 0.4.6 | Signature checklist after the first device signature |
| [`PATCH-0.4.14.md`](PATCH-0.4.14.md) | 0.4.14 | Follow the BSMS quorum for wallets with up to three hardware keys |
| [`PATCH-0.4.15.md`](PATCH-0.4.15.md) | 0.4.15 | Fix signed HWI/libusb loading; OneKey Classic 1S support; a cleared, unbroadcast mainnet dry run |
| [`PATCH-0.5.0.md`](PATCH-0.5.0.md) | 0.5.0 | Mainnet broadcast behind explicit final-screen and backend opt-ins; made the first live mainnet payment |
| [`PATCH-0.5.1.md`](PATCH-0.5.1.md) | 0.5.1 | First published mainnet-broadcast release; publishes the 0.5.0 engine unchanged and corrects the change-address guidance |
| [`PATCH-0.6.2.md`](PATCH-0.6.2.md) | 0.6.2 | **Published 2026-10-02 as `v0.6.2`.** Internal state fix: retiring a review also retires the network it was bound to, so a later payment cannot inherit the mainnet opt-in from an earlier one. No user-visible behaviour change and the engine is unchanged from 0.5.1 |
| [`PATCH-0.6.1.md`](PATCH-0.6.1.md) | 0.6.1 | **Published 2026-10-02 as `v0.6.1`.** Interface only: the app opens on mainnet and the practice networks move behind an "Enter Developer Mode" gate that offers Mutinynet and Testnet4 only; the engine is unchanged from 0.5.1. The 0.6.0 candidate that first carried the gate is superseded, so no 0.6.0 tag or release exists |
| [`PATCH-0.6.3.md`](PATCH-0.6.3.md) | 0.6.3 | Audit remediation in signing checks, embit, libusb, build inventory and release controls; owner-tested Mutinynet payment |
| [`PATCH-0.6.4.md`](PATCH-0.6.4.md) · [`RELEASE-NOTES-0.6.4.md`](RELEASE-NOTES-0.6.4.md) | 0.6.4 | API regression coverage and workflow-only publication of the verified candidate bytes |
| [`PATCH-0.6.5.md`](PATCH-0.6.5.md) · [`RELEASE-NOTES-0.6.5.md`](RELEASE-NOTES-0.6.5.md) | 0.6.5 | The unified pipeline: Windows and Linux built from one dispatch. The out-of-gate `v0.6.5-windows-x64` release was later deleted (CT-27) |
| [`PATCH-0.6.6.md`](PATCH-0.6.6.md) · [`RELEASE-NOTES-0.6.6.md`](RELEASE-NOTES-0.6.6.md) | 0.6.6 | Color Team cycle-2 remediation: BIP-143 vectors, money-path and HWI-identity pins, BIP-62 low-S, release-channel hygiene |
| [`PATCH-0.6.7.md`](PATCH-0.6.7.md) · [`RELEASE-NOTES-0.6.7.md`](RELEASE-NOTES-0.6.7.md) | 0.6.7 | Color Team cycle-3 build-process remediation, answering a grade set by process and not by the app |
| [`PATCH-0.6.8.md`](PATCH-0.6.8.md) · [`PLAN-0.6.8.md`](PLAN-0.6.8.md) · [`RELEASE-NOTES-0.6.8.md`](RELEASE-NOTES-0.6.8.md) | 0.6.8 | Color Team cycle-4 remediation: one ledger row per scheduled finding with a closing test the build loads, and a parsed `CONTROLS.md` inventory |
| [`PATCH-0.6.9.md`](PATCH-0.6.9.md) · [`PLAN-0.6.9.md`](PLAN-0.6.9.md) · [`RELEASE-NOTES-0.6.9.md`](RELEASE-NOTES-0.6.9.md) | 0.6.9 | Color Team cycle-5 remediation: `CONTROLS.md` citations bound to their own markers, every Low finding pinned by a test that can fail, and the recorded housekeeping closed |
| [`PATCH-0.7.0.md`](PATCH-0.7.0.md) · [`PLAN-0.7.0.md`](PLAN-0.7.0.md) · [`RELEASE-NOTES-0.7.0.md`](RELEASE-NOTES-0.7.0.md) | 0.7.0 | Color Team cycle-6 remediation: the prevout value and script limbs pinned by discriminating tests, a connection ceiling that retires an idle socket instead of refusing the window, the protections of the previous release tracked in `CONTROLS.md` as `CM-27`…`CM-32`, a fail-closed page limit on the retired-publisher guard, a bounded Windows startup dialog, and a precise `libusb` provenance sentence |
| [`PATCH-0.7.2.md`](PATCH-0.7.2.md) · [`PLAN-0.7.2.md`](PLAN-0.7.2.md) · [`RELEASE-NOTES-0.7.2.md`](RELEASE-NOTES-0.7.2.md) · [`BREAK-AND-WATCH-0.7.2.md`](BREAK-AND-WATCH-0.7.2.md) | 0.7.2 | Color Team cycle-8 remediation: the unconfirmed-payment pause asserted at the broadcast and again under the pre-submit lock, a duplicated-input refusal before any explorer is asked, and `http.client.HTTPException` in the three transport tuples |
| [`PATCH-0.7.1.md`](PATCH-0.7.1.md) · [`PLAN-0.7.1.md`](PLAN-0.7.1.md) · [`RELEASE-NOTES-0.7.1.md`](RELEASE-NOTES-0.7.1.md) · [`BREAK-AND-WATCH-0.7.1.md`](BREAK-AND-WATCH-0.7.1.md) | 0.7.1 | Color Team cycle-7 remediation: the retired-connection guard pinned by a test that can fail, the control inventory widened to the GitHub workflow files (`CM-33`…`CM-36`) with executable pins for the notarisation and checksum-signing credential guards, the busy-slot docstring corrected, and terms of use that incorporate the Bitseeker LLC standard legal framework |
| [`OWNER-ACCEPTANCE-2026-10-07.md`](OWNER-ACCEPTANCE-2026-10-07.md) | 0.6.6–0.6.7 | The owner's dated hardware-acceptance note for the promoted candidate |
| [`LINUX-0.6.4-ACCEPTANCE.md`](LINUX-0.6.4-ACCEPTANCE.md) | 0.6.4 | Owner-reported Linux AppImage walkthrough |
| [`platform-state.json`](platform-state.json) | — | Dated snapshot (2026-10-16T06:19:08Z) of the repository's GitHub platform settings |

## These are historical records

Every file here describes the repository as it stood at the time it was written.
They are deliberately **not** rewritten when the code, the layout, or the policy
changes — a record that gets edited to match the present is no longer evidence.

So a file here may say something that is no longer true. In particular, records
written before 0.5.0 say that mainnet broadcast is refused in code, which was
correct when they were written and is not correct now.

**A path a record names may no longer be in the repository.** The Color Team
audit plans, locks, reports and security statements that older records cite lived
in the repository root. They were removed from `main` on 2026-10-11 and remain in
the tag tree of the version each record describes: `bitcoin-easy-multisig-signer-
colorteam-audit-report-v0.6.6.md`, for example, is in the `v0.6.6` tree. A
citation in a record is therefore a name to look up in that tag, not a path to
expect in `main`.

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
