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
# Which notarisation credentials to present. notary-args.sh refuses a partial or
# ambiguous configuration rather than guessing, because guessing would mean signing
# with credentials the operator did not intend.
if ! notary_output="$(bash scripts/notary-args.sh)"; then
  echo "Notarisation credentials are set incompletely; refusing to guess." >&2
  exit 1
fi
notary_args=()
if [[ -n "$notary_output" ]]; then
  # A while-read loop, not mapfile: macOS ships bash 3.2, which has no mapfile.
  while IFS= read -r line; do
    [[ -n "$line" ]] && notary_args+=("$line")
  done <<< "$notary_output"
fi
if [[ "${RELEASE:-0}" == 1 && ( -z "${MAC_SIGN_IDENTITY:-}" || ${#notary_args[@]} -eq 0 ) ]]; then
  echo "Public DMG requires MAC_SIGN_IDENTITY and a notarisation credential: set MAC_NOTARY_PROFILE, or all of MAC_NOTARY_KEY_PATH, MAC_NOTARY_KEY_ID and MAC_NOTARY_ISSUER_ID." >&2
  exit 1
fi
# hwi 3.2.0 declares Requires-Python >=3.9,<3.13 and is bundled into the app, so a
# newer interpreter cannot install it. Fail here with an actionable message
# instead of deep inside pip.
#
# PYTHON names the interpreter, because on macOS the right one usually is NOT
# reachable as "python3". Homebrew's versioned kegs ship only python3.12, and the
# unversioned python3 belongs to whatever the default formula is. Telling somebody
# to "put 3.12 first on PATH" therefore cannot work - no python3 exists in that
# directory - and the shim it forces people to invent is easy to get wrong.
# Naming the interpreter outright is the only advice that holds on every machine.
python_bin="${PYTHON:-python3}"
command -v "$python_bin" >/dev/null 2>&1 || {
  echo "PYTHON=$python_bin was not found on PATH." >&2
    echo "Name a Python 3.10-3.12 interpreter, for example:" >&2
  echo "  PYTHON=python3.12 bash scripts/build-macos.sh <version>" >&2
  exit 1
}
python_minor="$("$python_bin" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
case "$python_minor" in
  3.10|3.11|3.12) ;;
  *)
    echo "This build needs Python 3.10-3.12; $python_bin is Python $python_minor." >&2
    echo "The bundled HWI requires <3.13 and embit requires >=3.10." >&2
    echo "Name a supported interpreter explicitly:" >&2
    echo "  PYTHON=python3.12 bash scripts/build-macos.sh $version" >&2
    echo "Homebrew's kegs provide python3.12 but deliberately no python3, so adding" >&2
    echo "them to PATH does not help. The GitHub Actions workflow pins 3.12 already." >&2
    exit 1
    ;;
esac
# Local builds always recreate the environment. CI prepares it before any
# signing secret is imported, then explicitly reuses that same environment in
# the build step; no install or fetch occurs while the certificate is present.
if [[ "${BUILD_DEPS_PREPARED:-0}" == 1 ]]; then
  [[ -x .build-venv/bin/python ]] || {
    echo "Prepared build environment is missing." >&2
    exit 1
  }
  expected_lock_sha="$(shasum -a 256 requirements-desktop.lock | awk '{print $1}')"
  [[ -f .build-venv/requirements-desktop.sha256 && \
     "$(cat .build-venv/requirements-desktop.sha256)" == "$expected_lock_sha" ]] || {
    echo "Prepared build environment does not match the desktop lock." >&2
    exit 1
  }
else
  rm -rf .build-venv
  "$python_bin" -m venv .build-venv
  .build-venv/bin/python -m pip install --disable-pip-version-check --require-hashes \
    -r requirements-desktop.lock
  shasum -a 256 requirements-desktop.lock | awk '{print $1}' \
    > .build-venv/requirements-desktop.sha256
fi
if [[ "${PREPARE_ONLY:-0}" == 1 ]]; then
  echo "Hash-locked build environment prepared."
  exit 0
fi
[[ -f assets/AppIcon.icns ]] || { echo "assets/AppIcon.icns is missing." >&2; exit 1; }
args=(--noconfirm --clean --windowed --onedir --name "Bitcoin Easy Signer"
      --icon "assets/AppIcon.icns"
      --add-data "ui.html:." --add-data "LICENSE:." --add-data "DISCLAIMER.md:." --add-data "PRIVACY.md:." --add-data "THIRD-PARTY-NOTICES.md:." \
      --add-data "vendor/libusb-COPYING:." \
      --collect-data certifi --distpath dist desktop.py)
if [[ -n "${MAC_SIGN_IDENTITY:-}" ]]; then
  args+=(--codesign-identity "$MAC_SIGN_IDENTITY")
fi
.build-venv/bin/python -m PyInstaller "${args[@]}"
app="dist/Bitcoin Easy Signer.app"
[[ -d "$app" ]] || { echo "PyInstaller did not produce the macOS app." >&2; exit 1; }
libusb_dylib="vendor/libusb-1.0.0.dylib"
[[ -f "$libusb_dylib" ]] || {
  echo "Bundling HWI requires the vendored libusb input at $libusb_dylib." >&2
  exit 1
}
# Integrity check for the bundled native library. The dylib is copied into the
# app with --add-binary and is then code-signed, so a swapped or unexpected
# binary would ship as trusted signed code. Verify it first.
#
# The input was captured from a successful macOS CI run before signing and
# committed under vendor/; vendor/README.md records its provenance. Build with
# the reviewed expected digest (64 lowercase hex characters):
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
mkdir -p build/libusb-alias
cp -f "$libusb_dylib" build/libusb-alias/libusb-1.0.dylib
hwi_args=(--noconfirm --clean --onefile --name hwi --collect-all hwilib
          --collect-all hid --collect-all requests --collect-all urllib3
          --collect-all certifi --add-binary "$libusb_dylib:." \
          --add-binary "build/libusb-alias/libusb-1.0.dylib:." --distpath dist/hwi
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
  if [[ "$target" == "$hwi_bin" && -n "${MAC_SIGN_IDENTITY:-}" ]]; then
    # HWI is a one-file PyInstaller helper. At runtime it extracts the bundled
    # libusb dylib (Homebrew-signed ad hoc) to its private temp directory. The
    # hardened runtime otherwise rejects that nested library before HWI can
    # enumerate any USB devices. Scope the exception to HWI, never the GUI app.
    codesign "${sign_flags[@]}" --entitlements scripts/hwi-entitlements.plist \
      --sign "$sign_identity" "$target"
  else
    codesign "${sign_flags[@]}" --sign "$sign_identity" "$target"
  fi
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

# Exercise the exact packaged USB stack before sealing the app. This loads libusb
# and queries USB descriptors without opening a hardware wallet or prompting it.
# On current macOS this launch can add a provenance xattr, so the bundle is cleaned
# again below before the outer code signature is made.
if ! "$hwi_bin" --dsh-check-libusb >/dev/null; then
  echo "Bundled HWI could not load libusb and query USB devices." >&2
  exit 1
fi

# macOS can attach com.apple.provenance while a nested helper is executed. Strip
# build-time xattrs after that preflight and before sealing the outer app.
xattr -cr "$app"

# Seal the .app last, with no recursive signing.
codesign "${sign_flags[@]}" --sign "$sign_identity" "$app"
codesign --verify --strict --verbose=2 "$app" || {
  echo "codesign verification failed for $app." >&2
  exit 1
}
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
if [[ "${RELEASE:-0}" == 1 ]]; then
  # Notarise and staple the APP before the image exists.
  #
  # The order matters and used to be wrong: the image was built first, from a copy
  # of an app that had no ticket, so the copy a downloader received carried none
  # either and Gatekeeper fell back to an ONLINE lookup - accepted when connected,
  # refused offline. For a tool people open when something has gone wrong, that is
  # the wrong way to fail.
  #
  # This was left undone because it needs a second Apple round trip and the first
  # submission took 54 minutes. Measured on 0.4.13: a later submission for the same
  # team took about 40 SECONDS, so the objection no longer holds.
  #
  # notarytool takes an archive, not a bare .app, hence the temporary zip.
  app_zip="dist/Bitcoin-Easy-Signer-v${version}-app.zip"
  ditto -c -k --keepParent "$app" "$app_zip"
  xcrun notarytool submit "$app_zip" "${notary_args[@]}" --wait
  rm -f "$app_zip"
  xcrun stapler staple "$app"
  xcrun stapler validate "$app"
fi
# The image is built from the app as it now stands, ticket included.
cp -R "$app" "$stage/"
# Strip extended attributes from the STAGED COPY only, and note that this must not
# be moved after notarisation: the staple is carried on the bundle, so clearing
# xattrs afterwards would take the ticket with it. The app itself was already
# cleaned before signing.
ln -s /Applications "$stage/Applications"
if [[ "${RELEASE:-0}" == 1 ]]; then
  dmg="dist/Bitcoin-Easy-Signer-v${version}-macOS.dmg"
else
  dmg="dist/Bitcoin-Easy-Signer-v${version}-UNSIGNED-TEST.dmg"
fi
hdiutil create -ov -format UDZO -volname "Bitcoin Easy Signer" \
  -srcfolder "$stage" "$dmg"
if [[ "${RELEASE:-0}" == 1 ]]; then
  xcrun notarytool submit "$dmg" "${notary_args[@]}" --wait
  xcrun stapler staple "$dmg"
  xcrun stapler validate "$dmg"
  # Prove the ticket reached the copy INSIDE the image, not just the build tree.
  # That copy is what a downloader runs, and it is the whole reason the app is
  # notarised before the image is made. A build that ships an unstapled app must
  # fail here rather than at somebody's first offline launch.
  mount_point="$(mktemp -d)"
  hdiutil attach "$dmg" -nobrowse -readonly -mountpoint "$mount_point" -quiet
  xcrun stapler validate "$mount_point/$(basename "$app")"
  spctl -a -t exec -vv "$mount_point/$(basename "$app")"
  hdiutil detach "$mount_point" -quiet
  rmdir "$mount_point"
  # Also staple the built app in dist/, which makes THAT copy self-contained for
  # offline testing here.
  #
  # This does NOT put a ticket inside the DMG, and an earlier version of this comment
  # claimed it did. The image was created at the line above from a copy taken before
  # this point, so the app a downloader receives stays unstapled and Gatekeeper
  # verifies it with an ONLINE lookup: accepted when connected, refused offline.
  # Measured on the published v0.4.12 DMG -- the image validates, the app inside
  # reports "does not have a ticket stapled to it".
  #
  # Closing that properly means notarizing and stapling the app FIRST, then building
  # the DMG from the stapled app, which costs a second Apple round trip per release.
  # Recorded rather than silently reasserted; see PHASE-HANDOFF.md.
  xcrun stapler staple "$app"
  xcrun stapler validate "$dmg"
  xcrun stapler validate "$app"
  # Gatekeeper is the gate the operator actually meets, so prove it here and fail
  # rather than ship an artifact that cannot be opened.
  #
  # Assess the APP, not the DMG. A disk image is not code-signed and
  # `spctl --type open` reports "rejected, source=no usable signature" for a
  # perfectly good notarized image -- measured against a real one, not assumed.
  # The app inside is what Gatekeeper must accept, and it reports
  # "accepted, Notarized Developer ID".
  spctl -a -t exec -vv "$app"
else
  echo "UNSIGNED TEST BUILD: not suitable for a simple public Mac installation."
fi
echo "Created $dmg; test opening the app, file import, balance, and native PSBT save on a Mac."
