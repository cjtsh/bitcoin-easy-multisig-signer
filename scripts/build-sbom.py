#!/usr/bin/env python3
"""Inventory the collected Python packages and native libusb in a built bundle.

Run with the fresh .build-venv interpreter after the platform build script completes.
The result is a CycloneDX JSON SBOM shipped beside the immutable release assets.
It contains package names/versions, hashes of the reviewed lock and libusb,
and the GitHub commit/run identifiers; never wallet or device data.

On Linux it also records the version of every OS package the build itself used
(CT-87). Those come from the runner image's moving archive rather than from a
pin, so they are accepted floating inputs, named at build time and explained in
releases/PATCH-0.6.8.md.
"""

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from version import APP_VERSION

# SPDX identifiers for the components this project ships or depends on.
# "GPL-2.0-or-later" for PyInstaller carries its explicit bundling exception,
# which is what makes distributing this MIT application with it permissible;
# see THIRD-PARTY-NOTICES.md.
LICENCES = {
    "embit": "MIT",
    "hwi": "MIT",
    "pywebview": "BSD-3-Clause",
    "pyinstaller": "GPL-2.0-or-later",
    "certifi": "MPL-2.0",
    "requests": "Apache-2.0",
    "pyyaml": "MIT",
}
EMBIT_WHEEL = Path("vendor/embit-0.8.2+besa.1-py3-none-any.whl")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


# Each platform names the frozen app bundle differently; the helper is "hwi"
# everywhere. Both analyses are looked up rather than assumed, so a build that
# never ran PyInstaller fails here instead of shipping an SBOM that quietly
# omits half the packages.
APP_BUNDLE_NAMES = ("Bitcoin Easy Signer", "bitcoin-easy-signer")

# The hash-locked dependency file this platform's build resolves against.
LOCK_FILE = {"darwin": "requirements-desktop.lock",
             "win32": "requirements-desktop-windows.lock"}.get(
                 sys.platform, "requirements-desktop-linux.lock")


def collected_packages(root: Path) -> set[str]:
    """Use both PyInstaller analyses, not the build virtualenv's installed set."""
    modules = set()
    analyses = []
    for name in (*APP_BUNDLE_NAMES, "hwi"):
        toc = root / "build" / name / "Analysis-00.toc"
        if toc.is_file():
            analyses.append(toc)
    if len(analyses) < 2:
        raise ValueError("Missing a PyInstaller analysis: expected the app bundle and hwi")
    for toc in analyses:
        analysis = ast.literal_eval(toc.read_text(encoding="utf-8"))
        for entry in analysis[11] + analysis[14] + analysis[15] + analysis[18]:
            modules.add(entry[0].split(".")[0].split("/")[0])
    mapping = importlib.metadata.packages_distributions()
    return {re.sub(r"[-_.]+", "-", name).lower()
            for module in modules for name in mapping.get(module, [])}


def frozen_helper(root: Path) -> Path:
    """Where PyInstaller put the standalone hardware-wallet helper."""
    if sys.platform == "darwin":
        return root / "dist" / "Bitcoin Easy Signer.app" / "Contents" / "MacOS" / "hwi"
    if sys.platform == "win32":
        return root / "dist" / "Bitcoin Easy Signer" / "hwi.exe"
    return root / "dist" / "hwi" / "hwi"


def helper_sidecars(helper: Path) -> list[Path]:
    """Every recorded digest for this helper that is actually present.

    Must agree with ``probe._hwi_sidecars``, which is the run-time half: an
    SBOM that looked somewhere the app does not would publish a digest nobody
    checks. macOS cannot keep the sidecar beside the helper — codesign refuses
    to seal an .app carrying a non-code file in Contents/MacOS — so the Mac
    build records it in Contents/Resources, where the outer signature seals it.
    Windows and an explicitly named helper keep it beside the binary.
    """
    candidates = [helper.with_name("hwi.sha256")]
    resources = helper.parent.parent / "Resources" / "hwi.sha256"
    if resources != candidates[0]:
        candidates.append(resources)
    return [candidate for candidate in candidates if candidate.is_file()]


def helper_digest(root: Path) -> str:
    """The helper's digest, with the sidecar the app will check at run time.

    The build writes hwi.sha256 into the signed bundle; probe.py refuses to run
    a helper whose bytes do not match that sidecar (CT-49). Recording the same
    digest here means a reader can compare the published SBOM against the file
    inside the artifact without trusting the app to describe itself. A missing
    or disagreeing sidecar fails the SBOM rather than publishing a weaker claim.
    """
    helper = frozen_helper(root)
    sidecars = helper_sidecars(helper)
    if not sidecars:
        raise ValueError(
            f"Missing hwi.sha256 for {helper.name}: the build must record the "
            "helper's digest inside the signed bundle."
        )
    digest = sha256(helper)
    for sidecar in sidecars:
        recorded = sidecar.read_text(encoding="utf-8").strip().split()
        if not recorded or recorded[0].lower() != digest:
            raise ValueError(
                f"{sidecar.name} does not match {helper.name}; refusing to publish "
                "an SBOM that disagrees with the artifact."
            )
    return digest


def native_library_names() -> tuple[str, ...]:
    """The names the bundled USB library ships under on this platform."""
    if sys.platform == "win32":
        return ("libusb-1.0.dll",)
    if sys.platform == "darwin":
        return ("libusb-1.0.0.dylib", "libusb-1.0.dylib")
    return ("libusb-1.0.so.0",)


def embedded_libusb(root: Path) -> dict[str, str]:
    """Hash the actual post-PyInstaller, post-signing bytes inside frozen HWI."""
    from PyInstaller.archive.readers import CArchiveReader

    archive = CArchiveReader(str(frozen_helper(root)))
    result = {}
    for name in native_library_names():
        content = archive.extract(name)
        if not isinstance(content, bytes) or not content:
            raise ValueError(f"Bundled HWI is missing {name}")
        result[name] = hashlib.sha256(content).hexdigest()
    return result


DEBIAN_ARCH = {"x86_64": "amd64", "aarch64": "arm64"}


def debian_release() -> tuple[str, str]:
    """The distro id and version from /etc/os-release, for the package purl.

    A build on a machine without that file still records its packages, under a
    neutral namespace rather than a guess.
    """
    values: dict[str, str] = {}
    release = Path("/etc/os-release")
    if release.is_file():
        for line in release.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator:
                values[key.strip()] = value.strip().strip('"')
    return values.get("ID") or "linux", values.get("VERSION_ID") or ""


def system_components(path: Path) -> list[dict]:
    """The OS packages this build used, from the ``name=version`` record.

    These are accepted floating inputs: the runner image's archive moves, so the
    build records the version each package resolved to rather than pinning a
    version that a runner refresh would invalidate. The trade is explained in
    releases/PATCH-0.6.8.md. A record that names nothing is refused, because an
    empty inventory reads like a clean one.
    """
    distro, release = debian_release()
    machine = platform.machine()
    qualifiers = f"arch={DEBIAN_ARCH.get(machine, machine)}"
    if release:
        qualifiers += f"&distro={distro}-{release}"
    components = []
    for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1):
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        name, separator, version = entry.partition("=")
        name, version = name.strip(), version.strip()
        if not separator or not name or not version:
            raise ValueError(
                f"{path}:{number}: expected name=version for an OS package, "
                f"got {entry!r}"
            )
        components.append({
            "type": "library", "name": name, "version": version,
            "purl": f"pkg:deb/{distro}/{name}@{version}?{qualifiers}",
            "properties": [{
                "name": "source",
                "value": ("resolved by dpkg-query on the build machine; an "
                          "accepted floating input, see releases/PATCH-0.6.8.md"),
            }],
        })
    if not components:
        raise ValueError(
            f"{path} records no OS packages; an empty record is not a record"
        )
    components.sort(key=lambda component: component["name"])
    return components


def build(lib_hash: str, root: Path, shipped: set[str], embedded: dict[str, str],
          helper_sha: str | None = None,
          system_packages: Path | None = None) -> dict:
    # Normalise before validating. CI passes the repository variable through
    # raw, and a SHA-256 is case-insensitive, so requiring lowercase here made an
    # uppercase variable fail *after* the build and tests had already succeeded.
    lib_hash = (lib_hash or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", lib_hash):
        raise ValueError("Expected the verified SHA-256 of libusb.")
    components = []
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if not name:
            continue
        normalized = re.sub(r"[-_.]+", "-", name).lower()
        if normalized not in shipped:
            continue
        version = distribution.version
        component = {
            "type": "library", "name": normalized, "version": version,
            "purl": f"pkg:pypi/{normalized}@{version}",
        }
        if normalized == "embit":
            wheel = root / EMBIT_WHEEL
            if not wheel.is_file():
                raise ValueError(f"Missing vendored embit wheel: {wheel}")
            component["hashes"] = [{
                "alg": "SHA-256", "content": sha256(wheel),
            }]
            component["properties"] = [{
                "name": "source",
                "value": (f"{EMBIT_WHEEL.as_posix()}; local patched wheel; "
                          "the PyPI purl is symbolic, not a PyPI artifact reference"),
            }]
        if normalized in LICENCES:
            component["licenses"] = [{"license": {"id": LICENCES[normalized]}}]
        components.append(component)
    system = system_components(system_packages) if system_packages is not None else []
    components.extend(system)
    components.sort(key=lambda component: (component["name"], component["version"]))
    for name in native_library_names():
        digest = embedded.get(name)
        if not digest or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Missing shipped digest for {name}")
        components.append({
            "type": "library", "name": name, "version": "1.0.30",
            "hashes": [{"alg": "SHA-256", "content": digest}],
            "licenses": [{"license": {"id": "LGPL-2.1-or-later"}}],
        })
    components.append({
        "type": "framework", "name": "cpython", "version": platform.python_version(),
        "purl": f"pkg:generic/cpython@{platform.python_version()}",
        "properties": [{"name": "python_build", "value": platform.python_build()[0]}],
    })
    return {
        "bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "component": {
                "type": "application", "name": "bitcoin-easy-multisig-signer",
                "version": APP_VERSION,
            },
            "properties": [
                {"name": "git_commit", "value": os.environ.get("GITHUB_SHA", "local-build")},
                {"name": "github_run_id", "value": os.environ.get("GITHUB_RUN_ID", "local-build")},
                {"name": "requirements_desktop_sha256",
                 "value": sha256(root / LOCK_FILE)},
                # PyInstaller re-signs each collected Mach-O, changing its bytes.
                # This pin is the verified build input; components above are shipped bytes.
                {"name": "libusb_input_sha256", "value": lib_hash},
                # The helper the app executes at run time, and the digest
                # hwi.sha256 beside it holds to. CT-49.
                {"name": "hwi_helper_sha256",
                 "value": helper_sha if helper_sha is not None else helper_digest(root)},
                # CT-87: the OS packages the build itself used. Linux names
                # them; the other platforms resolve none.
                {"name": "system_packages",
                 "value": (
                     f"{len(system)} OS packages recorded by dpkg-query on the "
                     "build machine; accepted floating inputs, see "
                     "releases/PATCH-0.6.8.md"
                 ) if system else (
                     "no OS packages recorded: this platform's build resolves none"
                 )},
            ],
        },
        "components": components,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--libusb-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--system-packages", type=Path, default=None,
        help="name=version lines for the OS packages this build used (Linux)",
    )
    args = parser.parse_args()
    repository = Path(__file__).resolve().parent.parent
    args.output.write_text(
        json.dumps(build(args.libusb_sha, repository,
                         collected_packages(repository), embedded_libusb(repository),
                         system_packages=args.system_packages),
                   indent=2) + "\n",
        encoding="utf-8",
    )
