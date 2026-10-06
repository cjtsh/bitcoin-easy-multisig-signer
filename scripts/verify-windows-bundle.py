#!/usr/bin/env python3
"""Checks a built Windows bundle before it is allowed to become a release asset.

The macOS build verified the frozen app by running the app's own headless
self-checks and comparing the .app's icon file. Windows has no equivalent icon
file to compare - the icon is embedded in the executable as a resource - so this
script checks the two things a Windows user would notice, from the outside:

  1. the executable carries the icon the project reviewed, not PyInstaller's
     stock one. PyInstaller copies each .ico frame into an RT_ICON resource
     byte-for-byte (PyInstaller/utils/win32/icon.py, CopyIcons_FromIco), so every
     frame payload of assets/AppIcon.ico must appear verbatim inside the .exe.
     Searching for the payloads needs no PE parser and cannot silently pass on a
     different image.
  2. the onedir payload really contains the files the app's own --check-bundle
     looks for, so a missing --add-data is caught here rather than by a user.

It also confirms the artefacts the release needs exist: the .zip, the bundled
hwi.exe, and the PyInstaller analysis files scripts/build-sbom.py reads.

Run after scripts/build-windows.ps1, on Windows or anywhere the bundle was copied:

    python scripts/verify-windows-bundle.py --version 0.6.4
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_NAME = "Bitcoin Easy Signer"
# What desktop.py's --check-bundle requires beside ui.html in the frozen data dir.
REQUIRED_DATA = (
    "ui.html",
    "LICENSE",
    "DISCLAIMER.md",
    "PRIVACY.md",
    "THIRD-PARTY-NOTICES.md",
    "libusb-COPYING",
)
# A frame smaller than this is not worth searching for: a handful of bytes would
# match any executable by chance.
MIN_FRAME_BYTES = 1024


class BundleError(SystemExit):
    def __init__(self, message: str) -> None:
        super().__init__(f"{message}")


def ico_frames(path: Path) -> list[tuple[int, int, bytes]]:
    """(width, height, payload) for each frame of an .ico, as PyInstaller sees it."""
    data = path.read_bytes()
    if len(data) < 6:
        raise BundleError(f"{path} is too short to be an icon file.")
    reserved, kind, count = struct.unpack_from("<HHH", data, 0)
    if reserved != 0 or kind != 1:
        raise BundleError(f"{path} is not an icon file (reserved={reserved}, type={kind}).")
    if count == 0:
        raise BundleError(f"{path} contains no images.")
    frames = []
    for index in range(count):
        width, height, _, _, _, _, size, offset = struct.unpack_from("<BBBBHHII", data, 6 + index * 16)
        if offset + size > len(data):
            raise BundleError(f"{path} frame {index} points past the end of the file.")
        frames.append((width or 256, height or 256, data[offset:offset + size]))
    return frames


def check_icon(exe: Path, icon: Path) -> None:
    if not icon.is_file():
        raise BundleError(f"{icon} is missing; it is the reviewed icon master.")
    frames = [(w, h, payload) for w, h, payload in ico_frames(icon) if len(payload) >= MIN_FRAME_BYTES]
    if not frames:
        raise BundleError(f"{icon} has no frame large enough to identify it by.")
    blob = exe.read_bytes()
    missing = [f"{width}x{height}" for width, height, payload in frames if payload not in blob]
    if missing:
        raise BundleError(
            f"{exe} does not carry the reviewed icon: the frame(s) {', '.join(missing)} "
            f"of {icon} are absent. It is probably still PyInstaller's stock icon, "
            "which means --icon was not applied."
        )
    print(f"  icon: {len(frames)} reviewed frame(s) embedded in {exe.name}")


def check_zip(dist: Path, version: str) -> Path:
    expected = f"Bitcoin-Easy-Signer-v{version}-windows-x64.zip"
    found = sorted(path.name for path in dist.glob("*.zip"))
    if found != [expected]:
        raise BundleError(
            f"{dist} should hold exactly one zip, {expected}; it holds "
            f"{found or 'nothing'}."
        )
    if not (dist / expected).is_file():
        raise BundleError(f"{dist / expected} is not a file.")
    print(f"  archive: {expected} ({(dist / expected).stat().st_size} bytes)")
    return dist / expected


def check_payload(app_dir: Path) -> None:
    # PyInstaller 6 keeps everything except the loader in a contents directory.
    candidates = [app_dir / "_internal", app_dir]
    contents = next((path for path in candidates if path.is_dir()), None)
    if contents is None:
        raise BundleError(f"{app_dir} has no contents directory; the bundle is not onedir.")
    missing = [name for name in REQUIRED_DATA if not (contents / name).is_file()]
    if missing:
        raise BundleError(
            f"{contents} is missing {', '.join(missing)}; the matching --add-data was dropped."
        )
    stray = sorted(path.name for path in app_dir.rglob("*.dylib"))
    if stray:
        raise BundleError(
            f"{app_dir} still contains a macOS library ({', '.join(stray)}); this is not a Windows bundle."
        )
    print(f"  payload: {len(REQUIRED_DATA)} required file(s) present in {contents.name}/")


def check_analysis(root: Path) -> None:
    for target in (APP_NAME, "hwi"):
        toc = root / "build" / target / "Analysis-00.toc"
        if not toc.is_file():
            raise BundleError(
                f"{toc} is missing; scripts/build-sbom.py needs the PyInstaller analysis "
                "to inventory the bundled dependencies."
            )
    print("  analysis: PyInstaller .toc files present for the app and hwi")


def check_sbom(sbom: Path) -> None:
    if not sbom.is_file():
        raise BundleError(f"{sbom} is missing; the release must ship a build SBOM.")
    try:
        document = json.loads(sbom.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise BundleError(f"{sbom} is not readable JSON: {error}") from error
    if document.get("bomFormat") != "CycloneDX":
        raise BundleError(f"{sbom} is not a CycloneDX document (bomFormat={document.get('bomFormat')!r}).")
    components = document.get("components") or []
    print(f"  sbom: {sbom.name} ({len(components)} component(s))")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", required=True, help="the version being verified")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    parser.add_argument("--dist", type=Path, default=None, help="dist directory")
    parser.add_argument("--icon", type=Path, default=None, help="the reviewed .ico")
    parser.add_argument("--sbom", type=Path, default=None, help="the generated BUILD-SBOM.json")
    options = parser.parse_args()

    root = options.root.resolve()
    dist = (options.dist or root / "dist").resolve()
    icon = (options.icon or root / "assets" / "AppIcon.ico").resolve()
    sbom = (options.sbom or dist / "BUILD-SBOM.json").resolve()
    app_dir = dist / APP_NAME
    exe = app_dir / f"{APP_NAME}.exe"
    hwi = app_dir / "hwi.exe"

    if not exe.is_file():
        raise BundleError(f"{exe} is missing; the app was not built.")
    if not hwi.is_file():
        raise BundleError(f"{hwi} is missing; --check-devices would look for it beside the app.")
    if exe.stat().st_size < 1024 * 1024:
        raise BundleError(f"{exe} is only {exe.stat().st_size} bytes; that is not a frozen app.")

    print(f"Checking {app_dir}:")
    check_icon(exe, icon)
    check_payload(app_dir)
    check_zip(dist, options.version)
    check_analysis(root)
    check_sbom(sbom)
    print("The Windows bundle passed every post-build check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
