#!/usr/bin/env bash
#
# Build Bitcoin Easy Signer for Linux x86_64: one AppImage, plus one tarball.
#
# The same discipline as scripts/build-macos.sh, for the same reasons: every
# reviewed input is hashed and refused on a mismatch, the dependency set comes
# from a file that was resolved on this platform under hash pinning, and no
# artifact leaves here. Two things are different.
#
# * There is no window toolkit. gui.py already serves the interface on
#   localhost and opens the user's own browser, so the payload is Python and
#   the browser the machine already has.
#
# * The AppImage is assembled by concatenating a pinned runtime with the
#   squashfs payload. The runtime in vendor/ is the statically linked one from
#   AppImage/type2-runtime: squashfuse and libfuse are inside it, so it never
#   loads the host's libfuse.so.2 -- the library whose absence has always made
#   a downloaded AppImage fail to start on a modern Ubuntu. Mounting still
#   needs /dev/fuse and a fusermount binary, which Ubuntu's fuse3 provides; a
#   machine without those can extract and run, which is what the tarball is for.
#
# Usage:
#   scripts/build-linux.sh <version>
#
# Environment:
#   BUILD_DEPS_PREPARED=1  reuse .build-venv; its recorded lock digest must match
#   PREPARE_ONLY=1         create .build-venv and stop
#   PYTHON=<path>          interpreter to build the environment with (3.10-3.12)

set -euo pipefail

# The reviewed AppImage runtime: AppImage/type2-runtime release 20251108,
# asset runtime-x86_64. Provenance and the download URL are in vendor/README.md.
REVIEWED_APPIMAGE_RUNTIME_SHA256="2fca8b443c92510f1483a883f60061ad09b46b978b2631c807cd873a47ec260d"
# The reviewed libusb source; the library the bundle carries is built from it
# here, and its digest is recorded in the SBOM.
REVIEWED_LIBUSB_SOURCE_SHA256="fea36f34f9156400209595e300840767ab1a385ede1dc7ee893015aea9c6dbaf"
REVIEWED_LIBUSB_VERSION="1.0.30"

APP_SLUG="bitcoin-easy-signer"
DISPLAY_NAME="Bitcoin Easy Signer"
# The name of the FILES, as opposed to the name the desktop shows. A file
# name with a space in it arrives as %20 and has to be quoted everywhere;
# the other platforms' artifacts are hyphenated for the same reason.
ARTIFACT_NAME="Bitcoin-Easy-Signer"

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
note() { printf '==> %s\n' "$*"; }
usage() {
    printf 'Usage: %s <version>\n\nBuilds %s for Linux x86_64.\n' \
        "$(basename "$0")" "$DISPLAY_NAME" >&2
}

version="${1:-}"
if [[ -z "$version" ]]; then
    usage
    fail "the version to build is required"
fi
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] \
    || fail "version must look like MAJOR.MINOR.PATCH, got '$version'"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

# ---- the machine this runs on ------------------------------------------
[[ "$(uname -s)" == "Linux" ]] \
    || fail "this script builds a Linux AppImage; run it on Linux (PyInstaller cannot cross-compile)"
[[ "$(uname -m)" == "x86_64" ]] \
    || fail "the published Linux build is x86_64; this machine is $(uname -m)"

declared="$(sed -n 's/^APP_VERSION = "\(.*\)"$/\1/p' version.py)"
[[ -n "$declared" ]] || fail "could not read APP_VERSION from version.py"
[[ "$declared" == "$version" ]] \
    || fail "version.py declares $declared, not the $version this build was asked for"

python_bin="${PYTHON:-python3}"
command -v "$python_bin" >/dev/null 2>&1 || fail "$python_bin is not on the PATH"
py_version="$("$python_bin" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
case "$py_version" in
    3.10 | 3.11 | 3.12) ;;
    *) fail "Python 3.10-3.12 is required (the bundled HWI needs <3.13, embit needs >=3.10); found $py_version" ;;
esac

for tool in mksquashfs tar sha256sum make; do
    command -v "$tool" >/dev/null 2>&1 \
        || fail "$tool is required (apt install squashfs-tools build-essential)"
done

# ---- the reviewed launcher ---------------------------------------------
runtime="vendor/appimage-runtime-x86_64"
[[ -f "$runtime" ]] || fail "$runtime is missing from the source tree"
runtime_sha="$(sha256sum "$runtime" | awk '{print $1}')"
[[ "$runtime_sha" == "$REVIEWED_APPIMAGE_RUNTIME_SHA256" ]] \
    || fail "$runtime is not the reviewed runtime: $runtime_sha"

# ---- build environment -------------------------------------------------
venv=".build-venv"
lock="requirements-desktop-linux.lock"
stamp="$venv/requirements-desktop-linux.sha256"

if [[ "${BUILD_DEPS_PREPARED:-0}" == "1" ]]; then
    [[ -x "$venv/bin/python" ]] || fail "BUILD_DEPS_PREPARED=1 but $venv/bin/python is missing"
    [[ -f "$stamp" ]] || fail "BUILD_DEPS_PREPARED=1 but $stamp is missing"
    [[ "$(cat "$stamp")" == "$(sha256sum "$lock" | awk '{print $1}')" ]] \
        || fail "$lock changed since the environment was prepared; rebuild it"
else
    note "Preparing $venv from $lock"
    rm -rf "$venv"
    "$python_bin" -m venv "$venv"
    # No `pip install --upgrade pip` here (CT-57). It was the one unpinned fetch
    # on the build path: whatever PyPI served as "current pip" became the
    # installer for a hash-locked tree, and neither build-macos.sh nor
    # build-windows.ps1 ever did it. The interpreter's own pip installs
    # --require-hashes just fine.
    "$venv/bin/python" -m pip install --disable-pip-version-check --require-hashes -r "$lock"
    sha256sum "$lock" | awk '{print $1}' > "$stamp"
fi

if [[ "${PREPARE_ONLY:-0}" == "1" ]]; then
    note "Build environment ready (Python $py_version)"
    exit 0
fi

# ---- native USB library, from the reviewed source ----------------------
libusb_source="vendor/libusb-1.0.30.tar.bz2"
[[ -f "$libusb_source" ]] || fail "$libusb_source is missing from the source tree"
libusb_source_sha="$(sha256sum "$libusb_source" | awk '{print $1}')"
[[ "$libusb_source_sha" == "$REVIEWED_LIBUSB_SOURCE_SHA256" ]] \
    || fail "$libusb_source is not the reviewed source: $libusb_source_sha"

note "Building libusb $REVIEWED_LIBUSB_VERSION from $libusb_source"
rm -rf build/libusb
mkdir -p build/libusb
tar -xjf "$libusb_source" -C build/libusb --strip-components=1
(
    cd build/libusb
    # --disable-udev keeps a libudev.so.1 dependency out of the bundle.
    # libusb only uses udev for hotplug notifications, which this app never
    # asks for: hwilib enumerates on demand. Without the flag the bundle would
    # refuse to load on a host that has systemd's udev library absent.
    ./configure --disable-static --enable-shared --disable-examples-build \
        --disable-udev >/dev/null
    make -j"$(nproc)" >/dev/null
)
libusb_built="$(find build/libusb/libusb/.libs -maxdepth 1 -name 'libusb-1.0.so.0.*' -type f | head -n 1)"
[[ -n "$libusb_built" ]] || fail "libusb built no shared library"
cp "$libusb_built" build/libusb-1.0.so.0
libusb_sha="$(sha256sum build/libusb-1.0.so.0 | awk '{print $1}')"
note "libusb $(basename "$libusb_built") sha256 $libusb_sha"

# ---- the payload -------------------------------------------------------
rm -rf dist
mkdir -p dist

note "Building the app bundle"
"$venv/bin/python" -m PyInstaller --noconfirm --clean --onedir --name "$APP_SLUG" \
    --paths . \
    --add-data "ui.html:." --add-data "LICENSE:." --add-data "DISCLAIMER.md:." \
    --add-data "PRIVACY.md:." --add-data "THIRD-PARTY-NOTICES.md:." \
    --add-data "vendor/libusb-COPYING:." \
    --add-binary "build/libusb-1.0.so.0:." \
    --collect-all hwilib --collect-data certifi \
    --distpath dist scripts/linux_entry.py

# The helper is a second, standalone PyInstaller binary, exactly as on macOS
# and Windows: the app runs it as a subprocess and looks for it beside the
# frozen executable.
note "Building the bundled hardware-wallet helper"
"$venv/bin/python" -m PyInstaller --noconfirm --clean --onefile --name hwi \
    --collect-all hwilib --collect-all hid --collect-all requests --collect-all urllib3 \
    --collect-data certifi --add-binary "build/libusb-1.0.so.0:." \
    --distpath dist/hwi scripts/hwi_entry.py
cp dist/hwi/hwi "dist/$APP_SLUG/hwi"
chmod 755 "dist/$APP_SLUG/hwi"
"dist/$APP_SLUG/hwi" --help >/dev/null \
    || fail "the bundled hardware-wallet helper cannot start"

# Record the helper's bytes beside the copies this build will ship and beside
# the PyInstaller output the SBOM hashes. probe.py refuses a helper whose bytes
# do not match the sidecar next to it (CT-49).
hwi_digest="$(sha256sum "dist/$APP_SLUG/hwi" | awk '{print $1}')"
printf '%s  %s\n' "$hwi_digest" "hwi" > "dist/$APP_SLUG/hwi.sha256"
printf '%s  %s\n' "$hwi_digest" "hwi" > "dist/hwi/hwi.sha256"
note "bundled hwi sha256 $hwi_digest (recorded in hwi.sha256)"

# ---- the checks, against the payload this build just made ---------------
# A double-clicked AppImage has no console, so each check writes what it
# verified to a file. An empty file is treated as a failure: a silent pass is
# not a pass.
checks_log="build/linux-self-check"
rm -rf "$checks_log"
mkdir -p "$checks_log"
log="dist/linux-self-check.log"
: > "$log"

note "Running the self-checks"
for flag in --dsh-check-bundle --dsh-check-network --dsh-check-save --dsh-check-devices --dsh-check-udev; do
    name="${flag#--dsh-check-}"
    export DSH_LINUX_CHECK_LOG="$checks_log/$name.log"
    if ! "dist/$APP_SLUG/$APP_SLUG" "$flag" >"$checks_log/$name.stdout" 2>&1; then
        cat "$checks_log/$name.stdout" "$checks_log/$name.log" >&2 2>/dev/null || true
        unset DSH_LINUX_CHECK_LOG
        fail "$flag failed on the payload this build produced"
    fi
    if [[ ! -s "$checks_log/$name.log" ]]; then
        cat "$checks_log/$name.stdout" >&2 2>/dev/null || true
        unset DSH_LINUX_CHECK_LOG
        fail "$flag reported nothing; a silent pass is not a pass"
    fi
    cat "$checks_log/$name.log" >> "$log"
    unset DSH_LINUX_CHECK_LOG
done
for flag in --dsh-check-libusb --dsh-capabilities; do
    "dist/$APP_SLUG/hwi" "$flag" >> "$log" 2>&1 \
        || fail "the bundled helper failed $flag"
done
cat "$log"

# ---- the AppDir --------------------------------------------------------
note "Assembling the AppDir"
appdir="build/AppDir"
rm -rf "$appdir"
mkdir -p "$appdir/usr/bin" \
    "$appdir/usr/share/applications" \
    "$appdir/usr/share/icons/hicolor/256x256/apps" \
    "$appdir/usr/lib/udev/rules.d"
cp -a "dist/$APP_SLUG" "$appdir/usr/bin/$APP_SLUG"

icon_png="build/AppIcon.png"
if [[ -f assets/AppIcon.png ]]; then
    cp assets/AppIcon.png "$icon_png"
else
    command -v rsvg-convert >/dev/null 2>&1 \
        || fail "assets/AppIcon.png is missing and rsvg-convert is not installed (apt install librsvg2-bin)"
    rsvg-convert -w 256 -h 256 assets/icon.svg -o "$icon_png"
fi
"$venv/bin/python" - "$icon_png" <<'PY'
import struct
import sys

raw = open(sys.argv[1], "rb").read()
if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
    raise SystemExit("the icon is not a PNG")
width, height = struct.unpack(">II", raw[16:24])
if (width, height) != (256, 256):
    raise SystemExit(f"the icon is {width}x{height}; the AppDir icon must be 256x256")
PY
cp "$icon_png" "$appdir/$APP_SLUG.png"
ln -sf "$APP_SLUG.png" "$appdir/.DirIcon"
cp "$icon_png" "$appdir/usr/share/icons/hicolor/256x256/apps/$APP_SLUG.png"

# The udev rules come from hwilib itself, so they are the rules the bundled
# tool was written against rather than a private copy that could drift.
udev_source="$("$venv/bin/python" -c 'import hwilib, pathlib; print(pathlib.Path(hwilib.__file__).parent / "udev")')"
[[ -d "$udev_source" ]] || fail "hwilib ships no udev rules; the bundle would leave USB wallets root-only"
cp "$udev_source"/*.rules "$appdir/usr/lib/udev/rules.d/"

cat > "$appdir/$APP_SLUG.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$DISPLAY_NAME
Comment=Sign multisig transactions with a hardware wallet
Exec=$APP_SLUG
Icon=$APP_SLUG
Terminal=false
Categories=Finance;Security;Network;
Keywords=bitcoin;multisig;hardware wallet;signer;
StartupNotify=true
X-AppImage-Version=$version
EOF
cp "$appdir/$APP_SLUG.desktop" "$appdir/usr/share/applications/$APP_SLUG.desktop"

cat > "$appdir/AppRun" <<EOF
#!/bin/sh
# The AppImage runtime mounts this directory and runs this file.
set -e
here="\$(dirname "\$(readlink -f "\$0")")"
exec "\$here/usr/bin/$APP_SLUG/$APP_SLUG" "\$@"
EOF
chmod 755 "$appdir/AppRun"

# ---- the AppImage ------------------------------------------------------
appimage="dist/$ARTIFACT_NAME-v$version-linux-x86_64.AppImage"
note "Packing $appimage"
rm -f build/appdir.squashfs
mksquashfs "$appdir" build/appdir.squashfs -root-owned -noappend -comp gzip -no-progress >/dev/null
cat "$runtime" build/appdir.squashfs > "$appimage"
chmod 755 "$appimage"

# Prove the packed artifact, not just the tree it came from. Extraction is
# handled by the runtime itself and needs no /dev/fuse, no fusermount and no
# libfuse.so.2 -- which is exactly what a machine without them would hit.
note "Verifying the packed AppImage"
"$appimage" --appimage-offset >/dev/null || fail "the AppImage cannot read its own payload offset"
extracted="build/extracted"
rm -rf "$extracted"
mkdir -p "$extracted"
(
    cd "$extracted"
    "$root/$appimage" --appimage-extract >/dev/null
) || fail "the AppImage could not be extracted"
[[ -x "$extracted/squashfs-root/AppRun" ]] || fail "the extracted AppImage has no AppRun"
rm -f build/packed-*.log
for flag in --dsh-check-bundle --dsh-check-save --dsh-check-devices --dsh-check-udev; do
    packed_report="build/packed-${flag#--dsh-check}.log"
    DSH_LINUX_CHECK_LOG="$packed_report" \
        "$extracted/squashfs-root/AppRun" "$flag" >/dev/null \
        || fail "the packed AppImage failed $flag"
    [[ -s "$packed_report" ]] \
        || fail "the packed AppImage reported nothing for $flag"
done
(cd "$extracted" && ls -l squashfs-root/usr/lib/udev/rules.d/*.rules >/dev/null) \
    || fail "the packed AppImage carries no udev rules"

# ---- the tarball, for a machine with no FUSE at all --------------------
tarball="dist/$ARTIFACT_NAME-v$version-linux-x86_64.tar.gz"
note "Packing $tarball"
tarball_root="build/tarball"
rm -rf "$tarball_root"
mkdir -p "$tarball_root/$APP_SLUG" "$tarball_root/udev"
cp -a "dist/$APP_SLUG/." "$tarball_root/$APP_SLUG/"
cp "$icon_png" "$tarball_root/$APP_SLUG.png"
cp "$appdir/$APP_SLUG.desktop" "$tarball_root/"
cp "$udev_source"/*.rules "$tarball_root/udev/"

cat > "$tarball_root/run-me.sh" <<EOF
#!/bin/sh
# Run Bitcoin Easy Signer from this directory. Nothing is installed and
# nothing is mounted: everything it needs is beside this script.
set -e
here="\$(cd "\$(dirname "\$0")" && pwd)"
exec "\$here/$APP_SLUG/$APP_SLUG" "\$@"
EOF
chmod 755 "$tarball_root/run-me.sh"

cat > "$tarball_root/README-LINUX.txt" <<EOF
$DISPLAY_NAME $version for Linux x86_64
================================================

Run it
------
    ./run-me.sh

That opens the interface in your browser. Nothing is installed and nothing is
copied outside this directory.

The AppImage
------------
$ARTIFACT_NAME-v$version-linux-x86_64.AppImage from the same release page is
the same program in one file. Before its first launch, mark it as executable.
In Ubuntu's Files app, right-click the AppImage, choose Properties, open
Permissions, and enable "Allow executing file as program". Close Properties,
then double-click the AppImage and choose Run if prompted. Other Linux file
managers have a similar executable-permission setting.

From a terminal, the equivalent is:

    chmod +x $ARTIFACT_NAME-v$version-linux-x86_64.AppImage
    ./$ARTIFACT_NAME-v$version-linux-x86_64.AppImage

It should simply start. The launcher inside it does not need libfuse.so.2 --
the library whose absence has always made a downloaded AppImage do nothing at
all on a modern Ubuntu.

If it still does nothing, your machine has no /dev/fuse or no fusermount
(Ubuntu: sudo apt install fuse3). You do not need either for this tarball, and
the AppImage can also start itself without them:

    APPIMAGE_EXTRACT_AND_RUN=1 ./$ARTIFACT_NAME-v$version-linux-x86_64.AppImage

Hardware wallets
----------------
A Trezor, Ledger, Coldcard, BitBox02, KeepKey or Jade reaches you through
udev, and the rules for that travel in this directory under udev/. If your
wallet is not detected:

    sudo cp udev/*.rules /usr/lib/udev/rules.d/
    sudo udevadm control --reload-rules && sudo udevadm trigger

From the AppImage the same thing is one command:

    ./$ARTIFACT_NAME-v$version-linux-x86_64.AppImage --dsh-install-udev-rules

Unplug and replug the device afterwards.

Verify this download
--------------------
The files of this release are listed in SHA256SUMS, which is attached to the
same release page and covers every platform. Download it into this directory
and check this tarball before you run it:

    sha256sum -c SHA256SUMS

The source this was built from is on the release page too, and BUILD-SBOM.json
lists every packaged component with its version and hash.
EOF

tar -czf "$tarball" -C "$tarball_root" .

# ---- the SBOM ----------------------------------------------------------
note "Writing the SBOM"
"$venv/bin/python" scripts/build-sbom.py \
    --libusb-sha "$libusb_sha" --output dist/BUILD-SBOM.json

# ---- what was made -----------------------------------------------------
note "Artifacts in dist/"
(cd dist && ls -l ./*.AppImage ./*.tar.gz BUILD-SBOM.json linux-self-check.log)
note "sha256 of the AppImage: $(sha256sum "$appimage" | awk '{print $1}')"
note "sha256 of the tarball:  $(sha256sum "$tarball" | awk '{print $1}')"
