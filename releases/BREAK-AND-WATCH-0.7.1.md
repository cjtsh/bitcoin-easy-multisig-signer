# Break-and-watch — v0.7.1 audit-technicality fixes

**Recorded:** 2026-10-26, 12:59 EDT (America/New_York).
**Rule this satisfies:** `AGENTS.md:37` and `RELEASE-PROCESS.md` §5 — "a release-path change is not done until a test is demonstrated able to fail: break the control on a disposable copy, watch the named test go red, restore. … The test must assert the *specific* refusal message the gate produces (so a weaker backend fallback cannot make it pass) and must include the positive half (the honest path still works)."

**Disposable copy:** `/Users/christerry/projects/kimicode/scratch/ct21`, a working copy of the 0.7.1 tree. Every break below was made there and reverted there. The repository tree was never in a broken state, and no break was made on `main`.

**Python:** the audit virtualenv `/Users/christerry/projects/kimicode/audit-target/.venv-audit/bin/python` (3.12.14).

**Invocation:** `PYTHONPATH=tests python -m unittest <test id>` from the copy's root — the same import path `python -m unittest discover -s tests` uses.

## Why these seven

The v0.7.0 Color Team audit raised three Info-level findings, all of them about the
build and audit apparatus rather than the signer: **CT-19** (a docstring in
`gui.py` claimed more than the code did), **CT-20** (`CONTROLS.md`'s scanned file
set was blind to the GitHub workflow files, so a control claim in the workflow was
untracked), and **CT-21** (the retired-connection guard had no test that could
fail). Fixing CT-20 and CT-21 added four control rows to `CONTROLS.md` —
**CM-33** … **CM-36** — and CT-21 added the executable test
`tests/test_gui_integration.py::RetiredConnectionGuardTests`.

Closing CT-19 and CT-20 needed two more tripwires, because a documentation fix and
a widened scan are both things the suite can lose without noticing. CT-19 corrected
the class docstring that says which state protects a slot; **CM-37** now names that
claim and two tests pin its two halves — a complete request head claims the slot
with no token at all, and a half-sent head claims nothing. CT-20 widened `SHIPPED`
to the workflow files; a test now fails if that file class leaves the scanned set,
because a marker nobody scans is a control nobody tracks. A row in the inventory is
only worth the tripwire behind it, so each of the seven was broken on the disposable
copy and its named test was watched to go red.

| Control | Claim | What was broken | Named test |
| --- | --- | --- | --- |
| CM-33 | the retired-publisher guard refuses when the platform reports more workflow registrations than the one page it reads can hold | both pagination refusals in the step replaced by `if False:` | `test_publish_guards.RetiredPublisherGuardTests::test_more_registrations_than_the_page_holds_refuses` |
| CM-34 | a notarized build that produced a DMG without a notarisation credential is refused | the guard's condition inverted, so it fires only when the build *refused* | `test_publish_guards.CredentialGuardTests::test_the_notarisation_guard_refuses_a_build_that_succeeded_and_accepts_one_that_refused` |
| CM-35 | a publish without the release key cannot ship an unsigned checksum manifest | the `no release key` refusal replaced by `if false:` | `test_publish_guards.CredentialGuardTests::test_the_release_key_guard_refuses_a_publish_without_a_key_and_signs_with_one` |
| CM-36 | a connection the server has retired is closed without an answer | the retired-connection guard removed from the request handler | `test_gui_integration.RetiredConnectionGuardTests::test_a_retired_connection_is_closed_without_an_answer` |
| CM-37 (a) | a complete request head claims a busy slot, and the page's token plays no part in the claim | the busy claim made to require the token, so a tokenless head claimed no slot | `test_gui_integration.SlotClaimSemanticsTests::test_a_complete_request_head_claims_the_slot_without_the_token` |
| CM-37 (b) | only a complete request head claims a slot — silence and a half-sent head claim nothing | admission made to put the connection straight into the busy set | `test_gui_integration.SlotClaimSemanticsTests::test_a_half_sent_request_head_claims_no_slot` |
| CT-20 | the claim-phrase net reads the release workflow files | `.github/workflows/*.yml` removed from `SHIPPED` | `test_controls_inventory.ControlInventoryTests::test_the_release_workflow_files_are_scanned` |

**A discarded run.** A first attempt invoked the tests without the `tests`
directory on the import path, so the "red" was `ModuleNotFoundError: No module
named 'test_publish_guards'` — the control never ran. An import error is not a
red. The transcripts below are from the corrected invocation; the discarded one
is not evidence and is not recorded here.

**What each red shows.** CM-33 fails on `assertNotEqual(result.returncode, 0)`
because the broken guard lets the run continue. CM-34 fails on the exact refusal
message — the broken guard never prints it, so the step fails later for a
different reason and the test refuses to call that a refusal. CM-35 fails on
`assertNotEqual(returncode, 0)` because a working `gpg` and a manifest are
present, so the guard is the only thing that can stop the publish. CM-36 fails
because the retired connection answers with an HTTP 400 body instead of closing
in silence. CM-37 (a) fails on `assertEqual(claimed, [True])` — with the token
required for the claim, the route is dispatched with the slot not busy, which is
exactly the sentence the docstring used to get wrong. CM-37 (b) fails on
`assertNotIn(server_side, server._busy)` — an admitted connection that has sent
only half a head is claimed as busy. CT-20 fails on `assertIn(".github/workflows/*.yml", SHIPPED)`,
which is the narrowing the v0.7.0 audit found.

**Restores.** After every break the affected file was restored and compared
byte-for-byte with the fixed copy (`cmp -s`, "byte-identical" below), and the
same named test was run again and watched to go green.

## Transcript

```text
================================================================
BREAK-AND-WATCH — v0.7.1 audit-technicality fixes
Disposable copy: /Users/christerry/projects/kimicode/scratch/ct21
Python: /Users/christerry/projects/kimicode/audit-target/.venv-audit/bin/python
================================================================

--- CM-33: the retired-publisher pagination guard ---------------
break: both pagination refusals in the 'Refuse while a retired publisher is runnable' step replaced by 'if False:'

$ PYTHONPATH=tests python -m unittest test_publish_guards.RetiredPublisherGuardTests.test_more_registrations_than_the_page_holds_refuses
F
======================================================================
FAIL: test_more_registrations_than_the_page_holds_refuses (test_publish_guards.RetiredPublisherGuardTests.test_more_registrations_than_the_page_holds_refuses)
CT-16: the read is one page, so more than one page must refuse.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christerry/projects/kimicode/scratch/ct21/tests/test_publish_guards.py", line 549, in test_more_registrations_than_the_page_holds_refuses
    self.assertNotEqual(result.returncode, 0)
AssertionError: 0 == 0

----------------------------------------------------------------------
Ran 1 test in 0.041s

FAILED (failures=1)
[exit status: 1]
RESULT: the named test went RED as required.
restore: the workflow file is byte-identical to the fixed copy

$ PYTHONPATH=tests python -m unittest test_publish_guards.RetiredPublisherGuardTests.test_more_registrations_than_the_page_holds_refuses
.
----------------------------------------------------------------------
Ran 1 test in 0.037s

OK
[exit status: 0]
RESULT: the named test is GREEN again after the restore.

--- CM-34: the notarisation credential guard --------------------
break: the guard's condition was inverted, so it now fires only when the build refused

$ PYTHONPATH=tests python -m unittest test_publish_guards.CredentialGuardTests.test_the_notarisation_guard_refuses_a_build_that_succeeded_and_accepts_one_that_refused
F
======================================================================
FAIL: test_the_notarisation_guard_refuses_a_build_that_succeeded_and_accepts_one_that_refused (test_publish_guards.CredentialGuardTests.test_the_notarisation_guard_refuses_a_build_that_succeeded_and_accepts_one_that_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christerry/projects/kimicode/scratch/ct21/tests/test_publish_guards.py", line 626, in test_the_notarisation_guard_refuses_a_build_that_succeeded_and_accepts_one_that_refused
    self.assertEqual(
AssertionError: '' != 'RELEASE=1 built without a notarisation credential; that must not happen.'
+ RELEASE=1 built without a notarisation credential; that must not happen.
 : the step must refuse by name, with the message the gate produces

----------------------------------------------------------------------
Ran 1 test in 0.025s

FAILED (failures=1)
[exit status: 1]
RESULT: the named test went RED as required.
restore: the workflow file is byte-identical to the fixed copy

$ PYTHONPATH=tests python -m unittest test_publish_guards.CredentialGuardTests.test_the_notarisation_guard_refuses_a_build_that_succeeded_and_accepts_one_that_refused
.
----------------------------------------------------------------------
Ran 1 test in 0.027s

OK
[exit status: 0]
RESULT: the named test is GREEN again after the restore.

--- CM-35: the release-key signing guard ------------------------
break: the 'no release key' refusal in the signing step replaced by 'if false:'

$ PYTHONPATH=tests python -m unittest test_publish_guards.CredentialGuardTests.test_the_release_key_guard_refuses_a_publish_without_a_key_and_signs_with_one
F
======================================================================
FAIL: test_the_release_key_guard_refuses_a_publish_without_a_key_and_signs_with_one (test_publish_guards.CredentialGuardTests.test_the_release_key_guard_refuses_a_publish_without_a_key_and_signs_with_one)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christerry/projects/kimicode/scratch/ct21/tests/test_publish_guards.py", line 681, in test_the_release_key_guard_refuses_a_publish_without_a_key_and_signs_with_one
    self.assertNotEqual(
AssertionError: 0 == 0 : a publish with no release key must not continue

----------------------------------------------------------------------
Ran 1 test in 0.028s

FAILED (failures=1)
[exit status: 1]
RESULT: the named test went RED as required.
restore: the workflow file is byte-identical to the fixed copy

$ PYTHONPATH=tests python -m unittest test_publish_guards.CredentialGuardTests.test_the_release_key_guard_refuses_a_publish_without_a_key_and_signs_with_one
.
----------------------------------------------------------------------
Ran 1 test in 0.027s

OK
[exit status: 0]
RESULT: the named test is GREEN again after the restore.

--- CM-36: the retired-connection guard -------------------------
break: the retired-connection guard was removed from the request handler

$ PYTHONPATH=tests python -m unittest test_gui_integration.RetiredConnectionGuardTests.test_a_retired_connection_is_closed_without_an_answer
F
======================================================================
FAIL: test_a_retired_connection_is_closed_without_an_answer (test_gui_integration.RetiredConnectionGuardTests.test_a_retired_connection_is_closed_without_an_answer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christerry/projects/kimicode/scratch/ct21/tests/test_gui_integration.py", line 1095, in test_a_retired_connection_is_closed_without_an_answer
    self.assertEqual(data, b"", "a retired connection must not answer")
AssertionError: b'<!DOCTYPE HTML>\n<html lang="en">\n    <h[344 chars]l>\n' != b'' : a retired connection must not answer

----------------------------------------------------------------------
Ran 1 test in 0.004s

FAILED (failures=1)
[exit status: 1]
RESULT: the named test went RED as required.
restore: gui.py is byte-identical to the fixed copy

$ PYTHONPATH=tests python -m unittest test_gui_integration.RetiredConnectionGuardTests.test_a_retired_connection_is_closed_without_an_answer
.
----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
[exit status: 0]
RESULT: the named test is GREEN again after the restore.

--- CM-37a: a complete head claims the slot, token or not -------
break: the busy claim now also requires the page's token, so a tokenless complete head claims no slot

$ PYTHONPATH=tests python -m unittest test_gui_integration.SlotClaimSemanticsTests.test_a_complete_request_head_claims_the_slot_without_the_token
F
======================================================================
FAIL: test_a_complete_request_head_claims_the_slot_without_the_token (test_gui_integration.SlotClaimSemanticsTests.test_a_complete_request_head_claims_the_slot_without_the_token)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christerry/projects/kimicode/scratch/ct21/tests/test_gui_integration.py", line 1000, in test_a_complete_request_head_claims_the_slot_without_the_token
    self.assertEqual(
AssertionError: Lists differ: [False] != [True]

First differing element 0:
False
True

- [False]
+ [True] : a complete request head must claim the slot before any route looks at the token

----------------------------------------------------------------------
Ran 1 test in 0.004s

FAILED (failures=1)
[exit status: 1]
RESULT: the named test went RED as required.
restore: gui.py is byte-identical to the fixed copy

$ PYTHONPATH=tests python -m unittest test_gui_integration.SlotClaimSemanticsTests.test_a_complete_request_head_claims_the_slot_without_the_token
.
----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
[exit status: 0]
RESULT: the named test is GREEN again after the restore.

--- CM-37b: a half-sent head claims no slot ---------------------
break: an admitted connection was put straight into the busy set, so a silent or half-sent connection claims a slot

$ PYTHONPATH=tests python -m unittest test_gui_integration.SlotClaimSemanticsTests.test_a_half_sent_request_head_claims_no_slot
F
======================================================================
FAIL: test_a_half_sent_request_head_claims_no_slot (test_gui_integration.SlotClaimSemanticsTests.test_a_half_sent_request_head_claims_no_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christerry/projects/kimicode/scratch/ct21/tests/test_gui_integration.py", line 1032, in test_a_half_sent_request_head_claims_no_slot
    self.assertNotIn(
AssertionError: <socket.socket fd=6, family=1, type=1, proto=0> unexpectedly found in {<socket.socket fd=6, family=1, type=1, proto=0>} : a half-sent head must not claim a busy slot

----------------------------------------------------------------------
Ran 1 test in 0.211s

FAILED (failures=1)
[exit status: 1]
RESULT: the named test went RED as required.
restore: gui.py is byte-identical to the fixed copy

$ PYTHONPATH=tests python -m unittest test_gui_integration.SlotClaimSemanticsTests.test_a_half_sent_request_head_claims_no_slot
.
----------------------------------------------------------------------
Ran 1 test in 0.208s

OK
[exit status: 0]
RESULT: the named test is GREEN again after the restore.

--- CT-20: the scanned set includes the release workflow --------
break: '.github/workflows/*.yml' was removed from SHIPPED, narrowing the scanned set back to the pre-v0.7.1 files

$ PYTHONPATH=tests python -m unittest test_controls_inventory.ControlInventoryTests.test_the_release_workflow_files_are_scanned
F
======================================================================
FAIL: test_the_release_workflow_files_are_scanned (test_controls_inventory.ControlInventoryTests.test_the_release_workflow_files_are_scanned)
CT-20: a claim in the release workflow is tracked, not invisible.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/christerry/projects/kimicode/scratch/ct21/tests/test_controls_inventory.py", line 235, in test_the_release_workflow_files_are_scanned
    self.assertIn(
AssertionError: '.github/workflows/*.yml' not found in ('*.py', 'scripts/*.py', 'scripts/*.sh', 'scripts/*.ps1') : the release workflow file class must stay in the scanned set

----------------------------------------------------------------------
Ran 1 test in 0.005s

FAILED (failures=1)
[exit status: 1]
RESULT: the named test went RED as required.
restore: the inventory test is byte-identical to the fixed copy

$ PYTHONPATH=tests python -m unittest test_controls_inventory.ControlInventoryTests.test_the_release_workflow_files_are_scanned
.
----------------------------------------------------------------------
Ran 1 test in 0.011s

OK
[exit status: 0]
RESULT: the named test is GREEN again after the restore.

--- summary: the restored copy -----------------------------------
CM-33: fixed copy GREEN.
CM-34: fixed copy GREEN.
CM-35: fixed copy GREEN.
CM-36: fixed copy GREEN.
CM-37a: fixed copy GREEN.
CM-37b: fixed copy GREEN.
CT-20: fixed copy GREEN.
================================================================
DONE
```
