#!/usr/bin/env bash
# CT-97 — where the release credentials live.
#
# Repository secrets are handed to a job on ANY ref. A dispatch at a historical
# tag therefore runs that tag's own frozen (older, less guarded) workflow text
# but still receives today's signing keys, because secrets are matched by name
# and not by tag. That was CT-97: a link on the publishing chain we could not
# show was safe. Tags are immutable history — AGENTS.md forbids moving or
# deleting a published one — so the fix cannot live in the tag. It lives in the
# platform: every credential moves into a protected environment whose deployment
# rule allows `main` only, and every job that names it declares that environment
# (`.github/workflows/build-candidate.yml`; pinned by
# tests/test_workflow_config.py::ReleaseCredentialScopePins).
#
# This script is the standing check for the half no unit test can reach. It
# reads configuration only — a secret value can never be read back, not by this
# script and not by anyone — and refuses (exit 1) unless all of:
#   1. No repository-level secret carries a watched credential name. This is
#      the load-bearing one: environment secrets are ADDED to repository
#      secrets, so while a repository-level copy exists every ref still gets
#      the key and nothing else here matters.
#   2. Every watched name is named by a job that declares an environment. A job
#      with no environment receives the secret on every ref, which is the whole
#      finding; a name that appears that way is a refusal, not a detail.
#   3. Each environment the workflows declare exists, allows deployments from
#      `main` only, declares no human gate, and holds no name beyond the watched
#      ones its jobs reference. A referenced name that is absent is reported as
#      a `note:`, not a refusal -- the workflow reads an optional route as empty
#      and every required credential is guarded by `: "${...:?}"`, so an absent
#      secret fails the release closed. A name the environment holds that no job
#      references IS a refusal: that is least privilege and an unscoped name.
#
# The watched name set is DERIVED from the workflow text (see `credential_scope`
# below) and never from a list in this file. CT-97's repository half was a
# hand-maintained five-name constant that did not know `MAC_NOTARY_KEY_P8_BASE64`
# existed in `.github/workflows/build-candidate.yml`: the sixth name was live and
# unwatched. A name is watched the day a workflow spells it.
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
# Usage: scripts/check-release-credentials.sh [owner/repo] [workflows-dir]
#        scripts/check-release-credentials.sh --print-scope [workflows-dir]
#
# The optional `workflows-dir` exists so an auditor can point the derivation at
# another checkout, and so the tests can show a hostile workflow being refused.
# It defaults to the `.github/workflows` beside this script. `--print-scope`
# prints the derivation (`name<TAB>environment<TAB>workflow:job`) and exits; the
# test suite runs it and asserts it agrees with an independent PyYAML parse.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_WORKFLOWS_DIR="$SCRIPT_DIR/../.github/workflows"

PRINT_SCOPE=0
if [[ "${1:-}" == "--print-scope" ]]; then
  PRINT_SCOPE=1
  REPO=""
  WORKFLOWS_DIR="${2:-$DEFAULT_WORKFLOWS_DIR}"
else
  REPO="${1:-cjtsh/bitcoin-easy-multisig-signer}"
  WORKFLOWS_DIR="${2:-$DEFAULT_WORKFLOWS_DIR}"
fi

REFUSAL="refusing: the release credentials are not environment-scoped"

# Print "<name>\t<environment>\t<workflow>:<job>" for every `secrets.NAME`,
# `secrets['NAME']` or `secrets["NAME"]` reference in every workflow under the
# workflows dir, sorted. `<environment>` is `-` when the job declares none.
#
# Deliberately stdlib-only and text-based: the operator's `python3` is the host
# interpreter, which has no PyYAML, and this check must run wherever `gh` does.
# The parse is conservative — a reference inside what it reads as a block is
# watched even if a human would call it a comment, and over-watching fails
# closed. `tests/test_release_credentials.py` asserts this derivation is exactly
# what PyYAML gives for the same files, so the two cannot drift apart silently.
#
# FAIL CLOSED (cycle-5 adversarial pass): the structured walk only reads what it
# can place under a job, and the attacker put a live credential in the
# WORKFLOW-LEVEL `env:` block above `jobs:` — never read — so the repository
# sweep below never refused a live repository copy of it. Every reference that
# survives comment stripping is now compared against the attributed set; one
# the walk did not place is emitted with no environment (`<unattributed>`),
# which the caller refuses. A quoted job key or an unusual `jobs:` indent is
# therefore a refusal, not silence.
#
# A `secrets.NAME` in a COMMENT is not live and is not watched: comment
# stripping runs on both paths, so prose cannot widen or narrow this set.
credential_scope() {
  python3 -c '
import os, re, sys
from collections import Counter

APOS, QUOTE = chr(39), chr(34)
directory = sys.argv[1]
SECRET = re.compile(r"secrets\s*\.\s*([A-Za-z0-9_-]+)"
                    r"|secrets\s*\[\s*[" + QUOTE + APOS + r"]([A-Za-z0-9_-]+)"
                    r"[" + QUOTE + APOS + r"]\s*\]")
# FAIL CLOSED (cycle-6 adversarial pass): `secrets[format(...)]` matched the
# dot form of nothing and the quoted form of nothing, so a name spelled through
# an expression was watched by neither path. Any bracket index is now read:
# quoted literals inside it are names, and an index with no literal at all is
# reported as a name this check cannot read, which the caller refuses rather
# than ignores.
BRACKET = re.compile(r"secrets\s*\[\s*([^\]\n]+?)\s*\]")
LITERAL = re.compile(r"[" + QUOTE + APOS + r"]([A-Za-z0-9_-]+)[" + QUOTE + APOS + r"]")
PLAIN = re.compile(r"^[" + QUOTE + APOS + r"]([A-Za-z0-9_-]+)[" + QUOTE + APOS + r"]$")
# A job key may be quoted. The pre-cycle-6 pattern required the bare spelling,
# so `  "leak":` was appended to the body of the previous job and its reference
# was attributed to the environment of that job, not read as unscoped.
JOB = re.compile(r"^  [" + QUOTE + APOS + r"]?([A-Za-z0-9_.-]+)[" + QUOTE + APOS + r"]?:[ \t]*$")
KEY = re.compile(r"^([ \t]*)([A-Za-z0-9_.-]+):(.*)$")


def strip_comment(line):
    out, quote = [], ""
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = ""
        elif ch in (QUOTE, APOS):
            # A quote opens a scalar only where a token can begin. `Don` + APOS
            # + `t` has one inside a word, and treating it as an opener would
            # swallow the `#` that ends the line, watching a name PyYAML sees
            # as a comment.
            if not out or out[-1].isspace() or out[-1] in ":,[{-":
                quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out)


def jobs(text):
    lines, index = text.splitlines(), 0
    while index < len(lines) and lines[index].rstrip() != "jobs:":
        index += 1
    name, body = None, []
    for line in lines[index + 1:]:
        clean = strip_comment(line)
        if not clean.strip():
            continue
        if not clean[0].isspace():
            break
        match = JOB.match(clean)
        if match:
            if name is not None:
                yield name, body
            name, body = match.group(1), []
        elif name is not None:
            body.append(clean)
    if name is not None:
        yield name, body


def environment(body):
    for position, line in enumerate(body):
        match = KEY.match(line)
        if not match or match.group(2) != "environment":
            continue
        indent, value = len(match.group(1)), match.group(3).strip()
        if indent < 4:
            continue
        if value:
            return value.strip(QUOTE + APOS)
        for follow in body[position + 1:]:
            deeper = KEY.match(follow)
            if not deeper or len(deeper.group(1)) <= indent:
                break
            if deeper.group(2) == "name":
                return deeper.group(3).strip().strip(QUOTE + APOS)
        return ""
    return ""


def names_on(line):
    """Every release-credential name this line names, best effort.

    `secrets.NAME` and `secrets["NAME"]` are read directly. Inside a bracket
    index that is an expression, every quoted literal is a candidate name; an
    index with no quoted literal at all becomes the literal text of the index,
    which is a name no environment can hold, so the caller refuses it instead
    of treating an unreadable spelling as absent.
    """
    clean = strip_comment(line)
    found = []
    for match in SECRET.finditer(clean):
        found.append(match.group(1) or match.group(2))
    for match in BRACKET.finditer(clean):
        inner = match.group(1)
        if PLAIN.match(inner):
            continue
        literals = LITERAL.findall(inner)
        found.extend(literals if literals else [inner])
    return found


def live_references(text):
    """Every `secrets.…` occurrence that survives comment stripping.

    The structured walk only reads lines it can place under a job in the
    `jobs:` block. This is the whole-file safety net: a reference the walk
    cannot attribute is still live, and is reported with no environment. It
    returns one entry per occurrence, because a name that appears both inside
    a scoped job and again somewhere the walk cannot place (a workflow-level
    `env:` block) is live in both places and only one of them is scoped.
    """
    found = []
    for line in text.splitlines():
        found.extend(names_on(line))
    return found


rows = []
if os.path.isdir(directory):
    for entry in sorted(os.listdir(directory)):
        if not entry.endswith((".yml", ".yaml")):
            continue
        with open(os.path.join(directory, entry), encoding="utf-8") as handle:
            text = handle.read()
        attributed = Counter()
        for job, body in jobs(text):
            where = environment(body) or "-"
            for line in body:
                for name in names_on(line):
                    attributed[name] += 1
                    rows.append((name, where, entry + ":" + job))
        # FAIL CLOSED (cycle-5 adversarial pass): every live reference that the
        # walk above did NOT place in a job is reported with no environment,
        # which is a refusal. The attacker named a credential only in the
        # WORKFLOW-LEVEL `env:` block above `jobs:`, which the old walk never
        # read, and showed that a quoted job key or an unusual `jobs:` indent
        # was invisible the same way. A name this check cannot attribute is now
        # an unscoped name, not silence.
        live = Counter(live_references(text))
        for name, count in sorted(live.items()):
            for _ in range(max(0, count - attributed.get(name, 0))):
                rows.append((name, "-", entry + ":<unattributed>"))
for name, where, source in sorted(set(rows)):
    print(name + "\t" + where + "\t" + source)
' "$WORKFLOWS_DIR" | tr -d '\r'
}

# The derivation, once. An empty scope is itself a refusal: with nothing to
# watch this check would pass vacuously, and a check that cannot fail is not a
# check.
scope="$(credential_scope)"

if (( PRINT_SCOPE )); then
  printf '%s\n' "$scope"
  exit 0
fi

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
# `--paginate` makes gh print one JSON document per page back to back, so every
# reader below decodes a stream of documents rather than one. A single document
# still works, and an unreadable stream is still an error: the cycle-6 referee
# showed that reading only the first page let a repository-level copy sitting on
# page 2 (the 31st secret) pass the sweep.
names_from() {
  python3 -c 'import json, sys
def documents(text):
    decoder = json.JSONDecoder()
    index = 0
    while True:
        while index < len(text) and text[index] in " \t\r\n":
            index += 1
        if index >= len(text):
            return
        value, index = decoder.raw_decode(text, index)
        yield value
try:
    payloads = list(documents(sys.stdin.read()))
except ValueError:
    sys.exit(1)
names = []
for payload in payloads:
    if not isinstance(payload, dict):
        sys.exit(1)
    for row in payload.get(sys.argv[1]) or []:
        if not isinstance(row, dict):
            sys.exit(1)
        names.append(row.get("name", ""))
print("\n".join(sorted(set(names))))' "$1" | tr -d '\r'
}

# Print "<name> <type>" for each deployment branch policy on stdin.
policy_lines() {
  python3 -c 'import json, sys
def documents(text):
    decoder = json.JSONDecoder()
    index = 0
    while True:
        while index < len(text) and text[index] in " \t\r\n":
            index += 1
        if index >= len(text):
            return
        value, index = decoder.raw_decode(text, index)
        yield value
try:
    payloads = list(documents(sys.stdin.read()))
except ValueError:
    sys.exit(1)
lines = []
for payload in payloads:
    if not isinstance(payload, dict):
        sys.exit(1)
    for row in payload.get("branch_policies") or []:
        if not isinstance(row, dict):
            sys.exit(1)
        lines.append("%s %s" % (row.get("name"), row.get("type")))
print("\n".join(sorted(set(lines))))' | tr -d '\r'
}

# Print any human gate declared on an environment on stdin: a required reviewer
# pauses the run for a person and a wait timer delays it. Either one means a
# release cannot start on its own, so either one is an offender here.
gate_lines() {
  python3 -c 'import json, sys
def documents(text):
    decoder = json.JSONDecoder()
    index = 0
    while True:
        while index < len(text) and text[index] in " \t\r\n":
            index += 1
        if index >= len(text):
            return
        value, index = decoder.raw_decode(text, index)
        yield value
try:
    payloads = list(documents(sys.stdin.read()))
except ValueError:
    sys.exit(1)
gates = []
for payload in payloads:
    if not isinstance(payload, dict):
        sys.exit(1)
    for rule in payload.get("protection_rules") or []:
        if not isinstance(rule, dict):
            sys.exit(1)
        kind = rule.get("type")
        if kind == "required_reviewers" and (rule.get("reviewers") or []):
            gates.append("required_reviewers(%d)" % len(rule["reviewers"]))
        elif kind == "wait_timer" and (rule.get("wait_timer") or 0):
            gates.append("wait_timer(%s)" % rule.get("wait_timer"))
print("\n".join(sorted(set(gates))))' | tr -d '\r'
}

# Every watched name, deduplicated.
#
# Both loops end in an `if` rather than `[[ ... ]] &&`: under `pipefail` a false
# test as the last command of a pipeline makes the whole substitution non-zero,
# and `expected="$(scoped_names ...)"` would then exit the script silently with
# no refusal printed.
all_names() {
  printf '%s\n' "$scope" | while IFS=$'\t' read -r name environment source; do
    if [[ -n "$name" ]]; then
      printf '%s\n' "$name"
    fi
  done | sort -u
}

# The watched names one environment holds, sorted.
scoped_names() {
  printf '%s\n' "$scope" | while IFS=$'\t' read -r name environment source; do
    if [[ "$environment" == "$1" ]]; then
      printf '%s\n' "$name"
    fi
  done | sort
}

# Every environment the workflows declare, minus the unscoped marker.
declared_environments() {
  printf '%s\n' "$scope" | cut -f2 | sort -u | grep -v '^-$' || true
}

if [[ -z "$scope" ]]; then
  report "no workflow under $WORKFLOWS_DIR names a release credential; with nothing to watch this check proves nothing, so it refuses"
fi

# 1a. A credential named by a job with no environment is reachable on every ref.
while IFS=$'\t' read -r name environment source; do
  [[ -n "$name" ]] || continue
  if [[ "$environment" == "-" && "$source" == *":<unattributed>" ]]; then
    report "${source%:<unattributed>} names the release credential $name somewhere this check cannot attribute to a job (a workflow-level env: block, a quoted job key, or a jobs: block it cannot read); a name with no scope reaches a job on every ref, so it is refused rather than assumed harmless"
  elif [[ "$environment" == "-" ]]; then
    report "$source names the release credential $name in a job that declares no environment; a repository secret reaches that job on every ref, including every historical tag — put the value in an environment and declare it on the job"
  elif [[ ! "$environment" =~ ^[A-Za-z0-9._-]+$ ]]; then
    report "$source names $name inside an environment this check cannot parse ($environment); a name that cannot be read cannot be scoped"
  fi
done <<< "$scope"

# 1b. No repository-level copy of a watched credential may exist.
if ! repo_names="$(gh api --paginate "repos/$REPO/actions/secrets" | names_from secrets)"; then
  report "could not read the repository secret names of $REPO (is gh authenticated with access to it?)"
  repo_names=""
fi
for name in $(all_names); do
  if printf '%s\n' "$repo_names" | grep -Fxq "$name"; then
    report "$REPO still has a REPOSITORY-level secret named $name; environment secrets are added to repository secrets, so every ref including every historical tag keeps receiving it — re-enter the value in its environment secrets and delete this copy"
  fi
done

# 2. Each declared environment exists, is main-only, is gate-free, and holds
# nothing beyond the watched names its jobs reference. Least privilege is the
# exactness that matters: an extra name means a job that needs one credential
# also loads another, and an unknown name is one nobody decided to scope.
#
# A name that is referenced but absent is NOT a refusal. The workflow reads a
# route it may not use as empty and falls back (the App Store Connect key), and
# every credential it truly needs is guarded by `: "${NAME:?}"`, so an absent
# secret fails the release closed rather than skipping a signature. Demanding
# that every referenced name exist would force the owner to create a value they
# may have no way to obtain, which is why the absent ones are only noted.
#
# CT-97 is the repository-level sweep above, and it covers every derived name
# including the optional ones: that is the half that was missing.
for env in $(declared_environments); do
  if ! env_json="$(gh api "repos/$REPO/environments/$env" 2>/dev/null)"; then
    report "$REPO has no environment named $env, so the credentials its jobs name have nowhere environment-scoped to live"
    continue
  fi
  if ! policies="$(gh api --paginate "repos/$REPO/environments/$env/deployment-branch-policies" 2>/dev/null | policy_lines)"; then
    report "could not read the deployment branch policies of the $env environment"
    policies=""
  fi
  if [[ "$policies" != "main branch" ]]; then
    report "the $env environment does not allow deployments from the main branch alone (found: ${policies:-none}); a tag must never be able to deploy into it"
  fi
  if ! actual="$(gh api --paginate "repos/$REPO/environments/$env/secrets" 2>/dev/null | names_from secrets)"; then
    report "could not read the secret names of the $env environment"
    actual=""
  fi
  expected="$(scoped_names "$env")"
  extra="$(comm -13 <(printf '%s\n' "$expected" | sort -u) <(printf '%s\n' "$actual" | sort -u) | sed '/^$/d')"
  if [[ -n "$extra" ]]; then
    report "the $env environment holds [$(printf '%s' "$extra" | tr '\n' ' ')], which no job that declares $env references; it must hold only [$(printf '%s' "$expected" | tr '\n' ' ')]"
  fi
  if [[ -z "$actual" ]]; then
    report "the $env environment holds none of the credentials its jobs reference [$(printf '%s' "$expected" | tr '\n' ' ')]; with nothing armed this check proves nothing"
  fi
  missing="$(comm -23 <(printf '%s\n' "$expected" | sort -u) <(printf '%s\n' "$actual" | sort -u) | sed '/^$/d')"
  if [[ -n "$missing" ]]; then
    echo "note: the $env environment does not hold [$(printf '%s' "$missing" | tr '\n' ' ')]; allowed only because the workflow reads each of those as optional and fails closed when one is required" >&2
  fi
  if ! gates="$(printf '%s' "$env_json" | gate_lines)"; then
    report "could not read the protection rules of the $env environment"
    gates=""
  fi
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
