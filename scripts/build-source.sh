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
mkdir -p "$stage/$root/tests" "$stage/$root/scripts" "$stage/$root/ci" "$stage/$root/releases"
cp README.md CURRENT-STATUS.md LICENSE THIRD-PARTY-NOTICES.md DISCLAIMER.md PRIVACY.md SECURITY.md CONTRIBUTING.md USER-MANUAL.md replit.md AGENTS.md PHASE-HANDOFF.md ROADMAP.md HWI-DEPENDENCY.md \
  RELEASE-HISTORY.md PROJECT-HISTORY.md CHANGE-ADDRESS-REVIEW.md \
  requirements.txt requirements.lock requirements-desktop.txt requirements-desktop.lock \
  requirements-ci.txt requirements-ci.lock version.py \
  gui.py desktop.py network_config.py network_settings.py probe.py safe_http.py \
  signing.py wallet_service.py ui.html "Start Easy Multisig.command" "$stage/$root/"

# The per-version evidence records (patch, plan, audit and security records) live in
# releases/ in the repository rather than in the root. Keep that exact layout in the
# archive: RELEASE-HISTORY.md links them as releases/<name>.md, and those links have to
# resolve for a reader who only has the tarball.
cp releases/*.md "$stage/$root/releases/"

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

# Every root document must ship too, including the licence and the third-party
# notices: the notices have no .md suffix for a glob to catch, and RELEASE-HISTORY.md
# was once left off this list while README.md and AGENTS.md still directed reviewers
# to read it, so the archive shipped a README linking to a file it did not contain.
# Every document under releases/ must ship for the same reason: RELEASE-HISTORY.md
# and the audit records link to them by name.
missing_docs=()
for file in ./*.md ./LICENSE ./THIRD-PARTY-NOTICES.md; do
  [[ -f "$stage/$root/$(basename "$file")" ]] || missing_docs+=("$(basename "$file")")
done
for file in ./releases/*.md; do
  [[ -f "$stage/$root/releases/$(basename "$file")" ]] || missing_docs+=("releases/$(basename "$file")")
done
if (( ${#missing_docs[@]} )); then
  echo "Source archive is missing documents: ${missing_docs[*]}" >&2
  exit 1
fi

# A glob copy cannot omit a record that exists, but it also cannot notice one that
# does not: RELEASE-HISTORY.md can link a record that was never written, or was
# renamed, or lives somewhere the copy line does not reach. That is the same defect
# class as the missing RELEASE-HISTORY.md above — a shipped document pointing at a
# file the archive does not contain — so resolve every link it makes before sealing.
missing_links=()
while IFS= read -r name; do
  [[ -n "$name" ]] || continue
  [[ -f "$stage/$root/releases/$name" ]] || missing_links+=("$name")
done < <(grep -oE 'releases/[A-Za-z0-9._-]+\.md' RELEASE-HISTORY.md 2>/dev/null | sort -u | sed 's|^releases/||' || true)
if (( ${#missing_links[@]} )); then
  echo "RELEASE-HISTORY.md links records the archive does not contain: ${missing_links[*]}" >&2
  exit 1
fi
cp tests/test_*.py tests/support.py tests/fake_explorer.py \
  tests/ui_*.cjs "$stage/$root/tests/"
mkdir -p "$stage/$root/assets"
cp assets/icon.svg assets/AppIcon.icns "$stage/$root/assets/"
mkdir -p "$stage/$root/vendor"
cp vendor/README.md vendor/embit-upstream-2b375a.tar.gz \
  vendor/embit-0.8.2+besa.1.tar.gz \
  vendor/embit-0.8.2+besa.1-py3-none-any.whl "$stage/$root/vendor/"
# USER-MANUAL.md links to these sanitized interface illustrations. Keep them in
# the source archive so the guide remains complete outside the Git checkout.
mkdir -p "$stage/$root/docs/assets"
cp docs/assets/manual-*.svg docs/assets/app-preview-developer-mode.svg \
  "$stage/$root/docs/assets/"
cp docs/privacy.html "$stage/$root/docs/privacy.html"
# Glob, not a list: build-macos.sh calls notary-args.sh, and an archive missing a
# script it invokes would build nothing while looking complete.
cp scripts/*.sh scripts/*.py scripts/*.plist "$stage/$root/scripts/"
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
