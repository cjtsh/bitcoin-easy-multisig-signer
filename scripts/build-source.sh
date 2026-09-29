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
root="bitcoin-easy-multisig-signer-v${version}"
mkdir -p dist
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/$root/tests" "$stage/$root/scripts" "$stage/$root/ci"
cp README.md DISCLAIMER.md replit.md AGENTS.md PHASE-HANDOFF.md ROADMAP.md \
  PROJECT-HISTORY.md AUDIT-BASELINE-0.1.27.md SECURITY-REVIEW-0.2.0.md \
  PATCH-0.2.1.md \
  requirements.txt requirements.lock requirements-desktop.txt requirements-desktop.lock version.py \
  gui.py desktop.py network_config.py network_settings.py probe.py safe_http.py \
  signing.py wallet_service.py ui.html "Start Easy Multisig.command" "$stage/$root/"

# Every root module must ship. Omitting safe_http.py produced an archive whose own
# code could not import, and nothing noticed because CI ran the tests from the
# checkout rather than from the archive.
missing=()
for file in ./*.py; do
  [[ -f "$stage/$root/$(basename "$file")" ]] || missing+=("$(basename "$file")")
done
if (( ${#missing[@]} )); then
  echo "Source archive is incomplete; missing: ${missing[*]}" >&2
  exit 1
fi
cp tests/test_*.py tests/support.py tests/fake_explorer.py "$stage/$root/tests/"
mkdir -p "$stage/$root/assets"
cp assets/icon.svg assets/AppIcon.icns "$stage/$root/assets/"
cp scripts/build-source.sh scripts/build-macos.sh scripts/build-sbom.py scripts/hwi_entry.py \
  scripts/make-icon.sh "$stage/$root/scripts/"
if [[ -f ci/build-candidate.yml ]]; then
  workflow=ci/build-candidate.yml
elif [[ -f .github/workflows/build-candidate.yml ]]; then
  workflow=.github/workflows/build-candidate.yml
else
  echo "Candidate build recipe is missing." >&2
  exit 1
fi
cp "$workflow" "$stage/$root/ci/build-candidate.yml"
tar -C "$stage" -czf "dist/$root.tar.gz" "$root"
echo "Created dist/$root.tar.gz (source only; Python required to run it)."
