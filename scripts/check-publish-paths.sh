#!/usr/bin/env bash
# Refuse a second publish path on any remote BRANCH.
#
# Scope (cycle-5 adversarial pass). The sweep enumerates branch refs only
# (`+refs/heads/*`), which is what the header claimed before the attacker read
# it as "any ref" and showed a tag-only `contents: write` + `gh release`
# workflow returning "ok". Tags are deliberately out of scope, and the reason is
# not that a tag's workflow cannot run: it is that
#   - a tag can only be created by someone who can already push a workflow, and
#   - every historical tag carries the publisher text that shipped with it, so
#     including tags would refuse this repository's own v0.6.x tags.
# The control for a tag ref is CT-97's environment scope, not this sweep: every
# release credential lives in an environment whose deployment branch policy
# allows `main` only (`scripts/check-release-credentials.sh`), so a job that
# declares one cannot start on a tag and a tag run has no signing key. The
# default-token path (`contents: write` with no secret) is the residual, and it
# is disclosed in `releases/PATCH-0.6.8.md` rather than silently assumed away.
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
#     `uploads.github.com`, `$GITHUB_API_URL`, `${{ github.api_url }}`,
#     `actions/github-script`, a camelCase REST release call such as
#     `createRelease`, a third-party release action such as
#     `action-gh-release`, or a `uses:` of a workflow in ANOTHER repository
#     (any name — the callee cannot be read from this checkout; a subdirectory
#     ACTION such as `github/codeql-action/init@v3` is not a callee and passes).
# Only the default branch (main) may carry one. Comments in a recipe that
# merely name the retired files are not publishers and are not flagged.
#
# The publisher patterns run on a NORMALIZED body (cycle-5 adversarial pass):
# comments stripped, `\`-continuations joined, quotes removed and runs of
# space/tab squeezed, so `gh  release`, `gh "release"` and `gh \`+newline+
# `release` are one spelling to the match. The `permissions:` parse runs before
# that normalization because it needs the real line shape.
#
# CT-73: the first version of this list was `contents: write` and
# `gh release`, and the cycle-4 audit walked past it with `gh api`, a REST
# upload to uploads.github.com and `softprops/action-gh-release`. A lexical
# sweep is only as good as its word list, so the list now names every shape
# the audit demonstrated, and it fails closed the other way too: a workflow on
# a non-main ref must SHOW that its token is read-only. An omitted
# `permissions:` block inherits the repository default, which no ref can
# disclose, so silence is an offender (`no-read-only-token-permissions`)
# rather than an assumption. Cycle 6 found the same hole one level down: a
# read-only `permissions:` on ONE JOB does not cover the jobs that declare
# none, so a partly-declared file is refused (`partial-token-permissions`)
# rather than letting one read-only job vouch for the rest.
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
# deliberately conservative in both directions — a `contents: write` (or
# `write-all`) mapping is an offender no matter what a duplicate
# `permissions:` key says afterwards, because YAML's last-wins reading is not
# something a release gate should bet on. Other writable scopes (`issues:
# write`, `pull-requests: write`) cannot create a release and are not grants.
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
#   - a `permissions:` construct the parser cannot read is an offender
#     (`unreadable-token-permissions`), because a construct this sweep cannot
#     read is not a read-only token. The pre-audit adversarial pass walked past
#     the parsed-mapping version with a YAML alias (`permissions: *w`), a merge
#     key (`<<: *w`) and a quoted key (`"contents": write`), each of which a
#     YAML parser resolves to a real `contents: write` grant while a lexical
#     reader sees nothing;
#   - command continuations are joined before the publisher vocabulary runs, so
#     a `gh \` split across a line break is read as `gh release`;
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

# CT-73 follow-up (cycle-5 adversarial pass): a shell line continuation is one
# command to bash and two lines to a substring match. `gh \` newline `release
# create` is the same invocation as `gh release create` and slipped past every
# publisher pattern below. The publisher checks run on the joined body; the
# permissions parse still needs the real line shape and runs on `clean`.
#
# Pure bash, for the same reason as everything else here: an external tool that
# is missing must not be able to turn a refusal into silence.
squash_continuations() {
    local line pending=""
    while IFS= read -r line; do
        if [ -n "$pending" ]; then
            line="${pending}${line#"${line%%[![:space:]]*}"}"
            pending=""
        fi
        case "$line" in
            *\\)
                # Drop the trailing backslash AND the whitespace before it, so
                # the join is `gh release` and not `gh  release`: a doubled
                # space is a different string to a substring match, which is
                # how the continuation slipped past the patterns to begin with.
                pending="${line%\\}"
                pending="${pending%"${pending##*[![:space:]]}"} "
                continue
                ;;
        esac
        printf '%s\n' "$line"
    done
    if [ -n "$pending" ]; then
        printf '%s\n' "$pending"
    fi
    return 0
}

# Cycle-6 adversarial pass (referee C1): YAML folds a `>` block scalar and a
# plain multi-line scalar into ONE line of space-separated words, so
#
#     - run: >
#         gh
#         release create v1
#
# is the single command `gh release create v1` to the runner and three lines to
# a substring match. The previous revision only joined backslash
# continuations, so that workflow passed the sweep. A literal `|` block keeps
# its newlines — each line is a separate command to the shell — so its body is
# copied through untouched rather than folded.
#
# Pure bash for the same reason as everything else here: a missing external
# tool must not be able to turn a refusal into silence.
fold_block_scalars() {
    FOLD=()
    local line text trimmed body n joined base
    # Patterns live in variables because /bin/bash 3.2 refuses a `>` or `|`
    # inside a `[[ =~ ]]` pattern written inline ("unexpected token").
    local pat_literal="^[[:space:]]*(-[[:space:]]+)?[A-Za-z_][A-Za-z0-9_.-]*:[[:space:]]*[|][-+]?[[:space:]]*$"
    local pat_folded="^[[:space:]]*(-[[:space:]]+)?[A-Za-z_][A-Za-z0-9_.-]*:[[:space:]]*[>][-+]?[[:space:]]*$"
    local pat_plain="^[[:space:]]*(-[[:space:]]+)?[A-Za-z_][A-Za-z0-9_.-]*:[[:space:]]*[^[:space:]].*$"
    while IFS= read -r line; do
        FOLD+=("${line%$'\r'}")
    done
    local i=0
    while [ "$i" -lt "${#FOLD[@]}" ]; do
        line="${FOLD[i]}"
        trimmed="${line%%[![:space:]]*}"
        base=${#trimmed}
        # A literal block: copy the indicator line and its body verbatim.
        if [[ "$line" =~ $pat_literal ]]; then
            printf '%s\n' "$line"
            i=$((i + 1))
            while [ "$i" -lt "${#FOLD[@]}" ]; do
                text="${FOLD[i]}"
                if [ -z "${text//[[:space:]]/}" ]; then
                    printf '%s\n' "$text"
                    i=$((i + 1))
                    continue
                fi
                trimmed="${text%%[![:space:]]*}"
                [ "${#trimmed}" -gt "$base" ] || break
                printf '%s\n' "$text"
                i=$((i + 1))
            done
            continue
        fi
        # A folded `>` scalar: join every deeper line onto the indicator line.
        if [[ "$line" =~ $pat_folded ]]; then
            joined=""
            n=$((i + 1))
            while [ "$n" -lt "${#FOLD[@]}" ]; do
                text="${FOLD[n]}"
                [ -n "${text//[[:space:]]/}" ] || break
                trimmed="${text%%[![:space:]]*}"
                [ "${#trimmed}" -gt "$base" ] || break
                joined="$joined ${text#"${text%%[![:space:]]*}"}"
                n=$((n + 1))
            done
            printf '%s%s\n' "$line" "$joined"
            i=$n
            continue
        fi
        # A plain scalar with a value on this line may continue on the next
        # deeper lines, provided the next line is text and not a nested key or
        # a sequence item (those are structure, not part of the value).
        if [[ "$line" =~ $pat_plain ]]; then
            joined=""
            n=$((i + 1))
            while [ "$n" -lt "${#FOLD[@]}" ]; do
                text="${FOLD[n]}"
                [ -n "${text//[[:space:]]/}" ] || break
                trimmed="${text%%[![:space:]]*}"
                [ "${#trimmed}" -gt "$base" ] || break
                body="${text#"${text%%[![:space:]]*}"}"
                [[ "$body" =~ ^(-[[:space:]]+)?[A-Za-z_][A-Za-z0-9_.-]*:[[:space:]] ]] && break
                [ "$body" = "-" ] && break
                joined="$joined $body"
                n=$((n + 1))
            done
            if [ -n "$joined" ]; then
                printf '%s%s\n' "$line" "$joined"
                i=$n
                continue
            fi
        fi
        printf '%s\n' "$line"
        i=$((i + 1))
    done
}

# Cycle-5 adversarial pass (attacker finding 4): bash collapses runs of
# whitespace and concatenates quoted with unquoted text, so `gh  release`,
# `gh "release"` and `gh 're'lease` are all the same invocation as
# `gh release` while every publisher pattern below is a substring match. The
# attacker's fixture showed all three returning "ok". Fold them to the single
# spelling the vocabulary is written against.
#
# Quotes are removed and runs of space/tab are squeezed to one. Newlines are
# deliberately left alone: `calls_a_remote_reusable_workflow` matches per line,
# and squeezing `[:space:]` would collapse the whole body into one line.
normalize_command_text() {
    local line
    while IFS= read -r line; do
        line="${line//\"/}"
        line="${line//\'/}"
        printf '%s\n' "$line"
    done | tr -s ' \t' ' '
}

# CT-73: what the token may do, read from the parsed `permissions:` mapping.
#
# Handles every spelling YAML allows here: `permissions: read-all` and
# `permissions: write-all` scalars, `permissions: {}`, a flow mapping
# `{contents: write}`, and a block mapping whose scopes may be spaced
# (`contents : write`), quoted (`contents: "write"`) or indented any depth
# (top level or per job). A duplicate `permissions:` key is not valid YAML and
# GitHub's last-wins parse of it is not something this gate will bet a release
# on, so a `contents: write` (or `write-all`) mapping wins over any other.
#
# FAIL CLOSED (cycle-5 adversarial pass): a spelling this parser cannot read is
# not a read-only value. `permissions: *w`, a merge key `<<: *w` and a quoted
# key `"contents": write` are all real write grants to YAML and all three read
# as nothing here, so any unreadable construct returns `unrecognized` and the
# caller treats it as an offender. Adding one spelling per audit round is the
# arms race that lost cycle 5; refusing what cannot be read ends it.
#
# stdout is one of: write-all | contents-write | unrecognized | read-only |
# absent
permissions_verdict() {
    PERM_LINES=()
    local line
    while IFS= read -r line; do
        PERM_LINES+=("${line%$'\r'}")
    done

    local saw_readonly=0 top_level_readonly=0 unrecognized=0 i n child child_indent child_trim
    local indent value key
    # `"permissions":` and `'permissions':` are the same key as the bare
    # spelling. Anything non-alphanumeric before the word is accepted, so a
    # key like `x-permissions` still does not match.
    local pat_perm='^([[:space:]]*)[^[:alnum:]_]*permissions[^[:alnum:]_]*[[:space:]]*:(.*)$'
    for (( i=0; i<${#PERM_LINES[@]}; i++ )); do
        line="${PERM_LINES[i]}"
        # A quoted key is the same key to YAML. The cycle-6 referee put
        # `"permissions": write-all` on one job of an otherwise read-only file
        # and the bare-key pattern never saw it, so the file passed.
        # The pattern lives in a variable: /bin/bash 3.2 misparses a quote
        # character written inline in a `[[ =~ ]]` pattern, and this one has to
        # accept a quoted key.
        if [[ "$line" =~ $pat_perm ]]; then
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
                    for (( n=i+1; n<${#PERM_LINES[@]}; n++ )); do
                        child="${PERM_LINES[n]}"
                        [ -n "${child//[[:space:]]/}" ] || continue
                        child_indent="${child%%[![:space:]]*}"
                        if (( ${#child_indent} <= ${#indent} )); then
                            break
                        fi
                        if [[ "$child" =~ ^[[:space:]]*([A-Za-z0-9_.-]+)[[:space:]]*:[[:space:]]*[\"\']?([A-Za-z0-9_-]+) ]]; then
                            key="${BASH_REMATCH[1]}"
                            value="${BASH_REMATCH[2]}"
                            # INDENT MATTERS: a read-only mapping on ONE job does
                            # not cover the jobs that declare none. Those inherit
                            # the repository default, which no ref can disclose,
                            # so a partly-declared file has the same hole as an
                            # undeclared one and is refused the same way.
                            saw_readonly=1
                            if [ -z "$indent" ]; then top_level_readonly=1; fi
                            case "$value" in
                                "write-all") printf 'write-all\n'; return 0 ;;
                            esac
                            case "$key:$value" in
                                "contents:write") printf 'contents-write\n'; return 0 ;;
                            esac
                            # A readable scope whose value is not in the
                            # vocabulary is not a read-only scope. Fail closed.
                            case "$value" in
                                "read"|"read-all"|"none"|"write") ;;
                                *) unrecognized=1 ;;
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
                                if [ -z "$indent" ]; then top_level_readonly=1; fi
                                ;;
                            *)
                                # `<<: *w`, `contents: *w`, a nested mapping, or
                                # any other child this parser cannot read. It is
                                # a scope it cannot prove read-only, so it is not
                                # a pass: fail closed.
                                unrecognized=1
                                ;;
                        esac
                    done
                    ;;
                "write-all"|"write")
                    printf 'write-all\n'; return 0
                    ;;
                "{}")
                    saw_readonly=1
                    if [ -z "$indent" ]; then top_level_readonly=1; fi
                    ;;
                "read-all"|"read"|"none")
                    saw_readonly=1
                    if [ -z "$indent" ]; then top_level_readonly=1; fi
                    ;;
                "{"*)
                    # Flow mapping, e.g. `{contents: write, issues: read}`.
                    if [[ "$value" =~ contents[[:space:]]*:[[:space:]]*[\"\']?write ]]; then
                        printf 'contents-write\n'; return 0
                    fi
                    if [[ "$value" =~ (^|[[:space:]{,])write-all([[:space:]},]|$) ]]; then
                        printf 'write-all\n'; return 0
                    fi
                    if [[ "$value" == *"*"* || "$value" == *"<<"* ]]; then
                        # An alias or merge key brings in scopes that live
                        # somewhere this sweep cannot see. Fail closed.
                        unrecognized=1
                    elif [[ "$value" =~ [A-Za-z0-9_.-]+[[:space:]]*: ]]; then
                        saw_readonly=1
                        if [ -z "$indent" ]; then top_level_readonly=1; fi
                    else
                        # `permissions: {…}` that is not a mapping at all.
                        unrecognized=1
                    fi
                    ;;
                *)
                    # `permissions: *w` is a YAML alias and resolves to a real
                    # mapping elsewhere in the file; any other value is a
                    # spelling this parse cannot resolve to read-only. Both fail
                    # closed rather than silently counting as nothing.
                    unrecognized=1
                    ;;
            esac
        fi
    done

    # An unreadable construct outranks a read-only one: a file that says both
    # `contents: read` and `permissions: *w` has not shown a read-only token.
    if [ "$unrecognized" -eq 1 ]; then
        printf 'unrecognized\n'
    elif [ "$saw_readonly" -eq 1 ]; then
        # A top-level read-only token covers every job. With job-level tokens
        # only, the coverage is as good as the least-declared job: a job that
        # declares nothing inherits the repository default, which no ref can
        # disclose, so the file is `partial` and refused like an undeclared one.
        if [ "$top_level_readonly" -eq 1 ] || _jobs_all_declare_permissions; then
            printf 'read-only\n'
        else
            printf 'partial\n'
        fi
    else
        printf 'absent\n'
    fi
}

# Every job under the top-level `jobs:` declares its own `permissions:`?
# Returns 0 (covered) only when there is at least one job and each job's block
# carries a `permissions:` key. Unreadable shapes (no `jobs:` line, a jobs block
# with no indent) return 1, because "cannot read it" must not become "covered".
_jobs_all_declare_permissions() {
    local i n k line indent inner inner_indent count=0 declared=0 job_indent=-1
    i=-1
    for (( n=0; n<${#PERM_LINES[@]}; n++ )); do
        if [[ "${PERM_LINES[n]}" =~ ^jobs[[:space:]]*:[[:space:]]*$ ]]; then
            i=$n
            break
        fi
    done
    [ "$i" -ge 0 ] || return 1
    for (( n=i+1; n<${#PERM_LINES[@]}; n++ )); do
        line="${PERM_LINES[n]}"
        [ -n "${line//[[:space:]]/}" ] || continue
        if [ "${line#"${line%%[![:space:]]*}"}" = "$line" ]; then
            break
        fi
        indent="${line%%[![:space:]]*}"
        if [ "$job_indent" -lt 0 ] || [ "${#indent}" -lt "$job_indent" ]; then
            job_indent=${#indent}
        fi
    done
    [ "$job_indent" -gt 0 ] || return 1
    for (( n=i+1; n<${#PERM_LINES[@]}; n++ )); do
        line="${PERM_LINES[n]}"
        [ -n "${line//[[:space:]]/}" ] || continue
        indent="${line%%[![:space:]]*}"
        if [ "${#indent}" -lt "$job_indent" ]; then
            break
        fi
        [ "${#indent}" -eq "$job_indent" ] || continue
        # Every key at the job indent is a job (a quoted key `"publish":` has
        # the same indent, and an anchor line is counted too — refusing more
        # than it should is the safe direction for a coverage proof). Only the
        # `permissions:` key itself is not a job.
        [[ "$line" =~ ^[[:space:]]*permissions[[:space:]]*: ]] && continue
        count=$((count + 1))
        for (( k=n+1; k<${#PERM_LINES[@]}; k++ )); do
            inner="${PERM_LINES[k]}"
            [ -n "${inner//[[:space:]]/}" ] || continue
            inner_indent="${inner%%[![:space:]]*}"
            if [ "${#inner_indent}" -le "${#indent}" ]; then
                break
            fi
            if [[ "$inner" =~ ^[[:space:]]*permissions[[:space:]]*: ]]; then
                declared=$((declared + 1))
                break
            fi
        done
    done
    [ "$count" -gt 0 ] || return 1
    [ "$declared" -eq "$count" ]
}

# CT-102: a reusable workflow hides its publisher behind `uses:`, and the sweep
# cannot read the callee. The first revision refused a callee whose path named a
# release (`…/release.yml@main`); the cycle-5 attacker called
# `other-org/ci/.github/workflows/publish-package.yml@main` with
# `secrets: inherit` and the sweep said `ok`, because a publisher can be named
# anything. The rule is inverted, as everywhere else here: a `uses:` that points
# at a workflow in ANOTHER repository is unreadable from this checkout, so it is
# refused whatever it is called, rather than assumed harmless.
#
# The refused shapes are the shapes GitHub accepts for a remote reusable
# workflow: `{owner}/{repo}/.github/workflows/{file}@{ref}`. GitHub will not run
# any other path as a workflow callee, so keying on that path refuses every
# remote callee without over-refusing the two classes the cycle-6 narrowing
# deliberately accepts: an action vendored under a path in another repository
# (`github/codeql-action/analyze@v3`) and a container reference however it is
# pinned (`docker://alpine:3.8`, `docker://ghcr.io/o/i@sha256:<digest>`) — a
# container image is not a workflow callee. That distinction matters — the first
# revision of this rule refused any `uses:` with two or more slashes before an
# `@`, which would have blocked a real dispatch that used a subdirectory action;
# `tests/test_workflow_config.py:1480`
# (`test_the_sweep_does_not_mistake_a_subdirectory_action_for_a_callee`) pins the
# accept. A value with two or more slashes whose last element is a YAML file is
# not a valid callee either, but it is not something this gate will bet a release
# on, so it is refused too. `actions/checkout@v4` (one slash, an action) does not
# match. A local `./.github/workflows/x.yml@ref` is fine: the sweep reads every
# workflow file on the ref, so the callee is in scope already.
#
# Matched one line at a time. `.` matches a newline in bash's ERE, so a
# whole-body `uses:.*@` pairs an unrelated `uses: actions/upload-artifact@…`
# line with a `uses:` further down the file.
calls_a_remote_reusable_workflow() {
    local line value path rest
    local pat_uses='^[[:space:]]*(-[[:space:]]+)?uses:[[:space:]]*(.*)$'
    while IFS= read -r line; do
        if [[ "$line" =~ $pat_uses ]]; then
            rest="${BASH_REMATCH[2]}"
            # A folded `>-` scalar was joined onto this line by
            # fold_block_scalars, so the first token is the indicator and the
            # callee is the token after it. Reading the indicator as the value
            # is how `uses: >-` passed the sweep while the same callee on one
            # line was refused.
            case "$rest" in
                ">"*|"|"*)
                    rest="${rest#?}"
                    case "$rest" in [-+]*) rest="${rest#?}" ;; esac
                    rest="${rest#"${rest%%[![:space:]]*}"}"
                    ;;
            esac
            value="${rest%%[[:space:]#]*}"
            case "$value" in
                ./*) continue ;;
            esac
            # An alias or merge key resolves to something this reader cannot
            # see. Refusing what cannot be read is the rule everywhere else in
            # this script, so it is the rule here: `uses: *w` is an offender.
            case "$value" in
                \**|'<<'*) return 0 ;;
            esac
            case "$value" in
                */.github/workflows/*) return 0 ;;
            esac
            path="${value%@*}"
            case "$path" in
                */*/*.yml|*/*/*.yaml) return 0 ;;
            esac
        fi
    done
    return 1
}

# Own namespace for the fetched heads so a caller's refs are never
# rewritten. It is NOT under refs/remotes/: a remote literally named
# `publish-audit` would own that namespace, and the emptying below
# would delete its tracking refs.
# The namespace is emptied first: a plain fetch does not delete a head that
# vanished on the remote, and a stale leftover would name a branch that is
# no longer there. A sweep that reports a ghost is as bad as one that misses.
AUDIT_REMOTE_REFS="refs/publish-audit"

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
            unrecognized)
                # A `permissions:` construct this sweep cannot read (a YAML
                # alias, a merge key, a quoted key, anything unrecognised) is
                # not a read-only token. Refusing it is the whole point: the
                # previous revision let `permissions: *w` grant contents: write
                # while reading as nothing here.
                report "$branch" "$path" "unreadable-token-permissions"
                continue
                ;;
            partial)
                # Only SOME jobs declare a read-only token. The rest inherit the
                # repository default, which no ref can disclose, so the file
                # grants a token it cannot prove read-only for every job. This
                # is the same hole as an undeclared file and is refused the same
                # way, rather than letting one read-only job vouch for the rest.
                report "$branch" "$path" "partial-token-permissions"
                continue
                ;;
        esac

        # CT-73 follow-up: the publisher patterns below are substring matches,
        # and `gh \` + newline + `release` is the same command split across two
        # lines, as is a YAML-folded `>` scalar. Reassign `clean` to the joined
        # form now that the permissions parse (which needs the real line shape)
        # has run.
        clean="$(printf '%s\n' "$clean" | fold_block_scalars | squash_continuations | normalize_command_text)"

        # `gh --repo owner/repo release create` and `gh -R owner/repo release
        # create` are the same invocation with the target in front of the
        # subcommand, so the contiguous `gh release` substring misses them.
        if [[ "$clean" == *"gh release"* \
              || "$clean" == *"gh --repo"*" release "* \
              || "$clean" == *"gh -R"*" release "* ]]; then
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
        if [[ "$clean" == *"api.github.com"* || "$clean" == *'$GITHUB_API_URL'* \
              || "$clean" == *"github.api_url"* ]]; then
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
                    "createReleaseAsset" \
                    "create_release" "update_release" "upload_release_asset"; do
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
        # callee in another repository cannot be read from here, so it fails
        # closed whatever it is named. Matched on the stripped body, so the
        # comments in this repository that discuss release workflows are not
        # offenders.
        if printf '%s\n' "$clean" | calls_a_remote_reusable_workflow; then
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
