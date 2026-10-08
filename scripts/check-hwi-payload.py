#!/usr/bin/env python3
"""Refuse a build environment whose hwilib is not the pinned release.

CT-90/CT-96/CT-112: the app hashes the whole installed `hwilib` tree before it
runs the helper, but nothing in CI ever put a *real* hwi 3.2.0 in front of that
check -- the accept path was only ever exercised against fixture bytes. This
script runs the app's own check against the prepared build environment, so a
desktop lock that resolved to different source than the manifest records fails
the build instead of shipping.

Run it with the prepared environment's own interpreter, because the package
roots it checks are the ones that interpreter imports from:

    .build-venv/bin/python scripts/check-hwi-payload.py

Exits non-zero with the refusal text on stderr.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import probe  # noqa: E402  (the repository root is put on the path above)


def main() -> int:
    if not probe._hwi_package_roots():
        print(
            "The prepared environment installed no hwilib; the desktop lock "
            "should have installed hwi " + probe.EXPECTED_HWI_VERSION + ".",
            file=sys.stderr,
        )
        return 1
    try:
        verified = probe._verify_hwi_payload()
    except probe.ProbeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        "hwilib matches the pinned tree ("
        + str(len(verified))
        + " files, hwi "
        + probe.EXPECTED_HWI_VERSION
        + ")"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
