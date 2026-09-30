#!/usr/bin/env bash
# Run ON a Mac. Build a self-contained desktop .app and a drag-to-install DMG.
# This does not publish a release. RELEASE=1 requires signing and notarization.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
[[ "$(uname -s)" == "Darwin" ]] || {
  echo "DMGs must be built and tested on macOS." >&2
  exit 1
}
[[ "$(uname -m)" == "arm64" ]] || {
  echo "The Mac app supports Apple Silicon (M-series) only; Intel-based Macs are not supported." >&2
  exit 1
}
version="${1:?Usage: scripts/build-macos.sh VERSION (e.g. 0.1.0)}"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
  echo "Expected a numeric version such as 0.1.0." >&2
  exit 1
}
app_version="$(python3 -c 'from version import APP_VERSION; print(APP_VERSION)')"
[[ "$version" == "$app_version" ]] || {
  echo "DMG version $version does not match app version $app_version." >&2
  exit 1
}
if [[ "${RELEASE:-0}" == 1 && ( -z "${MAC_SIGN_IDENTITY:-}" || -z "${MAC_NOTARY_PROFILE:-}" ) ]]; then
  echo "Public DMG requires MAC_SIGN_IDENTITY and MAC_NOTARY_PROFILE on this Mac." >&2
  exit 1
fi
# hwi 3.2.0 declares Requires-Python >=3.9,<3.13 and is bundled into the app, so a
# newer interpreter cannot install it. Fail here with an actionable message
# instead of deep inside pip.
python_minor="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
case "$python_minor" in
  3.9|3.10|3.11|3.12) ;;
  *)
    echo "This build needs Python 3.9-3.12; found Python $python_minor." >&2
    echo "The bundled hardware-wallet tool (hwi 3.2.0) requires >=3.9,<3.13." >&2
    echo "Install Python 3.12 (for example: brew install python@3.12), put it" >&2
    echo "first on PATH, or build through the GitHub Actions workflow, which" >&2
    echo "pins Python 3.12." >&2
    exit 1
    ;;
esac
# Always rebuild the virtualenv from scratch: a stale .build-venv left over from
# an earlier run (possibly with tampered or outdated dependencies) must never be
# reused to produce a build.
rm -rf .build-venv
python3 -m venv .build-venv
.build-venv/bin/python -m pip install --disable-pip-version-check --require-hashes \
  -r requirements-desktop.lock
[[ -f assets/AppIcon.icns ]] || { echo "assets/AppIcon.icns is missing." >&2; exit 1; }
args=(--noconfirm --clean --windowed --onedir --name "Bitcoin Easy Signer"
      --icon "assets/AppIcon.icns"
      --add-data "ui.html:." --add-data "LICENSE:." --add-data "THIRD-PARTY-NOTICES.md:." \
      --collect-data certifi --distpath dist desktop.py)
if [[ -n "${MAC_SIGN_IDENTITY:-}" ]]; then
  args+=(--codesign-identity "$MAC_SIGN_IDENTITY")
fi
.build-venv/bin/python -m PyInstaller "${args[@]}"
app="dist/Bitcoin Easy Signer.app"
[[ -d "$app" ]] || { echo "PyInstaller did not produce the macOS app." >&2; exit 1; }
libusb_dylib="$(brew --prefix libusb)/lib/libusb-1.0.0.dylib"
[[ -f "$libusb_dylib" ]] || {
  echo "Bundling HWI requires libusb; install it with: brew install libusb" >&2
  exit 1
}
# Integrity check for the bundled native library. The dylib is copied into the
# app with --add-binary and is then code-signed, so a swapped or unexpected
# Homebrew build would ship as trusted signed code. Verify it first.
#
# Compute the digest on a Mac you trust:
#   shasum -a 256 "$(brew --prefix libusb)/lib/libusb-1.0.0.dylib"
# Then build with the expected digest (64 lowercase hex characters):
#   LIBUSB_SHA256=<64-hex> bash scripts/build-macos.sh <version>
# LIBUSB_SHA256 is mandatory: no artifact is built from an unverified dylib.
libusb_sha256="$(shasum -a 256 "$libusb_dylib" | awk '{print $1}')"
if [[ -n "${LIBUSB_SHA256:-}" ]]; then
  [[ "${LIBUSB_SHA256}" =~ ^[0-9a-fA-F]{64}$ ]] || {
    echo "LIBUSB_SHA256 must be a 64-character hex SHA-256 digest." >&2
    exit 1
  }
  libusb_sha256_expected="$(printf '%s' "$LIBUSB_SHA256" | tr '[:upper:]' '[:lower:]')"
  if [[ "$libusb_sha256_expected" != "$libusb_sha256" ]]; then
    echo "libusb integrity check FAILED: $libusb_dylib" >&2
    echo "  expected (LIBUSB_SHA256):   $libusb_sha256_expected" >&2
    echo "  actual   (shasum -a 256):   $libusb_sha256" >&2
    echo "Refusing to bundle a native library that does not match LIBUSB_SHA256." >&2
    exit 1
  fi
  echo "libusb integrity check passed (sha256 $libusb_sha256)."
else
  echo "LIBUSB_SHA256 is required; refusing an unverified native library." >&2
  echo "Observed digest: $libusb_sha256" >&2
  exit 1
fi
hwi_args=(--noconfirm --clean --onefile --name hwi --collect-all hwilib
          --collect-all hid --collect-all requests --collect-all urllib3
          --collect-all certifi --add-binary "$libusb_dylib:." --distpath dist/hwi
          scripts/hwi_entry.py)
if [[ -n "${MAC_SIGN_IDENTITY:-}" ]]; then
  hwi_args+=(--codesign-identity "$MAC_SIGN_IDENTITY")
fi
.build-venv/bin/python -m PyInstaller "${hwi_args[@]}"
cp dist/hwi/hwi "$app/Contents/MacOS/hwi"
chmod 755 "$app/Contents/MacOS/hwi"
"$app/Contents/MacOS/hwi" --help >/dev/null
# Adding HWI after PyInstaller created the app invalidates its original seal, so
# the bundle is signed again here. Recursive signing is deliberately NOT used:
# Apple deprecates it and it does not reliably sign nested code, so every nested
# Mach-O executable is signed explicitly, innermost first, and only then is the
# .app itself sealed.
# PyInstaller leaves CFBundleShortVersionString at 0.0.0, so Finder's Get Info
# would misreport which test build is installed. Record the real version before
# the bundle is sealed.
plist="$app/Contents/Info.plist"
for key in CFBundleShortVersionString CFBundleVersion; do
  /usr/libexec/PlistBuddy -c "Set :$key $version" "$plist" 2>/dev/null \
    || /usr/libexec/PlistBuddy -c "Add :$key string $version" "$plist"
done
# Strip extended attributes before signing. On a machine whose files live in a
# synced folder (iCloud/Documents FileProvider), macOS attaches com.apple.FinderInfo
# and com.apple.fileprovider.* to bundle contents; codesign --verify --strict
# rejects those as unsealed "detritus", which would fail a notarized release.
xattr -cr "$app"
sign_flags=(--force)
sign_identity="-"
if [[ -n "${MAC_SIGN_IDENTITY:-}" ]]; then
  sign_flags+=(--options runtime)
  sign_identity="$MAC_SIGN_IDENTITY"
fi

sign_nested_executable() {
  local target="$1"
  echo "Signing nested executable: $target"
  codesign "${sign_flags[@]}" --sign "$sign_identity" "$target"
}

hwi_bin="$app/Contents/MacOS/hwi"
[[ -f "$hwi_bin" ]] || {
  echo "The bundled hwi binary is missing from $app/Contents/MacOS." >&2
  exit 1
}

signed_hwi=0
while IFS= read -r -d '' candidate; do
  case "$(file -b "$candidate")" in
    *Mach-O*)
      sign_nested_executable "$candidate"
      if [[ "$candidate" == "$hwi_bin" ]]; then
        signed_hwi=1
      fi
      ;;
  esac
done < <(find "$app/Contents/MacOS" -type f -print0)
(( signed_hwi == 1 )) || {
  echo "Bundled hwi ($hwi_bin) was not signed as a Mach-O executable; refusing to continue." >&2
  exit 1
}

# Seal the .app last, with no recursive signing.
codesign "${sign_flags[@]}" --sign "$sign_identity" "$app"
codesign --verify --strict --verbose=2 "$app" || {
  echo "codesign verification failed for $app." >&2
  exit 1
}
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
cp -R "$app" "$stage/"
# The copy inside the DMG is what users receive; make sure it carries no stray
# extended attributes either.
xattr -cr "$stage/$(basename "$app")"
ln -s /Applications "$stage/Applications"
if [[ "${RELEASE:-0}" == 1 ]]; then
  dmg="dist/Bitcoin-Easy-Signer-v${version}-macOS.dmg"
else
  dmg="dist/Bitcoin-Easy-Signer-v${version}-UNSIGNED-TEST.dmg"
fi
hdiutil create -ov -format UDZO -volname "Bitcoin Easy Signer" \
  -srcfolder "$stage" "$dmg"
if [[ "${RELEASE:-0}" == 1 ]]; then
  xcrun notarytool submit "$dmg" --keychain-profile "$MAC_NOTARY_PROFILE" --wait
  xcrun stapler staple "$dmg"
else
  echo "UNSIGNED TEST BUILD: not suitable for a simple public Mac installation."
fi
echo "Created $dmg; test opening the app, file import, balance, and native PSBT save on a Mac."
