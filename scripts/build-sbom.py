#!/usr/bin/env python3
"""Inventory the collected Python packages and native libusb in a built DMG.

Run with the fresh .build-venv interpreter after build-macos.sh completes.
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collected_packages(root: Path) -> set[str]:
    """Use both PyInstaller analyses, not the build virtualenv's installed set."""
    modules = set()
    for name in ("Bitcoin Easy Signer", "hwi"):
        toc = root / "build" / name / "Analysis-00.toc"
        if not toc.is_file():
            raise ValueError(f"Missing PyInstaller analysis: {toc}")
        analysis = ast.literal_eval(toc.read_text(encoding="utf-8"))
        for entry in analysis[11] + analysis[14] + analysis[15] + analysis[18]:
            modules.add(entry[0].split(".")[0].split("/")[0])
    mapping = importlib.metadata.packages_distributions()
    return {re.sub(r"[-_.]+", "-", name).lower()
            for module in modules for name in mapping.get(module, [])}


def embedded_libusb(root: Path) -> dict[str, str]:
    """Hash the actual post-PyInstaller, post-signing bytes inside frozen HWI."""
    from PyInstaller.archive.readers import CArchiveReader

    archive = CArchiveReader(str(root / "dist" / "Bitcoin Easy Signer.app"
                                 / "Contents" / "MacOS" / "hwi"))
    result = {}
    for name in ("libusb-1.0.0.dylib", "libusb-1.0.dylib"):
        content = archive.extract(name)
        if not isinstance(content, bytes) or not content:
            raise ValueError(f"Bundled HWI is missing {name}")
        result[name] = hashlib.sha256(content).hexdigest()
    return result


def build(lib_hash: str, root: Path, shipped: set[str], embedded: dict[str, str]) -> dict:
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
        if normalized in LICENCES:
            component["licenses"] = [{"license": {"id": LICENCES[normalized]}}]
        components.append(component)
    components.sort(key=lambda component: (component["name"], component["version"]))
    for name in ("libusb-1.0.0.dylib", "libusb-1.0.dylib"):
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
                 "value": sha256(root / "requirements-desktop.lock")},
                # PyInstaller re-signs each collected Mach-O, changing its bytes.
                # This pin is the verified build input; components above are shipped bytes.
                {"name": "libusb_input_sha256", "value": lib_hash},
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
