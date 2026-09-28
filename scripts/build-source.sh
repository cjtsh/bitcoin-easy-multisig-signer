#!/usr/bin/env bash
# Curated source tarball: no private wallet files, caches, environments or builds.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
version="${1:?Usage: scripts/build-source.sh VERSION (e.g. 0.1.0)}"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
  echo "Expected a numeric version such as 0.1.0." >&2
  exit 1
}
app_version="$(python3 -c 'from version import APP_VERSION; print(APP_VERSION)')"
[[ "$version" == "$app_version" ]] || {
  echo "Archive version $version does not match app version $app_version." >&2
  exit 1
}
root="easy-bitcoin-multisig-signer-v${version}"
mkdir -p dist
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/$root/tests" "$stage/$root/scripts" "$stage/$root/ci"
cp README.md DISCLAIMER.md replit.md requirements.txt requirements-desktop.txt version.py \
  gui.py desktop.py network_config.py network_settings.py probe.py \
  wallet_service.py ui.html "Start Easy Multisig.command" "$stage/$root/"
cp tests/test_*.py "$stage/$root/tests/"
cp scripts/build-source.sh scripts/build-macos.sh "$stage/$root/scripts/"
cp ci/build-candidate.yml "$stage/$root/ci/"
tar -C "$stage" -czf "dist/$root.tar.gz" "$root"
echo "Created dist/$root.tar.gz (source only; Python required to run it)."