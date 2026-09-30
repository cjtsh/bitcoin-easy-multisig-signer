#!/usr/bin/env bash
# Print the credential arguments `notarytool submit` should use, one per line.
#
# Kept separate from build-macos.sh so the argument assembly can be tested without
# Apple credentials. The notarisation round trip itself cannot be tested here; the
# decision of WHICH credentials to present can be, and that is the part most
# likely to be silently wrong.
#
# Two routes are supported:
#   MAC_NOTARY_PROFILE                                  a keychain profile, made on
#                                                       a Mac you control with
#                                                       `xcrun notarytool store-credentials`
#   MAC_NOTARY_KEY_PATH + MAC_NOTARY_KEY_ID +
#   MAC_NOTARY_ISSUER_ID                                an App Store Connect API key,
#                                                       which is what an ephemeral
#                                                       CI runner can use
#
# Prints nothing and exits 0 when no route is configured: the caller decides
# whether that is fatal. A partial or ambiguous configuration is an error, because
# guessing would mean signing with credentials the operator did not intend.
set -euo pipefail

key_path="${MAC_NOTARY_KEY_PATH:-}"
key_id="${MAC_NOTARY_KEY_ID:-}"
issuer_id="${MAC_NOTARY_ISSUER_ID:-}"
profile="${MAC_NOTARY_PROFILE:-}"

key_count=0
for value in "$key_path" "$key_id" "$issuer_id"; do
  [[ -n "$value" ]] && key_count=$((key_count + 1))
done

if [[ -n "$profile" && $key_count -gt 0 ]]; then
  echo "Set either MAC_NOTARY_PROFILE or the App Store Connect key variables, not both." >&2
  exit 2
fi

if [[ -n "$profile" ]]; then
  printf '%s\n' --keychain-profile "$profile"
  exit 0
fi

if [[ $key_count -eq 3 ]]; then
  printf '%s\n' --key "$key_path" --key-id "$key_id" --issuer "$issuer_id"
  exit 0
fi

if [[ $key_count -gt 0 ]]; then
  echo "App Store Connect notarisation needs all three of MAC_NOTARY_KEY_PATH, MAC_NOTARY_KEY_ID and MAC_NOTARY_ISSUER_ID; only $key_count were set." >&2
  exit 2
fi
