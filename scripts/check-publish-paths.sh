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
#   - grant a writable token — `write-all`, or `write` on `contents` — when the
#     `permissions:` mapping is PARSED (see below), or
#   - run a publisher by any of the names the Actions surface offers:
#     `gh release`, `gh api`, `gh api graphql`, `api.github.com`,
#     `uploads.github.com`, `$GITHUB_API_URL`, `actions/github-script`, a
#     camelCase REST release call such as `createRelease`, a third-party
#     release action such as `action-gh-release`, or a reusable workflow whose
#     path names a release (`uses: …release…@…`).
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
# CT-73 + CT-102, cycle 5: the word list was not the only way past this sweep.
# The token arm was a REGEX OVER THE FILE TEXT, so the audit moved it in two
# directions at once:
#   - `contents : write` — YAML that Ruby's parser resolves to a real write
#     grant, and a regex demanding the colon immediately after the key did not
#     match, so the write arm stayed silent; and
#   - a COMMENT that said `contents: read` satisfied the read-only arm, so a
#     workflow that granted nothing read-only proved itself read-only with
#     prose. The same bug ran the false-positive way: a comment that merely
#     mentioned `contents: write` was reported as a grant.
# Both directions are now closed the same way: comments are stripped before
# ANY decision (a comment is not code), and the token grant comes from the
# `permissions:` mapping being parsed, never from the text. The parse is
# deliberately conservative in both directions — any mapping that grants a
# writable token is an offender no matter what a duplicate `permissions:` key
# says afterwards, because YAML's last-wins reading is not something a release
# gate should bet on.
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

# CT-73 + CT-102: comments are not code. Every decision below runs on the body
# with its comments removed, so neither a comment that says `contents: read`
# nor one that says `contents: write` can move a verdict.
#
# A `#` starts a comment unless it sits inside a quoted scalar. A line with no
# quote at all is truncated at its first `#`; only a line that carries both a
# quote and a `#` needs the character walk, which keeps the common case cheap.
strip_comments() {
    local line ch out quote i
    while IFS= read -r line; do
        line="${line%$'\r'}"
        if [[ "$line" != *"#"* ]]; then
            printf '%s\n' "$line"
            continue
        fi
        if [[ "$line" != *'"'* && "$line" != *"'"* ]]; then
            printf '%s\n' "${line%%#*}"
            continue
        fi
        out=""
        quote=""
        for (( i=0; i<${#line}; i++ )); do
            ch="${line:i:1}"
            if [ -n "$quote" ]; then
                out+="$ch"
                [ "$ch" = "$quote" ] && quote=""
                continue
            fi
            case "$ch" in
                '"'|"'") quote="$ch"; out+="$ch" ;;
                '#') break ;;
                *) out+="$ch" ;;
            esac
        done
        printf '%s\n' "$out"
    done
}

# CT-73: what the token may do, read from the parsed `permissions:` mapping.
#
# Handles every spelling YAML allows here: `permissions: read-all` and
# `permissions: write-all` scalars, `permissions: {}`, a flow mapping
# `{contents: write}`, and a block mapping whose scopes may be spaced
# (`contents : write`), quoted (`contents: "write"`) or indented any depth
# (top level or per job). A duplicate `permissions:` key is not valid YAML and
# GitHub's last-wins parse of it is not something this gate will bet a release
# on, so ANY mapping that grants a writable token wins over any other.
#
# stdout is one of: write-all | contents-write | read-only | absent
permissions_verdict() {
    local -a lines=()
    local line
    while IFS= read -r line; do
        lines+=("${line%$'\r'}")
    done

    local saw_readonly=0 i n child child_indent child_trim indent value key
    for (( i=0; i<${#lines[@]}; i++ )); do
        line="${lines[i]}"
        if [[ "$line" =~ ^([[:space:]]*)permissions[[:space:]]*:(.*)$ ]]; then
            indent="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            # Trim surrounding whitespace, then surrounding quotes.
            value="${value#"${value%%[![:space:]]*}"}"
            value="${value%"${value##*[![:space:]]}"}"
            value="${value#\"}"; value="${value%\"}"
            value="${value#\'}"; value="${value%\'}"
            # Every comparison below is `case` or `[[ ]]` under nocasematch,
            # which is what makes `CONTENTS: WRITE` a grant. `${value,,}` would
            # be shorter and is not available: /bin/bash on macOS is 3.2.
            case "$value" in
                "")
                    # Block mapping: the scopes are the deeper-indented lines.
                    for (( n=i+1; n<${#lines[@]}; n++ )); do
                        child="${lines[n]}"
                        [ -n "${child//[[:space:]]/}" ] || continue
                        child_indent="${child%%[![:space:]]*}"
                        if (( ${#child_indent} <= ${#indent} )); then
                            break
                        fi
                        if [[ "$child" =~ ^[[:space:]]*([A-Za-z0-9_.-]+)[[:space:]]*:[[:space:]]*[\"\']?([A-Za-z0-9_-]+) ]]; then
                            key="${BASH_REMATCH[1]}"
                            value="${BASH_REMATCH[2]}"
                            saw_readonly=1
                            case "$value" in
                                "write-all") printf 'write-all\n'; return 0 ;;
                            esac
                            case "$key:$value" in
                                "contents:write") printf 'contents-write\n'; return 0 ;;
                            esac
                            continue
                        fi
                        # A bare `write-all` (optionally a `- ` sequence item) is
                        # a grant too. It is not valid YAML for `permissions:`,
                        # which is exactly why it is worth refusing rather than
                        # letting a spelling this sweep cannot read pass.
                        child_trim="${child#"${child%%[![:space:]]*}"}"
                        child_trim="${child_trim%"${child_trim##*[![:space:]]}"}"
                        child_trim="${child_trim#- }"
                        child_trim="${child_trim#-}"
                        case "$child_trim" in
                            "write-all"|"write")
                                printf 'write-all\n'; return 0
                                ;;
                            "read-all"|"read"|"none"|"{}")
                                saw_readonly=1
                                ;;
                        esac
                    done
                    ;;
                "write-all"|"write")
                    printf 'write-all\n'; return 0
                    ;;
                "{}")
                    saw_readonly=1
                    ;;
                "read-all"|"read"|"none")
                    saw_readonly=1
                    ;;
                "{"*)
                    # Flow mapping, e.g. `{contents: write, issues: read}`.
                    if [[ "$value" =~ contents[[:space:]]*:[[:space:]]*[\"\']?write ]]; then
                        printf 'contents-write\n'; return 0
                    fi
                    if [[ "$value" =~ (^|[[:space:]{,])write-all([[:space:]},]|$) ]]; then
                        printf 'write-all\n'; return 0
                    fi
                    if [[ "$value" =~ [A-Za-z0-9_.-]+[[:space:]]*: ]]; then
                        saw_readonly=1
                    fi
                    ;;
            esac
        fi
    done

    if [ "$saw_readonly" -eq 1 ]; then
        printf 'read-only\n'
    else
        printf 'absent\n'
    fi
}

# CT-102: a reusable workflow hides its publisher behind `uses:`, and the sweep
# cannot read the callee. A called workflow whose path names a release is a
# publish path this gate refuses to assume is harmless.
#
# Matched one line at a time on the comment-stripped body. `.` matches a
# newline in bash's ERE, so a whole-body `uses:.*release.*@` pairs an unrelated
# `uses: actions/upload-artifact@…` line with the word "release" anywhere else
# in the file — it flagged this repository's own windows-inputs.yml branches.
calls_a_release_workflow() {
    local line
    while IFS= read -r line; do
        if [[ "$line" =~ ^[[:space:]]*(-[[:space:]]+)?uses:.*release.*@ ]]; then
            return 0
        fi
    done
    return 1
}

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

        # CT-73 + CT-102: every decision below runs on the comment-stripped
        # body, and the token grant is parsed rather than pattern-matched.
        clean="$(printf '%s\n' "$body" | strip_comments)"
        verdict="$(printf '%s\n' "$clean" | permissions_verdict)"
        case "$verdict" in
            contents-write)
                report "$branch" "$path" "grants-contents-write"
                continue
                ;;
            write-all)
                report "$branch" "$path" "grants-write-all"
                continue
                ;;
        esac

        if [[ "$clean" == *"gh release"* ]]; then
            report "$branch" "$path" "runs-gh-release"
            continue
        fi
        # CT-73: `gh api` writes as readily as `gh release` when it is given a
        # non-GET method or an upload host, and the method sits on a different
        # line from the command. A lexical sweep cannot pair the two, so any
        # `gh api` on a non-main ref is a publisher. `gh api graphql` is the
        # same command wearing the GraphQL endpoint's name.
        if [[ "$clean" == *"gh api"* || "$clean" == *"gh graphql"* ]]; then
            report "$branch" "$path" "runs-gh-api"
            continue
        fi
        # CT-73: the REST forms. The upload host only ever receives release
        # assets; the API host can create them, so a non-main ref that talks to
        # it fails closed rather than proving the method was a GET.
        if [[ "$clean" == *"uploads.github.com"* ]]; then
            report "$branch" "$path" "uploads-release-asset-by-rest"
            continue
        fi
        if [[ "$clean" == *"api.github.com"* || "$clean" == *'$GITHUB_API_URL'* ]]; then
            report "$branch" "$path" "talks-to-the-rest-api"
            continue
        fi
        # CT-102: `actions/github-script` is a publisher when the script it runs
        # creates a release, and the sweep cannot read JavaScript. The camelCase
        # REST calls are the same write as `uploads.github.com` in another
        # spelling.
        if [[ "$clean" == *"github-script"* ]]; then
            report "$branch" "$path" "runs-github-script"
            continue
        fi
        for call in "createRelease" "updateRelease" "uploadReleaseAsset" \
                    "createReleaseAsset"; do
            if [[ "$clean" == *"$call"* ]]; then
                report "$branch" "$path" "calls-the-rest-release-api"
                continue 2
            fi
        done
        # CT-73: the third-party publishing actions, by the names they publish
        # under. `softprops/action-gh-release` was the one the audit used.
        for publisher in "action-gh-release" "release-action" "upload-release-asset" \
                         "create-release" "gh-release"; do
            if [[ "$clean" == *"$publisher"* ]]; then
                report "$branch" "$path" "runs-release-action"
                continue 2
            fi
        done
        # CT-102: a reusable workflow hides its publisher behind `uses:`. A
        # called workflow that names a release is a publish path the sweep
        # cannot read, so it fails closed rather than assuming the callee is
        # read-only. Matched on the stripped body, so the comments in this
        # repository that discuss release workflows are not offenders.
        if printf '%s\n' "$clean" | calls_a_release_workflow; then
            report "$branch" "$path" "calls-a-release-workflow"
            continue
        fi
        # Last, and only for a body that published nothing above: the token.
        # A workflow whose grant cannot be shown to be read-only inherits the
        # repository default, and the sweep cannot read that default off a ref.
        if [ "$verdict" = "absent" ]; then
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
