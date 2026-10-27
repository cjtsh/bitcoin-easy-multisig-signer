"""The ledger is the backlog: every scheduled finding has exactly one closing row.

`releases/PATCH-0.7.5.md` is where a finding stops being open. Nothing read the file
when this test was written, and the cost was concrete: the 0.6.8 ledger held six rows
for the twenty-six findings its plan scheduled, so twenty were closed by silence —
eighteen of them already fixed and committed, two deliberately deferred but
unrecorded. A fix a reader cannot find is a fix that did not happen.

The plan is the schedule, the ledger is the record, and this test holds the two to each
other: the same finding ids on both sides, one row each, a severity on every row, and a
closing test the reader can actually load. The only rows allowed to cite nothing are the
deferrals the plan itself makes (pinned below), so "no test" has to be a deliberate,
reviewable act rather than an omission.

It reads text, so it cannot see whether a cited test is *good* — only that it exists and
runs. That is the same limit `tests/test_controls_inventory.py` has, and it is the right
one: the file's job is to make silence impossible, not to grade the evidence.
"""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "releases" / "PLAN-0.7.5.md"
LEDGER = ROOT / "releases" / "PATCH-0.7.5.md"

# The plan's work-order rows: `| W1 | CT-72 | High | … |`, and rows that schedule two
# findings (`| W2 | CT-76, CT-77 | High | … |`).
WORK_ORDER = re.compile(r"^\|\s*W\d+\s*\|\s*((?:CT-\d+\s*,\s*)*CT-\d+)\s*\|", re.M)

# A ledger row begins `| CT-## |` and holds four cells: id, severity, fix, evidence.
ROW_START = re.compile(r"^\|\s*(CT-\d+)\s*\|")

# `tests/test_x.py::Class` or `tests/test_x.py::Class::method` — the backticks are
# optional because the ledger writes both forms.
CITED = re.compile(
    r"`?(tests/[A-Za-z0-9_]+\.py)::([A-Za-z_][A-Za-z0-9_]*)(?:::([A-Za-z_][A-Za-z0-9_]*))?`?"
)

SEVERITIES = ("High", "Med", "Low", "Info")

# Findings the plan schedules but deliberately does not fix in this cycle, with the
# reason. Adding an id here is the reviewable act that lets a row cite no test.
#
# 0.7.5 defers nothing: all five scheduled work orders close with a test, so this
# is empty on purpose. The audit's three housekeeping notes (CT-32, the previous
# plan's stale line citations; CT-34, `explorer_get`'s truncated-body contract,
# which the callers already fail closed on; and CT-35, the five failed candidate
# attempts in the previous release window) are recorded in the plan's §6 and in the
# ledger's "Observations recorded" section rather than scheduled: none changes
# behaviour, so none can have a closing test, and scheduling them would have made
# this set the place where that is hidden instead of the place where it is written
# down. The 0.6.8 pair this set used to hold (CT-90, the second practice-network
# oracle that needs an owner policy decision; CT-54, the libusb dylib rebuilt at
# the next dependency bump) were resolved in the 0.6.8 cycle, and the 0.7.0, 0.7.1
# and 0.7.2 cycles deferred nothing either. An empty set here is a claim the next
# cycle has to re-earn, not a default.
NO_TEST = set()


def cells(line):
    """Split a markdown table row on unescaped pipes, dropping the edge empties."""
    parts = re.split(r"(?<!\\)\|", line)
    return [part.strip() for part in parts[1:-1]]


def ledger_rows(text):
    """id -> (severity, fix, evidence) for every `| CT-## |` table row."""
    rows = {}
    for line in text.splitlines():
        match = ROW_START.match(line)
        if not match:
            continue
        fields = cells(line)
        if len(fields) < 4:
            continue
        identifier = match.group(1)
        rows.setdefault(identifier, []).append(tuple(fields[1:4]))
    return rows


def scheduled_findings(text):
    identifiers = []
    for match in WORK_ORDER.finditer(text):
        identifiers.extend(part.strip() for part in match.group(1).split(","))
    return identifiers


def cited_tests(row):
    text = row[1] + "\n" + row[2]
    return [match.group(0).strip("`") for match in CITED.finditer(text)]


def dotted_name(citation):
    path, _, rest = citation.partition("::")
    module = Path(path).stem
    return module + "." + rest.replace("::", ".")


class LedgerCompletenessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in (PLAN, LEDGER):
            if not path.is_file():
                raise AssertionError("%s is missing" % path.relative_to(ROOT))
        cls.plan = PLAN.read_text(encoding="utf-8")
        cls.ledger = LEDGER.read_text(encoding="utf-8")
        cls.scheduled = scheduled_findings(cls.plan)
        cls.entries = ledger_rows(cls.ledger)
        cls.rows = {rid: entries[0] for rid, entries in cls.entries.items()}
        cls.citations = {rid: cited_tests(row) for rid, row in cls.rows.items()}
        if str(ROOT / "tests") not in sys.path:
            sys.path.insert(0, str(ROOT / "tests"))
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))

    def test_the_plan_and_the_ledger_name_the_same_findings(self):
        scheduled = set(self.scheduled)
        recorded = set(self.rows)
        missing = sorted(scheduled - recorded, key=lambda item: int(item.split("-")[1]))
        orphaned = sorted(recorded - scheduled, key=lambda item: int(item.split("-")[1]))
        self.assertEqual(
            (missing, orphaned),
            ([], []),
            "the plan schedules findings the ledger does not close: %s; the ledger holds "
            "rows the plan does not schedule: %s" % (missing, orphaned),
        )

    def test_no_finding_is_recorded_twice(self):
        duplicates = sorted(
            rid for rid, entries in self.entries.items() if len(entries) != 1
        )
        self.assertEqual(
            duplicates, [], "more than one ledger row for %s" % duplicates
        )

    def test_every_row_states_a_severity(self):
        bad = {
            rid: row[0]
            for rid, row in self.rows.items()
            if row[0].split()[0] not in SEVERITIES
        }
        self.assertEqual(bad, {}, "rows with no recognised severity: %s" % bad)

    def test_every_row_states_a_fix_and_a_closing_evidence_cell(self):
        bad = [
            rid for rid, row in self.rows.items() if not row[1] or not row[2]
        ]
        self.assertEqual(
            bad, [], "rows missing a fix or a closing-evidence cell: %s" % bad
        )

    def test_every_row_cites_a_closing_test_unless_it_is_pinned_as_deferred(self):
        silent = {rid for rid, cited in self.citations.items() if not cited}
        self.assertEqual(
            silent,
            NO_TEST,
            "rows citing no test: %s; pinned as deferred without one: %s — a finding "
            "that is neither may not close silently" % (sorted(silent), sorted(NO_TEST)),
        )

    def test_every_cited_closing_test_loads(self):
        from support import missing_test_reason

        broken = {}
        for rid, citations in sorted(
            self.citations.items(), key=lambda item: int(item[0].split("-")[1])
        ):
            for citation in citations:
                reason = missing_test_reason(dotted_name(citation))
                if reason is not None:
                    broken.setdefault(rid, []).append(reason)
        self.assertEqual(
            broken, {}, "rows citing a test that does not exist or does not load: %s" % broken
        )


if __name__ == "__main__":
    unittest.main()
