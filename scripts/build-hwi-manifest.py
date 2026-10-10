#!/usr/bin/env python3
"""Build, or check, the whole-package digest manifest for the HWI payload.

CT-73 and CT-95. The app used to pin two files of the installed ``hwilib``
package -- ``hwilib/__init__.py`` and ``hwilib/_cli.py``. That is 2 of the 115
``.py`` files the package ships, so a poisoned ``hwilib/devices/trezor.py``
passed the check and then ran the moment the helper imported the package. The
pin was also only ever asserted as a constant in the test suite, so it could
not fail on real bytes.

This script records a digest for every regular file under the installed
package. ``probe.py`` recomputes that set at run time and refuses a file that
is missing, a file that was added, and a file whose bytes changed.

    python scripts/build-hwi-manifest.py                     # write it
    python scripts/build-hwi-manifest.py --check             # stale = failure
    python scripts/build-hwi-manifest.py --package-dir DIR   # from a scratch tree

``--check`` is the build gate: a package that no longer matches the committed
manifest fails the build and names every file that differs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

# The rule is part of the manifest: it is what a reader needs to reproduce the
# set, and it is what keeps a byte-compiled cache from looking like a change.
RULE = (
    "every regular file under the installed hwilib package directory, with "
    "POSIX-relative paths, excluding __pycache__ directories and *.pyc files"
)
SKIP_DIRS = {"__pycache__"}


def pinned_version() -> str:
    """EXPECTED_HWI_VERSION from probe.py, without importing probe.

    The version has one home -- probe.py, which is what refuses the wrong
    helper -- so it is read from there rather than repeated here.
    """
    text = (REPO / "probe.py").read_text(encoding="utf-8")
    match = re.search(r'^EXPECTED_HWI_VERSION\s*=\s*"([^"]+)"', text, re.M)
    if match is None:
        raise SystemExit("probe.py no longer defines EXPECTED_HWI_VERSION")
    return match.group(1)


def package_dir(explicit: str | None) -> pathlib.Path:
    """The ``hwilib`` directory, located without importing it.

    ``importlib.util.find_spec`` builds the spec from the finder; it does not
    execute the package's ``__init__.py``. That matters: a manifest check that
    imports the thing it is checking has already run the attacker's code.
    """
    if explicit:
        root = pathlib.Path(explicit).resolve()
    else:
        spec = importlib.util.find_spec("hwilib")
        if spec is None or not spec.submodule_search_locations:
            raise SystemExit(
                "hwilib is not installed in this environment; install hwi "
                f"{pinned_version()} or pass --package-dir"
            )
        root = pathlib.Path(list(spec.submodule_search_locations)[0]).resolve()
    if not root.is_dir():
        raise SystemExit(f"{root} is not a directory")
    return root


def collect(root: pathlib.Path) -> dict[str, str]:
    """path -> sha256 for every file the rule covers, in a stable order."""
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if SKIP_DIRS.intersection(relative.parts):
            continue
        if relative.name.endswith(".pyc"):
            continue
        files[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def build(root: pathlib.Path, version: str, source: str | None) -> dict:
    files = collect(root)
    manifest = {
        "distribution": "hwi",
        "version": version,
        "rule": RULE,
        "file_count": len(files),
        "source": source,
        "files": files,
    }
    return manifest


def serialise(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, sort_keys=False) + "\n"


def compare(committed: dict, current: dict) -> list[str]:
    """Named differences between the committed manifest and the real package."""
    problems: list[str] = []
    if committed.get("version") != current["version"]:
        problems.append(
            f"version: manifest says {committed.get('version')!r}, "
            f"probe.py pins {current['version']!r}"
        )
    old = committed.get("files") or {}
    new = current["files"]
    for name in sorted(set(old) - set(new)):
        problems.append(f"missing from the installed package: {name}")
    for name in sorted(set(new) - set(old)):
        problems.append(f"not recorded in the manifest: {name}")
    for name in sorted(set(old) & set(new)):
        if old[name] != new[name]:
            problems.append(
                f"bytes changed: {name}\n"
                f"      manifest {old[name]}\n"
                f"      installed {new[name]}"
            )
    if not problems and committed.get("rule") != current["rule"]:
        problems.append("the manifest's recorded rule is not the one this tool uses")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="compare against the committed manifest instead of writing it")
    parser.add_argument("--package-dir", default=None,
                        help="the hwilib directory (default: the installed package)")
    parser.add_argument("--out", default=None,
                        help="manifest path (default: vendor/hwi-payload-<version>.json)")
    parser.add_argument("--record-source", default=None,
                        help="provenance to record, e.g. the wheel name and its sha256")
    args = parser.parse_args(argv)

    version = pinned_version()
    root = package_dir(args.package_dir)
    out = pathlib.Path(args.out) if args.out else REPO / "vendor" / f"hwi-payload-{version}.json"
    current = build(root, version, args.record_source)

    if not args.check:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(serialise(current), encoding="utf-8", newline="\n")
        print(f"wrote {out.relative_to(REPO) if out.is_relative_to(REPO) else out} "
              f"({current['file_count']} files)")
        return 0

    if not out.is_file():
        print(f"{out} does not exist; the pinned payload is not recorded", file=sys.stderr)
        return 1
    committed = json.loads(out.read_text(encoding="utf-8"))
    problems = compare(committed, current)
    if problems:
        print(f"{out.name} is stale for the hwilib in this environment:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print("Regenerate it only after reviewing the change, and move the pin with it.",
              file=sys.stderr)
        return 1
    print(f"{out.name} matches the installed hwilib ({current['file_count']} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
