"""The release dependency inventory must be parseable and identify its inputs."""

import hashlib
import importlib.util
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


class SystemPackageTests(unittest.TestCase):
    """CT-87: the SBOM names the OS packages the build itself used.

    Those packages come from the runner image's moving archive rather than from
    a pin, so the honest thing is to record the version each one resolved to and
    say why the pin is declined. A record that cannot be read, or that names
    nothing, is refused: an empty inventory reads like a clean one.
    """

    def _record(self, folder: str, text: str) -> Path:
        path = Path(folder) / "system-packages.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def test_the_record_names_each_package_and_its_version(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self._record(folder, "squashfs-tools=1:4.6.1-1build1\n"
                                        "librsvg2-bin=2.58.0+dfsg-1build1\n"
                                        "\n# a comment\n")
            components = {component["name"]: component
                          for component in build_sbom.system_components(path)}
        self.assertEqual(sorted(components), ["librsvg2-bin", "squashfs-tools"])
        self.assertEqual(components["squashfs-tools"]["version"],
                         "1:4.6.1-1build1")
        self.assertIn("accepted floating input",
                      components["squashfs-tools"]["properties"][0]["value"])

    def test_the_purl_names_the_distro_and_architecture(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self._record(folder, "fuse3=3.14.0-4\n")
            with patch.object(build_sbom, "debian_release",
                              return_value=("ubuntu", "24.04")), \
                    patch.object(build_sbom.platform, "machine",
                                 return_value="x86_64"):
                component = build_sbom.system_components(path)[0]
        self.assertEqual(
            component["purl"],
            "pkg:deb/ubuntu/fuse3@3.14.0-4?arch=amd64&distro=ubuntu-24.04",
        )

    def test_a_line_that_is_not_name_equals_version_is_refused(self):
        for text in ("nonsense\n", "=1.2\n", "name=\n"):
            with tempfile.TemporaryDirectory() as folder:
                path = self._record(folder, text)
                with self.assertRaises(ValueError) as caught:
                    build_sbom.system_components(path)
            self.assertIn(f"{path}:1:", str(caught.exception))
            self.assertIn("expected name=version", str(caught.exception))

    def test_an_empty_record_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self._record(folder, "\n# only a comment\n")
            with self.assertRaises(ValueError) as caught:
                build_sbom.system_components(path)
        self.assertIn("empty record is not a record", str(caught.exception))

    def test_the_inventory_records_how_many_os_packages_it_saw(self):
        embedded = {name: "d" * 64 for name in build_sbom.native_library_names()}
        with tempfile.TemporaryDirectory() as folder:
            path = self._record(folder, "fuse3=3.14.0-4\n"
                                        "squashfs-tools=1:4.6.1-1build1\n")
            result = build_sbom.build("a" * 64, ROOT, {"embit", "hwi"}, embedded,
                                      helper_sha="c" * 64, system_packages=path)
        properties = {entry["name"]: entry["value"]
                      for entry in result["metadata"]["properties"]}
        self.assertIn("2 OS packages", properties["system_packages"])
        names = [component["name"] for component in result["components"]]
        self.assertIn("fuse3", names)
        self.assertIn("squashfs-tools", names)

        result = build_sbom.build("a" * 64, ROOT, {"embit", "hwi"}, embedded,
                                  helper_sha="c" * 64)
        properties = {entry["name"]: entry["value"]
                      for entry in result["metadata"]["properties"]}
        self.assertIn("no OS packages recorded", properties["system_packages"])

    def test_the_linux_build_hands_its_record_to_the_sbom(self):
        script = (ROOT / "scripts" / "build-linux.sh").read_text(encoding="utf-8")
        self.assertIn('system_packages="build/system-packages.txt"', script)
        self.assertIn("dpkg-query", script)
        self.assertIn('--system-packages "$system_packages"', script)


if __name__ == "__main__":
    unittest.main()
