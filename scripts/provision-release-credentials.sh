#!/usr/bin/env bash
#
# provision-release-credentials.sh — rebuild the release credentials in the two
# GitHub environments from the copies that live on this Mac.
#
# Why this exists: GitHub never returns a secret's value, not even to an
# administrator, so a lost environment secret can only be rebuilt from its master
# copy. Every release credential except the Apple app-specific password has one on
# this machine — the release key is in the GnuPG keyring and the Developer ID
# identity is in the login keychain — so this script re-derives them, re-sets them
# and re-proves them in one command. It never prints a value, it passes every value
# on standard input rather than in argv (argv is visible to `ps`), and it keeps its
# working copy in a mode-700 temporary directory that is scrubbed on exit.
#
# See SIGNING.md → "If the credentials vanish" for the runbook.
#
set -euo pipefail

REPO_DEFAULT="cjtsh/bitcoin-easy-multisig-signer"
RELEASE_ENV="release-signing"
APPLE_ENV="apple-signing"

# The master copies, pinned by fingerprint so the script cannot silently pick up a
# different key or certificate that happens to be on the machine.
GPG_FINGERPRINT="ACCC2F1CD4369128D549CC58E97285D2DD0BD6D7"
GPG_UID="Bitseeker LLC <release@bitseeker.llc>"
CERT_SHA1="02624AD5998203927864C7167C461DE0E6D19707"
CERT_LABEL="Developer ID Application: Bitseeker LLC (B8G5L7M8TB)"
LOGIN_KEYCHAIN="$HOME/Library/Keychains/login.keychain-db"

# GitHub rejects an empty secret, and the release key in use carries no passphrase
# so the publish job can sign unattended, so this name holds a placeholder that
# says exactly that. The workflow branches on non-empty and gpg ignores it for an
# unprotected key. If the key is ever given a passphrase, set the real one here.
GPG_PASSPHRASE_PLACEHOLDER="unused-the-release-key-carries-no-passphrase"

REPO="$REPO_DEFAULT"
DRY=0; ONLY=""; PRUNE=0; VERIFY=1; KEEP=0; APP_FILE=""; APP_PROMPT=0

usage() {
  cat <<'EOF'
Rebuild the release credentials in the GitHub environments from this Mac.

Usage: scripts/provision-release-credentials.sh [options]

  --repo <owner/name>          repository (default cjtsh/bitcoin-easy-multisig-signer)
  --only <name>[,<name>...]    provision only these secret names
  --app-password-file <path>   read MAC_APP_SPECIFIC_PASSWORD from this file
  --app-password-prompt        ask for it (input never echoed, never in history)
  --prune                      delete repository-level copies of what was touched
  --no-verify                  skip scripts/check-release-credentials.sh
  --dry-run                    print the plan and touch nothing
  --keep-temp                  keep the mode-700 temp dir (debugging only)
  -h, --help                   this text

The four machine-recoverable secrets are re-derived from their master copies; the
Apple app-specific password can only come from the owner, because only they can
sign in to appleid.apple.com and create one.
EOF
}

die() { echo "provision-release-credentials: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) [ $# -ge 2 ] || die "--repo needs a value"; REPO="$2"; shift 2 ;;
    --only) [ $# -ge 2 ] || die "--only needs a value"; ONLY="$2"; shift 2 ;;
    --app-password-file) [ $# -ge 2 ] || die "--app-password-file needs a path"; APP_FILE="$2"; shift 2 ;;
    --app-password-prompt) APP_PROMPT=1; shift ;;
    --prune) PRUNE=1; shift ;;
    --no-verify) VERIFY=0; shift ;;
    --dry-run) DRY=1; shift ;;
    --keep-temp) KEEP=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "unknown option: $1" ;;
  esac
done

case "$REPO" in
  */*) ;;
  *) die "--repo must look like owner/name" ;;
esac

# Which names to touch. No --only means all of them.
want() {
  if [ -z "$ONLY" ]; then return 0; fi
  case ",$ONLY," in
    *",$1,"*) return 0 ;;
    *) return 1 ;;
  esac
}

for name in ${ONLY//,/ }; do
  case "$name" in
    GPG_PRIVATE_KEY|GPG_PASSPHRASE|MAC_CERT_P12_BASE64|MAC_CERT_PASSWORD|MAC_APP_SPECIFIC_PASSWORD) ;;
    *) die "unknown secret name: $name" ;;
  esac
done

if [ "$DRY" = 1 ]; then
  echo "dry run: nothing will be exported, set or deleted"
  if want GPG_PRIVATE_KEY; then echo "would set GPG_PRIVATE_KEY in $RELEASE_ENV (the armored release key $GPG_FINGERPRINT, exported from the GnuPG keyring)"; fi
  if want GPG_PASSPHRASE; then echo "would set GPG_PASSPHRASE in $RELEASE_ENV (the documented placeholder)"; fi
  if want MAC_CERT_P12_BASE64; then echo "would set MAC_CERT_P12_BASE64 in $APPLE_ENV (a fresh p12 exported from the login keychain identity \"$CERT_LABEL\" $CERT_SHA1)"; fi
  if want MAC_CERT_PASSWORD; then echo "would set MAC_CERT_PASSWORD in $APPLE_ENV (a fresh random password)"; fi
  if want MAC_APP_SPECIFIC_PASSWORD; then echo "would set MAC_APP_SPECIFIC_PASSWORD in $APPLE_ENV from --app-password-file or --app-password-prompt"; fi
  if [ "$PRUNE" = 1 ]; then echo "would delete any repository-level copy of those names"; fi
  if [ "$VERIFY" = 1 ]; then echo "would run scripts/check-release-credentials.sh"; fi
  exit 0
fi

for tool in gh gpg security base64 python3; do
  command -v "$tool" >/dev/null 2>&1 || die "required tool not found: $tool"
done

TMP="$(mktemp -d "${TMPDIR:-/tmp}/besa-cred.XXXXXX")"
chmod 700 "$TMP"
scrubbed=0

cleanup() {
  [ "$scrubbed" = 1 ] && return 0
  scrubbed=1
  if [ "$KEEP" = 1 ]; then
    echo "provision-release-credentials: kept $TMP (mode 700) for inspection" >&2
    return 0
  fi
  # Best effort only: APFS does not promise the old blocks are gone, which is why
  # nothing here is a backup destination and no value is ever written twice.
  find "$TMP" -type f 2>/dev/null | while read -r f; do
    dd if=/dev/urandom of="$f" bs=4096 count=1 conv=notrunc 2>/dev/null || true
  done
  rm -rf "$TMP"
}
trap 'cleanup || true' EXIT

set_secret() { # <environment> <name> <file>
  gh secret set "$2" --env "$1" --repo "$REPO" < "$3"
  echo "set $2 in the $1 environment"
}

provision_gpg() {
  gpg --list-secret-keys "$GPG_FINGERPRINT" >/dev/null 2>&1 \
    || die "the release key $GPG_UID ($GPG_FINGERPRINT) is not in this keyring"
  gpg --armor --export-secret-keys "$GPG_FINGERPRINT" > "$TMP/GPG_PRIVATE_KEY" 2>/dev/null
  [ -s "$TMP/GPG_PRIVATE_KEY" ] || die "exporting the release key produced nothing"
  printf '%s' "$GPG_PASSPHRASE_PLACEHOLDER" > "$TMP/GPG_PASSPHRASE"
  if want GPG_PRIVATE_KEY; then set_secret "$RELEASE_ENV" GPG_PRIVATE_KEY "$TMP/GPG_PRIVATE_KEY"; fi
  if want GPG_PASSPHRASE; then set_secret "$RELEASE_ENV" GPG_PASSPHRASE "$TMP/GPG_PASSPHRASE"; fi
}

provision_cert() {
  local pw
  security find-identity -v -p codesigning "$LOGIN_KEYCHAIN" 2>/dev/null | grep -q "$CERT_SHA1" \
    || die "$CERT_LABEL is not in $LOGIN_KEYCHAIN"
  pw="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
  printf '%s' "$pw" > "$TMP/MAC_CERT_PASSWORD"
  security export -t identities -f pkcs12 -k "$LOGIN_KEYCHAIN" -P "$pw" -o "$TMP/cert.p12" >/dev/null 2>&1 \
    || die "the login keychain refused to export the Developer ID identity"
  [ -s "$TMP/cert.p12" ] || die "the exported p12 is empty"
  # tr -d '\n' because the secret must survive JSON/API transport intact.
  base64 -i "$TMP/cert.p12" | tr -d '\n' > "$TMP/MAC_CERT_P12_BASE64"
  if want MAC_CERT_P12_BASE64; then set_secret "$APPLE_ENV" MAC_CERT_P12_BASE64 "$TMP/MAC_CERT_P12_BASE64"; fi
  if want MAC_CERT_PASSWORD; then set_secret "$APPLE_ENV" MAC_CERT_PASSWORD "$TMP/MAC_CERT_PASSWORD"; fi
}

provision_app_password() {
  local file="$TMP/MAC_APP_SPECIFIC_PASSWORD" value
  if [ -n "$APP_FILE" ]; then
    [ -r "$APP_FILE" ] || die "cannot read $APP_FILE"
    tr -d '\r\n' < "$APP_FILE" > "$file"
  elif [ "$APP_PROMPT" = 1 ]; then
    if [ -t 0 ]; then
      read -r -s -p "Apple app-specific password (input hidden): " value
      echo
    else
      read -r -s value
    fi
    printf '%s' "$value" > "$file"
    unset value
  else
    echo "no app-specific password given: leaving MAC_APP_SPECIFIC_PASSWORD alone" >&2
    return 0
  fi
  [ -s "$file" ] || die "the app-specific password is empty"
  set_secret "$APPLE_ENV" MAC_APP_SPECIFIC_PASSWORD "$file"
}

prune_repo_secrets() {
  local existing name
  existing="$(gh api "repos/$REPO/actions/secrets" --jq '.secrets[].name' 2>/dev/null || true)"
  for name in GPG_PRIVATE_KEY GPG_PASSPHRASE MAC_CERT_P12_BASE64 MAC_CERT_PASSWORD MAC_APP_SPECIFIC_PASSWORD; do
    if ! want "$name"; then continue; fi
    if printf '%s\n' "$existing" | grep -qx "$name"; then
      gh secret delete "$name" --repo "$REPO" >/dev/null
      echo "deleted the repository-level $name"
    fi
  done
}

if want GPG_PRIVATE_KEY || want GPG_PASSPHRASE; then provision_gpg; fi
if want MAC_CERT_P12_BASE64 || want MAC_CERT_PASSWORD; then provision_cert; fi
if want MAC_APP_SPECIFIC_PASSWORD && { [ -n "$APP_FILE" ] || [ "$APP_PROMPT" = 1 ]; }; then
  provision_app_password
fi
if [ "$PRUNE" = 1 ]; then prune_repo_secrets; fi

if [ "$VERIFY" = 1 ]; then
  echo
  echo "== the standing check =="
  if ! bash "$(dirname "$0")/check-release-credentials.sh" "$REPO"; then
    echo "provision-release-credentials: the check still refuses — finish what it names above" >&2
    exit 1
  fi
fi
