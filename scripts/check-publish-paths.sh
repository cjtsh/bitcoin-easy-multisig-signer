#!/usr/bin/env bash
# Refuse a publish path anywhere but the one file on the default branch.
#
# Why this exists: the cycle-3 audit graded the repository BLOCKED because
# .github/workflows/build-windows.yml and build-linux.yml were still live on
# the windows-port and linux-port branches while build-candidate.yml claimed
# no second publish path could attach bytes to a release. The claim was
# checked only against the local checkout, which is exactly why it survived.
#
# This script enumerates the REMOTE's refs, not the checkout, so a branch or
# tag that was never merged can still be seen. Run it as a release gate on
# every dispatch. It is pure bash + git (no gh, no Python, no grep) so it runs
# the same on the Windows job and in a fixture repo on a laptop.
#
#   bash scripts/check-publish-paths.sh [remote]   # default: origin
#
# WHAT IT CHECKS, exactly:
#
#   heads (every remote branch)
#     - main may carry exactly one publish-capable workflow, and it must be
#       ALLOWED_PUBLISHER. A second one on main is an offender, because the
#       documented claim is one publish path, not "main may hold as many as
#       it likes".
#     - no other head may carry any workflow file that grants write access
#       or names a release surface.
#
#   tags (every remote tag)
#     - tags are immutable history: AGENTS.md forbids deleting or moving a
#       published tag, so a tag that carries a publisher cannot be "fixed" by
#       deleting it. Tags are therefore judged by what they can DO from their
#       own ref, not by the words they contain:
#         * a tag whose publisher refuses to run off main (it tests
#           `refs/heads/main` and exits 1) is recorded as inert and passes;
#         * a tag that predates that guard and is on the enumerated
#           LEGACY_UNGUARDED_TAGS list below is recorded as an accepted
#           residual and passes;
#         * any other tag carrying a publisher is an offender, so a NEW tag
#           cannot reintroduce an unguarded publisher. That is what keeps this
#           rule closed under change.
#
# WHAT IT DOES NOT CHECK (do not read the pass line as more than it says):
#   - the 46 enumerated legacy tags CAN still publish if someone dispatches
#     their workflow against the tag ref. The residual is accepted, recorded
#     in RELEASE-PROCESS.md section 5 and in the release ledger, and it is
#     bounded by the same thing that bounds every other release control:
#     dispatching any ref, and editing any file, requires push or dispatch
#     rights on this repository, which is the owner account that the audit
#     plan's section 0 already declares the strongest in-scope capability.
#   - it reads .github/workflows. A publisher placed anywhere else, or a
#     GitHub App installed on the repository, is outside its reach.
#
# A ref is "publish-capable" when one of its workflow files
#   - is named build-windows.yml or build-linux.yml (the retired publishers),
#     or
#   - spells `contents: write` (or a quoted variant), or
#   - spells `write-all`, or
#   - spells a `gh release` invocation, or
#   - names a release surface (`/releases`, `*-action-gh-release`,
#     `actions/create-release`).
#
# The match runs over whole lines, minus lines that are entirely a comment. A
# line is treated as a comment only when its first non-whitespace character is
# `#` — the sweep never truncates a line at a `#`, so a `#` inside a quoted
# string cannot hide a publisher later on the same line. The one false positive
# left is a trailing comment on a code line that spells a pattern; that fails
# closed, and the fix is to move the comment onto its own line. (The retired
# file NAMES are matched on the basename, so a comment that merely mentions
# them is fine.)
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
#     absence could turn a refusal into silence. CONTROL: CM-10

set -euo pipefail

REMOTE="${1:-origin}"
ALLOWED_BRANCH="main"
ALLOWED_PUBLISHER="build-candidate.yml"
REFUSAL="refusing: a non-main ref carries a publish-capable workflow"

# The tags that were published before the default-branch guard existed, read
# from the real repository on 2026-10-11: v0.1.7 through v0.6.3. They are
# immutable, they cannot be deleted under AGENTS.md, and they are recorded as
# an accepted residual above. The list may only be extended by a deliberate
# edit, and a tag that is not on it must carry the guard: that is the
# closed-under-change half of this rule. Tags v0.6.4 and later are all
# guarded, so a new release tag passes without touching this line.
LEGACY_UNGUARDED_TAGS="v0.1.7 v0.1.8 v0.1.9 v0.1.10 v0.1.11 v0.1.12 v0.1.13 v0.1.14 v0.1.15 v0.1.16 v0.1.17 v0.1.18 v0.1.19 v0.1.20 v0.1.21 v0.1.22 v0.1.23 v0.1.24 v0.1.25 v0.1.26 v0.1.27 v0.2.0 v0.2.1 v0.2.2 v0.3.0 v0.3.1 v0.3.2 v0.4.0 v0.4.1 v0.4.2 v0.4.3 v0.4.4 v0.4.5 v0.4.6 v0.4.7 v0.4.8 v0.4.9 v0.4.10 v0.4.11 v0.4.12 v0.4.13 v0.4.14 v0.5.1 v0.6.1 v0.6.2 v0.6.3"

# YAML permission keys and release surfaces are matched case-insensitively,
# as the grep -i this replaced did. nocasematch only affects [[ ]], which is
# the only matcher used below.
shopt -s nocasematch

# Matches `contents: write`, `contents: "write"`, `contents: 'write'`.
CONTENT_WRITE_RE='contents:[[:space:]]*["'\'']?write["'\'']?'
# The blanket grant: `permissions: write-all` (any indentation).
WRITE_ALL_RE='write-all'
# The release CLI, in any spelling.
GH_RELEASE_RE='gh[[:space:]]+release'
# A release surface named without the CLI: the REST path, the common third
# party actions, and anything that would create or upload a release.
RELEASE_SURFACE_RE='(\/releases|action-gh-release|create-release)'
# A workflow that tests this has been told which branch it may publish from.
MAIN_REF_RE='refs\/heads\/main'

# Private namespaces for the fetched refs so a caller's refs are never
# rewritten. They are emptied first: a plain fetch does not delete a ref that
# vanished on the remote, and a stale leftover would name a branch or tag that
# is no longer there. A sweep that reports a ghost is as bad as one that
# misses.
AUDIT_HEADS="refs/remotes/publish-audit/heads"
AUDIT_TAGS="refs/remotes/publish-audit/tags"

for stale in $(git for-each-ref --format='%(refname)' \
    "$AUDIT_HEADS" "$AUDIT_TAGS" 2>/dev/null); do
    git update-ref -d "$stale"
done

# --no-tags stops git from auto-following tags into the caller's refs/tags;
# the explicit tag refspec still fetches every tag into our own namespace.
git fetch --no-tags --quiet "$REMOTE" \
    "+refs/heads/*:${AUDIT_HEADS}/*" \
    "+refs/tags/*:${AUDIT_TAGS}/*" >&2

offenders=0
guarded=0
legacy=0
report() {
    # One line per offender: <ref> <file> <reason>
    printf '%s %s %s\n' "$1" "$2" "$3"
    offenders=$((offenders + 1))
}
note() {
    # One line per accepted-but-recorded ref, on stderr so the offender
    # stream on stdout stays machine-readable.
    printf 'info: %s %s %s\n' "$1" "$2" "$3" >&2
}

# without_comment_lines <body> -> the body minus the lines that are entirely a
# comment. A line counts as a comment only when its first non-whitespace
# character is `#`. No line is ever truncated at a `#`, so a `#` inside a
# quoted string cannot hide a publisher later on the same line.
without_comment_lines() {
    local line trimmed out=""
    while IFS= read -r line; do
        trimmed="${line#"${line%%[![:space:]]*}"}"
        [ "${trimmed:0:1}" = "#" ] && continue
        out="${out}${line}"$'\n'
    done <<< "$1"
    printf '%s' "$out"
}

# match_reason <body> -> the first reason this body is publish-capable, or
# nothing. Ordered so the most specific reason wins.
match_reason() {
    local body="$1"
    if [[ "$body" =~ $CONTENT_WRITE_RE ]]; then
        printf 'grants-contents-write'
    elif [[ "$body" =~ $WRITE_ALL_RE ]]; then
        printf 'grants-write-all'
    elif [[ "$body" =~ $GH_RELEASE_RE ]]; then
        printf 'runs-gh-release'
    elif [[ "$body" =~ $RELEASE_SURFACE_RE ]]; then
        printf 'names-release-surface'
    fi
}

# check_file <ref-label> <path> <oid> <head|tag> [tag-name]
check_file() {
    local label="$1" path="$2" oid="$3" mode="$4" tag="${5:-}"
    local base="${path##*/}"
    local body reason

    # The retired per-platform publishers must not exist as workflow files on
    # any ref, even if a rewrite strips their release job.
    if [ "$base" = "build-windows.yml" ] || [ "$base" = "build-linux.yml" ]; then
        report "$label" "$path" "retired-per-platform-publisher"
        return
    fi

    if ! body="$(git cat-file blob "$oid" 2>/dev/null)"; then
        # An unreadable body is not a clean body. Anything else lets a broken
        # sweep keep reporting "ok" while a publisher sits on a ref nobody is
        # looking at.
        report "$label" "$path" "unreadable-workflow"
        printf 'git cat-file blob %s failed for %s:%s\n' \
            "$oid" "$label" "$path" >&2
        return
    fi

    # Comments describe; they do not publish. Strip the lines that are entirely
    # a comment before matching, so a file cannot be flagged (or, worse, be
    # cleared on a tag) by prose. Every remaining line is matched whole.
    body="$(without_comment_lines "$body")"

    reason="$(match_reason "$body")"
    [ -n "$reason" ] || return 0

    if [ "$mode" = "head" ]; then
        if [ "$label" = "$ALLOWED_BRANCH" ]; then
            # On main exactly one publisher is allowed, by name.
            if [ "$base" = "$ALLOWED_PUBLISHER" ]; then
                return 0
            fi
            report "$label" "$path" "second-publisher-on-main"
            return
        fi
        report "$label" "$path" "$reason"
        return
    fi

    # A tag. What matters is whether this publisher can publish from a tag
    # ref, which it cannot if it refuses everything that is not main.
    if [[ "$body" =~ $MAIN_REF_RE ]] && [[ "$body" == *"exit 1"* ]]; then
        note "$label" "$path" "guarded-tag-publisher"
        guarded=$((guarded + 1))
        return
    fi
    case " $LEGACY_UNGUARDED_TAGS " in
        *" $tag "*)
            note "$label" "$path" "legacy-unguarded-tag-publisher"
            legacy=$((legacy + 1))
            return
            ;;
    esac
    report "$label" "$path" "unguarded-tag-publisher"
}

# Enumerate remote heads in the private namespace. Deliberately not
# `ls-tree` on the working copy: the whole point is refs we are not on.
for ref in $(git for-each-ref --format='%(refname)' "$AUDIT_HEADS"); do
    branch="${ref#"${AUDIT_HEADS}"/}"

    # <mode> SP <type> SP <oid> TAB <path> -- the oid lets us read the blob
    # without spelling `ref:path`, which is the form that went blind on Windows.
    while IFS=$'\t' read -r meta path; do
        [ -n "$path" ] || continue
        check_file "$branch" "$path" "${meta##* }" head
    done < <(git ls-tree -r "$ref" -- .github/workflows 2>/dev/null)
done

for ref in $(git for-each-ref --format='%(refname)' "$AUDIT_TAGS"); do
    tag="${ref#"${AUDIT_TAGS}"/}"
    while IFS=$'\t' read -r meta path; do
        [ -n "$path" ] || continue
        check_file "$tag" "$path" "${meta##* }" tag "$tag"
    done < <(git ls-tree -r "$ref" -- .github/workflows 2>/dev/null)
done

if [ "$offenders" -gt 0 ]; then
    printf '%s (%d)\n' "$REFUSAL" "$offenders" >&2
    printf 'Only %s may carry a publish-capable workflow. Delete the file on the ref above, then re-run.\n' "$ALLOWED_BRANCH" >&2
    exit 1
fi

if [ "$guarded" -gt 0 ]; then
    printf 'noted: %d tag(s) carry a publisher that refuses to publish off main\n' \
        "$guarded" >&2
fi
if [ "$legacy" -gt 0 ]; then
    printf 'noted: %d enumerated legacy tag(s) predate that guard and are an accepted residual (see RELEASE-PROCESS.md section 5)\n' \
        "$legacy" >&2
fi

printf 'ok: no non-main ref carries a publish-capable workflow\n' >&2
exit 0
