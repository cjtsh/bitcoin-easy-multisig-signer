#!/usr/bin/env bash
# Curated source tarball: no private wallet files, caches, environments or builds.
#
# This is the Windows port's archive, and it deliberately excludes docs/ — the
# GitHub Pages website is a published site, not a build input. It does NOT
# exclude scripts/*.plist any more: build-macos.sh codesigns the bundled HWI
# helper with scripts/hwi-entitlements.plist, so a tarball that left the plist
# out could not reproduce a signed Mac build from itself. The remaining
# completeness checks are kept in spirit: they caught a real defect each, and a
# rewritten copy step is exactly when they stop matching reality.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
version="${1:?Usage: scripts/build-source.sh VERSION (e.g. 0.6.4)}"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
  echo "Expected a numeric version such as 0.6.4." >&2
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
root_docs=(
  README.md CURRENT-STATUS.md DISCLAIMER.md PRIVACY.md SECURITY.md
  CONTRIBUTING.md USER-MANUAL.md replit.md AGENTS.md RELEASE-PROCESS.md
  PHASE-HANDOFF.md ROADMAP.md HWI-DEPENDENCY.md RELEASE-HISTORY.md
  PROJECT-HISTORY.md CHANGE-ADDRESS-REVIEW.md WINDOWS-PORT.md LINUX-PORT.md
  SIGNING.md requirements-desktop-linux.txt
)
# requirements-desktop-windows.lock is the only lock that can be installed on
# Windows. requirements-desktop.lock is macOS-resolved and is deliberately still
# shipped: it is the record of what the audited macOS build installs, and dropping
# it here would silently erase that. requirements-desktop-linux.lock is the
# Linux-resolved record, and the archive's own test suite checks it.
cp "${root_docs[@]}" LICENSE THIRD-PARTY-NOTICES.md "Start Easy Multisig.command" \
  requirements.txt requirements.lock requirements-desktop.txt requirements-desktop.lock \
  requirements-desktop-windows.lock requirements-desktop-linux.lock \
  requirements-ci.txt requirements-ci.lock \
  requirements-piptools.txt requirements-piptools.lock version.py \
  gui.py desktop.py network_config.py network_settings.py probe.py safe_http.py \
  signing.py wallet_service.py ui.html "$stage/$root/"

# The per-version evidence records (patch, plan, audit and security records) live in
# releases/ in the repository rather than in the root. Keep that exact layout in the
# archive: RELEASE-HISTORY.md links them as releases/<name>.md, and those links have to
# resolve for a reader who only has the tarball.
cp releases/*.md "$stage/$root/releases/"

# The machine-readable half of the release evidence ships too: a reader of the
# tarball holds the platform record (environments, branch policies, required
# reviewers, secret *names*, rulesets, registrations) and the script that diffs
# it against the live platform, so the record can be re-checked without network
# access to this repository's history.
if compgen -G "releases/*.json" >/dev/null; then
  cp releases/*.json "$stage/$root/releases/"
fi

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
for file in "${root_docs[@]}" LICENSE THIRD-PARTY-NOTICES.md; do
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
cp assets/icon.svg assets/AppIcon.icns assets/AppIcon.ico "$stage/$root/assets/"
mkdir -p "$stage/$root/assets/manual"
cp assets/manual/*.svg "$stage/$root/assets/manual/"

# USER-MANUAL.md underlines every step with an illustration. Those images lived in
# docs/assets/ for the website; deleting the website would have left the manual
# pointing at nine files the archive does not contain, so they moved to
# assets/manual/ and the links moved with them. Resolve the links from the document
# itself rather than from a list, so a tenth illustration cannot be forgotten here.
#
# This runs after the copy above on purpose. A completeness check that runs before
# the copy it is checking reports every file as missing, which is what it did.
missing_manual=()
while IFS= read -r target; do
  [[ -n "$target" ]] || continue
  [[ -f "$stage/$root/$target" ]] || missing_manual+=("$target")
done < <(grep -oE 'assets/manual/[A-Za-z0-9._-]+\.svg' USER-MANUAL.md 2>/dev/null | sort -u || true)
# Only the illustrations the manual actually references are shipped, so a stale link
# in the manual is caught here rather than at a reader's screen. The loop is inside the
# guard because macOS ships bash 3.2, where "${array[@]}" on an empty array is an
# unbound variable under `set -u`.
if (( ${#missing_manual[@]} )); then
  for target in "${missing_manual[@]}"; do
    echo "USER-MANUAL.md references an illustration to copy first: $target" >&2
  done
  exit 1
fi
mkdir -p "$stage/$root/vendor"
# Both reviewed native libraries ship with the archive. The suite that runs from
# inside the extracted archive verifies each one against the digest recorded in
# tests/test_libusb_vendor.py on every platform, so an archive that dropped a
# library would fail its own tests -- which is the point: the archive has to be a
# complete copy of the two build paths, not a platform-specific subset. The
# libusb-1.0.30 tarball is the source both libraries are accountable to.
cp vendor/README.md vendor/embit-upstream-2b375a.tar.gz \
  vendor/embit-0.8.2+besa.1.tar.gz \
  vendor/embit-0.8.2+besa.1-py3-none-any.whl \
  vendor/libusb-1.0.0.dylib \
  vendor/libusb-1.0.30.tar.bz2 \
  vendor/libusb-1.0.dll \
  vendor/appimage-runtime-x86_64 \
  vendor/libusb-COPYING "$stage/$root/vendor/"
# The hwilib payload manifest is a vendor record like the libraries above, and the
# archive's own suite reads it (tests/test_hardening_pins.py): an archive that left
# it out could not verify the package it ships instructions for.
cp vendor/hwi-payload-*.json "$stage/$root/vendor/"
# Glob, not a list: build-windows.ps1 calls the other scripts, and an archive missing
# a script it invokes would build nothing while looking complete. The plist is not
# optional either — build-macos.sh passes it to codesign for the bundled HWI helper,
# and a signed Mac build from this tarball fails without it (CT-56).
cp scripts/*.sh scripts/*.py scripts/*.ps1 scripts/*.plist "$stage/$root/scripts/"
# The build recipes, under ci/ rather than .github/workflows/, because the archive
# is a source tree and the workflow contract tests read them from wherever they
# land. One pipeline builds and publishes every platform; the two input producers
# feed it reviewed Windows and Linux build inputs.
for recipe in build-candidate.yml windows-inputs.yml linux-inputs.yml; do
  if [[ -f "ci/$recipe" ]]; then
    workflow="ci/$recipe"
  elif [[ -f ".github/workflows/$recipe" ]]; then
    workflow=".github/workflows/$recipe"
  else
    echo "Build recipe $recipe is missing." >&2
    exit 1
  fi
  cp "$workflow" "$stage/$root/ci/$recipe"
done
tar -C "$stage" -czf "dist/$root.tar.gz" "$root"
echo "Created dist/$root.tar.gz (source only; Python required to run it)."
