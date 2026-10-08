#!/usr/bin/env bash
# CT-97 — where the release credentials live.
#
# Repository secrets are handed to a job on ANY ref. A dispatch at a historical
# tag therefore runs that tag's own frozen (older, less guarded) workflow text
# but still receives today's signing keys, because secrets are matched by name
# and not by tag. That was CT-97: a link on the publishing chain we could not
# show was safe. Tags are immutable history — AGENTS.md forbids moving or
# deleting a published one — so the fix cannot live in the tag. It lives in the
# platform: the credentials move into two protected environments whose
# deployment rule allows `main` only, and the two jobs that use them declare
# those environments (`.github/workflows/build-candidate.yml`; pinned by
# tests/test_workflow_config.py::ReleaseCredentialScopePins).
#
# This script is the standing check for the half no unit test can reach. It
# reads configuration only — a secret value can never be read back, not by this
# script and not by anyone — and refuses (exit 1) unless all of:
#   1. No repository-level secret carries a release credential name. This is
#      the load-bearing one: environment secrets are ADDED to repository
#      secrets, so while a repository-level copy exists every ref still gets
#      the key and nothing else here matters.
#   2. `release-signing` exists, allows deployments from `main` only, declares no
#      human gate, and holds exactly the two GPG names.
#   3. `apple-signing` exists, allows deployments from `main` only, declares no
#      human gate, and holds exactly the three Apple names.
#
# A "human gate" is a required reviewer or a wait timer. Publishing must start on
# its own: the project owner asked for a release path any agent team can run, and
# with `prevent_self_review: false` a required reviewer is click-through by the
# same token that dispatched the run, so it buys no separation of duties while
# giving a release a way to stall. The ref rule (`main` only) is the control that
# does the work.
#
# Run it before a promotion (RELEASE-PROCESS.md §3) and in every audit cycle
# (SIGNING.md). It needs `gh` authenticated with read access to the repository's
# environment settings; the default `GITHUB_TOKEN` in CI cannot read them, so
# this is an operator/auditor check, not a workflow step.
#
# Usage: scripts/check-release-credentials.sh [owner/repo]

set -euo pipefail

REPO="${1:-cjtsh/bitcoin-easy-multisig-signer}"
RELEASE_ENV="release-signing"
APPLE_ENV="apple-signing"
RELEASE_SECRETS="GPG_PRIVATE_KEY GPG_PASSPHRASE"
APPLE_SECRETS="MAC_CERT_P12_BASE64 MAC_CERT_PASSWORD MAC_APP_SPECIFIC_PASSWORD"
ALL_SECRETS="$RELEASE_SECRETS $APPLE_SECRETS"
REFUSAL="refusing: the release credentials are not environment-scoped"

for tool in gh python3; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "check-release-credentials: $tool is required" >&2
    exit 2
  }
done

offenders=0
report() {
  printf '%s\n' "$*" >&2
  offenders=$((offenders + 1))
}

# Print the sorted `name` field of a JSON collection on stdin.
#
# Every helper that pipes Python into bash ends with `tr -d '\r'` because
# Windows Python writes CRLF: a trailing carriage return makes a name compare
# unequal to the same name built by bash, which would turn an honest
# configuration into a refusal. Command substitution strips a trailing newline
# and not a carriage return, so the strip has to be explicit. `pipefail` (set
# above) keeps a Python failure visible through the pipe.
names_from() {
  python3 -c 'import json, sys
rows = json.load(sys.stdin).get(sys.argv[1]) or []
print("\n".join(sorted(row.get("name", "") for row in rows)))' "$1" | tr -d '\r'
}

# Print "<name> <type>" for each deployment branch policy on stdin.
policy_lines() {
  python3 -c 'import json, sys
rows = json.load(sys.stdin).get("branch_policies") or []
print("\n".join(sorted("%s %s" % (row.get("name"), row.get("type")) for row in rows)))' | tr -d '\r'
}

# Print any human gate declared on an environment on stdin: a required reviewer
# pauses the run for a person and a wait timer delays it. Either one means a
# release cannot start on its own, so either one is an offender here.
gate_lines() {
  python3 -c 'import json, sys
rules = json.load(sys.stdin).get("protection_rules") or []
gates = []
for rule in rules:
    kind = rule.get("type")
    if kind == "required_reviewers" and (rule.get("reviewers") or []):
        gates.append("required_reviewers(%d)" % len(rule["reviewers"]))
    elif kind == "wait_timer" and (rule.get("wait_timer") or 0):
        gates.append("wait_timer(%s)" % rule.get("wait_timer"))
print("\n".join(sorted(gates)))' | tr -d '\r'
}

expected_rules() {
  if [[ "$1" == "$RELEASE_ENV" ]]; then
    printf '%s\n' "$RELEASE_SECRETS" | tr ' ' '\n' | sort
  else
    printf '%s\n' "$APPLE_SECRETS" | tr ' ' '\n' | sort
  fi
}

# 1. No repository-level copy of a release credential may exist.
if ! repo_names="$(gh api "repos/$REPO/actions/secrets" | names_from secrets)"; then
  report "could not read the repository secret names of $REPO (is gh authenticated with access to it?)"
  repo_names=""
fi
for name in $ALL_SECRETS; do
  if printf '%s\n' "$repo_names" | grep -Fxq "$name"; then
    report "$REPO still has a REPOSITORY-level secret named $name; environment secrets are added to repository secrets, so every ref including every historical tag keeps receiving it — re-enter the value in its environment secrets and delete this copy"
  fi
done

# 2./3. Each environment exists, is main-only, is gate-free, holds its own names.
for env in "$RELEASE_ENV" "$APPLE_ENV"; do
  if ! env_json="$(gh api "repos/$REPO/environments/$env" 2>/dev/null)"; then
    report "$REPO has no environment named $env, so the credentials have nowhere environment-scoped to live"
    continue
  fi
  if ! policies="$(gh api "repos/$REPO/environments/$env/deployment-branch-policies" 2>/dev/null | policy_lines)"; then
    report "could not read the deployment branch policies of the $env environment"
    policies=""
  fi
  if [[ "$policies" != "main branch" ]]; then
    report "the $env environment does not allow deployments from the main branch alone (found: ${policies:-none}); a tag must never be able to deploy into it"
  fi
  if ! actual="$(gh api "repos/$REPO/environments/$env/secrets" 2>/dev/null | names_from secrets)"; then
    report "could not read the secret names of the $env environment"
    actual=""
  fi
  expected="$(expected_rules "$env")"
  if [[ "$actual" != "$expected" ]]; then
    report "the $env environment must hold exactly [$(printf '%s' "$expected" | tr '\n' ' ')] — found [$(printf '%s' "$actual" | tr '\n' ' ')]"
  fi
  gates="$(printf '%s' "$env_json" | gate_lines)"
  if [[ -n "$gates" ]]; then
    report "the $env environment declares a human gate ($(printf '%s' "$gates" | tr '\n' ' ')); publishing must start on its own, so remove it"
  fi
done

if (( offenders > 0 )); then
  echo "$REFUSAL" >&2
  echo "Only environment-scoped, main-only credentials may sign a release. See SIGNING.md and RELEASE-PROCESS.md." >&2
  exit 1
fi

echo "ok: the release credentials are environment-scoped, main-only, and unreachable from any tag"
