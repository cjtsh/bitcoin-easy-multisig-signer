# 0.7.1: Color Team cycle-7 remediation

The v0.7.0 audit graded **⚠️ CONDITIONAL**. The conversion gate was met in full —
the White referee re-broke both conversion-gating findings from the cycle before
(the fair-admission server in both directions, and each of CT-14's three prevout
limbs) and watched the discriminating tests fail, so 18 of 18 prior findings are
verified fixed **by execution**, none dropped, none closed by acceptance — and the
delta introduced no Critical or High. The grade was held by CT-21 and CT-20, two
new Informational findings in the lineage's pin-accuracy family, plus one
Informational observation (CT-19) the owner accepted and asked to have documented
accurately.

This release closes all three. Every row below cites a test the build loads
(`tests/test_ledger_completeness.py` holds this file to `releases/PLAN-0.7.1.md`),
and every control was break-and-watched on a disposable copy — broken, the named
test watched going red, the copy restored byte-for-byte and re-run green. The full
transcripts are kept in `releases/BREAK-AND-WATCH-0.7.1.md`, because this cycle's
findings are about test and tracking evidence and the record of the breaks is the
evidence. Code citations are at the `v0.7.0` revision `4fe8f29` — `file:line` in
the tree that ships this file — unless a row says otherwise.

## Finding → fix → test

| ID | Sev | Fix | Closing evidence |
| --- | --- | --- | --- |
| CT-19 | Info | `gui.py:106-127`. The ceiling's class docstring described the availability trade inaccurately: it implied the page's token was what protected a slot, when the code claims a slot as soon as a complete request head has arrived and only then asks whether the route needs the token. The docstring now says exactly that — a slot is claimed by a complete request head "and nothing more", the token is required only by the routes that do something, and a newcomer is refused only when every admitted connection is busy. The trade itself is accepted rather than changed: a local process that keeps complete requests in flight can occupy every slot, which is availability only, self-heals within the 15 s read budget, and reaches no declared asset. The corrected sentence is then pinned, because a description nothing holds is how the next cycle finds it again: a test class drives a real bounded server over a socketpair and asserts both halves — a complete request head claims the slot with no token present (the route is then dispatched and refuses it with 403), and a half-sent head claims no slot. Break-and-watch: making the busy claim require the token turned the first case red with `[False] != [True]`; putting admitted connections straight into the busy set turned the second red. Both restores were byte-identical and both cases went green again. Row `CM-37` names the claim. | `tests/test_gui_integration.py::SlotClaimSemanticsTests::test_a_complete_request_head_claims_the_slot_without_the_token` and `tests/test_gui_integration.py::SlotClaimSemanticsTests::test_a_half_sent_request_head_claims_no_slot` |
| CT-20 | Info | `tests/test_controls_inventory.py:34-39`. The inventory's claim-phrase net scanned the shipped Python and the release scripts but not `.github/workflows/*.yml`, so a "fail closed" comment added to the workflow passed the inventory suite unseen, and the CT-16 guard's own claim had arrived untracked. `SHIPPED` now includes the workflow files, and each claim the workflow makes has its own row and its own `CONTROL: CM-##` marker inside the cited range: `CM-33` the retired-publisher pagination guard, `CM-34` the notarisation credential guard, `CM-35` the release-key signing guard. `CM-33` reuses the CT-16 pins; `CM-34` and `CM-35` gained executable pins that run the workflow step body with stubbed `bash` and `gpg`, assert the exact refusal message the gate prints, and assert the positive half, so a later stage failing for its own reason cannot be mistaken for the guard. A test now fails if the workflow file class leaves the scanned set, which is the specific regression the audit found. `ui.html` stays outside the set deliberately, and the reason is recorded in the inventory's preamble: the page's one control claim is already `CM-30`, pinned by `tests/test_ui_scripts.py`, so adding it would add a scanned file without adding a control. Widening the net was checked against every shipped comment block before it was pinned, so it cannot fail the build on wording alone. The source archive then caught the new test itself: a tarball has no `.github/` directory — `scripts/build-source.sh` ships the same recipes as `ci/<name>.yml` — so the scan read no workflow file there and the archive's own suite went red. `logical_relative` now maps the archive's copy back to the canonical name, which is the resolver-over-hardcoded-path rule the rows already keep, and the extracted archive's suite runs green. Break-and-watch: removing the workflow glob turned the scanned-set case red; deleting the notarisation refusal turned the `CM-34` pin red; replacing the key check with `if false:` turned the `CM-35` pin red. | `tests/test_controls_inventory.py::ControlInventoryTests::test_the_release_workflow_files_are_scanned` and `tests/test_controls_inventory.py::ControlInventoryTests::test_every_marker_has_a_row_in_the_same_file`, plus each new row's own closing test: `tests/test_publish_guards.py::RetiredPublisherGuardTests::test_more_registrations_than_the_page_holds_refuses` (`CM-33`), `tests/test_publish_guards.py::CredentialGuardTests::test_the_notarisation_guard_refuses_a_build_that_succeeded_and_accepts_one_that_refused` (`CM-34`) and `tests/test_publish_guards.py::CredentialGuardTests::test_the_release_key_guard_refuses_a_publish_without_a_key_and_signs_with_one` (`CM-35`) |
| CT-21 | Info | `gui.py:669-679`. The retired-set guard in the handler's `parse_request` had no test that could fail — deleting it left the full integration suite green — because its precondition (a connection retired between accept and parse) is not reachable under the server's HTTP/1.0 semantics. The guard is kept and pinned synthetically rather than dropped: one handler instance is driven over a `socket.socketpair()` against a real `BoundedThreadingHTTPServer`, the connection is admitted, a newcomer evicts it through the production `_admit` path with `gui._shutdown_quietly` patched to a no-op, and only then is a malformed request written and the handler run. The test asserts the retired connection sends **zero bytes** and that no route was dispatched; the positive half runs the same malformed request on a live connection and expects the 400 with no dispatch, so the assertion cannot pass by failing to serve anything at all. No line was added to `gui.py` for this test: the `CONTROL: CM-36` marker is appended to an existing comment line, so no other row's citation moved. The alternative the auditor offered — drop the guard and record the reliance on shutdown semantics — was considered and rejected: the guard costs nothing at runtime and the pin is honest about what it demonstrates. Break-and-watch: deleting the guard turned the retired half red with an HTTP 400 body where it expects `b""`; the restore was byte-identical and the case went green again. | `tests/test_gui_integration.py::RetiredConnectionGuardTests::test_a_retired_connection_is_closed_without_an_answer` and `tests/test_gui_integration.py::RetiredConnectionGuardTests::test_a_live_connection_still_answers_a_malformed_request` |

## Terms of use

On 2026-10-25, after this cycle's three findings were already in hand, the owner
asked that Bitcoin Easy Signer's terms of use carry the default legal section the
company publishes at [cjtsh/software-disclaimer](https://github.com/cjtsh/software-disclaimer)
(framework v1.2.2, effective 2026-10-21). `DISCLAIMER.md` is now the project's copy
of that framework with the signer's specifics folded into it — what the software
does and does not guarantee, the Bitcoin-specific risks, the AI-generated audit
reports, the fee guidance being informational, and the rule that the operator must
verify every transaction and treat signed-but-unbroadcast bytes as spendable by
anyone. Every surface that points at the terms now names both the project's copy
and the canonical URL: `README.md`, `USER-MANUAL.md`, the `docs/` pages, the in-app
About dialog and footer, and `CURRENT-STATUS.md`.

The framework's own rule is stated rather than softened, because it is the honest
one: a notice or a link alone may not establish contractual assent, and the
framework does not make every provision a binding contract merely because someone
visited the repository. **No acceptance gate was added.** An in-app "I agree"
prompt would be a functional change to the shipped software, and this release
contains none. Whoever distributes, hosts or deploys the software is the party who
must obtain any assent their distribution and jurisdiction require.

## Accepted floating inputs

Unchanged from `releases/PATCH-0.7.0.md`, and restated here because the workflow
files were edited this cycle (CT-20) and a reviewer should not have to walk back a
ledger to check that the floating inputs were noticed. Pinning the runner's
packages to exact versions remains **declined**: the `noble-updates` and
`noble-security` archives move as Canonical ships fixes, a pin would fail the build
on a runner refresh without making the AppImage reproducible, and the package is
only one input among many. A pin that breaks the build and buys nothing is not a
control.

What is accepted, and what stands in for the pin:

- **The runner image's packages**: `squashfs-tools`, `librsvg2-bin`,
  `build-essential`, `fuse3`, resolved from the `ubuntu-24.04` runner's archives.
  Recorded per build in the SBOM (name and version), declared once in
  `scripts/build-linux.sh`, and a test asserts the workflow installs exactly that
  set.
- **The proof container's packages**: `fuse3` and `ca-certificates`, installed
  inside the digest-pinned container. Printed into the run log; the proof is a
  pass/fail assertion about the AppImage, not shipped bytes.
- **The container image**: pinned by the digest
  `sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55`;
  the refresh command is recorded beside the pin and in `scripts/build-linux.sh`.

A review of this release should re-run the refresh command, move the digest, and,
if any of the four runner packages changes, update `SYSTEM_PACKAGES`, this
section, and the SBOM expectations in the same commit.

## Notes

**What did not change.** No wallet, signing or broadcast behaviour changed. The
engine's refusals, the money-path gates, the fee logic, the PSBT handling and the
device handling are byte-for-byte what `v0.7.0` shipped. The three finding rows are
tests, tracking and one docstring: `gui.py`'s shipped behaviour is identical to
`v0.7.0` except for the docstring text and the appended `CONTROL:` comment marker,
both of which are comments. The full suite passes unchanged.

**The one behaviour change, and where it is felt.** There is none. This is the
release of a cycle that added tests, widened a scanned file set, added inventory
rows and corrected a comment.

**Why one fixture spells its credential names in pieces.** `tests/test_publish_guards.py`
ships inside the source archive, and the release's own secret scan reads the bytes a
tag would publish. A keyword like `PRIVATE_KEY` next to a value in a fixture reads to
that scan exactly like a leak, so the two environment names in `CredentialGuardTests`
are composed from fragments — the same reason the workflow's canary is. The first
candidate build for this release went red on that finding before anything was
published: the fixture was rewritten, and the scan was left alone.

**Evidence kept in the repository, and evidence that is not.** The break-and-watch
transcripts for all seven tripwires are kept in
`releases/BREAK-AND-WATCH-0.7.1.md` with the breaks, the exact failure text, the
byte-identical restores and the green re-runs. The auditor's private coaching
document, evidence index and lane reports remain outside the repository by design,
as in every prior cycle.

**No earlier record was edited.** The v0.7.0 audit plan, lock, report and security
statement are byte-identical to what was published, and so are the v0.6.8 and
v0.6.9 artifacts under `audit-history/`.
