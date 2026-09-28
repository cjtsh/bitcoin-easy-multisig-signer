#!/usr/bin/env bash
# Run ON a Mac. Build a self-contained desktop .app and a drag-to-install DMG.
# This does not publish a release. RELEASE=1 requires signing and notarization.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
[[ "$(uname -s)" == "Darwin" ]] || {
  echo "DMGs must be built and tested on macOS." >&2
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
python3 -m venv .build-venv
.build-venv/bin/python -m pip install --disable-pip-version-check -r requirements-desktop.txt
args=(--noconfirm --clean --windowed --onedir --name "Easy Bitcoin Multisig"
      --add-data "ui.html:." --collect-data certifi --distpath dist desktop.py)
if [[ -n "${MAC_SIGN_IDENTITY:-}" ]]; then
  args+=(--codesign-identity "$MAC_SIGN_IDENTITY")
fi
.build-venv/bin/python -m PyInstaller "${args[@]}"
app="dist/Easy Bitcoin Multisig.app"
[[ -d "$app" ]] || { echo "PyInstaller did not produce the macOS app." >&2; exit 1; }
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
cp -R "$app" "$stage/"
ln -s /Applications "$stage/Applications"
if [[ "${RELEASE:-0}" == 1 ]]; then
  dmg="dist/Easy-Bitcoin-Multisig-v${version}-macOS.dmg"
else
  dmg="dist/Easy-Bitcoin-Multisig-v${version}-UNSIGNED-TEST.dmg"
fi
hdiutil create -ov -format UDZO -volname "Easy Bitcoin Multisig" \
  -srcfolder "$stage" "$dmg"
if [[ "${RELEASE:-0}" == 1 ]]; then
  xcrun notarytool submit "$dmg" --keychain-profile "$MAC_NOTARY_PROFILE" --wait
  xcrun stapler staple "$dmg"
else
  echo "UNSIGNED TEST BUILD: not suitable for a simple public Mac installation."
fi
echo "Created $dmg; test opening the app, file import, balance, and native PSBT save on a Mac."