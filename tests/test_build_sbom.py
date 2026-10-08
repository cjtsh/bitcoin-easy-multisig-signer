"""The release dependency inventory must be parseable and identify its inputs."""

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("build_sbom", ROOT / "scripts" / "build-sbom.py")
build_sbom = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_sbom)


class BuildSbomTests(unittest.TestCase):
    def test_inventory_names_lock_commit_and_native_digest(self):
        digest = "a" * 64
        # The native library names and the lock file differ per platform; the
        # module is the one authority on both.
        names = build_sbom.native_library_names()
        shipped = {name: chr(ord("b") + index) * 64
                   for index, name in enumerate(names)}
        result = build_sbom.build(digest, ROOT, {"embit", "hwi"}, shipped,
                                  helper_sha="c" * 64)
        self.assertEqual(result["bomFormat"], "CycloneDX")
        self.assertEqual(result["specVersion"], "1.6")
        components = {component["name"]: component
                      for component in result["components"]}
        for name in names:
            self.assertEqual(components[name]["hashes"][0]["content"], shipped[name])
        self.assertEqual(components["cpython"]["version"], sys.version.split()[0])
        self.assertIn("embit", components)
        self.assertEqual(
            components["embit"]["hashes"],
            [{"alg": "SHA-256",
              "content": hashlib.sha256(
                  (ROOT / build_sbom.EMBIT_WHEEL).read_bytes()).hexdigest()}],
        )
        self.assertIn("symbolic", components["embit"]["properties"][0]["value"])
        self.assertNotIn("pip", components)
        properties = {entry["name"]: entry["value"]
                      for entry in result["metadata"]["properties"]}
        self.assertEqual(properties["requirements_desktop_sha256"],
                         hashlib.sha256((ROOT / build_sbom.LOCK_FILE)
                                        .read_bytes()).hexdigest())
        self.assertEqual(properties["libusb_input_sha256"], digest)
        self.assertEqual(properties["hwi_helper_sha256"], "c" * 64)


class HelperDigestPins(unittest.TestCase):
    """CT-49: the helper's digest is recorded and checked, not assumed.

    probe.py refuses to run a helper whose bytes disagree with the hwi.sha256
    beside it. The SBOM must publish the same digest, and must fail rather than
    publish when the sidecar is missing or wrong — an SBOM that disagrees with
    the artifact is worse than no SBOM.
    """

    def _tree(self, folder: str) -> Path:
        helper = Path(folder) / "hwi"
        helper.write_bytes(b"synthetic helper bytes\n")
        return helper

    def test_the_recorded_digest_is_the_helper_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._tree(folder)
            digest = hashlib.sha256(helper.read_bytes()).hexdigest()
            helper.with_name("hwi.sha256").write_text(f"{digest}  hwi\n")
            with patch.object(build_sbom, "frozen_helper", return_value=helper):
                self.assertEqual(build_sbom.helper_digest(ROOT), digest)

    def test_a_missing_sidecar_fails_rather_than_publishing_a_weaker_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._tree(folder)
            with patch.object(build_sbom, "frozen_helper", return_value=helper):
                with self.assertRaisesRegex(ValueError, "Missing hwi.sha256"):
                    build_sbom.helper_digest(ROOT)

    def test_a_disagreeing_sidecar_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            helper = self._tree(folder)
            helper.with_name("hwi.sha256").write_text("0" * 64 + "  hwi\n")
            with patch.object(build_sbom, "frozen_helper", return_value=helper):
                with self.assertRaisesRegex(ValueError, "does not match hwi"):
                    build_sbom.helper_digest(ROOT)

    def test_every_platform_build_writes_the_sidecar_into_the_signed_bundle(self):
        """The digest the app checks has to be produced by the build that ships.

        Pinned against the write, not the mention: an echo or a comment that
        says 'hwi.sha256' does not create the file, and a first version of this
        test went green while the write had been renamed away. Break-and-watch:
        rename the redirection target, watch this go red.
        """
        for name in ("build-macos.sh", "build-linux.sh", "build-windows.ps1"):
            with self.subTest(script=name):
                text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
                writes = [
                    line for line in text.splitlines()
                    if "hwi.sha256" in line
                    and not line.lstrip().startswith("#")
                    and (" > " in line or "Set-Content" in line)
                ]
                self.assertTrue(
                    writes,
                    f"{name} must redirect a digest into hwi.sha256; "
                    f"naming it in prose is not a write",
                )
                self.assertTrue(
                    any("CT-49" in line or "CT-49" in text for line in writes)
                    or "CT-49" in text,
                    f"{name} must say why it writes the sidecar",
                )

    def test_the_macos_sidecar_is_written_outside_contents_macos(self):
        """macOS reserves Contents/MacOS for executables.

        The 0.6.7 candidate recorded the digest beside the helper and codesign
        refused to seal the app: "code object is not signed at all / In
        subcomponent: .../Contents/MacOS/hwi.sha256". Contents/Resources is
        both legal and better -- the outer signature seals it into
        _CodeSignature/CodeResources, so editing the sidecar breaks the seal.
        """
        text = (ROOT / "scripts" / "build-macos.sh").read_text(encoding="utf-8")
        self.assertIn("Contents/Resources/hwi.sha256", text,
                      "build-macos.sh must record the helper digest in "
                      "Contents/Resources")
        self.assertNotIn("Contents/MacOS/hwi.sha256", text,
                         "a non-code file in Contents/MacOS breaks codesign; "
                         "the sidecar must not be written there")
        writes = [
            line for line in text.splitlines()
            if "hwi.sha256" in line
            and not line.lstrip().startswith("#")
            and " > " in line
        ]
        self.assertTrue(writes, "build-macos.sh must still write the sidecar")
        for line in writes:
            self.assertIn("Contents/Resources", line,
                          f"the sidecar write must target Contents/Resources: {line}")

    def test_the_sbom_reads_the_sidecar_from_the_place_the_app_checks(self):
        """build-sbom and probe must look in the same places.

        If they disagree, the SBOM publishes a digest for a file the app never
        reads, and a substituted helper is checked against nothing. Both accept
        the macOS Contents/Resources layout; both accept the beside-the-helper
        layout the other two platforms use.
        """
        import types

        sys.path.insert(0, str(ROOT))
        try:
            import probe
        finally:
            sys.path.pop(0)

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            macos = (root / "dist" / "Bitcoin Easy Signer.app" / "Contents" / "MacOS")
            resources = macos.parent / "Resources"
            macos.mkdir(parents=True)
            resources.mkdir(parents=True)
            helper = macos / "hwi"
            helper.write_bytes(b"synthetic helper bytes\n")
            digest = hashlib.sha256(helper.read_bytes()).hexdigest()
            (resources / "hwi.sha256").write_text(f"{digest}  hwi\n")

            with patch.object(build_sbom, "sys",
                              types.SimpleNamespace(platform="darwin")):
                self.assertEqual(build_sbom.helper_digest(root), digest)
            found = probe._hwi_sidecars(str(helper))
            self.assertEqual(found, [resources / "hwi.sha256"])

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            windows = root / "dist" / "Bitcoin Easy Signer"
            windows.mkdir(parents=True)
            helper = windows / "hwi.exe"
            helper.write_bytes(b"synthetic helper bytes\n")
            digest = hashlib.sha256(helper.read_bytes()).hexdigest()
            helper.with_name("hwi.sha256").write_text(f"{digest}  hwi\n")

            with patch.object(build_sbom, "sys",
                              types.SimpleNamespace(platform="win32")):
                self.assertEqual(build_sbom.helper_digest(root), digest)
            self.assertEqual(probe._hwi_sidecars(str(helper)),
                             [helper.with_name("hwi.sha256")])


class ToolchainDisclosurePins(unittest.TestCase):
    """CT-100: the toolchain a build used is recorded, not assumed.

    A hosted runner's image floats inside its pinned label (apt, MSVC, the
    Docker base, the tool cache), so no rebuild is bit-reproducible from this
    repository. The remedy that IS available here is disclosure: the SBOM that
    ships with, and is attested alongside, the assets must name the toolchain
    this build actually resolved, so a rebuild on a different one differs in a
    named field instead of in silence.
    """

    # CT-100: iterating TOOLCHAIN_PROBES proves only that the table agrees with
    # itself, so deleting a probe or renaming one stayed green while the SBOM
    # field silently disappeared. These names are literals, independent of the
    # source they describe.
    EXPECTED_PROBE_NAMES = (
        "toolchain_platform", "toolchain_python", "toolchain_cc",
        "toolchain_clang", "toolchain_msbuild", "toolchain_docker",
    )

    def _inventory(self):
        embedded = {name: "b" * 64 for name in build_sbom.native_library_names()}
        return build_sbom.build("a" * 64, ROOT, set(), embedded, helper_sha="c" * 64)

    def test_the_inventory_records_every_named_probe(self):
        with patch.object(build_sbom, "probe_toolchain",
                          side_effect=lambda argv: "banner of " + argv[0]):
            result = self._inventory()
        properties = {entry["name"]: entry["value"]
                      for entry in result["metadata"]["properties"]}
        self.assertEqual([name for name, _ in build_sbom.TOOLCHAIN_PROBES],
                         list(self.EXPECTED_PROBE_NAMES),
                         "the SBOM must carry exactly these toolchain fields")
        for name, argv in build_sbom.TOOLCHAIN_PROBES:
            self.assertEqual(properties[name], "banner of " + argv[0], name)
        for name in self.EXPECTED_PROBE_NAMES:
            self.assertIn(name, properties)

    def test_a_tool_that_is_not_installed_is_recorded_and_not_omitted(self):
        with patch.object(build_sbom.subprocess, "run",
                          side_effect=FileNotFoundError("no msbuild")):
            self.assertEqual(build_sbom.probe_toolchain(("msbuild", "-version")),
                             "not found")

    def test_a_tool_that_refuses_to_answer_is_recorded(self):
        refused = subprocess.CompletedProcess(["cc", "--version"], 1, "", "")
        with patch.object(build_sbom.subprocess, "run", return_value=refused):
            self.assertEqual(build_sbom.probe_toolchain(("cc", "--version")),
                             "not found")

    def test_a_banner_written_to_stderr_is_still_read(self):
        banner = subprocess.CompletedProcess(
            ["clang", "--version"], 0, "", "clang version 18.1.3\nTarget: arm64\n")
        with patch.object(build_sbom.subprocess, "run", return_value=banner):
            self.assertEqual(build_sbom.probe_toolchain(("clang", "--version")),
                             "clang version 18.1.3")

    def test_the_platform_probe_answers_on_this_interpreter(self):
        # The one probe that must work wherever the module runs: the build
        # interpreter naming the platform it is building on.
        value = build_sbom.probe_toolchain(build_sbom.TOOLCHAIN_PROBES[0][1])
        self.assertNotEqual(value, "not found")
        self.assertTrue(value.strip())


if __name__ == "__main__":
    unittest.main()
