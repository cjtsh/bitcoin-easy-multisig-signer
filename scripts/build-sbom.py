#!/usr/bin/env python3
"""Inventory the exact Python environment and native libusb in a built DMG.

Run with the fresh .build-venv interpreter after build-macos.sh completes.
The result is a CycloneDX JSON SBOM shipped beside the immutable release assets.
It contains package names/versions, hashes of the reviewed lock and libusb,
and the GitHub commit/run identifiers; never wallet or device data.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from version import APP_VERSION


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build(lib_hash: str, root: Path) -> dict:
    if not re.fullmatch(r"[0-9a-f]{64}", lib_hash):
        raise ValueError("Expected the verified lowercase SHA-256 of libusb.")
    components = []
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if not name:
            continue
        normalized = re.sub(r"[-_.]+", "-", name).lower()
        version = distribution.version
        components.append({
            "type": "library", "name": normalized, "version": version,
            "purl": f"pkg:pypi/{normalized}@{version}",
        })
    components.sort(key=lambda component: (component["name"], component["version"]))
    components.append({
        "type": "library", "name": "libusb", "version": "1.0.30",
        "hashes": [{"alg": "SHA-256", "content": lib_hash}],
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
                {"name": "libusb_sha256", "value": lib_hash},
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
        json.dumps(build(args.libusb_sha, repository), indent=2) + "\n",
        encoding="utf-8",
    )
