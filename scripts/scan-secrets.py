#!/usr/bin/env python3
"""Refuse to ship a source tree that carries a secret.

CT-86. GitHub's secret scanning and push protection are enabled at the platform
level and scripts/check-platform-state.sh records that, but until 0.6.8 nothing
in the repository read the bytes a tag actually publishes. A credential that
reaches a tag is public for as long as the tag exists; deleting the file in a
later commit does not unpublish it.

The scanner is detect-secrets, pinned by version and hash in
requirements-ci.lock -- the same ``--require-hashes`` set the source job already
installs. It is deliberately not a GitHub Action: a floating action would be a
new unverified input on the release path, and the plan (releases/PLAN-0.6.8.md,
W13) asks for a scanner pinned by version and digest instead.

Two plugin classes are disabled on purpose. HexHighEntropyString and
Base64HighEntropyString fire on every digest in this repository: the pinned
hwilib payload manifest, the BIP-143 test vectors, the vendored libusb digests
in the platform build scripts. That is 194 findings in 12 files, and the list
would move whenever a test vector moved, so an operator learns to skip the
report. What remains catches a credential by its shape (a GitHub token, an AWS
key, a private key) or by the keyword that names it. The tradeoff is real: a
high-entropy secret with no recognisable shape and no keyword is not caught
here, and is left to the platform's secret scanning.

detect-secrets exits 0 even when it reports findings, so the exit code is
decided here from the parsed report. A scan that reports nothing because it
could not read the tree is worse than no scan, so every path that could hide a
finding refuses with exit 2: a target that does not exist or is empty, a
scanner that is not the pinned version, a scanner whose disabled plugins are
still active, or unreadable output. Exit 1 means findings. Exit 0 means the
bytes were read and nothing matched.

Usage:
    scripts/scan-secrets.py PATH [PATH ...]
"""

from __future__ import annotations

import contextlib
import importlib.metadata
import json
import os
import pathlib
import subprocess
import sys
from typing import Iterator

SCANNER_DISTRIBUTION = "detect-secrets"
SCANNER_MODULE = "detect_secrets"
SCANNER_VERSION = "1.5.0"

# See the module docstring: these two are what make the report unreadable.
DISABLED_PLUGINS = ("HexHighEntropyString", "Base64HighEntropyString")

# releases/platform-state.json records the platform's own scanning posture, so
# it holds lines like `"secret_scanning": "enabled"`. detect-secrets reads those
# as a keyword next to a value -- two findings in a file that is generated,
# names-only, and reviewed by scripts/check-platform-state.sh. The exclusion is
# line-shaped and matches no other shape: a credential on any other line of the
# same file is still a finding, and CanaryTests proves it.
STATUS_LINE_EXCLUSION = r'"secret_scanning(_[a-z_]+)?":\s*"(enabled|disabled)"'

CLEAN = 0
FINDINGS = 1
REFUSED = 2


class Refusal(Exception):
    """The scan could not honestly report on the bytes it was given."""


def installed_version() -> str:
    try:
        return importlib.metadata.version(SCANNER_DISTRIBUTION)
    except importlib.metadata.PackageNotFoundError as error:
        raise Refusal(
            f"{SCANNER_DISTRIBUTION} is not installed; the source job installs "
            "requirements-ci.lock with --require-hashes before it runs this"
        ) from error


def require_pinned_scanner(version: str) -> str:
    """Refuse a scanner that is not the one the lock pins."""
    if version != SCANNER_VERSION:
        raise Refusal(
            f"{SCANNER_DISTRIBUTION} {version} is not the pinned "
            f"{SCANNER_VERSION}; bump the pin in requirements-ci.txt and "
            "regenerate requirements-ci.lock in the same commit"
        )
    return version


def scan_command(target: str) -> list[str]:
    command = [sys.executable, "-m", SCANNER_MODULE, "scan", "--all-files"]
    for plugin in DISABLED_PLUGINS:
        command += ["--disable-plugin", plugin]
    command += ["--exclude-lines", STATUS_LINE_EXCLUSION]
    command.append(target)
    return command


def read_report(stdout: str) -> dict:
    try:
        report = json.loads(stdout)
    except ValueError as error:
        raise Refusal(f"the scanner wrote no readable report ({error})") from error
    if not isinstance(report, dict) or not isinstance(report.get("results"), dict):
        raise Refusal("the scanner's report has no results map")
    return report


def refuse_active_disabled_plugin(report: dict) -> None:
    """A disabled plugin that is still active means the flags did not arrive."""
    active = set(DISABLED_PLUGINS) & {
        plugin.get("name")
        for plugin in report.get("plugins_used", [])
        if isinstance(plugin, dict)
    }
    if active:
        raise Refusal(
            f"the scanner still has {', '.join(sorted(active))} enabled, so it is "
            "not the scan this wrapper was written against"
        )


@contextlib.contextmanager
def in_directory(directory: pathlib.Path) -> Iterator[None]:
    previous = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(previous)


def locate(path: pathlib.Path) -> tuple[pathlib.Path, str]:
    """The working directory and the argument the scanner can actually read.

    detect-secrets drops any path that is not under the process's working
    directory: ``get_files_to_scan`` relativises against ``root or os.getcwd()``
    and silently skips whatever falls outside, which looks exactly like a clean
    tree. Scanning from the target's own directory removes that trap for every
    caller. An empty target is refused for the same reason.
    """
    resolved = path.resolve()
    if not resolved.exists():
        raise Refusal(f"{path} does not exist, so there was nothing to scan")
    if resolved.is_file():
        return resolved.parent, resolved.name
    if not any(resolved.iterdir()):
        raise Refusal(f"{path} is empty, so a clean result would prove nothing")
    return resolved, "."


def scan(path: pathlib.Path) -> list[str]:
    """The findings under *path*, as readable lines."""
    directory, target = locate(path)
    with in_directory(directory):
        completed = subprocess.run(
            scan_command(target), capture_output=True, text=True, check=False
        )
    if completed.returncode != 0:
        detail = completed.stderr.strip()
        raise Refusal(
            f"{SCANNER_DISTRIBUTION} exited {completed.returncode} on {path}"
            + (f": {detail}" if detail else "")
        )
    report = read_report(completed.stdout)
    refuse_active_disabled_plugin(report)
    return [
        f"{directory / found}:{hit.get('line_number', '?')}: {hit.get('type', 'finding')}"
        for found, hits in sorted(report["results"].items())
        for hit in hits
    ]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: scan-secrets.py PATH [PATH ...]", file=sys.stderr)
        return REFUSED
    try:
        require_pinned_scanner(installed_version())
    except Refusal as refusal:
        print(f"refused: {refusal}", file=sys.stderr)
        return REFUSED
    found: list[str] = []
    for name in argv[1:]:
        try:
            found.extend(scan(pathlib.Path(name)))
        except Refusal as refusal:
            print(f"refused: {refusal}", file=sys.stderr)
            return REFUSED
    if found:
        print(f"refused: {len(found)} secret(s); a tag would publish them:")
        for line in found:
            print(f"  {line}")
        return FINDINGS
    print(f"ok: no secrets in {', '.join(argv[1:])}")
    return CLEAN


if __name__ == "__main__":
    sys.exit(main(sys.argv))
