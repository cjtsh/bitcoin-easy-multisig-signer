#!/usr/bin/env bash
# Refuse a second publish path on any ref.
#
# Why this exists: the cycle-3 audit graded the repository BLOCKED because
# .github/workflows/build-windows.yml and build-linux.yml were still live on
# the windows-port and linux-port branches while build-candidate.yml claimed
# no second publish path could attach bytes to a release. The claim was
# checked only against the local checkout, which is exactly why it survived.
#
# This script enumerates the REMOTE's heads, not the checkout, so a branch
# that was never merged can still be seen. Run it as a release gate on every
# dispatch. It is pure bash + git (no gh, no Python, no grep) so it runs the
# same on the Windows job and in a fixture repo on a laptop.
#
#   bash scripts/check-publish-paths.sh [remote]   # default: origin
#
# A ref is "publish-capable" when its workflows either
#   - are named build-windows.yml or build-linux.yml (the retired publishers),
#     or
#   - grant `contents: write` or `write-all`, or
#   - run a publisher by any of the names the Actions surface offers:
#     `gh release`, `gh api`, `api.github.com`, `uploads.github.com`, or a
#     third-party release action such as `action-gh-release`.
# Only the default branch (main) may carry one. Comments in a recipe that
# merely name the retired files are not publishers and are not flagged.
#
# CT-73: the first version of this list was `contents: write` and
# `gh release`, and the cycle-4 audit walked past it with `gh api`, a REST
# upload to uploads.github.com and `softprops/action-gh-release`. A lexical
# sweep is only as good as its word list, so the list now names every shape
# the audit demonstrated, and it fails closed the other way too: a workflow on
# a non-main ref must SHOW that its token is read-only. An omitted
# `permissions:` block inherits the repository default, which no ref can
# disclose, so silence is an offender (`no-read-only-token-permissions`)
# rather than an assumption.
#
# FAIL CLOSED. The first version of this script read each workflow body with
# `git show ref:path 2>/dev/null || true` and matched it with `grep`. On the
# Windows job that read returned nothing, `|| true` swallowed the failure, and
# a branch that publishes was reported clean. Four tests went red there while
# staying green on Mac and Linux, which is the only reason anyone noticed. So:
#   - the body comes from `git cat-file blob <oid>`, not `git show ref:path`,
#     because the object id is not a path and cannot be mangled;
#   - a body that cannot be read is itself an offender (`unreadable-workflow`),
#     never a pass;
#   - matching is `[[ ]]` under nocasematch, with no external tool whose
#     absence could turn a refusal into silence.
#
# CT-76: the same namespace is emptied on the way OUT as well as on the way in.
# A clean run used to leave the fetched refs behind, and a later
# `git for-each-ref` in the caller's repository reported fifteen branches that
# do not exist on the remote. The sweep may not change what a caller sees.

set -euo pipefail

REMOTE="${1:-origin}"
ALLOWED="main"
REFUSAL="refusing: a non-main ref carries a publish-capable workflow"

# YAML permission keys and the `gh release` invocation are matched
# case-insensitively, as the grep -i this replaced did. nocasematch only
# affects [[ ]], which is the only matcher used below.
shopt -s nocasematch

# Matches `contents: write`, `contents: "write"`, `contents: 'write'`.
CONTENT_WRITE_RE='contents:[[:space:]]*["'\'']?write["'\'']?'

# Matches `permissions: write-all`, `permissions: "write-all"`.
WRITE_ALL_RE='permissions:[[:space:]]*["'\'']?write-all["'\'']?'

# Matches a token grant that is provably read-only: `permissions: read-all`,
# `permissions: {}` (no scopes beyond metadata), or a `contents: read` scope.
# Needed because an omitted `permissions:` block inherits the repository
# default, which the sweep cannot read off a ref.
READ_ONLY_RE='permissions:[[:space:]]*["'\'']?read-all["'\'']?|permissions:[[:space:]]*\{\}|contents:[[:space:]]*["'\'']?read["'\'']?'

# Own namespace for the fetched heads so a caller's refs are never rewritten.
# The namespace is emptied first: a plain fetch does not delete a head that
# vanished on the remote, and a stale leftover would name a branch that is
# no longer there. A sweep that reports a ghost is as bad as one that misses.
AUDIT_REMOTE_REFS="refs/remotes/publish-audit"

for stale in $(git for-each-ref --format='%(refname)' "${AUDIT_REMOTE_REFS}" 2>/dev/null); do
    git update-ref -d "$stale"
done

# CT-76: leave nothing behind, on every path out. `trap` rather than a final
# statement so the refusal path (`exit 1`) and a failure under `set -e` clean up
# too. The `|| true` keeps a cleanup failure from becoming the exit status.
cleanup() {
    for leaked in $(git for-each-ref --format='%(refname)' \
        "${AUDIT_REMOTE_REFS}" 2>/dev/null || true); do
        git update-ref -d "$leaked" 2>/dev/null || true
    done
}
trap cleanup EXIT

git fetch --no-tags --quiet "$REMOTE" "+refs/heads/*:${AUDIT_REMOTE_REFS}/*" >&2

offenders=0
report() {
    # One line per offender: <branch> <file> <reason>
    printf '%s %s %s\n' "$1" "$2" "$3"
    offenders=$((offenders + 1))
}

# Enumerate remote heads in the private namespace. Deliberately not
# `ls-tree` on the working copy: the whole point is refs we are not on.
for ref in $(git for-each-ref --format='%(refname)' "${AUDIT_REMOTE_REFS}"); do
    branch="${ref#"${AUDIT_REMOTE_REFS}"/}"
    if [ "$branch" = "$ALLOWED" ]; then
        continue
    fi

    # <mode> SP <type> SP <oid> TAB <path> -- the oid lets us read the blob
    # without spelling `ref:path`, which is the form that went blind on Windows.
    while IFS=$'\t' read -r meta path; do
        [ -n "$path" ] || continue
        oid="${meta##* }"
        base="${path##*/}"

        # The retired per-platform publishers must not exist as workflow
        # files on any ref, even if a rewrite strips their release job.
        if [ "$base" = "build-windows.yml" ] || [ "$base" = "build-linux.yml" ]; then
            report "$branch" "$path" "retired-per-platform-publisher"
            continue
        fi

        if ! body="$(git cat-file blob "$oid" 2>/dev/null)"; then
            # An unreadable body is not a clean body. Anything else lets a
            # broken sweep keep reporting "ok" while a publisher sits on a
            # branch nobody is looking at.
            report "$branch" "$path" "unreadable-workflow"
            printf 'git cat-file blob %s failed for %s:%s\n' \
                "$oid" "$branch" "$path" >&2
            continue
        fi

        if [[ "$body" =~ $CONTENT_WRITE_RE ]]; then
            report "$branch" "$path" "grants-contents-write"
            continue
        fi
        if [[ "$body" =~ $WRITE_ALL_RE ]]; then
            report "$branch" "$path" "grants-write-all"
            continue
        fi
        if [[ "$body" == *"gh release"* ]]; then
            report "$branch" "$path" "runs-gh-release"
            continue
        fi
        # CT-73: `gh api` writes as readily as `gh release` when it is given a
        # non-GET method or an upload host, and the method sits on a different
        # line from the command. A lexical sweep cannot pair the two, so any
        # `gh api` on a non-main ref is a publisher.
        if [[ "$body" == *"gh api"* ]]; then
            report "$branch" "$path" "runs-gh-api"
            continue
        fi
        # CT-73: the REST forms. The upload host only ever receives release
        # assets; the API host can create them, so a non-main ref that talks to
        # it fails closed rather than proving the method was a GET.
        if [[ "$body" == *"uploads.github.com"* ]]; then
            report "$branch" "$path" "uploads-release-asset-by-rest"
            continue
        fi
        if [[ "$body" == *"api.github.com"* ]]; then
            report "$branch" "$path" "talks-to-the-rest-api"
            continue
        fi
        # CT-73: the third-party publishing actions, by the names they publish
        # under. `softprops/action-gh-release` was the one the audit used.
        for publisher in "action-gh-release" "release-action" "upload-release-asset" \
                         "create-release" "gh-release"; do
            if [[ "$body" == *"$publisher"* ]]; then
                report "$branch" "$path" "runs-release-action"
                continue 2
            fi
        done
        # Last, and only for a body that published nothing above: the token.
        # A workflow whose grant cannot be shown to be read-only inherits the
        # repository default, and the sweep cannot read that default off a ref.
        if ! [[ "$body" =~ $READ_ONLY_RE ]]; then
            report "$branch" "$path" "no-read-only-token-permissions"
            continue
        fi
    done < <(git ls-tree -r "$ref" -- .github/workflows 2>/dev/null)
done

if [ "$offenders" -gt 0 ]; then
    printf '%s (%d)\n' "$REFUSAL" "$offenders" >&2
    printf 'Only %s may carry a publish-capable workflow. Delete the file on the ref above, then re-run.\n' "$ALLOWED" >&2
    exit 1
fi

printf 'ok: no non-main ref carries a publish-capable workflow\n' >&2
exit 0
