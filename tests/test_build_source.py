"""Keep source archives limited to the project's explicit document allowlist."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class BuildSourceTests(unittest.TestCase):
    def test_worktree_only_markdown_files_are_not_archive_inputs(self):
        script = (ROOT / "scripts" / "build-source.sh").read_text(encoding="utf-8")
        self.assertIn("root_docs=(", script)
        self.assertIn('cp "${root_docs[@]}" LICENSE THIRD-PARTY-NOTICES.md', script)
        # CT-93 put the release public key on this loop as well; the point of the
        # pin is that the completeness loop reads the allowlist, not a file glob.
        self.assertIn(
            'for file in "${root_docs[@]}" LICENSE THIRD-PARTY-NOTICES.md signing-key.asc;',
            script)
        self.assertNotIn("for file in ./*.md", script)

    def test_the_archive_carries_what_its_own_tests_read(self):
        """The suite runs again inside the archive, so nothing it needs may be left out.

        The archive is extracted and the tests are re-run from inside it. A test that
        reads a file the archive did not copy fails there, and a missing reviewed
        native library fails the provenance check -- so the archive has to carry both
        libraries and both workflow recipes, in the shape the tests look for.
        """
        script = (ROOT / "scripts" / "build-source.sh").read_text(encoding="utf-8")
        for name in ("vendor/libusb-1.0.0.dylib", "vendor/libusb-1.0.dll",
                     "vendor/libusb-1.0.30.tar.bz2", "vendor/libusb-COPYING"):
            self.assertIn(name, script, f"the archive must ship {name}")
        self.assertIn("requirements-desktop-windows.lock", script)
        self.assertIn(
            "for recipe in build-candidate.yml windows-inputs.yml linux-inputs.yml",
            script, "the archive must ship the unified pipeline and both inputs recipes")
        self.assertIn('cp "$workflow" "$stage/$root/ci/$recipe"', script)


class ArchiveCompletenessTests(unittest.TestCase):
    """CT-56: a tarball that cannot rebuild the app is not a source tarball.

    Every assertion here targets the COPY, not the mention. A file named in a
    comment is still missing from the archive — the same defect the hwi.sha256
    pin had to be taught, where a test matched an echo while the write had been
    renamed away. Comments are dropped before anything is matched.
    """

    def setUp(self):
        self.script = (ROOT / "scripts" / "build-source.sh").read_text(encoding="utf-8")
        self.active = "\n".join(
            line for line in self.script.splitlines()
            if not line.lstrip().startswith("#")
        )

    def _root_docs(self) -> set[str]:
        match = re.search(r"root_docs=\((.*?)\)", self.script, re.DOTALL)
        self.assertIsNotNone(match, "build-source.sh has no root_docs=(...) allowlist")
        return set(match.group(1).split())

    def test_the_macos_entitlements_plist_reaches_the_archive(self):
        """build-macos.sh codesigns the HWI helper with it; without it a signed
        Mac build from the tarball fails at the codesign step."""
        self.assertTrue(
            (ROOT / "scripts" / "hwi-entitlements.plist").is_file(),
            "the plist this archive must ship does not exist in the tree")
        copies = [
            line for line in self.active.splitlines()
            if 'scripts/' in line and "$stage/$root/scripts/" in line
        ]
        self.assertTrue(copies, "build-source.sh copies nothing into scripts/")
        self.assertTrue(
            any("plist" in line for line in copies),
            "the scripts/ copy must carry *.plist; build-macos.sh passes "
            "scripts/hwi-entitlements.plist to codesign and a source archive "
            "without it cannot reproduce a signed Mac build",
        )
        self.assertIn(
            "hwi-entitlements.plist",
            (ROOT / "scripts" / "build-macos.sh").read_text(encoding="utf-8"),
            "build-macos.sh no longer uses the plist; revisit what the archive ships",
        )

    def test_the_linux_port_inputs_reach_the_archive(self):
        """LINUX-PORT.md and the Linux lock input are build records, not debris.

        The lock was already shipped; its input file and the port document were
        not, so an archive reader could not regenerate the lock or read the
        rules it was generated under.
        """
        docs = self._root_docs()
        for name in ("LINUX-PORT.md", "requirements-desktop-linux.txt"):
            with self.subTest(name=name):
                self.assertIn(name, docs,
                              f"{name} must be in root_docs so the archive ships "
                              f"it and the completeness loop checks it")
                self.assertTrue((ROOT / name).is_file(),
                                f"{name} is named in root_docs but missing from "
                                f"the working tree")

    def test_the_source_mode_lock_reaches_the_archive(self):
        """CT-92: the archive must carry the lock the source install path uses.

        `Start Easy Multisig.command` installs `--require-hashes -r
        requirements-source.lock`, and `tests/test_launcher.py` opens both the
        input and the lock from wherever the suite runs. A source tarball
        without them cannot build a working source install or pass its own
        suite, so both names must sit on the `cp` that carries the lock set.
        """
        self.assertIn('cp "${root_docs[@]}"', self.active,
                      "the requirement copy block moved; revisit this test")
        self.assertIn("requirements-source.txt requirements-source.lock",
                      self.active,
                      "the archive's copy must carry the source-mode lock and its "
                      "input; the launcher and the archive's own test suite read them")
        for name in ("requirements-source.txt", "requirements-source.lock"):
            with self.subTest(name=name):
                self.assertTrue((ROOT / name).is_file(),
                                f"{name} is named in the copy but missing from the tree")

    def test_the_release_public_key_reaches_the_archive(self):
        """CT-93: SIGNING.md tells a downloader to import the committed key.

        `SIGNING.md` and `RELEASE-PROCESS.md` both check `SHA256SUMS.asc`
        against the committed public key. A source archive without that key
        cannot run the verification those documents describe, so the file the
        instructions name has to be on the root copy — the tarball is where an
        archive-only reader runs them. This is the same defect class as the
        missing plist: a shipped document pointing at a file the archive does
        not contain.

        The filename is read out of SIGNING.md rather than written here twice,
        because the control is that the instruction and the archive agree. A
        first version only asked whether the string appeared anywhere in the
        script and in the document; the completeness loop names the key too, so
        deleting it from the copy line, or renaming it in the instruction, both
        sailed through the untouched half. Pin the pair, not the token.
        """
        signing = (ROOT / "SIGNING.md").read_text(encoding="utf-8")
        match = re.search(r"gpg --import (\S+)", signing)
        self.assertIsNotNone(
            match, "SIGNING.md no longer shows how to import the release key")
        key = match.group(1)
        self.assertTrue((ROOT / key).is_file(),
                        f"SIGNING.md tells a downloader to import {key}, which "
                        f"is not in the working tree")
        copy = re.search(r'cp "\$\{root_docs\[@\]\}".*?"\$stage/\$root/"',
                         self.active, re.DOTALL)
        self.assertIsNotNone(copy, "build-source.sh no longer has a root copy command")
        self.assertIn(key, copy.group(0),
                      f"the root copy must carry {key}; SIGNING.md tells an "
                      f"archive reader to import it and a tarball without it "
                      f"cannot check SHA256SUMS.asc")
        self.assertIn(key, (ROOT / "RELEASE-PROCESS.md").read_text(encoding="utf-8"),
                      "RELEASE-PROCESS.md no longer names the key the archive "
                      "ships; the agreement this test pins has moved")

    def test_the_header_comment_does_not_claim_the_plist_is_absent(self):
        """A comment that overclaims — or understates — a control is a finding.

        This header used to say the port "has neither" docs/ nor scripts/*.plist.
        The tree has carried the plist since the HWI hardened-runtime fix, so
        the comment was describing a decision the script had already reversed.

        The negative half is matched case-insensitively and against more than
        one phrasing on purpose: a first version looked for the exact sentence
        "the port has neither", and a break that capitalized the T sailed
        straight through it. Pin the claim, not one spelling of it.
        """
        lowered = self.script.lower()
        for phrase in ("has neither", "those lines are gone", "the port has not"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(
                    phrase, lowered,
                    f"build-source.sh's header claims scripts/*.plist is absent "
                    f"({phrase!r}); it is present and required for a signed Mac build")
        self.assertIn("hwi-entitlements.plist", self.script,
                      "the header must name the plist it now ships and why")
        self.assertRegex(
            self.script,
            r"(?is)does\s+not\s+(?:#\s*)?exclude\s+scripts/\*\.plist",
            "the header must state affirmatively that the plist ships, not "
            "merely avoid the false claim",
        )

    def test_every_local_helper_the_shipped_tests_import_is_shipped(self):
        """A test module whose helper the archive left out cannot run there.

        The suite runs again from inside the archive. CT-86 found this the hard
        way: tests/workflow_harness.py was added to tests/ and never added to the
        copy line, so `unittest discover` inside the archive could not import
        test_workflow_config or test_publish_guards -- 525 tests run, 2 errors,
        while the repository's own suite stayed green. A helper that is imported
        by a shipped test module has to travel with it.
        """
        match = re.search(r"cp tests/.*?\"\$stage/\$root/tests/\"", self.active, re.DOTALL)
        self.assertIsNotNone(
            match, "build-source.sh no longer copies anything into tests/")
        copy = match.group(0)
        self.assertIn(
            "tests/test_*.py", copy,
            "every test module must travel, and the glob is what keeps a newly "
            "added test_*.py from being left behind")

        helpers = {path.stem for path in (ROOT / "tests").glob("*.py")
                   if not path.name.startswith("test_")}
        imports = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
        needed: set[str] = set()
        for path in sorted((ROOT / "tests").glob("test_*.py")):
            for name in imports.findall(path.read_text(encoding="utf-8")):
                if name in helpers:
                    needed.add(name)
        self.assertIn("workflow_harness", needed,
                      "no shipped test module imports tests/workflow_harness.py; "
                      "if that helper is gone, delete this pin deliberately")
        for name in sorted(needed):
            with self.subTest(module=name):
                self.assertIn(
                    f"{name}.py", copy,
                    f"tests/{name}.py is imported by a shipped test module and "
                    f"must be in the tests/ copy, or the archive's own suite "
                    f"cannot import the module that needs it")

    def test_the_completeness_loop_covers_the_new_inputs(self):
        """The existing missing_docs loop must actually check what we just added.

        Adding a file to root_docs is only half the fix: the loop that reports a
        missing document reads the same array, and pinning that relationship is
        what stops the two drifting apart.
        """
        self.assertRegex(
            self.active,
            r'for file in "\$\{root_docs\[@\]\}"',
            "the completeness loop no longer iterates root_docs",
        )
        self.assertIn("missing_docs", self.script)


if __name__ == "__main__":
    unittest.main()
