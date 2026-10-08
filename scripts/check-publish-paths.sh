#!/usr/bin/env bash
# Refuse a second publish path on any remote non-main BRANCH.
#
# Scope (cycle-5 adversarial pass; claim narrowed in cycle 7). The sweep
# enumerates branch refs only (`+refs/heads/*`) and fetches with `--no-tags`,
# so it never reads a tag ref. That is by design, and the ok/refusal wording
# below says "branch" rather than "ref" because of it:
#   - a released tag's tree IS the released code, so every published tag
#     necessarily contains the release workflow that produced it; fetching tags
#     would refuse this repository's own v0.6.x tags, not a second publish path;
#   - a tag can only be created by someone who can already push a workflow.
# The control for tag-triggered publication is the environment branch policy in
# `scripts/check-release-credentials.sh`, not this sweep: every release
# credential lives in an environment whose deployment branch policy allows
# `main` only, so a job that names one cannot start on a tag and a tag run has
# no signing key. The default-token path (`contents: write` with no secret) is
# the residual, and it is disclosed in `releases/PATCH-0.6.8.md` rather than
# silently assumed away.
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
REFUSAL="refusing: a non-main branch carries a publish-capable workflow"

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
        # A double-quoted YAML key can spell another key with an escape:
        # `"permiss\u0069ons": write-all` IS `permissions: write-all` after
        # parsing. The explicit-key spelling is the same class of problem:
        # `? permissions` puts the key on one line and `: write-all` on the
        # next, so a colon-keyed reader never sees the token. Both were found
        # by attacking the first fix for the quoted-key case; both are key
        # spellings this reader cannot resolve, so both fail closed.
        # The escape pattern requires the quote in a KEY position (start of the
        # line, after `- `, or after `{`/`,`) so a Python snippet inside a
        # `run:` block that happens to hold a `"\x7f"` literal — which the
        # repository's own build workflow does — is not read as a key.
        local pat_escaped_key='(^[[:space:]]*(-[[:space:]]+)?|[{,][[:space:]]*)["][^"]*\\[uUxX][0-9A-Fa-f]+[^"]*["][[:space:]]*:'
        local pat_explicit_key='^[[:space:]]*\?[[:space:]]*["]?permissions'
        if [[ "$line" =~ $pat_escaped_key ]] || [[ "$line" =~ $pat_explicit_key ]]; then
            unrecognized=1
        fi
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
                    # A mapping the fold did not complete — `permissions: {issues:
                    # read,` with `contents: write}` on the next line — is a
                    # mapping this parse cannot read. Fail closed rather than
                    # reading the first scope and calling the rest absent.
                    case "$value" in
                        *"}"*) ;;
                        *) unrecognized=1; continue ;;
                    esac
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
        # A flow mapping puts `permissions:` mid-line:
        #     publish: {runs-on: …, permissions: {contents: write}, …}
        #     "publish": {…}
        #     publish: !!map {…}
        #     publish:
        #       {runs-on: …, permissions: {contents: write}, …}
        # The anchored pattern above cannot see any of those, so a job could grant
        # itself a write token while the top level (or another job) showed a
        # read-only one. Read it the same way and refuse the same values; a
        # mid-line spelling this parse cannot read fails closed too.
        # The gate is an opening brace at the start of the line or after
        # space/comma — the positions a flow mapping can begin in — so prose in a
        # `run:` string (`echo "{permissions: write}"`) is not read as a grant.
        if [[ ! "$line" =~ $pat_perm ]]; then
            local pat_flowopen='(^|[[:space:],])[\{]'
            if [[ "$line" =~ $pat_flowopen ]]; then
                # Cycle-7: the key needs a left boundary. Without one, an
                # unrelated flow key whose name merely ENDS in `permissions`
                # (`with: {x-permissions: {contents: write}}` on a `read-all`
                # workflow) was read as the token and refused as
                # `grants-contents-write`, while the real token was `read-all`.
                # A key spelled exactly `permissions` begins at the start of the
                # line or after space, `{` or `,` — the positions a flow mapping
                # key can begin in.
                local pat_inline='(^|[[:space:]{,])permissions[^[:alnum:]_]*:(.*)$'
                if [[ "$line" =~ $pat_inline ]]; then
                    value="${BASH_REMATCH[2]}"
                    value="${value#"${value%%[![:space:]]*}"}"
                    case "$value" in
                        "write-all"*) printf 'write-all\n'; return 0 ;;
                        "write"*) printf 'write-all\n'; return 0 ;;
                        "read-all"*|"read"*|"none"*|"{}"*) saw_readonly=1 ;;
                        *"{"*)
                            if [[ "$value" =~ contents[[:space:]]*:[[:space:]]*[\"\']?write ]]; then
                                printf 'contents-write\n'; return 0
                            fi
                            if [[ "$value" =~ (^|[[:space:]{,])write-all([[:space:]},]|$) ]]; then
                                printf 'write-all\n'; return 0
                            fi
                            if [[ "$value" == *"*"* || "$value" == *"<<"* ]]; then
                                unrecognized=1
                            else
                                saw_readonly=1
                            fi
                            ;;
                        *"*"*|*"<<"*) unrecognized=1 ;;
                        *) unrecognized=1 ;;
                    esac
                fi
            fi
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

# Cycle-7 flow readers, for the `jobs:` coverage proof below. A workflow may
# spell its jobs as a flow mapping instead of indented blocks, and the
# line-and-indent proof cannot see a job key that sits inside braces. These
# readers resolve only the shapes they can close completely; anything they
# cannot read returns 1, because "cannot read it" must not become "covered".

# The top-level members of one balanced flow mapping. $1 must be a single
# `{...}` mapping; sets FLOW_MEMBERS to its comma-separated members and returns
# 1 for an unclosed mapping, a trailing token or a nested-bracket mismatch.
_flow_members() {
    FLOW_MEMBERS=()
    local s="$1" i ch depth=0 in_quote="" member="" closed=0
    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"
    [ "${s:0:1}" = "{" ] || return 1
    for (( i=0; i<${#s}; i++ )); do
        ch="${s:i:1}"
        if [ -n "$in_quote" ]; then
            member+="$ch"
            if [ "$ch" = "$in_quote" ]; then in_quote=""; fi
            continue
        fi
        case "$ch" in
            '"'|"'") in_quote="$ch"; member+="$ch" ;;
            '{'|'[')
                depth=$((depth + 1))
                if [ "$depth" -ge 2 ]; then member+="$ch"; fi
                ;;
            '}'|']')
                if [ "$depth" -eq 1 ] && [ "$ch" = "}" ]; then
                    local after="${s:i+1}"
                    [ -z "${after//[[:space:]]/}" ] || return 1
                    depth=0
                    closed=1
                    break
                fi
                [ "$depth" -gt 0 ] || return 1
                depth=$((depth - 1))
                member+="$ch"
                ;;
            ',')
                if [ "$depth" -eq 1 ]; then
                    if [ -n "${member//[[:space:]]/}" ]; then
                        FLOW_MEMBERS+=("$member")
                    fi
                    member=""
                else
                    member+="$ch"
                fi
                ;;
            *)
                if [ "$depth" -ge 1 ]; then member+="$ch"; fi
                ;;
        esac
    done
    [ "$closed" -eq 1 ] || return 1
    [ -z "$in_quote" ] || return 1
    if [ -n "${member//[[:space:]]/}" ]; then
        FLOW_MEMBERS+=("$member")
    fi
    return 0
}

# Split one flow member at its first top-level colon. Sets FLOW_KEY (trimmed,
# surrounding quotes stripped) and FLOW_VALUE (trimmed); returns 1 for a member
# with no top-level colon (an explicit key or an alias).
_flow_key_value() {
    local s="$1" i ch depth=0 in_quote="" key=""
    FLOW_KEY=""
    FLOW_VALUE=""
    for (( i=0; i<${#s}; i++ )); do
        ch="${s:i:1}"
        if [ -n "$in_quote" ]; then
            key+="$ch"
            if [ "$ch" = "$in_quote" ]; then in_quote=""; fi
            continue
        fi
        case "$ch" in
            '"'|"'") in_quote="$ch"; key+="$ch" ;;
            '{'|'[') depth=$((depth + 1)); key+="$ch" ;;
            '}'|']') depth=$((depth - 1)); key+="$ch" ;;
            ':')
                if [ "$depth" -eq 0 ]; then
                    FLOW_KEY="$key"
                    FLOW_VALUE="${s:i+1}"
                    FLOW_KEY="${FLOW_KEY#"${FLOW_KEY%%[![:space:]]*}"}"
                    FLOW_KEY="${FLOW_KEY%"${FLOW_KEY##*[![:space:]]}"}"
                    FLOW_KEY="${FLOW_KEY#\"}"; FLOW_KEY="${FLOW_KEY%\"}"
                    FLOW_KEY="${FLOW_KEY#\'}"; FLOW_KEY="${FLOW_KEY%\'}"
                    FLOW_VALUE="${FLOW_VALUE#"${FLOW_VALUE%%[![:space:]]*}"}"
                    FLOW_VALUE="${FLOW_VALUE%"${FLOW_VALUE##*[![:space:]]}"}"
                    return 0
                fi
                key+="$ch"
                ;;
            *) key+="$ch" ;;
        esac
    done
    return 1
}

# Does one flow job member (`build: {…}`) carry a `permissions:` key at the job
# mapping's OWN depth? A `permissions:` nested deeper (inside an `env:` or
# `strategy:` flow mapping) is a variable, not the job's token, exactly as in
# the block form the cycle-6 fix hardened.
_flow_job_declares_permissions() {
    local member="$1" m k
    _flow_key_value "$member" || return 1
    [ -n "$FLOW_KEY" ] || return 1
    [ "${FLOW_VALUE:0:1}" = "{" ] || return 1
    _flow_members "$FLOW_VALUE" || return 1
    for m in "${FLOW_MEMBERS[@]}"; do
        _flow_key_value "$m" || continue
        k="$FLOW_KEY"
        if [ "$k" = "permissions" ]; then
            return 0
        fi
    done
    return 1
}

# Every job in a flow-style `jobs` mapping declares its own `permissions:`.
# Returns 0 only when the mapping has at least one job and every job carries the
# token at its own depth.
_flow_jobs_mapping_covers() {
    local m k count=0 declared=0
    _flow_members "$1" || return 1
    [ "${#FLOW_MEMBERS[@]}" -gt 0 ] || return 1
    for m in "${FLOW_MEMBERS[@]}"; do
        _flow_key_value "$m" || return 1
        k="$FLOW_KEY"
        [ -n "$k" ] || return 1
        count=$((count + 1))
        if _flow_job_declares_permissions "$m"; then
            declared=$((declared + 1))
        fi
    done
    [ "$count" -gt 0 ] || return 1
    [ "$declared" -eq "$count" ]
}

# Collect the one balanced flow mapping that begins with `{` on
# PERM_LINES[$1]. A mapping spread over several lines is joined with spaces; an
# unterminated one sets nothing and returns 1.
_collect_flow() {
    local start="$1" i n ch line depth=0 in_quote="" seen=0
    FLOW_TEXT=""
    for (( n=start; n<${#PERM_LINES[@]}; n++ )); do
        line="${PERM_LINES[n]}"
        for (( i=0; i<${#line}; i++ )); do
            ch="${line:i:1}"
            if [ "$seen" -eq 0 ]; then
                if [ "$ch" != "{" ]; then
                    continue
                fi
                seen=1
            fi
            if [ -n "$in_quote" ]; then
                FLOW_TEXT+="$ch"
                if [ "$ch" = "$in_quote" ]; then in_quote=""; fi
                continue
            fi
            case "$ch" in
                '"'|"'") in_quote="$ch"; FLOW_TEXT+="$ch" ;;
                '{'|'[') depth=$((depth + 1)); FLOW_TEXT+="$ch" ;;
                '}'|']')
                    depth=$((depth - 1))
                    FLOW_TEXT+="$ch"
                    if [ "$depth" -eq 0 ]; then
                        return 0
                    fi
                    ;;
                *) FLOW_TEXT+="$ch" ;;
            esac
        done
        if [ "$seen" -eq 1 ]; then
            FLOW_TEXT+=" "
        fi
    done
    FLOW_TEXT=""
    return 1
}

# Every job under the top-level `jobs:` declares its own `permissions:`?
# Returns 0 (covered) only when there is at least one job and each job's block
# carries a `permissions:` key. Unreadable shapes (no `jobs:` line, a jobs block
# with no indent) return 1, because "cannot read it" must not become "covered".
# Cycle-7: a flow-style `jobs` mapping (`jobs: {build: {…}}` on one line, or a
# bare `jobs:` whose flow mapping begins on the next line) declares its jobs
# with braces. The block proof below counts job-key LINES and sees zero jobs for
# that shape, so a read-only flow job was refused as `partial-token-permissions`
# while PyYAML resolved `jobs.build.permissions.contents == "read"`. The flow
# shape is now read by its own proof; anything that cannot be closed returns 1.
_jobs_all_declare_permissions() {
    local i n k line indent inner inner_indent count=0 declared=0 job_indent=-1 child_min
    local tail="" flow_start=-1
    i=-1
    for (( n=0; n<${#PERM_LINES[@]}; n++ )); do
        if [[ "${PERM_LINES[n]}" =~ ^jobs[[:space:]]*:[[:space:]]*(.*)$ ]]; then
            i=$n
            tail="${BASH_REMATCH[1]}"
            break
        fi
    done
    [ "$i" -ge 0 ] || return 1
    tail="${tail#"${tail%%[![:space:]]*}"}"
    if [ -n "$tail" ]; then
        if [ "${tail:0:1}" = "{" ]; then
            flow_start=$i
        fi
    else
        for (( n=i+1; n<${#PERM_LINES[@]}; n++ )); do
            line="${PERM_LINES[n]}"
            [ -n "${line//[[:space:]]/}" ] || continue
            line="${line#"${line%%[![:space:]]*}"}"
            if [ "${line:0:1}" = "{" ]; then
                flow_start=$n
            fi
            break
        done
    fi
    if [ "$flow_start" -ge 0 ]; then
        if _collect_flow "$flow_start" && _flow_jobs_mapping_covers "$FLOW_TEXT"; then
            return 0
        fi
        return 1
    fi
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
        # Cycle-7: a job whose value is a flow mapping on the job's own line
        # (`build: {runs-on: …, permissions: {contents: read}}`) declares its
        # token in the braces, not on a child line. Only the job value being a
        # `{...}` mapping counts; every other shape falls through to the block
        # proof, so a deeper `permissions:` under `env:` still does not cover.
        if _flow_key_value "$line" && [ "${FLOW_VALUE:0:1}" = "{" ] \
           && _flow_job_declares_permissions "$line"; then
            declared=$((declared + 1))
            continue
        fi
        # The job's own `permissions:` is a DIRECT child: it sits at the smallest
        # indent inside the job block. A deeper `permissions:` (under `env:` or
        # `strategy:`, say) is not the job's token. The cycle-6 attacker put
        # `env:` + `permissions: read` in a job that declares none, and counting
        # any deeper key as declared made the coverage proof pass.
        child_min=-1
        for (( k=n+1; k<${#PERM_LINES[@]}; k++ )); do
            inner="${PERM_LINES[k]}"
            [ -n "${inner//[[:space:]]/}" ] || continue
            inner_indent="${inner%%[![:space:]]*}"
            if [ "${#inner_indent}" -le "${#indent}" ]; then
                break
            fi
            if [ "$child_min" -lt 0 ] || [ "${#inner_indent}" -lt "$child_min" ]; then
                child_min=${#inner_indent}
            fi
        done
        if [ "$child_min" -lt 0 ]; then
            continue
        fi
        for (( k=n+1; k<${#PERM_LINES[@]}; k++ )); do
            inner="${PERM_LINES[k]}"
            [ -n "${inner//[[:space:]]/}" ] || continue
            inner_indent="${inner%%[![:space:]]*}"
            if [ "${#inner_indent}" -le "${#indent}" ]; then
                break
            fi
            if [ "${#inner_indent}" -eq "$child_min" ] && [[ "$inner" =~ ^[[:space:]]*permissions[[:space:]]*: ]]; then
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
# match. A local `./.github/workflows/x.yml@ref` is fine: the main loop reads
# every workflow file under `.github/workflows` on the ref, so that callee is in
# scope already. Any OTHER `./` value is a local ACTION, not a workflow: the
# loop never looks outside `.github/workflows`, so `.github/actions/publish`
# (a composite action holding `run: gh release create`) and `./tools/publish`
# are bodies this sweep does not read. Cycle 7 showed
# `uses: ./.github/actions/publish` returning "ok" while the action published, so
# the check now keeps the pass ONLY for a local value that is itself a workflow
# file it reads and refuses every other local target, printing the distinct
# reason `calls-a-local-action`.
#
# Matched one line at a time. `.` matches a newline in bash's ERE, so a
# whole-body `uses:.*@` pairs an unrelated `uses: actions/upload-artifact@…`
# line with a `uses:` further down the file.
calls_a_remote_reusable_workflow() {
    local line value path rest
    # The key may be anywhere on the line, not only first: a flow mapping or a
    # flow-sequence step carries it as `{uses: …}` or `[{uses: …}]`, and the
    # first revision's line-anchored pattern never saw those, so a remote callee
    # could hide in flow style while the sweep said `ok`. `uses` must be a whole
    # word (no alphanumeric, underscore or dash before it), exactly like the
    # `permissions` pattern, so `x-uses:` is not a key.
    local pat_uses='(^|[^[:alnum:]_-])uses[[:space:]]*:[[:space:]]*(.*)$'
    # The explicit-key spelling splits the key and its value across lines:
    # `- ? uses` then `  : other-org/ci/.github/workflows/x.yml@main`. The key
    # line carries no colon, so the pattern above misses the callee entirely; a
    # `uses` spelled this way is refused rather than read past.
    local pat_explicit_uses='(^|[^[:alnum:]_-])\?[[:space:]]*["]?uses([[:space:]]|$)'
    while IFS= read -r line; do
        if [[ "$line" =~ $pat_explicit_uses ]]; then
            return 0
        fi
        if [[ "$line" =~ $pat_uses ]]; then
            rest="${BASH_REMATCH[2]}"
            # A folded `>-` scalar was joined onto this line by
            # fold_block_scalars, so the first token is the indicator and the
            # callee is the token after it. Reading the indicator as the value
            # is how `uses: >-` passed the sweep while the same callee on one
            # line was refused.
            case "$rest" in
                ">"*|"|"*)
                    # The indicator may carry a chomping sign and/or an explicit
                    # indentation digit in either order (`|2-`, `>+2`, `>-2`). The
                    # cycle-6 referee put the callee on the next line under `>2-`
                    # and the sign-only strip read the value as `2-`, so the
                    # callee was never seen.
                    rest="${rest#?}"
                    # Strip the whole run: `|2-` and `>-2` both carry a digit
                    # and a sign, and `${var##[-+0-9]}` removes one character,
                    # not the run.
                    while [ -n "$rest" ] && [[ "$rest" == [-+0-9]* ]]; do
                        rest="${rest#?}"
                    done
                    rest="${rest#"${rest%%[![:space:]]*}"}"
                    ;;
            esac
            value="${rest%%[[:space:]#]*}"
            # A `uses:` with nothing on its own line is a block scalar (`uses: |`)
            # or a continuation whose callee sits on a deeper line this reader
            # never joins. That is a callee it cannot read, and the rule here is
            # to refuse what it cannot read: the cycle-6 referee smuggled a remote
            # workflow in under `uses: |` and `|2-` and the sweep said ok.
            [ -n "$value" ] || return 0
            # A local `./` target is only in scope when it is a workflow file
            # this sweep already reads: the main loop enumerates
            # `.github/workflows/*.yml|*.yaml` and nothing else. Any other `./`
            # value is a local ACTION — `.github/actions/publish`, `./tools/
            # publish` — whose body this check never reads, so a composite
            # action holding `run: gh release create` published while the sweep
            # printed ok (cycle-7 attacker). Keep the pass for the workflow-file
            # shape only and refuse every other local target, with its own
            # reason so the report names what was unread.
            case "$value" in
                ./*)
                    path="${value%@*}"
                    # A flow callee carries the mapping's closing brace (or a
                    # sequence bracket/comma) in the same token:
                    # `steps: [{uses: ./.github/workflows/other.yml}]` reads the
                    # value as `…other.yml}]`. Strip that punctuation before the
                    # workflow-file test so a legitimate local callee in flow
                    # style still passes, exactly as it did before cycle 7.
                    while [ -n "$path" ]; do
                        case "$path" in
                            *[]},]) path="${path%?}" ;;
                            *) break ;;
                        esac
                    done
                    case "$path" in
                        ./.github/workflows/*.yml|./.github/workflows/*.yaml)
                            continue ;;
                    esac
                    printf 'calls-a-local-action\n'
                    return 0
                    ;;
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
        # offenders. The function prints the specific unread shape when it has
        # one (`calls-a-local-action`); anything else is the remote callee.
        if callee_reason="$(printf '%s\n' "$clean" | calls_a_remote_reusable_workflow)"; then
            report "$branch" "$path" \
                "${callee_reason:-calls-a-release-workflow}"
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

printf 'ok: no non-main branch carries a publish-capable workflow\n' >&2
exit 0
