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
# dispatch. It is pure bash + git (no gh, no Python) so it runs the same on
# the Windows job and in a fixture repo on a laptop.
#
#   bash scripts/check-publish-paths.sh [remote]   # default: origin
#
# A ref is "publish-capable" when its workflows either
#   - are named build-windows.yml or build-linux.yml (the retired publishers),
#     or
#   - grant `contents: write` or run `gh release` (the release job that
#     actually attaches bytes).
# Only the default branch (main) may carry one. Comments in a recipe that
# merely name the retired files are not publishers and are not flagged.

set -euo pipefail

REMOTE="${1:-origin}"
ALLOWED="main"
REFUSAL="refusing: a non-main ref carries a publish-capable workflow"

# Own namespace for the fetched heads so a caller's refs are never rewritten.
# The namespace is emptied first: a plain fetch does not delete a head that
# vanished on the remote, and a stale leftover would name a branch that is
# no longer there. A sweep that reports a ghost is as bad as one that misses.
AUDIT_REMOTE_REFS="refs/remotes/publish-audit"

for stale in $(git for-each-ref --format='%(refname)' "${AUDIT_REMOTE_REFS}" 2>/dev/null); do
    git update-ref -d "$stale"
done

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

    for path in $(git ls-tree -r --name-only "$ref" -- .github/workflows 2>/dev/null); do
        base="${path##*/}"

        # The retired per-platform publishers must not exist as workflow
        # files on any ref, even if a rewrite strips their release job.
        if [ "$base" = "build-windows.yml" ] || [ "$base" = "build-linux.yml" ]; then
            report "$branch" "$path" "retired-per-platform-publisher"
            continue
        fi

        body="$(git show "${ref}:${path}" 2>/dev/null || true)"

        if printf '%s\n' "$body" | grep -qiE 'contents:[[:space:]]*["'\'']?write["'\'']?'; then
            report "$branch" "$path" "grants-contents-write"
            continue
        fi
        if printf '%s\n' "$body" | grep -qF 'gh release'; then
            report "$branch" "$path" "runs-gh-release"
            continue
        fi
    done
done

if [ "$offenders" -gt 0 ]; then
    printf '%s (%d)\n' "$REFUSAL" "$offenders" >&2
    printf 'Only %s may carry a publish-capable workflow. Delete the file on the ref above, then re-run.\n' "$ALLOWED" >&2
    exit 1
fi

printf 'ok: no non-main ref carries a publish-capable workflow\n' >&2
exit 0
