#!/usr/bin/env python3
"""Inventory the collected Python packages and native libusb in a built bundle.

Run with the fresh .build-venv interpreter after the platform build script completes.
The result is a CycloneDX JSON SBOM shipped beside the immutable release assets.
It contains package names/versions, hashes of the reviewed lock and libusb,
and the GitHub commit/run identifiers; never wallet or device data.
"""

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
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
    Windows keeps it beside the binary in the same user-writable directory, and
    neither the helper nor the sidecar is signed there — see SIGNING.md (CT-105).
    An explicitly named helper keeps its own beside the binary.
    """
    candidates = [helper.with_name("hwi.sha256")]
    resources = helper.parent.parent / "Resources" / "hwi.sha256"
    if resources != candidates[0]:
        candidates.append(resources)
    return [candidate for candidate in candidates if candidate.is_file()]


def helper_digest(root: Path) -> str:
    """The helper's digest, with the sidecar the app will check at run time.

    The build writes hwi.sha256 beside the helper — in Contents/Resources on
    macOS, where the bundle signature covers it, and beside the binary on
    Windows, where nothing signs it (CT-105); probe.py refuses to run a helper
    whose bytes do not match that sidecar (CT-49). Recording the same digest
    here means a reader can compare the published SBOM against the file inside
    the artifact without trusting the app to describe itself. A missing or
    disagreeing sidecar fails the SBOM rather than publishing a weaker claim.
    """
    helper = frozen_helper(root)
    sidecars = helper_sidecars(helper)
    if not sidecars:
        raise ValueError(
            f"Missing hwi.sha256 for {helper.name}: the build must record the "
            "helper's digest beside it."
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


# CT-100: a hosted runner's image floats inside its pinned label (apt, MSVC,
# the Docker base image, the tool cache), so a build is not bit-reproducible
# from this repository. What the repository CAN do is stop that being
# invisible: the SBOM ships with, and is attested alongside, the assets, so
# the toolchain this build actually resolved belongs inside it. A rebuild on a
# different toolchain then differs in a named field instead of in silence.
TOOLCHAIN_PROBES = (
    ("toolchain_platform",
     (sys.executable, "-c", "import platform; print(platform.platform())")),
    ("toolchain_python", (sys.executable, "--version")),
    ("toolchain_cc", ("cc", "--version")),
    ("toolchain_clang", ("clang", "--version")),
    ("toolchain_msbuild", ("msbuild", "-version")),
    ("toolchain_docker", ("docker", "--version")),
)


def probe_toolchain(argv: tuple[str, ...]) -> str:
    """The first line of a tool's banner, or "not found" if it will not say.

    Absence is a fact to record, not a reason to fail: the SBOM is written on
    every platform, and a tool this platform does not use must still be named.
    """
    try:
        completed = subprocess.run(argv, capture_output=True, text=True,
                                   timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return "not found"
    if completed.returncode != 0:
        return "not found"
    banner = (completed.stdout or completed.stderr).strip().splitlines()
    return banner[0].strip() if banner else "not found"


def build(lib_hash: str, root: Path, shipped: set[str], embedded: dict[str, str],
          helper_sha: str | None = None) -> dict:
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
                # CT-100: what this build ran on, recorded rather than assumed.
                *({"name": name, "value": probe_toolchain(argv)}
                  for name, argv in TOOLCHAIN_PROBES),
            ],
        },
        "components": components,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--libusb-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parent.parent
    args.output.write_text(
        json.dumps(build(args.libusb_sha, repository,
                         collected_packages(repository), embedded_libusb(repository)),
                   indent=2) + "\n",
        encoding="utf-8",
    )
