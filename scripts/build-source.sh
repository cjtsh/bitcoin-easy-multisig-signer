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
cp README.md CURRENT-STATUS.md LICENSE THIRD-PARTY-NOTICES.md DISCLAIMER.md replit.md AGENTS.md PHASE-HANDOFF.md ROADMAP.md \
  RELEASE-HISTORY.md PROJECT-HISTORY.md AUDIT-BASELINE-0.1.27.md \
  AUDIT-DEEPSEEK-0.4.3.md AUDIT-ZAI-0.4.3.md SECURITY-REVIEW-0.2.0.md \
  PATCH-0.2.1.md PATCH-0.2.2.md PATCH-0.3.0.md PATCH-0.3.1.md PATCH-0.3.2.md PATCH-0.4.0.md PATCH-0.4.1.md PATCH-0.4.2.md PATCH-0.4.6.md CHANGE-ADDRESS-REVIEW.md \
  PLAN-0.3.0.md PLAN-0.4.4.md MUTINYNET-0.3.0.md \
  requirements.txt requirements.lock requirements-desktop.txt requirements-desktop.lock version.py \
  gui.py desktop.py network_config.py network_settings.py probe.py safe_http.py \
  signing.py wallet_service.py ui.html "Start Easy Multisig.command" "$stage/$root/"
