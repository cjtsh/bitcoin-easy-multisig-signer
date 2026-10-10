"""The control inventory is a checked document, not a claim about itself.

`CONTROLS.md` lists the security controls this project relies on, the code that
makes each claim, and the test that would go red if the claim stopped being
true. A document like that rots the moment it is written unless something reads
it, so this module reads it five ways:

* every row's `Where` names a file in the tree and a line, or range, inside it;
* every row's `Test` names a test the loader can actually load, so a renamed or
  deleted test breaks the inventory rather than quietly emptying a row;
* every `CONTROL: CM-##` marker in shipped code has a row for that id citing
  the same file, so a marker cannot outlive its entry or drift to another file;
* every comment block that *claims* a control (it uses one of the pinned
  phrases) must say `CONTROL: CM-##` or point at `CONTROLS.md`, so a new claim
  cannot arrive without an entry;
* every block that points at `CONTROLS.md` must be cited by a row of either
  table, so the pointer is not a substitute for the entry.

The phrase list is deliberately short and pinned here rather than inferred:
inventing categories at scan time would make the scan unfalsifiable.
"""

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "CONTROLS.md"

SHIPPED = (
    "*.py",
    "scripts/*.py",
    "scripts/*.sh",
    "scripts/*.ps1",
)

# A sentence that claims a protection. A comment block that claims one of these
# has to say which control it is, or say that no control is claimed.
PHRASES = (
    "fail closed",
    "fails closed",
    "refused rather than believed",
    "is not trusted",
    "cannot be bypassed",
    "poisoned",
    "a claim rather than a control",
    "never believed",
    "claims to",
)

ROW = re.compile(r"^\|\s*(CM-\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|\s*$", re.M)
NOTE = re.compile(r"^\|\s*(`[^|`]+`)\s*\|([^|]*)\|\s*$", re.M)
WHERE = re.compile(r"`([^`:]+?):(\d+)(?:-(\d+))?`")
MARKER = re.compile(r"CONTROL:\s*(CM-\d+)")
TEST_ID = re.compile(
    r"`(tests/([A-Za-z0-9_]+)\.py)::([A-Za-z_][A-Za-z0-9_]*)"
    r"::([A-Za-z_][A-Za-z0-9_]*)`"
)


def site(text):
    """Return (relative path, first line, last line) from a backticked cell."""
    match = WHERE.search(text)
    if match is None:
        return None
    relative, first, last = match.groups()
    return relative, int(first), int(last or first)


def cited_file(relative, root=ROOT):
    """The file a row cites, from the checkout or from an extracted archive.

    The rows cite the canonical recipe as
    ``.github/workflows/build-candidate.yml``. A source archive is a source
    tree: ``scripts/build-source.sh`` ships that recipe as
    ``ci/build-candidate.yml``, so a raw ``ROOT / relative`` lookup reports a
    missing file there. 0.6.6 caught ``PipToolsPinTests`` making this mistake,
    0.6.7 caught ``ToolchainPinTests``, and the 0.6.8 candidate run (38082865187)
    caught this inventory making it a third time. Every pin that reads a recipe
    goes through ``support.find_build_recipe``.
    """
    path = root / relative
    if path.is_file():
        return path
    parts = pathlib.PurePosixPath(relative).parts
    if len(parts) == 3 and parts[:2] == (".github", "workflows"):
        sys.path.insert(0, str(root / "tests"))
        from support import find_build_recipe

        return find_build_recipe(root, parts[2])
    return None


def comment_blocks(path):
    """Yield (first_line, last_line, text) for each comment block in `path`.

    A block is a run of full-line comments, or one trailing comment. The text
    is whitespace-normalized so a phrase is found however the line wraps.
    """
    blocks = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = None
    current = []

    for number, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            if start is None:
                start = number
            current.append(stripped.lstrip("#").strip())
            continue
        if current:
            blocks.append(
                (start + 1, number, re.sub(r"\s+", " ", " ".join(current))))
            start, current = None, []
        inline = re.search(r"\s#\s?(.*)$", line)
        if inline:
            blocks.append((number + 1, number + 1, re.sub(r"\s+", " ", inline.group(1))))
    if current:
        blocks.append((start + 1, len(lines), re.sub(r"\s+", " ", " ".join(current))))
    return blocks


class ControlInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not INVENTORY.is_file():
            raise AssertionError("CONTROLS.md is missing")
        cls.text = INVENTORY.read_text(encoding="utf-8")
        cls.rows = [
            {
                "id": match.group(1).strip(),
                "claim": match.group(2).strip(),
                "where": match.group(3).strip(),
                "test": match.group(4).strip(),
            }
            for match in ROW.finditer(cls.text)
        ]
        cls.notes = [
            {"where": match.group(1).strip(), "why": match.group(2).strip()}
            for match in NOTE.finditer(cls.text)
        ]
        cls.blocks = []
        for pattern in SHIPPED:
            for path in sorted(ROOT.glob(pattern)):
                for first, last, text in comment_blocks(path):
                    cls.blocks.append((path, first, last, text))

    def _cited(self, relative, first, last):
        """True when a row of either table cites a line inside this block."""
        for cell in [row["where"] for row in self.rows] + [note["where"] for note in self.notes]:
            parsed = site(cell)
            if parsed is None:
                continue
            cited_path, cited_first, cited_last = parsed
            if cited_path == relative and cited_first <= last and first <= cited_last:
                return True
        return False

    def test_the_inventory_has_rows(self):
        self.assertTrue(self.rows, "CONTROLS.md lists no controls")

    def test_every_id_is_unique(self):
        ids = [row["id"] for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)), "a control id is listed twice")

    def test_every_row_names_code_that_exists(self):
        for row in self.rows + [{"id": note["where"], **note} for note in self.notes]:
            with self.subTest(control=row["id"]):
                parsed = site(row["where"])
                self.assertIsNotNone(
                    parsed, f"{row['id']} does not cite a `file:line` in backticks")
                relative, first, last = parsed
                path = cited_file(relative)
                self.assertIsNotNone(path, f"{row['id']} cites missing {relative}")
                count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
                self.assertLessEqual(
                    last, count,
                    f"{row['id']} cites line {last} of {relative}, which has {count}")

    def test_every_row_names_a_test_that_loads(self):
        sys.path.insert(0, str(ROOT / "tests"))
        from support import missing_test_reason

        for row in self.rows:
            with self.subTest(control=row["id"]):
                match = TEST_ID.search(row["test"])
                self.assertIsNotNone(
                    match, f"{row['id']} does not cite a tests/...py::Class::method")
                module, stem, klass, method = match.groups()
                self.assertTrue((ROOT / module).is_file(), f"{row['id']} cites missing {module}")
                reason = missing_test_reason(f"{stem}.{klass}.{method}")
                self.assertIsNone(
                    reason,
                    f"{row['id']} cites {module}::{klass}::{method}, which does not load: {reason}")

    def test_every_marker_has_a_row_in_the_same_file(self):
        for path, first, last, text in self.blocks:
            for control in MARKER.findall(text):
                relative = path.relative_to(ROOT).as_posix()
                with self.subTest(marker=f"{relative}:{first} {control}"):
                    self.assertTrue(
                        any(row["id"] == control
                            and (site(row["where"]) or ("", 0, 0))[0] == relative
                            for row in self.rows),
                        f"{relative}:{first} marks {control}, which has no row citing {relative}")

    def test_a_claim_comment_points_at_the_inventory(self):
        for path, first, last, text in self.blocks:
            if not any(phrase in text.lower() for phrase in PHRASES):
                continue
            with self.subTest(comment=f"{path.name}:{first}"):
                self.assertTrue(
                    MARKER.search(text) or "CONTROLS.md" in text,
                    f"{path.relative_to(ROOT)}:{first} claims a control but names no "
                    f"entry: add `CONTROL: CM-##` or cite CONTROLS.md\n  {text[:200]}")

    def test_a_pointer_to_the_inventory_is_cited(self):
        for path, first, last, text in self.blocks:
            if "CONTROLS.md" not in text:
                continue
            relative = path.relative_to(ROOT).as_posix()
            with self.subTest(comment=f"{relative}:{first}"):
                self.assertTrue(
                    self._cited(relative, first, last),
                    f"{relative}:{first} points at CONTROLS.md, so a row of either "
                    f"table must cite that block\n  {text[:200]}")

    def test_the_release_process_names_the_inventory(self):
        process = (ROOT / "RELEASE-PROCESS.md").read_text(encoding="utf-8")
        self.assertIn("CONTROLS.md", process, "RELEASE-PROCESS.md does not name CONTROLS.md")


if __name__ == "__main__":
    unittest.main()
