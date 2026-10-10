"""The source-mode launcher and the lock it installs must agree.

The launcher skips the hash-verified install only while the venv already holds
the exact pinned build of *both* libraries the app uses: the vendored embit and
the hardware-wallet library. If either guard drifts from
`requirements-source.lock`, a stale public-registry copy passes it — audit
finding CT-04. If the lock itself loses the device library, the launcher
installs a set that cannot reach a signer at all — CT-92, where the guard looked
only at embit, so an environment created before the device library was needed
skipped the install forever and the user saw "Install hwi 3.2.0" with no
command that would do it.

The source set is not resolved from scratch: it is compiled through the reviewed
desktop lock, so source mode and the released bundle cannot run two different
builds of the same library. `test_every_source_entry_matches_the_reviewed_desktop_lock`
is what holds that.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE_LOCK = "requirements-source.lock"
DESKTOP_LOCK = "requirements-desktop.lock"

# The closure `hwi` actually needs, not just the six entries pip-compile's
# `# via hwi` lines name. A dependency added to this set is an edit here too,
# which is the point: a new source-mode package gets read before it ships.
EXPECTED_SOURCE_PACKAGES = {
    "cbor2", "certifi", "cffi", "charset-normalizer", "cryptography", "ecdsa",
    "embit", "hidapi", "hwi", "idna", "libusb1", "mnemonic", "noiseprotocol",
    "protobuf", "pyaes", "pycparser", "pyserial", "requests", "semver", "six",
    "typing-extensions", "urllib3",
}

# A wheel filename: distribution, version, then the build tags. The version may
# not contain a hyphen (the wheel spec escapes those as underscores), which is
# what makes the second field unambiguous.
WHEEL = re.compile(r"^(?P<name>[A-Za-z0-9_.]+)-(?P<version>[^-]+)-")
ENTRY = re.compile(r"^(?P<name>[A-Za-z0-9_.+-]+)==(?P<version>\S+)\s*\\?$")
HASH = re.compile(r"--hash=sha256:([0-9a-f]{64})")
JOINED_LITERALS = re.compile(r'"\s*\n\s*"')


def canonical(name: str) -> str:
    """PEP 503 spelling, so `typing_extensions` and `typing-extensions` agree."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_lock(path: Path) -> dict[str, dict]:
    """Read a pip-compile `--generate-hashes` lock into {name: entry}.

    Each entry is `{"version": ..., "hashes": set}`. Only column-zero lines open
    an entry; the hash and `# via` continuations are indented, which is what
    keeps `--hash=` out of a version string.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: dict[str, dict] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line or line[0].isspace() or line.startswith("#"):
            continue
        match = ENTRY.match(line)
        if match:
            name, version = match.group("name"), match.group("version")
        elif line.startswith(("file:", "http")):
            wheel = WHEEL.match(line.rstrip("\\").strip().rsplit("/", 1)[-1])
            if not wheel:
                raise AssertionError(f"{path.name}: unreadable requirement {line!r}")
            name, version = wheel.group("name"), wheel.group("version")
        else:
            raise AssertionError(f"{path.name}: unreadable lock line {line!r}")
        entry = {"version": version, "hashes": set()}
        entries[canonical(name)] = entry
        while index < len(lines) and (not lines[index] or lines[index][0].isspace()):
            found = HASH.search(lines[index])
            if found:
                entry["hashes"].add(found.group(1))
            index += 1
    return entries


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.launcher = (ROOT / "Start Easy Multisig.command").read_text(encoding="utf-8")
        self.source = parse_lock(ROOT / SOURCE_LOCK)

    def test_embit_guard_matches_the_locked_version(self):
        expected = self.source["embit"]["version"]
        self.assertIn(f'm.version("embit") == "{expected}"', self.launcher)

    def test_hwi_guard_matches_the_locked_pin(self):
        expected = self.source["hwi"]["version"]
        self.assertIn(f'm.version("hwi") == "{expected}"', self.launcher)

    def test_both_guards_guard_the_one_hash_verified_install(self):
        """The device-library guard has to be in the same condition as embit's.

        A second, separate `if` after the install would still work; a guard that
        is merely *near* the install is what CT-92 found, so pin the structure:
        one install command, both version checks inside the condition that
        reaches it.
        """
        install = ("--disable-pip-version-check --require-hashes "
                   "-r requirements-source.lock")
        self.assertEqual(self.launcher.count(install), 1,
                         "the launcher must install the source lock exactly once")
        self.assertNotIn("-r requirements.lock", self.launcher,
                         "the launcher installs the source set, not the test set")
        condition = (self.launcher[:self.launcher.index(install)]
                     .rsplit("if !", 1)[1].split("; then", 1)[0])
        self.assertIn('m.version("embit")', condition)
        self.assertIn('m.version("hwi")', condition)

    def test_the_guards_read_metadata_and_never_import_the_package(self):
        """`probe.py` hashes the installed hwilib and refuses a substituted copy.

        The launcher must not be the process that executes the package first, so
        both checks read distribution metadata only — no `import hwilib`.
        """
        for name in ("embit", "hwi"):
            self.assertIn(
                f'import importlib.metadata as m; raise SystemExit(0 if '
                f'm.version("{name}")', self.launcher,
                f"the {name} guard must read metadata, not import the package")


class SourceLockTests(unittest.TestCase):
    def test_the_device_library_is_pinned_with_hashes(self):
        source = parse_lock(ROOT / SOURCE_LOCK)
        for name in ("hwi", "libusb1", "hidapi"):
            self.assertIn(name, source, f"{SOURCE_LOCK} must ship {name}")
        for name, entry in source.items():
            self.assertTrue(entry["hashes"],
                            f"{name} has no --hash in {SOURCE_LOCK}; "
                            f"`--require-hashes` cannot verify it")
        self.assertEqual(source["hwi"]["version"], "3.2.0")

    def test_the_source_set_is_the_expected_closure(self):
        self.assertEqual(set(parse_lock(ROOT / SOURCE_LOCK)), EXPECTED_SOURCE_PACKAGES)

    def test_every_source_entry_matches_the_reviewed_desktop_lock(self):
        source = parse_lock(ROOT / SOURCE_LOCK)
        desktop = parse_lock(ROOT / DESKTOP_LOCK)
        for name, entry in source.items():
            with self.subTest(package=name):
                self.assertIn(name, desktop,
                              f"{name} is in the source lock but not the reviewed "
                              f"desktop lock")
                self.assertEqual(entry["version"], desktop[name]["version"])
                self.assertEqual(entry["hashes"], desktop[name]["hashes"],
                                 f"{name} resolves to a different artifact than the "
                                 f"released app installs")
        self.assertLess(len(source), len(desktop),
                        "the source set is meant to be the desktop set minus the "
                        "app-only packages; an equal size means one of them changed")


class DocumentedInstallPathTests(unittest.TestCase):
    def test_the_refusal_names_the_command_that_installs_the_library(self):
        """A user who is told to install HWI needs a command that works.

        The literal in `probe.py` is written across two source lines, so join
        adjacent implicit-concatenation literals before matching; matching the
        module's source is the only way to pin what the operator actually reads.
        """
        probe = (ROOT / "probe.py").read_text(encoding="utf-8")
        flat = JOINED_LITERALS.sub("", probe)
        self.assertIn("python -m pip install --require-hashes -r "
                      "requirements-source.lock", flat,
                      "the device refusal must name the exact install command")
        self.assertIn("EXPECTED_HWI_VERSION", flat)

    def test_every_install_path_names_the_source_lock(self):
        for name in ("Start Easy Multisig.command", "probe.py", "README.md",
                     "HWI-DEPENDENCY.md"):
            with self.subTest(document=name):
                self.assertIn(SOURCE_LOCK,
                              (ROOT / name).read_text(encoding="utf-8"),
                              f"{name} must name {SOURCE_LOCK}")


if __name__ == "__main__":
    unittest.main()
