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
#   - grant a writable token — `write-all`, or ANY `key: write` scope (cycle 8:
#     `contents`, `packages` and `id-token` are all publish grants) — when the
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
# The token arm is the GUARANTEE; the publisher-name list is DEFENCE IN DEPTH.
# That list names only the publishers an audit demonstrated, so a workflow that
# publishes through an action not named here — authenticated by a repository
# secret rather than by a writable default token — is not caught BY THIS
# SCRIPT. That case is covered beside it: `scripts/check-release-credentials.sh`
# proves no environment holding a release credential admits a non-main ref, and
# the repository carries no repository-level secrets. Do not read a clean sweep
# as "no action anywhere can publish"; read it as "no non-main branch can
# publish with the default token or through a named publisher".
#
# THE DOCTRINE (cycle 9). This sweep is a parser, not a word list, and a
# construct it cannot classify is REFUSED — never silently read as read-only.
# Every earlier revision recognised dangerous SPELLINGS one at a time, so a
# YAML spelling it had not been shown walked past it as harmless. The fix for
# that whole class is to invert the default: prove the token read-only, or
# refuse. A round-10 identity waiver (below) waives ONLY the identity arm; it
# never waives this parser, which does not read the allowlist at all. A waived
# change that still grants a writable token or calls a publisher is therefore
# refused here exactly as it would be without the waiver. In practice:
#   - a flow `permissions:` mapping is taken apart member by member, and each
#     scope's value has its YAML presentation (a tag such as `!!str`, an anchor
#     such as `&a`, surrounding quotes) removed before the decision. A member
#     whose value does not resolve to `read`/`read-all`/`none`/`write`/
#     `write-all` — an alias, a merge key, a nested mapping, an empty value —
#     makes the mapping UNREADABLE and it is refused
#     (`unreadable-token-permissions`), never counted as read-only. The old
#     fallback that saw any `key:` and called the mapping read-only is gone. On
#     a line that spells the mapping inline, `permissions` is found in KEY
#     POSITION only, so a quoted scalar in VALUE position (the note
#     `env: {NOTE: "permissions: write"}`) is data, not a grant, while a quoted
#     key or value (`"permissions": {issues: read, "contents" : "write"}`) is
#     still read as the token it is;
#   - a `uses:` value that STARTS with `&`, `*` or `!` is refused: an anchor or
#     a tag is presentation this reader does not resolve to a name, and an
#     alias points at a name the file holds elsewhere. A leading tag or anchor
#     is stripped first and the remainder re-tested as the callee, so
#     `uses: !!str owner/repo/.github/workflows/x.yml@main` is still refused as
#     the remote callee it is, and `uses: &a |` (an anchored block scalar) is
#     refused rather than read as empty;
#   - BOTH readers require KEY POSITION. A `permissions:` or `uses:` token
#     inside the value of a scalar key (`run:`, `with:`, `if:`, `env:`,
#     `name:`, `shell:`, `working-directory:`) is data, not a key; that value
#     and any block body under it are removed before either decision. The
#     publisher vocabulary still sees that body — `gh release` inside `run: |`
#     really is a publisher — so the stripping is applied only to the
#     permissions and callee readers, never to the publisher text;
#   - a job id is recognised by its POSITION under the workflow `jobs:` key,
#     never by its spelling: `env:`, `run:`, `with:`, `if:`, `name:`, `shell:`
#     and `working-directory:` are all legal job ids, so a non-blank line at
#     the job-id indent inside the jobs block is never removed as a scalar
#     key's value. The exemption is scoped to the jobs block — a `run:` under
#     `defaults:`/`on:` or a workflow-level `env:` keeps the KEY-POSITION rule
#     above. The locator reads the KEY, not data: a `jobs:`-shaped line inside a
#     top-level block scalar (`name: |`, `run-name: |`, `defaults: … |`) is not
#     a key, and a quoted `"jobs":` is the same key as the bare one. Anything
#     the locator cannot resolve unambiguously — an escaped key spelling, two
#     candidates, or a candidate whose block holds no job declaration — is
#     REFUSED (`unreadable-token-permissions`), never read as a file with no
#     jobs. The same rule covers a `jobs:`-shaped line inside a MULTI-LINE
#     QUOTED scalar (`name: "start` / `jobs:` / `end"`), which the locator
#     tracks by carrying the quote state across lines;
#   - YAML DOUBLE-QUOTED ESCAPES are decoded before any callee or publisher
#     decision, because
#     `uses: "other-org/ci\x2f.github\x2fworkflows\x2fpublish.yml@main"` is a
#     remote callee to YAML and to GitHub while the literal `\x2f` matched
#     nothing here. `\xHH`, `\uHHHH`, `\UHHHHHHHH`, `\/`, `\\`, `\"`, `\ ` and
#     the short names decode to the characters they denote; an escape this
#     reader does not know — or a trailing `\` whose folded continuation it does
#     not resolve — is not left standing as literal text but refused
#     (`unreadable-escape-sequence`). Escapes are decoded ONLY inside a
#     double-quoted scalar opened in node position, so a shell regex in a plain
#     scalar (`run: grep "\d+"`) is data and is not mistaken for YAML escapes;
#   - a file with MORE THAN ONE YAML DOCUMENT is refused
#     (`unreadable-multiple-documents`). A second document's read-only
#     `permissions:` and empty `jobs: {}` would otherwise clear the first
#     document's fail-closed sentinel while doc0's job really granted a writable
#     token. Nothing here can bound a construct to the document it belongs to;
#   - a `jobs:`-shaped line at column 0 INSIDE a multi-line quoted scalar makes
#     the file's key location unprovable, and the file is refused as
#     unclassifiable (`unreadable-token-permissions`) whatever else it carries:
#     two readings of such a file agree on neither the key nor the job, so no
#     grant inferred from either is trusted. A quoted `"permissions":` KEY, by
#     contrast, is the same key as the bare spelling and is read normally.
#
#   - ROUND 10, the decidable identity arm: a non-main branch may not ADD OR
#     MODIFY any path under `.github/workflows/` or `.github/actions/` relative
#     to its MERGE BASE with main. That arm compares blob OIDS, so it needs no
#     YAML classification at all and cannot be spelled around; it is reported as
#     `branch-changes-workflow-file`. A path whose oid is unchanged — a
#     mode-only change included — is inherited, reviewed content and passes; a
#     deletion adds no capability and passes; an added path, a changed blob, and
#     a symlink or gitlink at a workflow path are changes. A branch may be
#     waived by a line on MAIN, never on the branch itself, in
#     `.github/publish-sweep-allowlist.txt`, naming exactly
#     `<branch> <path> <blob-oid>` — an exact match, never a prefix and never a
#     glob. A missing allowlist file is an empty list, not an error; a file that
#     exists but cannot be read, a shallow clone, an empty or failed merge base
#     and an unlistable main tree are all refusals (`unreadable-*`), never "ok".
#     The parser NEVER reads the allowlist, so a waived change that is still
#     publish-capable is refused by the parser exactly as before: a waiver
#     cannot smuggle a publish path past the token and callee readers. Where the
#     parser and this arm both refuse the same branch and path, the parser's
#     reason is the one reported. The closing summary names each class that is
#     present — a publish-capable workflow refusal, a CI change relative to the
#     merge base with main, or both — with the number of offending branches in
#     that class, and attaches each remedy to the class it can fix. An
#     identity-only refusal therefore never claims a publish-capable workflow,
#     and the old "delete the file on the ref above" sentence is gone.
#
# The publisher patterns run on a NORMALIZED body (cycle-5 adversarial pass):
# comments stripped, `\`-continuations joined, quotes removed and runs of
# space/tab squeezed, so `gh  release`, `gh "release"` and `gh \`+newline+
# `release` are one spelling to the match. The `permissions:` parse runs before
# that normalization because it needs the real line shape; since cycle 9 it runs
# on the body with the values and block bodies of scalar keys removed (the
# KEY-POSITION rule above), while the publisher patterns still see the full body.
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
# something a release gate should bet on. Cycle 8 removed the old claim that
# other writable scopes are harmless: this sweep cannot know which scope a
# publisher needs, `packages: write` pushes a package and `id-token: write`
# mints the OIDC token an `npm publish` trusts, so EVERY `key: write` (and
# `write-all`) is a grant.
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
# Addendum #3: the closing banner is composed per refusal class at the end of
# the run, so there is no single fixed refusal sentence to keep here.

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

# Cycle-8 adversarial pass (over-refusal): a `uses:` inside the literal body of
# some OTHER key is data, not a callee. A `run: |` step whose script merely
# echoes the text `uses: owner/repo/.github/workflows/publish.yml@main` was
# refused as a remote reusable-workflow call even though the job runs a shell
# echo. This filter drops the body of every `|` literal block whose key is not
# `uses`, and it runs only on the text handed to the callee reader. It must not
# touch the text the publisher vocabulary sees: a `gh release` inside `run: |`
# really is a publisher. A `uses: |` block is left intact so the callee reader
# still refuses a callee hidden that way.
strip_non_uses_literal_bodies() {
    local -a SB=()
    local line key text trimmed base i
    local pat_literal="^[[:space:]]*(-[[:space:]]+)?([A-Za-z_][A-Za-z0-9_.-]*):[[:space:]]*[|][-+]?[[:space:]]*$"
    while IFS= read -r line; do
        SB+=("${line%$'\r'}")
    done
    i=0
    while [ "$i" -lt "${#SB[@]}" ]; do
        line="${SB[i]}"
        if [[ "$line" =~ $pat_literal ]]; then
            key="${BASH_REMATCH[2]}"
            trimmed="${line%%[![:space:]]*}"
            base=${#trimmed}
            printf '%s\n' "$line"
            i=$((i + 1))
            while [ "$i" -lt "${#SB[@]}" ]; do
                text="${SB[i]}"
                if [ -z "${text//[[:space:]]/}" ]; then
                    if [ "$key" = "uses" ]; then printf '%s\n' "$text"; fi
                    i=$((i + 1))
                    continue
                fi
                trimmed="${text%%[![:space:]]*}"
                [ "${#trimmed}" -gt "$base" ] || break
                if [ "$key" = "uses" ]; then printf '%s\n' "$text"; fi
                i=$((i + 1))
            done
            continue
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
# Cycle-9 addendum (defeat 3): the quote stripper above removed the `"` that
# DELIMITS a double-quoted scalar but never DECODED the escapes inside it. YAML
# (and GitHub) decode `\x2f` to `/`, so
# `uses: "other-org/ci\x2f.github\x2fworkflows\x2fpublish.yml@main"` is a remote
# callee to every real parser while the literal `\x2f` never matched
# `/.github/workflows/` here and the sweep printed ok. The decoder below renders
# the escapes before the callee and publisher readers run. It decodes the whole
# documented double-quoted vocabulary: `\xHH`, `\uHHHH`, `\UHHHHHHHH`, `\/`,
# `\\`, `\"`, `\ ` and the short names. An escape it does not recognise — or a
# trailing `\` (a folded line continuation this line-based reader does not
# resolve) — becomes the DQ_BAD sentinel, which the main loop refuses as
# `unreadable-escape-sequence`. An escape is decoded ONLY inside a double-quoted
# scalar opened in node position: a `"` in the middle of a plain scalar
# (`run: grep "\d+"`) is data, not an opener, so ordinary shell regexes are not
# mistaken for YAML escapes.
DQ_BAD='*sweep-undecodable-escape*'

# Print one Unicode code point as UTF-8. Bash 3.2's printf decodes `\xHH` under
# `%b` but not `\u`/`\U`, so the UTF-8 bytes are assembled by hand.
emit_cp() {
    local v=$1 b1 b2 b3 b4
    if [ "$v" -lt 32 ] || [ "$v" -eq 127 ]; then
        printf ' '
    elif [ "$v" -lt 128 ]; then
        printf '%b' "\\x$(printf '%02x' "$v")"
    elif [ "$v" -lt 2048 ]; then
        b1=$(( 192 | (v >> 6) )); b2=$(( 128 | (v & 63) ))
        printf '%b' "\\x$(printf '%02x' "$b1")\\x$(printf '%02x' "$b2")"
    elif [ "$v" -lt 65536 ]; then
        b1=$((224 | (v >> 12))); b2=$((128 | ((v >> 6) & 63))); b3=$((128 | (v & 63)))
        printf '%b' "\\x$(printf '%02x' "$b1")\\x$(printf '%02x' "$b2")\\x$(printf '%02x' "$b3")"
    else
        b1=$((240 | (v >> 18))); b2=$((128 | ((v >> 12) & 63)))
        b3=$((128 | ((v >> 6) & 63))); b4=$((128 | (v & 63)))
        printf '%b' "\\x$(printf '%02x' "$b1")\\x$(printf '%02x' "$b2")\\x$(printf '%02x' "$b3")\\x$(printf '%02x' "$b4")"
    fi
}

normalize_command_text() {
    local line s i j n ch esc ap c2 out in_dq="" in_sq="" node=1
    while IFS= read -r line; do
        s="${line%$'\r'}"
        i=0; n=${#s}; out=""; node=1
        # in_dq/in_sq deliberately persist across lines: a quoted scalar may
        # span them (`name: "start` … `end"`), and the lines between are data.
        while [ "$i" -lt "$n" ]; do
            ch="${s:i:1}"
            if [ -n "$in_dq" ]; then
                case "$ch" in
                    '"') in_dq=""; node=0; i=$((i + 1)); continue ;;
                    '\')
                        if [ "$((i + 1))" -ge "$n" ]; then
                            out="${out}${DQ_BAD}"; i=$((i + 1)); continue
                        fi
                        esc="${s:i+1:1}"
                        case "$esc" in
                            x) ap="${s:i+2:2}"
                               if [[ "$ap" =~ ^[0-9A-Fa-f][0-9A-Fa-f]$ ]]; then
                                   out="${out}$(emit_cp $((16#$ap)))"; i=$((i + 4))
                               else out="${out}${DQ_BAD}"; i=$((i + 2)); fi ;;
                            u) ap="${s:i+2:4}"
                               if [[ "$ap" =~ ^[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]$ ]]; then
                                   out="${out}$(emit_cp $((16#$ap)))"; i=$((i + 6))
                               else out="${out}${DQ_BAD}"; i=$((i + 2)); fi ;;
                            U) ap="${s:i+2:8}"
                               if [[ "$ap" =~ ^[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]$ ]]; then
                                   out="${out}$(emit_cp $((16#$ap)))"; i=$((i + 10))
                               else out="${out}${DQ_BAD}"; i=$((i + 2)); fi ;;
                            '"') out="${out}\""; i=$((i + 2)) ;;
                            '\') out="${out}\\"; i=$((i + 2)) ;;
                            '/') out="${out}/"; i=$((i + 2)) ;;
                            ' ') out="${out} "; i=$((i + 2)) ;;
                            n|r|t|v|f|N|_|L|P) out="${out} "; i=$((i + 2)) ;;
                            0|a|b|e) out="${out} "; i=$((i + 2)) ;;
                            *) out="${out}${DQ_BAD}"; i=$((i + 2)) ;;
                        esac
                        continue ;;
                    *) out="${out}${ch}"; i=$((i + 1)); continue ;;
                esac
            fi
            if [ -n "$in_sq" ]; then
                if [ "$ch" = "'" ]; then
                    if [ "${s:i+1:1}" = "'" ]; then
                        out="${out}'"; i=$((i + 2)); continue
                    fi
                    in_sq=""; node=0; i=$((i + 1)); continue
                fi
                out="${out}${ch}"; i=$((i + 1)); continue
            fi
            # Node position: at the start of a line, after a structural
            # character, or after a tag/anchor token (which annotate the value
            # that follows rather than being it).
            case "$ch" in
                :|-|,|\[|\{|\?|\||\>) node=1; out="${out}${ch}"; i=$((i + 1)); continue ;;
                '!'|'&')
                    if [ "$node" -eq 1 ]; then
                        j=$i
                        while [ "$j" -lt "$n" ]; do
                            c2="${s:j:1}"
                            case "$c2" in [[:space:]]) break ;; esac
                            j=$((j + 1))
                        done
                        out="${out}${s:i:j-i}"; i=$j; continue
                    fi ;;
            esac
            if [ "$ch" = '"' ] || [ "$ch" = "'" ]; then
                if [ "$node" -eq 1 ]; then
                    if [ "$ch" = '"' ]; then in_dq=1; else in_sq=1; fi
                    i=$((i + 1)); continue
                fi
                # A quote inside a plain scalar is literal text; it delimits
                # nothing, and its bytes are not escapes. Drop it exactly as the
                # old stripper did, without decoding anything.
                i=$((i + 1)); continue
            fi
            out="${out}${ch}"
            case "$ch" in [[:space:]]) : ;; *) node=0 ;; esac
            i=$((i + 1))
        done
        printf '%s\n' "$out"
    done | tr -s ' \t' ' '
}

# Cycle-9 adversarial pass (the fix for the whole class). The flow
# `permissions:` reader used to spell out each writable shape it knew
# (`contents: write`, `key: write`, `write-all`) and treat every other pair in
# braces as read-only. A YAML tag (`!!str write`), an anchor (`&a write`) or a
# quote between the colon and the `write` made the spelling unrecognisable, and
# the fallback then declared the mapping read-only — a real write grant the
# sweep reported clean. The same fallback accepted any `key: something` pair, so
# an unreadable scope value read as read-only too.
#
# The fix is not another spelling. A flow mapping is taken apart into its
# members, each member's key and value is normalised once (a tag, an anchor and
# a quote are presentation, and YAML allows space before the colon), and every
# scope must then be one this sweep can prove read-only. A member it cannot
# classify — an alias, a merge key, a nested mapping or sequence, a value
# outside the read/write/none vocabulary, an empty value — makes the whole
# mapping unreadable and the caller refuses it. That closes the class instead of
# chasing the spellings.

# Sets BALANCED to the first balanced `{...}` flow mapping in $1, skipping any
# tag/anchor tokens in front of it. Returns 1 when there is no opening brace, a
# `[` opens first, or the mapping never closes.
take_balanced_flow() {
    BALANCED=""
    local s="$1" i=0 j n ch depth=0 in_quote=""
    n=${#s}
    while [ "$i" -lt "$n" ]; do
        ch="${s:i:1}"
        case "$ch" in
            "{" ) break ;;
            "[" ) return 1 ;;
            * ) i=$((i + 1)) ;;
        esac
    done
    [ "$i" -lt "$n" ] || return 1
    j=$i
    while [ "$j" -lt "$n" ]; do
        ch="${s:j:1}"
        if [ -n "$in_quote" ]; then
            if [ "$ch" = "$in_quote" ]; then in_quote=""; fi
            j=$((j + 1))
            continue
        fi
        case "$ch" in
            '"'|"'") in_quote="$ch" ;;
            '{'|'[') depth=$((depth + 1)) ;;
            '}'|']')
                depth=$((depth - 1))
                if [ "$depth" -eq 0 ] && [ "$ch" = "}" ]; then
                    BALANCED="${s:i:$((j - i + 1))}"
                    return 0
                fi
                ;;
        esac
        j=$((j + 1))
    done
    return 1
}

# Echoes one YAML scalar with its presentation removed: tags (`!!str`,
# `!<tag:...>`), anchors (`&a`), quotes, doubled whitespace and the space before
# a colon. Sets FLOW_UNREADABLE=1 for a construct that cannot be resolved by
# stripping presentation — an alias (`*a`) or a merge key (`<<`).
normalize_flow_value() {
    FLOW_UNREADABLE=0
    local s="$1" out="" ch i
    s="${s//\"/}"
    s="${s//\'/}"
    i=0
    while [ "$i" -lt "${#s}" ]; do
        ch="${s:i:1}"
        case "$ch" in
            '*') FLOW_UNREADABLE=1; out+="$ch"; i=$((i + 1)) ;;
            '<')
                if [ "${s:$((i + 1)):1}" = "<" ]; then FLOW_UNREADABLE=1; fi
                out+="$ch"; i=$((i + 1))
                ;;
            '!')
                i=$((i + 1))
                if [ "${s:i:1}" = "<" ]; then
                    while [ "$i" -lt "${#s}" ] && [ "${s:i:1}" != ">" ]; do i=$((i + 1)); done
                    i=$((i + 1))
                else
                    while [ "$i" -lt "${#s}" ]; do
                        ch="${s:i:1}"
                        case "$ch" in
                            [A-Za-z0-9_:-]) i=$((i + 1)) ;;
                            *) break ;;
                        esac
                    done
                fi
                ;;
            '&')
                i=$((i + 1))
                while [ "$i" -lt "${#s}" ]; do
                    ch="${s:i:1}"
                    case "$ch" in
                        [A-Za-z0-9_-]) i=$((i + 1)) ;;
                        *) break ;;
                    esac
                done
                ;;
            *) out+="$ch"; i=$((i + 1)) ;;
        esac
    done
    out="$(printf '%s' "$out" | tr -s ' \t' ' ')"
    while [[ "$out" == *" :"* ]]; do
        out="${out// :/:}"
    done
    out="${out#"${out%%[![:space:]]*}"}"
    FLOW_NORMALIZED="$out"
}

# Decide one flow `permissions:` value. Prints one of
# contents-write | write-all | writable-scope | unrecognized | read-only.
# `read-only` means the caller records `saw_readonly`; every other word is a
# verdict the caller reports (or refuses, for `unrecognized`). A member this
# reader cannot classify is `unrecognized`, never `read-only`.
decide_flow_permissions() {
    local value="$1" m k v
    if ! take_balanced_flow "$value"; then
        printf 'unrecognized\n'
        return 0
    fi
    if ! _flow_members "$BALANCED"; then
        printf 'unrecognized\n'
        return 0
    fi
    if [ "${#FLOW_MEMBERS[@]}" -eq 0 ]; then
        # `permissions: {}` and nothing else: a mapping with no scopes grants
        # nothing, so it is the one flow value that is provably read-only.
        printf 'read-only\n'
        return 0
    fi
    for m in "${FLOW_MEMBERS[@]}"; do
        if ! _flow_key_value "$m"; then
            printf 'unrecognized\n'
            return 0
        fi
        k="$FLOW_KEY"
        if [ -z "$k" ]; then
            printf 'unrecognized\n'
            return 0
        fi
        normalize_flow_value "$FLOW_VALUE"
        v="$FLOW_NORMALIZED"
        if [ "$FLOW_UNREADABLE" -eq 1 ]; then
            printf 'unrecognized\n'
            return 0
        fi
        case "$v" in
            "write")
                case "$k" in
                    "contents") printf 'contents-write\n'; return 0 ;;
                    *) printf 'writable-scope\n'; return 0 ;;
                esac
                ;;
            "write-all") printf 'write-all\n'; return 0 ;;
            "read"|"read-all"|"none") ;;
            *)
                # An unrecognised scope value, a nested mapping/sequence, or an
                # empty value: a construct this sweep cannot prove read-only is
                # not a pass.
                printf 'unrecognized\n'
                return 0
                ;;
        esac
    done
    printf 'read-only\n'
    return 0
}

# Cycle-9 adversarial pass (over-refusal): the VALUE of a scalar key is data,
# not workflow structure. A `permissions:`-shaped token inside `run:`, `with:`,
# `if:`, `env:`, `name:`, `shell:` or `working-directory:` is not the token, and
# a `uses:`-shaped token there is not a callee; three honest workflows were
# refused because a line reader saw text inside such a value. This filter runs
# only on the text handed to the permissions and callee readers: it drops the
# inline value of those keys and, when the value is a block (nothing after the
# colon, or a `|`/`>` indicator), its deeper-indented body too. The publisher
# vocabulary still sees the raw body — `gh release` inside `run: |` really is a
# publisher — so this must never be applied to `clean`.
#
# Cycle-10 adversarial pass (job ids): a JOB ID may be spelled exactly like one
# of those keys — `env:`, `run:`, `with:`, `if:`, `name:`, `shell:` and
# `working-directory:` are all legal job ids. A job id is recognised by its
# POSITION, never by its spelling: a non-blank line at the job-id indent inside
# the workflow `jobs:` block is a job declaration and is never dropped. The
# exemption is scoped to that block, so a `run:` under `defaults:`/`on:` or a
# workflow-level `env:` keeps the KEY-POSITION rule above. Cycle 11 hardens the
# block locator: a line inside a top-level block scalar (`name: |`, `run-name:
# |`, `defaults: …`) is data, never a `jobs:` key, so a decoy `jobs:`-shaped line
# in a `|` body cannot steal the scan; a quoted top-level key (`"jobs":`) reads
# the same as the bare key; and anything the locator cannot resolve
# unambiguously — an escaped key spelling, two candidates, or a candidate whose
# block holds no job declaration — is REFUSED (a `permissions:` token the reader
# cannot classify), never read as a job-less file. Only a trimmed `jobs:` value
# beginning with `{` is the flow form; an empty, comment, anchor or alias value
# is the block form.
_strip_flow_close_line() {
    local start="$1" n i ch depth=0 seen=0 inq=""
    for (( n=start; n<${#SS[@]}; n++ )); do
        local s="${SS[n]}"
        for (( i=0; i<${#s}; i++ )); do
            ch="${s:i:1}"
            if [ -n "$inq" ]; then
                # Cycle-11: a backslash escapes the next character inside a
                # double-quoted scalar, so `\"` does not close the quote. Without
                # this the scanner closed the quote at the escaped `"`, read the
                # `}}` that followed as flow depth 0, and stopped protecting the
                # mapping — its real job line was then stripped before either
                # reader saw it.
                if [ "$inq" = '"' ] && [ "$ch" = '\' ]; then
                    i=$((i + 1))
                    continue
                fi
                [ "$ch" = "$inq" ] && inq=""
                continue
            fi
            case "$ch" in
                '"'|"'") inq="$ch" ;;
                '{'|'[') depth=$((depth + 1)); seen=1 ;;
                '}'|']')
                    depth=$((depth - 1))
                    if [ "$seen" -eq 1 ] && [ "$depth" -le 0 ]; then
                        printf '%s\n' "$n"
                        return 0
                    fi
                    ;;
            esac
        done
    done
    printf '%s\n' "$(( ${#SS[@]} - 1 ))"
}
# Cycle-11: locate the workflow `jobs:` key from the SS array (dynamic scope).
#
# The cycle-10 locator took the first line matching `^[[:space:]]*jobs[[:space:]]*:`
# anywhere. A top-level block scalar (`name: |`, `run-name: |`, `defaults: … |`)
# whose BODY holds a `jobs:`-shaped line won the scan; its block then ended at
# the next column-0 line, so `jobid_indent` stayed -1, the job declaration was
# stripped with its body, and a hidden grant or callee read as absent. A quoted
# top-level key (`"jobs":`) was not matched at all, to the same effect.
#
# A key is a mapping key, so a line inside a block scalar body is not one: a
# value of `|`/`>` (with optional chomping/indent indicators) opens a body that
# runs to the first non-blank line whose indent is not deeper than the key's.
# A column-0 candidate is accepted only when its block actually holds
# job-declaration lines. Anything ambiguous — a key spelling this reader cannot
# resolve, two candidates, a candidate whose block has no jobs — sets
# JOBS_UNREADABLE, and the caller refuses rather than reading the file as
# job-less.
#
# Sets: JOBS_I, JOBS_INDENT, JOBS_TAIL, JOBS_FLOW_END, JOBS_BLOCK_END,
#       JOBS_JOBID_INDENT, JOBS_UNREADABLE.
_jobs_key_kind() {
    local k="$1" q="" again=1
    k="${k#"${k%%[![:space:]]*}"}"
    k="${k%"${k##*[![:space:]]}"}"
    # Cycle-12: a node's tag (`!!tag`, `!tag`, `!<uri>`) and its anchor
    # (`&name`) are PRESENTATION, not the key name, and YAML allows them in
    # either order before the key. Without this the real `&j jobs:` key read as
    # an unknown key, so it was not a candidate: the locator settled on a decoy
    # and the scalar-key rule deleted the real job ids with their bodies.
    while [ "$again" -eq 1 ]; do
        again=0
        case "$k" in
            "&"*)
                k="${k#&}"
                k="${k#*[[:space:]]}"
                again=1
                ;;
            "!"*)
                case "$k" in
                    "!<"*) k="${k#!<}"; k="${k#*>}" ;;
                    *) k="${k#!}"; k="${k#!}"; k="${k#*[[:space:]]}" ;;
                esac
                again=1
                ;;
        esac
        k="${k#"${k%%[![:space:]]*}"}"
        k="${k%"${k##*[![:space:]]}"}"
    done
    case "$k" in
        \"*\") q='"'; k="${k#\"}"; k="${k%\"}" ;;
        \'*\') q="'"; k="${k#\'}"; k="${k%\'}" ;;
    esac
    if [ "$k" = "jobs" ]; then
        printf '0\n'
        return 0
    fi
    if [ -n "$q" ] && [[ "$k" == *\\* ]]; then
        printf '2\n'
        return 0
    fi
    printf '1\n'
}
# Cycle-12: which quoted scalar, if any, is still open at the end of one line?
#
# A `jobs:`-shaped line can sit at column 0 INSIDE a double- or single-quoted
# scalar (`name: "start` / `jobs:` / `end"`), where YAML lets the continuation
# sit at indent 0, and the line is text, not a key. Finding the real key needs
# the cross-line quote state. A quote opens a scalar only in NODE POSITION —
# after `:`/`-`/`?`/`[`/`{`/`,` or at the start of the scalar — so an apostrophe
# inside a plain scalar (`name: Bob's job`) is not a quote and must not put the
# scanner into a state that skips every later line. Inside `"…"` a backslash
# escapes the next character; inside `'…'` a doubled `''` is an escaped quote.
#
# Round 20: `?` is the YAML explicit-key indicator and it begins a key node
# exactly as `-` begins a block entry, so a quote that follows it opens the
# scalar. Referee H's H-1 payloads (`? "a` in block position, `{? "a}` in flow
# position, each continued on a column-0 line) took the default arm here, the
# quote never opened, the continuation ended the `jobs:` block and the second
# job's `permissions: contents: write` was stripped as scalar data. The `?`
# reaches this rule only in key or flow position -- the property-token scan
# breaks at whitespace/flow/quote, and a plain scalar's interior `?` takes the
# default arm -- so the rule is "the last significant character is a node
# position indicator", not a list of payload spellings. Where the position is
# undecidable the scanner errs toward opening the quote: an over-tracked quote
# keeps the block open and makes the sweep refuse (fail closed), while an
# untracked quote is the false ok.
#
# Round 19: a node PROPERTY is node position too. `name: !!str "a` begins a
# quoted scalar after a tag; `&anc "a` and `! "a` do the same, and a tagged KEY
# (`run: !!str "a`) has the same token shape. Before this the character before
# the opening quote was the last character of the property token (`r`), which is
# not one of the boundary characters, so the quote never opened, the column-0
# continuation `b"` was read as the end of the `jobs:` block, and a later job's
# `permissions: contents: write` was stripped as data — a false ok (referee F
# F-1). A tag (`!`, `!!`, `!<uri>`), anchor (`&name`) or alias (`*name`) token
# now records that a node property just ended and the next quote — with only
# spaces between — opens the scalar. The property token is any spelling the YAML
# reader accepts: a tag suffix and a verbatim `!<uri>` may carry `:` and `?`
# (`!foo:bar`, `!<tag:yaml.org,2002:str>`), so the token runs to whitespace, a
# flow delimiter or a quote and never stops at a colon (round-19 follow-up: a
# URI tag made the sweep a false ok again). No list of tag spellings is kept.
# The mark is cleared by the next real
# character, so `name: Bob's job` still has no quote; it is never set by a
# `&`/`!`/`*` that the YAML reader would take as part of a plain scalar.
#
# Sets QS_OUT to the still-open quote character, or the empty string. Pass the
# caller's carried state as $2: a line that continues a multi-line quoted scalar
# must not be re-scanned from scratch (its opener is on an earlier line, so a
# fresh scan would see no quote and drop the state).
# Cycle-6 (round 21): ONE node-position rule for both scanners.
#
# Rounds 18-20 tried to decide "may a quote open here?" from the previous
# CHARACTER. That is not enough: `name: a?"b` is the plain scalar `a?"b` to
# PyYAML -- the `?` is scalar content and the `"` cannot open a scalar -- but a
# previous-character test saw `?` and opened a quote. The quote state then
# desynced, a column-0 continuation ended the `jobs:` block, and a job's
# `contents: write` was stripped as scalar data (referee I's regression class).
#
# The rule is node position, computed from INDICATOR BOUNDEDNESS, the way a YAML
# reader does it:
#   * at line start, or after whitespace/a separator/a value indicator, the
#     reader is at a node position (`ps=0`);
#   * an indicator (`-`, `?`, `:`, `,`) only ENDS the current node when it is
#     itself bounded -- followed by whitespace, end of line, or a flow
#     delimiter; an unbounded one is plain-scalar content;
#   * inside a plain scalar (`ps=1`) every quote is content; only a bounded `:`
#     (or a flow `,`) returns to a node position;
#   * a node property (`&name`, `*name`, `!`, `!!str`, `!<uri>`) is consumed as
#     one token at a node position and leaves the reader AT a node position, so
#     `&a "x` and `!!str "a` still open (F-1);
#   * `?` is node position only when bounded (`? "a`, `{? "a}`), never inside a
#     scalar (`a?"b`).
# The same function serves both scanners, so they cannot disagree about what is
# data and what is structure.
_qs_line_open_quote() {
    _line_node_state "$1" "${2:-}" "${3:-0}" "${4:-0}" "${5:--1}"
    QS_OUT="$LCS_QUOTE"
    QS_DEPTH="$LCS_DEPTH"
    QS_PS="$LCS_PS"
    QS_IND="$LCS_IND"
}

# Cycle-9 addendum (defeat 4): a plain YAML file holds exactly one document. A
# second document is a second, independent workflow whose `jobs:` and top-level
# `permissions:` can clear the first one's fail-closed sentinel — the referee's
# second doc ends with `permissions: read-all` / `jobs: {}`, so the locator found
# a read-only top-level token and an empty jobs block while doc0's flow job
# really granted `id-token: write`. Nothing here can bound a construct to the
# document it belongs to, so more than one document is refused outright.
# Document markers are only markers at column 0 and outside a multi-line quoted
# scalar (the same context `_locate_jobs_key` tracks).
has_multiple_documents() {
    local line in_q="" flow=0 seen=0 pps=0 pind=-1
    while IFS= read -r line; do
        line="${line%$'\r'}"
        if [ -z "$in_q" ]; then
            if [[ "$line" =~ ^---([[:space:]]|$) ]]; then
                [ "$seen" -eq 1 ] && return 0
                seen=1
                continue
            fi
            if [[ "$line" =~ ^\.\.\.([[:space:]]|$) ]]; then
                [ "$seen" -eq 1 ] && return 0
                continue
            fi
            case "$line" in
                ""|"#"*) ;;
                *) seen=1 ;;
            esac
        fi
        _qs_line_open_quote "$line" "$in_q" "$flow" "$pps" "$pind"
        in_q="$QS_OUT"
        flow="$QS_DEPTH"
        pps="$QS_PS"
        pind="$QS_IND"
    done
    return 1
}

# Cycle-9 (round 9): a `jobs:`-shaped line at column 0 INSIDE a multi-line
# quoted scalar is data, not the jobs key. The locator now skips it, but the
# file then has two competing readings — which line is the key depends on
# whether the quoted scalar is really a scalar, and a lexical reader cannot
# decide that in general. Rather than trust a locator that cannot tell data from
# structure, mark the file ambiguous; `report` then refuses whatever construct
# trips it as unclassifiable. This is deliberately narrow: it fires only when a
# decoy `jobs:` line sits inside a quoted scalar AND either the real key is the
# bare `jobs` (no presentation to tell the two apart) or the decoy carries no
# body (so even the decoy's shape is uninformative). It is called with a
# here-string so it runs in the CURRENT shell and can set AMBIG_DECOY.
_ambiguously_placed_jobs_key() {
    AMBIG_DECOY=0
    local line in_q="" flow=0 keytext saw_decoy=0 decoy_body=0 real_plain=0 pps=0 pind=-1
    while IFS= read -r line; do
        line="${line%$'\r'}"
        if [ -n "$in_q" ]; then
            if [ "$saw_decoy" -eq 0 ]; then
                [[ "$line" =~ ^jobs[[:space:]]*: ]] && saw_decoy=1
            elif [ "$decoy_body" -eq 0 ]; then
                [[ "$line" =~ ^[[:space:]]+[^[:space:]] ]] && decoy_body=1
            fi
            _qs_line_open_quote "$line" "$in_q" "$flow" "$pps" "$pind"
            in_q="$QS_OUT"
            flow="$QS_DEPTH"
            pps="$QS_PS"
            pind="$QS_IND"
            continue
        fi
        if [ "$saw_decoy" -eq 1 ] && [ "$real_plain" -eq 0 ]; then
            case "$line" in
                jobs*)
                    keytext="${line%%:*}"
                    keytext="${keytext%"${keytext##*[![:space:]]}"}"
                    [ "$keytext" = "jobs" ] && real_plain=1
                    ;;
            esac
        fi
        _qs_line_open_quote "$line" "$in_q" "$flow" "$pps" "$pind"
        in_q="$QS_OUT"
        flow="$QS_DEPTH"
        pps="$QS_PS"
        pind="$QS_IND"
    done
    if [ "$saw_decoy" -eq 1 ] \
        && { [ "$real_plain" -eq 1 ] || [ "$decoy_body" -eq 0 ]; }; then
        AMBIG_DECOY=1
        return 0
    fi
    return 1
}

# Referee E (round 16): a line that continues a quoted scalar, a block scalar
# body, or an open flow collection is DATA, not structure. `_locate_jobs_key`
# already skipped quoted scalars and block scalars while hunting for the
# `jobs:` key, but it then measured the block with raw indentation, so a
# continuation at a low indent lowered the job-id column and the real job line
# at the true column fell out of the job-declaration protection — its whole
# body, including a real `permissions:` write, was stripped as if it were data.
# This scanner reports the carried quote state (LCS_QUOTE) and flow
# (LCS_DEPTH) after one line. `$2` is the quote char carried in, `$3` the flow
# depth carried in. It follows the same node-position rule for opening a quote
# as `_qs_line_open_quote`, including the round-19 node-property rule: any node
# property a YAML reader accepts — a tag (`!`, `!!str`, `!foo:bar`,
# `!<tag:yaml.org,2002:str>`), an anchor (`&name`), an alias (`*name`), or a
# combination such as `&a !!str` — immediately before the opening quote still
# opens it (F-1), and the round-20 rule that the explicit-key indicator `?` is
# node position too (`{? "a}`, H-1 flow form).
_line_node_state() {
    local s="$1" i=0 n ch q="${2:-}" ps=0 ws=1 sep=0 ind=-1
    local pps="${4:-0}" pind="${5:--1}" TAB=$'\t'
    # `base` is the indentation of the ENCLOSING BLOCK COLLECTION -- the column
    # pyyaml's `scan_plain` measures a continuation line against. `scan_plain`
    # computes `indent = self.indent + 1`, and `self.indent` is the block
    # mapping/sequence indent last established by a real `key:`/`- ` line; it
    # does NOT advance on a continuation line. A line indented past it continues
    # the plain scalar, so a quote there is data. Carrying the node line's base
    # unchanged across the whole run is what makes the SECOND and later
    # same-indent continuation lines behave like the first; the round-21 defect
    # was comparing against the immediately previous line's indent, which a
    # same-indent continuation resets to itself. `base` is -1 at the document
    # root, where `self.indent` is -1 and `scan_plain` uses `indent = 0`, so a
    # column-0 line can still continue a root-level plain scalar.
    local base="$pind" carried=0
    n=${#s}
    LCS_DEPTH="${3:-0}"
    while [ "$i" -lt "$n" ]; do
        ch="${s:i:1}"
        case "$ch" in ' '|"$TAB") i=$((i + 1)); continue ;; esac
        break
    done
    if [ "$i" -ge "$n" ]; then
        # A blank or whitespace-only line cannot open or close a scalar, so it
        # neither ends nor advances a plain scalar.
        LCS_QUOTE="$q"
        LCS_PS=0
        [ -n "$q" ] || LCS_PS="$pps"
        LCS_IND="$base"
        return 0
    fi
    ind="$i"
    # A comment-only line is where `scan_plain` stops: `scan_plain_spaces`
    # returns, and the caller's `self.peek() == '#'` test breaks the loop, so
    # the plain scalar ends here and the comment cannot open a node. It is not a
    # block entry, so it leaves the enclosing-collection indent alone. A `#`
    # after a token is a trailing comment, handled by the `ws` test below.)
    if [ -z "$q" ] && [ "${s:i:1}" = '#' ]; then
        LCS_QUOTE="$q"
        LCS_PS=0
        LCS_IND="$base"
        return 0
    fi
    # A plain scalar continues onto a following line whose column is past the
    # ENCLOSING COLLECTION's indent (pyyaml's `scan_plain`: `indent =
    # self.indent+1`, and the scalar ends only when `self.column < indent`), and
    # a quote on such a line is data, not an opener. Carrying `pps`/`base` across
    # the whole run is what makes every same-indent continuation line behave
    # like the first. A line at or below the enclosing indent starts a new node.
    if [ -z "$q" ] && [ "$pps" -eq 1 ] && [ "$ind" -gt "$base" ]; then
        ps=1
        carried=1
    fi
    while [ "$i" -lt "$n" ]; do
        ch="${s:i:1}"
        # Inside a quoted scalar: only the closing quote (respecting escapes and
        # the single-quote doubling rule) changes the state. Everything else,
        # quotes included, is data.
        if [ -n "$q" ]; then
            if [ "$q" = '"' ] && [ "$ch" = '\' ]; then i=$((i + 2)); ws=0; continue; fi
            if [ "$q" = "'" ] && [ "$ch" = "'" ] && [ "${s:i+1:1}" = "'" ]; then i=$((i + 2)); ws=0; continue; fi
            if [ "$ch" = "$q" ]; then q=""; ps=0; fi
            ws=0
            i=$((i + 1))
            continue
        fi
        case "$ch" in
            ' '|"$TAB") ws=1; i=$((i + 1)); continue ;;
        esac
        # `#` starts a comment only where a token may start: at line start or
        # after whitespace. `a#b` is one plain scalar, so the check is bounded.
        if [ "$ws" -eq 1 ] && [ "$ch" = '#' ]; then break; fi
        # Is the FOLLOWING character a break for a plain scalar? pyyaml's
        # `scan_plain` ends a scalar at whitespace/EOL, at a `:` followed by
        # whitespace/EOL, and -- in flow context only -- at `,?[]{}` and at a
        # `:` followed by `,[]{}`. `"` and `'` are NOT break characters: a quote
        # inside a plain scalar is data.
        sep=0
        if [ $((i + 1)) -ge "$n" ]; then sep=1
        else case "${s:i+1:1}" in ' '|"$TAB") sep=1 ;; esac
        fi
        case "$ch" in
            '"'|"'")
                if [ "$ps" -eq 0 ]; then q="$ch"; fi
                ws=0
                ;;
            '&'|'!'|'*')
                if [ "$ps" -eq 0 ]; then
                    # A node property is one token and leaves the reader at a
                    # node position. A tag suffix or verbatim URI may carry
                    # `:`/`?`/`,`, so the token ends only at whitespace, a flow
                    # delimiter or a quote.
                    i=$((i + 1))
                    if [ "$ch" = '!' ] && [ "${s:i:1}" = '<' ]; then
                        while [ "$i" -lt "$n" ]; do
                            ch="${s:i:1}"
                            i=$((i + 1))
                            if [ "$ch" = '>' ]; then break; fi
                        done
                    else
                        while [ "$i" -lt "$n" ]; do
                            ch="${s:i:1}"
                            case "$ch" in
                                ' '|"$TAB"|'['|']'|'{'|'}'|','|'"'|"'") break ;;
                            esac
                            i=$((i + 1))
                        done
                    fi
                    ws=0
                    continue
                fi
                ps=1; ws=0
                ;;
            '{'|'[')
                if [ "$ps" -eq 0 ] || [ "$LCS_DEPTH" -gt 0 ]; then
                    LCS_DEPTH=$((LCS_DEPTH + 1))
                    ps=0
                else
                    # Block-context `[`/`{` inside a plain scalar is content
                    # (`a["c` is the plain scalar `a["c`).
                    ps=1
                fi
                ws=0
                ;;
            '}'|']')
                if [ "$LCS_DEPTH" -gt 0 ]; then
                    LCS_DEPTH=$((LCS_DEPTH - 1))
                    ps=0
                else
                    ps=1
                fi
                ws=0
                ;;
            ',')
                # A flow separator ends a plain scalar and returns to a node
                # position; in block context a comma is plain content.
                if [ "$LCS_DEPTH" -gt 0 ]; then ps=0; else ps=1; fi
                ws=0
                ;;
            ':')
                if [ "$ps" -eq 0 ]; then
                    if [ "$LCS_DEPTH" -gt 0 ]; then
                        ps=0
                    elif [ "$sep" -eq 1 ]; then
                        ps=0
                    else
                        ps=1
                    fi
                elif [ "$sep" -eq 1 ]; then
                    ps=0
                elif [ "$LCS_DEPTH" -gt 0 ]; then
                    case "${s:i+1:1}" in
                        ','|'['|']'|'{'|'}') ps=0 ;;
                        *) ps=1 ;;
                    esac
                else
                    ps=1
                fi
                ws=0
                ;;
            '-')
                # A block sequence entry only at a node position, bounded by
                # whitespace/EOL. Inside a plain scalar it is content
                # (`a - "b` is one plain scalar); in flow there is no entry
                # indicator.
                if [ "$ps" -eq 0 ] && [ "$LCS_DEPTH" -eq 0 ] && [ "$sep" -eq 1 ]; then
                    ps=0
                else
                    ps=1
                fi
                ws=0
                ;;
            '?')
                # An explicit-key indicator at a node position in flow, or in
                # block when bounded by whitespace/EOL. Inside a block plain
                # scalar it is content (`a?"b` is the plain scalar `a?"b`).
                if [ "$LCS_DEPTH" -gt 0 ]; then
                    ps=0
                elif [ "$ps" -eq 0 ] && [ "$sep" -eq 1 ]; then
                    ps=0
                else
                    ps=1
                fi
                ws=0
                ;;
            *)
                ps=1; ws=0
                ;;
        esac
        # A real block-collection entry -- a `:` bounded by whitespace/EOL in
        # block context, or a `- ` entry indicator -- establishes the indent a
        # later plain scalar is measured against, exactly as pyyaml's
        # `add_indent(self.column)` does when it tokenizes that entry. A plain
        # scalar CARRIED in from an earlier line (`carried`) is a continuation
        # of that earlier node even when the line holds a `:`; it must not raise
        # the base, because a raised base would let the next continuation fall
        # below it and be misread as a new node (under-tracking -> a quote opens
        # where there is none -> false ok). Leaving the base alone there keeps
        # the carry open, which fails closed.
        if [ "$LCS_DEPTH" -eq 0 ] && [ "$sep" -eq 1 ] && [ "$ps" -eq 0 ] \
            && [ "$carried" -eq 0 ]; then
            case "$ch" in
                ':'|'-'|'?') base="$ind" ;;
            esac
        fi
        i=$((i + 1))
    done
    LCS_QUOTE="$q"
    LCS_PS="$ps"
    LCS_IND="$base"
}

_locate_jobs_key() {
    JOBS_I=-1
    JOBS_INDENT=0
    JOBS_TAIL=""
    JOBS_FLOW_END=-1
    JOBS_BLOCK_END=${#SS[@]}
    JOBS_JOBID_INDENT=-1
    JOBS_UNREADABLE=0
    local n line ind kind keykey tail cand=0 start=0 in_bs=0 bs_indent=0 m l2 cline
    local pat_bs='^[[:space:]]*(-[[:space:]]+)?[^:]+:[[:space:]]*[|>][0-9+-]*[[:space:]]*$'
    local in_q="" flowq=0 pps=0 pind=-1
    for (( n=0; n<${#SS[@]}; n++ )); do
        line="${SS[n]}"
        [ -n "${line//[[:space:]]/}" ] || continue
        ind="${line%%[![:space:]]*}"
        if [ "$in_bs" -eq 1 ]; then
            [ "${#ind}" -gt "$bs_indent" ] && continue
            in_bs=0
        fi
        # Cycle-12: a line inside a multi-line quoted scalar is DATA, not a key.
        # Skip it whole and keep tracking the quote until it closes.
        if [ -n "$in_q" ]; then
            _qs_line_open_quote "$line" "$in_q" "$flowq" "$pps" "$pind"
            in_q="$QS_OUT"
            flowq="$QS_DEPTH"
            pps="$QS_PS"
            pind="$QS_IND"
            continue
        fi
        # A block scalar header opens a body; its lines are data, not keys.
        if [[ "$line" =~ $pat_bs ]]; then
            in_bs=1
            bs_indent=${#ind}
            continue
        fi
        # Does THIS line open a quoted scalar that continues past its end?
        _qs_line_open_quote "$line" "$in_q" "$flowq" "$pps" "$pind"
        in_q="$QS_OUT"
        flowq="$QS_DEPTH"
        pps="$QS_PS"
        pind="$QS_IND"
        [ "${#ind}" -eq 0 ] || continue
        start=$n
        tail=""
        if [[ "$line" =~ ^\?[[:space:]]+(.*)$ ]]; then
            kind="$(_jobs_key_kind "${BASH_REMATCH[1]}")"
            if [ "$kind" != 0 ]; then
                [ "$kind" = 2 ] && JOBS_UNREADABLE=1
                continue
            fi
            m=$((n + 1))
            while [ "$m" -lt "${#SS[@]}" ]; do
                l2="${SS[m]}"
                if [ -z "${l2//[[:space:]]/}" ]; then m=$((m + 1)); continue; fi
                if [[ "$l2" =~ ^[[:space:]]*:[[:space:]]*(.*)$ ]]; then
                    tail="${BASH_REMATCH[1]}"
                    start=$m
                    cand=$((cand + 1))
                fi
                break
            done
            continue
        fi
        # Cycle-12: a `!<uri>` tag carries colons of its own (`tag:yaml.org,…`),
        # so the first-colon split below would cut it in half and the key would
        # never be seen. Drop the URI tag from the line before splitting.
        cline="$line"
        case "$cline" in
            "!<"*) cline="${cline#!<}"; cline="${cline#*>}" ;;
        esac
        if [[ "$cline" =~ ^([^:]*):(.*)$ ]]; then
            keykey="${BASH_REMATCH[1]}"
            tail="${BASH_REMATCH[2]}"
        else
            continue
        fi
        kind="$(_jobs_key_kind "$keykey")"
        if [ "$kind" = 2 ]; then
            JOBS_UNREADABLE=1
            continue
        fi
        [ "$kind" = 0 ] || continue
        cand=$((cand + 1))
        JOBS_I=$start
        JOBS_TAIL="$tail"
        JOBS_INDENT=0
    done
    if [ "$cand" -ne 1 ]; then
        JOBS_UNREADABLE=1
        JOBS_I=-1
        return 0
    fi
    tail="${JOBS_TAIL#"${JOBS_TAIL%%[![:space:]]*}"}"
    if [ "${tail:0:1}" = "{" ]; then
        JOBS_FLOW_END=$(_strip_flow_close_line "$JOBS_I")
        return 0
    fi
    # The job-id column is the indentation of the FIRST structural child of the
    # block: in a valid block mapping every job key sits at that one column, and
    # the first child cannot be a continuation. The old minimum-over-all-lines
    # heuristic let any low-indent continuation move the column (referee E's 30
    # fixtures), and a continuation at column 0 also truncated the block so a
    # later job's body was stripped. Both the block-end and job-id scans now
    # skip continuation lines: a line inside a quoted scalar, a block scalar
    # body, or an open flow collection is DATA, not structure. A construct that
    # leaves no readable structural child fails closed.
    local flow=0 saw_child=0 pps=0 pind=-1
    in_q=""
    in_bs=0
    bs_indent=0
    for (( n=JOBS_I + 1; n<${#SS[@]}; n++ )); do
        l2="${SS[n]}"
        [ -n "${l2//[[:space:]]/}" ] || continue
        ind="${l2%%[![:space:]]*}"
        if [ "$in_bs" -eq 1 ]; then
            [ "${#ind}" -gt "$bs_indent" ] && continue
            in_bs=0
        fi
        if [ -n "$in_q" ]; then
            _line_node_state "$l2" "$in_q" "$flow" "$pps" "$pind"
            in_q="$LCS_QUOTE"
            flow="$LCS_DEPTH"
            pps="$LCS_PS"
            pind="$LCS_IND"
            continue
        fi
        if [ "$flow" -gt 0 ]; then
            _line_node_state "$l2" "" "$flow" "$pps" "$pind"
            in_q="$LCS_QUOTE"
            flow="$LCS_DEPTH"
            pps="$LCS_PS"
            pind="$LCS_IND"
            continue
        fi
        if [ "${#ind}" -le "$JOBS_INDENT" ]; then
            JOBS_BLOCK_END=$n
            break
        fi
        if [ "$saw_child" -eq 0 ]; then
            JOBS_JOBID_INDENT=${#ind}
            saw_child=1
        fi
        if [[ "$l2" =~ $pat_bs ]]; then
            in_bs=1
            bs_indent=${#ind}
            continue
        fi
        _line_node_state "$l2" "" 0 "$pps" "$pind"
        in_q="$LCS_QUOTE"
        flow="$LCS_DEPTH"
        pps="$LCS_PS"
        pind="$LCS_IND"
    done
    if [ "$saw_child" -eq 0 ] || [ "$JOBS_JOBID_INDENT" -lt 1 ]; then
        JOBS_UNREADABLE=1
        JOBS_I=-1
    fi
}

strip_scalar_bodies() {
    local -a SS=()
    local line key text trimmed base i j rest n tail
    local pat_scalar='^([[:space:]]*(-[[:space:]]+)?)([A-Za-z_][A-Za-z0-9_.-]*)[[:space:]]*:(.*)$'
    while IFS= read -r line; do
        SS+=("${line%$'\r'}")
    done
    # Compute the job-id position once from the real `jobs:` key. Anything the
    # locator cannot resolve fails closed: the readers are handed a
    # `permissions:` token they cannot classify, so the branch is refused rather
    # than read as job-less. (MT6 mutates the block-end bound below.)
    _locate_jobs_key
    if [ "$JOBS_UNREADABLE" -eq 1 ]; then
        printf '%s\n' 'permissions: *sweep-cannot-locate-the-jobs-key'
        for (( n=0; n<${#SS[@]}; n++ )); do
            printf '%s\n' "${SS[n]}"
        done
        return 0
    fi
    local jobs_i="$JOBS_I" jobs_indent="$JOBS_INDENT"
    local jobs_flow_end="$JOBS_FLOW_END" jobid_indent="$JOBS_JOBID_INDENT"
    local jobs_block_end="$JOBS_BLOCK_END"
    local protect_until=-1
    i=0
    while [ "$i" -lt "${#SS[@]}" ]; do
        line="${SS[i]}"
        # Flow `jobs:` mapping: nothing from the jobs line to its close is a
        # scalar-key value of the listed spellings.
        if [ "$jobs_flow_end" -ge 0 ] && [ "$i" -ge "$jobs_i" ] && [ "$i" -le "$jobs_flow_end" ]; then
            printf '%s\n' "$line"
            i=$((i + 1))
            continue
        fi
        if [ "$protect_until" -ge "$i" ]; then
            printf '%s\n' "$line"
            i=$((i + 1))
            continue
        fi
        # Job declaration: a non-blank line at the job-id indent inside the jobs
        # block. Print it; if its value opens a flow mapping, keep that flow
        # body out of the stripper too.
        if [ "$jobid_indent" -ge 0 ] && [ "$i" -gt "$jobs_i" ] && [ "$i" -lt "$jobs_block_end" ]; then
            text="${line%%[![:space:]]*}"
            if [ -n "${line//[[:space:]]/}" ] && [ "${#text}" -eq "$jobid_indent" ]; then
                rest="${line#*:}"
                trimmed="${rest#"${rest%%[![:space:]]*}"}"
                if [ "${trimmed:0:1}" = "{" ]; then
                    protect_until=$(_strip_flow_close_line "$i")
                fi
                printf '%s\n' "$line"
                i=$((i + 1))
                continue
            fi
        fi
        if [[ "$line" =~ $pat_scalar ]]; then
            key="${BASH_REMATCH[3]}"
            case "$key" in
                run|with|if|env|name|shell|working-directory) ;;
                *)
                    printf '%s\n' "$line"
                    i=$((i + 1))
                    continue
                    ;;
            esac
            base=${#BASH_REMATCH[1]}
            rest="${BASH_REMATCH[4]}"
            trimmed="${rest#"${rest%%[![:space:]]*}"}"
            # The key line is dropped along with its value/body: nothing under a
            # data key is code, and leaving a bare `env:`/`with:` behind would
            # let fold_block_scalars join it onto the previous line (a bare key
            # has no trailing space for the fold's structure test to see).
            if [ -n "$trimmed" ]; then
                case "$trimmed" in
                    "|"*|">"*) ;;
                    *) i=$((i + 1)); continue ;;
                esac
            fi
            j=$((i + 1))
            while [ "$j" -lt "${#SS[@]}" ]; do
                text="${SS[j]}"
                if [ -z "${text//[[:space:]]/}" ]; then j=$((j + 1)); continue; fi
                trimmed="${text%%[![:space:]]*}"
                [ "${#trimmed}" -gt "$base" ] || break
                j=$((j + 1))
            done
            i=$j
            continue
        fi
        printf '%s\n' "$line"
        i=$((i + 1))
    done
}

# CT-73: what the token may do, read from the parsed `permissions:` mapping.
#
# Resolves the spellings it can prove: `permissions: read-all` and
# `permissions: write-all` scalars, `permissions: {}`, a flow mapping
# `{contents: write}`, and a block mapping whose scopes may be spaced
# (`contents : write`), quoted (`contents: "write"`) or indented any depth
# (top level or per job). A duplicate `permissions:` key is not valid YAML and
# GitHub's last-wins parse of it is not something this gate will bet a release
# on, so a `contents: write` (or `write-all`) mapping wins over any other.
# A spelling it cannot resolve is NOT read-only — see the doctrine above.
#
# FAIL CLOSED (cycle-5 adversarial pass): a spelling this parser cannot read is
# not a read-only value. `permissions: *w`, a merge key `<<: *w` and a quoted
# key `"contents": write` are all real write grants to YAML and all three read
# as nothing here, so any unreadable construct returns `unrecognized` and the
# caller treats it as an offender. Adding one spelling per audit round is the
# arms race that lost cycle 5; refusing what cannot be read ends it. Cycle 9
# extends the same rule to a flow mapping MEMBER by MEMBER: the value of every
# scope has its tag/anchor/quote presentation removed and is then resolved
# exactly, and a member that does not resolve to a known verb makes the whole
# mapping `unrecognized` instead of the mapping being assumed read-only.
#
# Cycle-11: find a `permissions` KEY on one line, in flow KEY POSITION.
#
# The cycle-7 inline regex accepted a `"` (or `'`) as a left boundary anywhere
# on the line. On the exempted job-declaration line the word inside a quoted
# scalar VALUE (`env: {NOTE: "permissions: write"}`) then matched, its value
# looked like `write…`, and an honest read-only workflow was refused as
# `grants-write-all` — a regression the cycle-11 referee caught. `permissions`
# is a key only in key position: a quoted scalar in key position is a key
# (`"permissions"`), but a quoted scalar in value position is data. Braces,
# brackets, commas and colons move between the two positions; a quoted scalar is
# skipped whole, with a backslash escaping the next character inside `"…"` and a
# doubled `'` inside `'…'`.
#
# Sets FLOW_PERM_VALUE to the text after the key's colon. Returns 1 when the
# line holds no `permissions` key.
_flow_find_permissions() {
    local s="$1"
    local i=0 n=${#s} ch stack="k" q k2 j rest
    FLOW_PERM_VALUE=""
    while [ "$i" -lt "$n" ]; do
        ch="${s:i:1}"
        case "$ch" in
            ' '|'	') i=$((i + 1)) ;;
            '{'|'[') stack="k$stack"; i=$((i + 1)) ;;
            '}'|']') stack="${stack#?}"; [ -n "$stack" ] || stack="v"; i=$((i + 1)) ;;
            ',') stack="k${stack#?}"; [ -n "$stack" ] || stack="k"; i=$((i + 1)) ;;
            ':') stack="v${stack#?}"; [ -n "$stack" ] || stack="v"; i=$((i + 1)) ;;
            '"'|"'")
                q="$ch"
                if [ "${stack:0:1}" = "k" ]; then
                    k2=""
                    i=$((i + 1))
                    while [ "$i" -lt "$n" ]; do
                        ch="${s:i:1}"
                        if [ "$q" = '"' ] && [ "$ch" = '\' ]; then
                            k2+="${s:i+1:1}"
                            i=$((i + 2))
                            continue
                        fi
                        if [ "$ch" = "$q" ]; then
                            if [ "$q" = "'" ] && [ "${s:i+1:1}" = "'" ]; then
                                k2+="'"
                                i=$((i + 2))
                                continue
                            fi
                            break
                        fi
                        k2+="$ch"
                        i=$((i + 1))
                    done
                    i=$((i + 1))
                    if [ "$k2" = "permissions" ]; then
                        rest="${s:i}"
                        rest="${rest#"${rest%%[![:space:]]*}"}"
                        if [ "${rest:0:1}" = ":" ]; then
                            FLOW_PERM_VALUE="${rest:1}"
                            return 0
                        fi
                    fi
                    stack="v${stack#?}"
                    [ -n "$stack" ] || stack="v"
                else
                    i=$((i + 1))
                    while [ "$i" -lt "$n" ]; do
                        ch="${s:i:1}"
                        if [ "$q" = '"' ] && [ "$ch" = '\' ]; then
                            i=$((i + 2))
                            continue
                        fi
                        if [ "$ch" = "$q" ]; then
                            if [ "$q" = "'" ] && [ "${s:i+1:1}" = "'" ]; then
                                i=$((i + 2))
                                continue
                            fi
                            break
                        fi
                        i=$((i + 1))
                    done
                    i=$((i + 1))
                fi
                ;;
            *)
                if [ "${stack:0:1}" = "k" ]; then
                    # Key-position node properties (`&p permissions:`) are
                    # presentation, not the key name. Peel them so the flow
                    # reader agrees with the block reader.
                    local peel=1
                    while [ "$peel" -eq 1 ]; do
                        peel=0
                        case "${s:i:1}" in
                            '&')
                                i=$((i + 1))
                                while [ "$i" -lt "$n" ]; do
                                    case "${s:i:1}" in ' '|'	'|':'|','|'{'|'}'|'['|']') break ;; esac
                                    i=$((i + 1))
                                done
                                peel=1
                                ;;
                            '!')
                                if [ "${s:i+1:1}" = "<" ]; then
                                    i=$((i + 1))
                                    while [ "$i" -lt "$n" ] && [ "${s:i:1}" != ">" ]; do i=$((i + 1)); done
                                    [ "$i" -lt "$n" ] && i=$((i + 1))
                                else
                                    while [ "$i" -lt "$n" ]; do
                                        case "${s:i:1}" in ' '|'	'|':'|','|'{'|'}'|'['|']') break ;; esac
                                        i=$((i + 1))
                                    done
                                fi
                                peel=1
                                ;;
                        esac
                        while [ "$i" -lt "$n" ]; do
                            case "${s:i:1}" in ' '|'	') i=$((i + 1)) ;; *) break ;; esac
                        done
                    done
                    k2=""
                    while [ "$i" -lt "$n" ]; do
                        ch="${s:i:1}"
                        case "$ch" in
                            ' '|'	'|':'|','|'{'|'}'|'['|']') break ;;
                        esac
                        k2+="$ch"
                        i=$((i + 1))
                    done
                    if [ "$k2" = "permissions" ]; then
                        j=$i
                        while [ "$j" -lt "$n" ]; do
                            ch="${s:j:1}"
                            case "$ch" in ' '|'	') j=$((j + 1)) ;; *) break ;; esac
                        done
                        if [ "${s:j:1}" = ":" ]; then
                            FLOW_PERM_VALUE="${s:j+1}"
                            return 0
                        fi
                    fi
                    stack="v${stack#?}"
                    [ -n "$stack" ] || stack="v"
                else
                    i=$((i + 1))
                fi
                ;;
        esac
    done
    return 1
}

# A YAML key may carry node properties — an anchor (`&p`), a tag (`!!str`,
# `!tag`, `!<uri>`) or both in either order — before the key name. They are
# PRESENTATION, not part of the name: `&p permissions:` IS the `permissions`
# key, so a reader that only matches the bare spelling lets a write token hide
# behind an anchor. This peels them, in either order, at the START of a line
# (key position); an explicit `?` marker is moved to the front so the existing
# explicit-key reader still sees `? permissions` whatever sits between the two.
# Whatever is left that a reader still cannot resolve fails closed.
_strip_key_props() {
    local s="$1" ind q=""
    ind="${s%%[![:space:]]*}"
    s="${s#"$ind"}"
    case "$s" in
        '?'[[:space:]]*) q="? "; s="${s#\?}"; s="${s#"${s%%[![:space:]]*}"}" ;;
    esac
    local again=1
    while [ "$again" -eq 1 ]; do
        again=0
        case "$s" in
            '&'*) s="${s#&}"; s="${s#*[[:space:]]}"; again=1 ;;
            '!'*)
                case "$s" in
                    '!<'*) s="${s#!<}"; s="${s#*>}" ;;
                    *) s="${s#!}"; s="${s#!}"; s="${s#*[[:space:]]}" ;;
                esac
                again=1
                ;;
        esac
        s="${s#"${s%%[![:space:]]*}"}"
    done
    printf '%s%s%s\n' "$ind" "$q" "$s"
}

# stdout is one of: write-all | contents-write | writable-scope | unrecognized |
# read-only | partial | absent
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
        # Key-position node properties are presentation: peel them first so an
        # anchored or tagged `permissions` key is read as the key it is.
        line="$(_strip_key_props "$line")"
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
        # Round 16: an explicit key on its own line (`? 'permissions'`,
        # `? "permiss\u0069ons"`) has no colon to require and may carry an
        # escape, so the explicit-key test accepts the single-quoted literal and
        # an escaped quoted key.
        # Round 17: the test is now the `?` INDICATOR itself, not the key text.
        # YAML may split that key across lines with a quoted line continuation
        # (`? "permis\` / `      sions"`), which this line-at-a-time reader
        # cannot rejoin; no line then holds complete `permissions` text, the job
        # read as declaring nothing, and a real write token passed. Triggering on
        # the indicator makes an explicit key anywhere in the scanned region fail
        # closed whether or not its text resolves on its own line.
        local pat_escaped_key='(^[[:space:]]*(-[[:space:]]+)?|[{,][[:space:]]*)["][^"]*\\[uUxX][0-9A-Fa-f]+[^"]*["][[:space:]]*:'
        local pat_explicit_indicator='^[[:space:]]*\?([[:space:]]|$)'
        if [[ "$line" =~ $pat_escaped_key ]] || [[ "$line" =~ $pat_explicit_indicator ]]; then
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
                            # Cycle-8: ANY scope at `write` is a grant. This
                            # sweep cannot know which scope an action needs in
                            # order to publish. `packages: write` pushes a
                            # package and `id-token: write` mints an OIDC token
                            # for a trusted publish; both were read as read-only
                            # while GitHub honoured them. `contents: write` is
                            # reported under its own reason above.
                            case "$value" in
                                "write") printf 'writable-scope\n'; return 0 ;;
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
                *"{"*)
                    # Flow mapping, e.g. `{contents: write, issues: read}`.
                    # Cycle-9: take it apart member by member. A tag, an anchor
                    # or a quote in front of the `write` is presentation, and a
                    # member this sweep cannot classify (an alias, a merge key,
                    # a nested mapping, a value outside read/write/none) makes
                    # the whole mapping unreadable rather than read-only. A
                    # mapping the fold did not complete — `permissions: {issues:
                    # read,` with `contents: write}` on the next line — has no
                    # balanced `{}` and fails closed the same way.
                    local flow_verdict
                    flow_verdict="$(decide_flow_permissions "$value")"
                    case "$flow_verdict" in
                        read-only)
                            saw_readonly=1
                            if [ -z "$indent" ]; then top_level_readonly=1; fi
                            ;;
                        *)
                            printf '%s\n' "$flow_verdict"
                            return 0
                            ;;
                    esac
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
                # Cycle-11: `permissions` is a KEY only in key position. A
                # quoted scalar in VALUE position is data, so the note
                # `env: {NOTE: "permissions: write"}` on an exempted job line is
                # not a grant. The scanner still reads quoted keys and values
                # (`{"contents" : "write"}` remains a grant) and skips a quoted
                # scalar with escape handling; an unrelated key such as
                # `x-permissions` is still not the token.
                if _flow_find_permissions "$line"; then
                    value="$FLOW_PERM_VALUE"
                    value="${value#"${value%%[![:space:]]*}"}"
                    case "$value" in
                        "write-all"*) printf 'write-all\n'; return 0 ;;
                        "write"*) printf 'write-all\n'; return 0 ;;
                        "read-all"*|"read"*|"none"*) saw_readonly=1 ;;
                        *)
                            # Cycle-9: the flow mapping after the `permissions:`
                            # key is decided member by member, exactly as in the
                            # block form, so a tag, an anchor or a quote cannot
                            # make a write look read-only and an unclassifiable
                            # member is refused. `{}` is read-only.
                            local inline_verdict
                            inline_verdict="$(decide_flow_permissions "$value")"
                            case "$inline_verdict" in
                                read-only) saw_readonly=1 ;;
                                *) printf '%s\n' "$inline_verdict"; return 0 ;;
                            esac
                            ;;
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
    # Cycle-9 addendum: `"permissions":` and `'permissions':` are the same key as
    # the bare spelling (YAML strips the quotes), so the coverage proof must
    # recognise both here and as the child declaration below. Round 14: the same
    # goes for a key carrying node properties (`&p permissions:`), which the
    # readers peel before matching; an anchored key must not invent coverage any
    # more than it may hide a grant.
    local pat_perm_key='^[[:space:]]*["'\'']?permissions["'\'']?[[:space:]]*:'
    i=-1
    for (( n=0; n<${#PERM_LINES[@]}; n++ )); do
        line="$(_strip_key_props "${PERM_LINES[n]}")"
        if [[ "$line" =~ ^jobs[[:space:]]*:[[:space:]]*(.*)$ ]]; then
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
        # `permissions:` key itself is not a job, whether it is bare, quoted or
        # carrying node properties (`&p permissions:`).
        [[ "$(_strip_key_props "$line")" =~ $pat_perm_key ]] && continue
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
            if [ "${#inner_indent}" -eq "$child_min" ] && [[ "$(_strip_key_props "$inner")" =~ $pat_perm_key ]]; then
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
# `tests/test_workflow_config.py:1754`
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
            # Cycle-9 fail closed: a leading YAML tag, anchor or alias is a
            # construct this reader cannot resolve to a name. `uses: &a callee`,
            # `uses: !!str callee` and `uses: !<tag:...> callee` all resolve to
            # the real remote callee to a YAML parser while the first-token read
            # below saw only the anchor/tag and called the line clean. A tag or
            # an anchor is stripped first and the remainder re-read, so a callee
            # hidden behind one is still classified as the callee it is; an alias
            # (`*a`) resolves to a name this file does not hold and is refused
            # outright. A tag/anchor with nothing behind it is refused too, which
            # also catches `uses: &a |` (an anchored literal block).
            rest="${rest#"${rest%%[![:space:]]*}"}"
            case "$rest" in
                "&"*|"*"*|"!"*)
                    local lead="$rest"
                    local stripped=0
                    while [ -n "$lead" ]; do
                        case "$lead" in
                            '!'*)
                                stripped=1
                                if [ "${lead:1:1}" = "<" ]; then
                                    lead="${lead#<}"
                                    lead="${lead#*>}"
                                else
                                    lead="${lead#?}"
                                    while [ -n "$lead" ]; do
                                        case "${lead:0:1}" in
                                            [A-Za-z0-9_:-]) lead="${lead#?}" ;;
                                            *) break ;;
                                        esac
                                    done
                                fi
                                lead="${lead#"${lead%%[![:space:]]*}"}"
                                ;;
                            '&'*)
                                stripped=1
                                lead="${lead#?}"
                                while [ -n "$lead" ]; do
                                    case "${lead:0:1}" in
                                        [A-Za-z0-9_-]) lead="${lead#?}" ;;
                                        *) break ;;
                                    esac
                                done
                                lead="${lead#"${lead%%[![:space:]]*}"}"
                                ;;
                            *) break ;;
                        esac
                    done
                    case "$lead" in
                        "*"*) return 0 ;;
                    esac
                    if [ "$stripped" -eq 0 ] || [ -z "$lead" ]; then
                        return 0
                    fi
                    rest="$lead"
                    ;;
            esac
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
            #
            # Cycle-8: `$/` is the other same-repository, same-commit spelling
            # of a reusable-workflow call (GitHub's documented replacement for
            # `./`, not available on GHES). It names the same file the main loop
            # already sweeps, so it is handled exactly like `./` — no refusal
            # for a `.github/workflows/*.yml|*.yaml` target, `calls-a-local-
            # action` for anything else. GitHub forbids an `@{ref}` on `$/`, so
            # the `%@*` strip is a no-op for it and cannot hide a ref.
            case "$value" in
                ./*|\$/*)
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
                        ./.github/workflows/*.yml|./.github/workflows/*.yaml|\$/.github/workflows/*.yml|\$/.github/workflows/*.yaml)
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
# Cycle-9 (round 9): set by _ambiguously_placed_jobs_key when a quoted-scalar
# decoy left the file's key location unprovable. Reset for every file.
AMBIG_DECOY=0
report() {
    # One line per offender: <branch> <file> <reason>
    # When the file's key location could not be proven, every construct in it is
    # unclassifiable, so the reason names that rather than a grant the reader
    # inferred from a key it cannot be sure is a key.
    local reason="$3"
    if [ "${AMBIG_DECOY:-0}" -eq 1 ]; then
        reason="unreadable-token-permissions"
    fi
    printf '%s %s %s\n' "$1" "$2" "$reason"
    offenders=$((offenders + 1))
    # Round 10: remember the refused <branch> <path>. The identity arm below
    # reports only a path the parser did not already refuse, so the parser's
    # reason for a file always wins over the identity arm's broader one.
    REPORTED_PATHS="${REPORTED_PATHS:-}${1} ${2}"$'\n'
    # Round 10 addendum #3: the closing banner must not describe an identity
    # refusal as a publish-capable workflow. Tag every refusal with the class
    # that raised it, so each offending branch is counted once per class.
    if [ "${REPORT_CLASS:-parser}" = "identity" ]; then
        BRANCH_IDENTITY=1
    else
        BRANCH_PARSER=1
    fi
}

# ---------------------------------------------------------------------------
# Round 10: the DECIDABLE identity arm.
#
# The parser above is a hand-rolled YAML-subset reader, and six adversarial
# rounds defeated it six different ways. Every defeat was an unclassifiable
# construct read as read-only. This arm removes that dependence for workflow
# and action content entirely: it compares blob OIDS, which needs no YAML
# knowledge and cannot be spelled around.
#
# A non-main branch may not add or modify a path under `.github/workflows/`
# or `.github/actions/` unless the change is waived by a line on the ALLOWED
# branch naming exactly <branch> <path> <blob-oid>. The allowlist is read
# from the allowed ref only, never from the branch under test, so a branch
# cannot widen its own permission. Deletions are ignored: a path present at
# the merge base but absent from the branch adds no capability, and the
# parser still rules on whatever workflows remain. An ADDED path is a change.
#
# The parser does NOT consult the allowlist. A waived change that is still
# publish-capable is refused by the parser exactly as before, so a waiver
# cannot smuggle a publish path past the token and callee readers.
#
# Two baselines, not one. A path whose blob oid matches the MERGE BASE is
# inherited, already-reviewed content; a path whose blob oid matches the
# ALLOWED REF'S TIP is main's own content presented unchanged. Neither is the
# branch's own change, and neither is reported. Only a blob that differs from
# both is a change, and only then does the allowlist matter. The parser applies
# the same tip test as a second belt: a file main itself carries unchanged is
# not judged at all, so a branch forked from main is never a finding, while a
# STALE inherited publisher still is, because its blob differs from main's tip.
#
# The ok line says exactly what is proven, no more: no non-main branch carries
# a publish-capable workflow DIFFERING FROM MAIN'S.
# ---------------------------------------------------------------------------
ALLOWED_REF="${AUDIT_REMOTE_REFS}/${ALLOWED}"

# Fail closed when history is unusable: a shallow clone has no merge base, so
# no branch can be proven unchanged and every one is refused rather than read
# as clean.
SHALLOW_REPO=0
if [ "$(git rev-parse --is-shallow-repository 2>/dev/null || printf 'false')" = "true" ]; then
    SHALLOW_REPO=1
fi

# The allowlist, read once from the allowed ref only. A missing file is an
# empty list, not an error; a file that is present but unreadable is a refusal,
# never an empty list that would waive every change.
ALLOWLIST=""
ALLOWLIST_OK=1
ALLOWED_TREE_OK=0
if allowed_tree="$(git ls-tree -r "$ALLOWED_REF" -- .github 2>/dev/null)"; then
    ALLOWED_TREE_OK=1
    while IFS=$'\t' read -r allowlist_meta allowlist_path; do
        [ -n "$allowlist_path" ] || continue
        [ "$allowlist_path" = ".github/publish-sweep-allowlist.txt" ] || continue
        allowlist_mode="${allowlist_meta%% *}"
        allowlist_oid="${allowlist_meta##* }"
        # The allowlist must be a regular file (mode 100644). A symlink
        # (120000) or gitlink (160000) is refused rather than followed: git
        # cat-file on a symlink returns the link target, not reviewed file
        # text, so an attacker can commit a symlink whose target string reads
        # as a valid waiver line.
        if [ "$allowlist_mode" = "100644" ] \
            && allowlist_blob="$(git cat-file blob "$allowlist_oid" 2>/dev/null)"; then
            ALLOWLIST="$allowlist_blob"
        else
            ALLOWLIST_OK=0
        fi
        break
    done <<< "$allowed_tree"
fi

# 0 when the allowlist names exactly this branch, path and blob oid. Three
# whitespace-separated fields, an exact match: never a prefix and never a glob,
# so a waiver for one revision does not cover the next edit of the same path.
_allowlisted_change() {
    local allow_branch allow_path allow_oid allow_extra
    while IFS=$' \t\r' read -r allow_branch allow_path allow_oid allow_extra; do
        [ -n "$allow_branch" ] || continue
        case "$allow_branch" in
            \#*) continue ;;
        esac
        [ -z "$allow_extra" ] || continue
        if [ "$allow_branch" = "$1" ] && [ "$allow_path" = "$2" ] \
           && [ "$allow_oid" = "$3" ]; then
            return 0
        fi
    done <<< "$ALLOWLIST"
    return 1
}

# 0 when the parser already refused this <branch> <path>, so its reason wins.
_already_reported() {
    local reported_line
    while IFS= read -r reported_line; do
        if [ "$reported_line" = "$1 $2" ]; then
            return 0
        fi
    done <<< "${REPORTED_PATHS:-}"
    return 1
}

# Every identity refusal is counted separately from the parser's offenders so
# the closing banner can name the two legal ways out of this arm.
IDENTITY_OFFENDERS=0
_report_identity() {
    # The class tag makes report() count this as an identity refusal, not a
    # publish-capable one, and leaves the parser as the default afterwards.
    REPORT_CLASS=identity
    report "$1" "$2" "$3"
    REPORT_CLASS=parser
    IDENTITY_OFFENDERS=$((IDENTITY_OFFENDERS + 1))
}

# A precondition that fails for the WHOLE repository is stated once and ends
# the run. It is not this branch or that branch that is at fault, and printing
# it once per branch implied a dozen separate findings. The path column holds a
# real path for a per-file reason and `-` for a per-branch reason, so a reader
# can never mistake the placeholder for a file called `.`.
if [ "$SHALLOW_REPO" -eq 1 ]; then
    printf "refusing: the repository is a shallow clone, so a branch's CI cannot be compared with the merge base it shares with %s. Fetch the full history (checkout with fetch-depth: 0, or \`git fetch --unshallow\`) and re-run. (1)\n" "$ALLOWED" >&2
    exit 1
fi
if [ "$ALLOWED_TREE_OK" -ne 1 ]; then
    printf "refusing: the %s tree under .github cannot be listed, so no branch's workflow content can be compared with it. Check the fetch and re-run. (1)\n" "$ALLOWED" >&2
    exit 1
fi

# Addendum #3: distinct offending branches, counted per class and in total, so
# the closing banner can name only the classes that are actually present.
PARSER_BRANCHES=0
IDENTITY_BRANCHES=0
OFFENDING_BRANCHES=0

# Enumerate remote heads in the private namespace. Deliberately not
# `ls-tree` on the working copy: the whole point is refs we are not on.
for ref in $(git for-each-ref --format='%(refname)' "${AUDIT_REMOTE_REFS}"); do
    branch="${ref#"${AUDIT_REMOTE_REFS}"/}"
    if [ "$branch" = "$ALLOWED" ]; then
        continue
    fi

    # Round 10: the parser runs first, and its reason for a path wins; the
    # identity pass after it names only a change the parser did not already
    # refuse.
    REPORTED_PATHS=""
    BRANCH_PARSER=0
    BRANCH_IDENTITY=0

    # <mode> SP <type> SP <oid> TAB <path> -- the oid lets us read the blob
    # without spelling `ref:path`, which is the form that went blind on Windows.
    while IFS=$'\t' read -r meta path; do
        [ -n "$path" ] || continue
        AMBIG_DECOY=0
        oid="${meta##* }"
        base="${path##*/}"

        # Round 10 addendum: a branch created from main presents main's own
        # reviewed bytes for this path. That is not the branch's change --
        # refusing it would fail every branch forked from main, and the refusal
        # text would tell the operator to delete the released workflow. An
        # empty allowed_oid (main has no such path) falls through to the full
        # judgement below, which still catches a STALE inherited publisher
        # because a stale blob differs from main's tip.
        allowed_oid="$(git rev-parse -q --verify "$ALLOWED_REF:$path" 2>/dev/null || true)"
        if [ -n "$allowed_oid" ] && [ "$oid" = "$allowed_oid" ]; then
            continue
        fi

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
        # Cycle-9: the permissions reader sees the body with the VALUES of
        # scalar keys (`run:`, `with:`, `if:`, `env:`, `name:`, `shell:`,
        # `working-directory:`) removed — a `permissions:`-shaped token there is
        # data, not a token. It does not need the folded form because it does
        # not join continuations.
        clean="$(printf '%s\n' "$body" | strip_comments)"

        # Cycle-9 addendum (defeat 4): more than one document means a second
        # workflow whose read-only token and empty `jobs:` would vouch for the
        # first one's grant. Refuse before any reader runs.
        if has_multiple_documents <<< "$clean"; then
            report "$branch" "$path" "unreadable-multiple-documents"
            continue
        fi

        # Cycle-9 (round 9): if a quoted-scalar decoy leaves the file's key
        # location unprovable, remember it so `report` refuses whatever this
        # file carries rather than a grant inferred from an unprovable key.
        # Runs in the current shell (here-string, not a pipeline).
        if _ambiguously_placed_jobs_key <<< "$clean"; then
            :
        fi

        perm_text="$(printf '%s\n' "$clean" | strip_scalar_bodies)"
        verdict="$(printf '%s\n' "$perm_text" | permissions_verdict)"
        case "$verdict" in
            contents-write)
                report "$branch" "$path" "grants-contents-write"
                continue
                ;;
            write-all)
                report "$branch" "$path" "grants-write-all"
                continue
                ;;
            writable-scope)
                # Cycle-8: a `some-scope: write` that is not `contents`. The
                # sweep cannot know which scope a publisher needs — a package
                # push wants `packages: write`, a trusted publish wants
                # `id-token: write` — so every writable scope is a grant.
                report "$branch" "$path" "grants-writable-token-scope"
                continue
                ;;
            unrecognized)
                # A `permissions:` construct this sweep cannot read (a YAML
                # alias, a merge key, an escaped or explicit key, a flow mapping
                # the fold cannot close, a quoted scope key) is not a read-only
                # token. Refusing it is the whole point: the previous revision
                # let `permissions: *w` grant contents: write while reading as
                # nothing here. A quoted `permissions` KEY is not in this class
                # any more: the block pattern accepts it at line start and the
                # flow reader's left boundary accepts the inline spelling.
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
        #
        # Cycle-8: keep the pre-normalized form for the callee reader. A `uses:`
        # that is really the text of some other `|` block (`run: |` echoing a
        # `uses:` line) is data, not a callee, and telling the two apart needs
        # the block's indentation, which normalize_command_text squeezes away.
        # The other publisher patterns must still see that body — `gh release`
        # inside `run: |` really is a publisher — so only the callee reader gets
        # the filtered text.
        clean_raw="$clean"
        clean="$(printf '%s\n' "$clean_raw" | fold_block_scalars | squash_continuations | normalize_command_text)"

        # Cycle-9 addendum (defeat 3): normalize_command_text turns a
        # double-quoted escape it cannot decode into DQ_BAD rather than letting
        # the literal text stand (`\q`, or a trailing `\` whose folded
        # continuation this line-based reader does not resolve). An undecodable
        # escape means the value is unknown, not clean.
        case "$clean" in
            *"$DQ_BAD"*)
                report "$branch" "$path" "unreadable-escape-sequence"
                continue
                ;;
        esac
        # Cycle-9: the callee reader sees the same scalar-value stripping as the
        # permissions reader (a `uses:`-shaped token inside `with:`, `if:` or
        # `env:` is data, not a callee) on top of the `|`-body filter. The
        # stripping runs BEFORE the fold so a bare `env:`/`with:` key cannot be
        # joined onto the previous line, where its body would read as code.
        callee_text="$(printf '%s\n' "$clean_raw" | strip_scalar_bodies | fold_block_scalars | strip_non_uses_literal_bodies | squash_continuations | normalize_command_text)"

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
        #
        # Cycle-8: this list is DEFENCE IN DEPTH, not the guarantee. The token
        # arm above is the guarantee — a job that publishes needs a writable
        # token, and every `key: write` is now refused. This list only names
        # publishers a demonstrated audit used. A workflow that publishes
        # through an action not listed here and authenticates with a repository
        # secret is NOT caught by this script; that is why
        # `scripts/check-release-credentials.sh` proves no environment holding a
        # release credential admits a non-main ref, and why the repository
        # carries no repository-level secrets.
        for publisher in "action-gh-release" "release-action" "upload-release-asset" \
                         "create-release" "gh-release" \
                         "publish-release" "action-automatic-releases" \
                         "release-drafter" "goreleaser-action" \
                         "gh-action-pypi-publish"; do
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
        # Cycle-8: the filtered text drops `uses:` lines that are only the body
        # of another key's literal block, so an echoed `uses:` is not a callee.
        if callee_reason="$(printf '%s\n' "$callee_text" | calls_a_remote_reusable_workflow)"; then
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

    # --- Round 10: the identity arm, after the parser for this branch -----
    # A branch-level failure means nothing on it can be proven, so it is
    # refused whatever the parser said. Otherwise every workflow/action path
    # present on the branch must either match main's tip, match the merge
    # base's blob oid when the parser reads that path, or be waived by an
    # exact allowlist line. A refusal with no single path names `-` in the
    # path column, never a placeholder that looks like a file.
    AMBIG_DECOY=0
    identity_mb="$(git merge-base "$ALLOWED_REF" "$ref" 2>/dev/null || true)"
    if [ -z "$identity_mb" ]; then
        _report_identity "$branch" "-" "unreadable-merge-base"
    elif identity_tree="$(git ls-tree -r "$ref" -- .github/workflows .github/actions 2>/dev/null)"; then
        while IFS=$'\t' read -r identity_meta identity_path; do
            [ -n "$identity_path" ] || continue
            identity_oid="${identity_meta##* }"
            identity_base="$(git rev-parse -q --verify "$identity_mb:$identity_path" 2>/dev/null || true)"
            identity_tip="$(git rev-parse -q --verify "$ALLOWED_REF:$identity_path" 2>/dev/null || true)"
            # The merge base is a baseline ONLY for the paths the parser itself
            # reads, and the parser lists `.github/workflows` and nothing else.
            # An inherited `.github/actions` blob was never reviewed by that
            # read: main can rewrite the action while leaving the workflow
            # byte-identical, so the branch's inherited action is its own CI
            # definition and must be refused unless it matches main's tip or is
            # allowlisted. Main's tip is always a valid baseline: it is main's
            # own content adopted unchanged. A mode-only change keeps the oid
            # and is clean; a symlink or gitlink at a workflow path is a
            # different oid and is refused. The parser's reason for the same
            # path wins.
            identity_parser_reads=0
            case "$identity_path" in
                .github/workflows/*) identity_parser_reads=1 ;;
            esac
            if { [ "$identity_parser_reads" -eq 1 ] && [ "$identity_base" = "$identity_oid" ]; } \
                || { [ -n "$identity_tip" ] && [ "$identity_tip" = "$identity_oid" ]; }; then
                continue
            fi
            if _already_reported "$branch" "$identity_path"; then
                continue
            fi
            if [ "$ALLOWLIST_OK" -ne 1 ]; then
                _report_identity "$branch" "$identity_path" "unreadable-allowlist"
                continue
            fi
            if _allowlisted_change "$branch" "$identity_path" "$identity_oid"; then
                continue
            fi
            _report_identity "$branch" "$identity_path" \
                "branch-changes-workflow-file"
        done <<< "$identity_tree"
    else
        _report_identity "$branch" "-" "unreadable-branch-tree"
    fi

    # Count this branch once per class it offended in, and once in total.
    if [ "$BRANCH_PARSER" -eq 1 ]; then
        PARSER_BRANCHES=$((PARSER_BRANCHES + 1))
    fi
    if [ "$BRANCH_IDENTITY" -eq 1 ]; then
        IDENTITY_BRANCHES=$((IDENTITY_BRANCHES + 1))
    fi
    if [ "$BRANCH_PARSER" -eq 1 ] || [ "$BRANCH_IDENTITY" -eq 1 ]; then
        OFFENDING_BRANCHES=$((OFFENDING_BRANCHES + 1))
    fi
done

# Addendum #3: the banner names only the classes that are actually present, so
# an identity-only refusal never claims a publish-capable workflow, and each
# remedy is attached to the class it can actually fix.
_publish_capable_clause() {
    if [ "$1" -eq 1 ]; then
        printf '%d non-main branch carries a publish-capable workflow' "$1"
    else
        printf '%d non-main branches carry a publish-capable workflow' "$1"
    fi
}
_ci_definition_clause() {
    if [ "$1" -eq 1 ]; then
        printf '%d non-main branch changed its CI definition relative to the merge base with %s' "$1" "$ALLOWED"
    else
        printf '%d non-main branches changed their CI definition relative to the merge base with %s' "$1" "$ALLOWED"
    fi
}

if [ "$OFFENDING_BRANCHES" -gt 0 ]; then
    PARSER_OFFENDERS=$((offenders - IDENTITY_OFFENDERS))
    summary=""
    if [ "$PARSER_OFFENDERS" -gt 0 ]; then
        summary="$(_publish_capable_clause "$PARSER_BRANCHES")"
    fi
    if [ "$IDENTITY_BRANCHES" -gt 0 ]; then
        if [ -n "$summary" ]; then
            summary="$summary; "
        fi
        summary="${summary}$(_ci_definition_clause "$IDENTITY_BRANCHES")"
    fi
    printf 'refusing: %s (%d)\n' "$summary" "$OFFENDING_BRANCHES" >&2
    if [ "$PARSER_OFFENDERS" -gt 0 ]; then
        printf 'Land the publish-capable change on %s through review, or remove the grant on the branch above, then re-run.\n' "$ALLOWED" >&2
    fi
    if [ "$IDENTITY_BRANCHES" -gt 0 ]; then
        printf 'Merge or rebase the branch onto %s once the change has landed there, or commit a line on %s naming <branch> <path> <blob-oid> in .github/publish-sweep-allowlist.txt.\n' "$ALLOWED" "$ALLOWED" >&2
    fi
    exit 1
fi

printf "ok: no non-main branch carries a publish-capable workflow differing from main's\n" >&2
exit 0
