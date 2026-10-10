#!/usr/bin/env bash
# Read the half of this repository's security posture that does not live in git.
#
# Why this exists (CT-80, M7; releases/PLAN-0.6.8.md:161-166): at the audited tag
# 81f58ec the workflow declared no `environment:` at all, so no MAC_* or GPG_*
# secret could resolve there -- yet the 2026-10-07 candidate runs signed and
# notarized successfully. The wiring that made publication work was therefore
# not captured anywhere a reviewer could read it. Environments (their branch
# policies, their required reviewers and the *names* of their secrets), rulesets,
# Actions permissions and workflow registrations are all configured on GitHub and
# are invisible to `git log`.
#
#   scripts/check-platform-state.sh             diff the live platform against the record
#   scripts/check-platform-state.sh --record    replace the record with the live platform
#
# The record is releases/platform-state.json. Names are recorded; values never
# are. A secret's value cannot be read back through the API at all, and this
# script deliberately does not copy a variable's value, so the record stays
# publishable and reviewable. What the record can therefore prove is *wiring*:
# which environment holds which secret name, which refs may deploy, and how many
# reviewers stand between a candidate and the release environment.
#
# It fails closed. A missing `gh`, an unauthenticated `gh`, an API error or an
# unreadable record is a refusal -- never "no difference found". The one thing
# this script must never do is report a match it did not observe.
#
# `--record` rewrites the platform half of the file and carries the hand-written
# annotations (the `optional_secret_routes` map and the `notes` list) forward
# from the existing record, because those are statements about the workflow and
# the process rather than observations of the platform.
#
# Environment overrides, used by tests/test_platform_state.py:
#   PLATFORM_STATE_REPO    owner/name to read (default: the origin remote)
#   PLATFORM_STATE_RECORD  record path (default: releases/platform-state.json)
#   PLATFORM_STATE_GH      the GitHub CLI to run (default: gh)
#   PLATFORM_STATE_PYTHON  interpreter for the reader below (default: python3)
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
record="${PLATFORM_STATE_RECORD:-$root/releases/platform-state.json}"
gh_bin="${PLATFORM_STATE_GH:-gh}"
python_bin="${PLATFORM_STATE_PYTHON:-python3}"

mode="check"
case "${1:-}" in
  "") ;;
  --record) mode="record" ;;
  -h|--help) sed -n '2,40p' "${BASH_SOURCE[0]}"; exit 0 ;;
  *) echo "usage: $(basename "${BASH_SOURCE[0]}") [--record]" >&2; exit 2 ;;
esac
if (( $# > 1 )); then
  echo "usage: $(basename "${BASH_SOURCE[0]}") [--record]" >&2
  exit 2
fi

# The platform cannot be read without the tool that reads it, and a check that
# silently does nothing when `gh` is absent is the defect this script exists to
# avoid.
if ! command -v "$gh_bin" >/dev/null 2>&1; then
  echo "refusing: $gh_bin is not installed, so the platform state cannot be read." >&2
  echo "Install the GitHub CLI, run 'gh auth login', and run this script again." >&2
  exit 1
fi
if ! "$gh_bin" auth status >/dev/null 2>&1; then
  echo "refusing: $gh_bin is not authenticated, so the platform state cannot be read." >&2
  exit 1
fi

repo="${PLATFORM_STATE_REPO:-}"
if [[ -z "$repo" ]]; then
  origin="$(git -C "$root" config --get remote.origin.url 2>/dev/null || true)"
  # https://github.com/owner/name.git  |  git@github.com:owner/name.git
  repo="$(printf '%s' "$origin" | sed -E 's#^.*github\.com[:/]##; s#\.git$##')"
fi
if [[ ! "$repo" =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]]; then
  echo "refusing: cannot tell which repository to read (got '$repo')." >&2
  echo "Set PLATFORM_STATE_REPO=owner/name, or give the checkout an origin remote." >&2
  exit 1
fi

"$python_bin" - "$repo" "$record" "$mode" "$gh_bin" <<'PY'
"""Read the live platform state with `gh` and either record it or diff it."""
import datetime
import json
import pathlib
import subprocess
import sys

REPO, RECORD, MODE, GH = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3], sys.argv[4]
# Keys in the record that are statements rather than observations: the timestamp
# moves on every re-record, and the annotations below are hand-written about the
# workflow and the process. They are outside the diff, and `--record` carries
# the annotations forward so recording never erases them.
NOT_OBSERVED = ("recorded_at", "optional_secret_routes", "notes")


def api(path):
    """One `gh api` call, or a refusal. A failed read is never an empty answer."""
    result = subprocess.run(
        [GH, "api", f"repos/{REPO}/{path}"], capture_output=True, text=True
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise SystemExit(f"refusing: gh api {path} failed:\n{detail}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"refusing: gh api {path} did not return JSON: {exc}")


def environments():
    """Every environment: branch policies, required reviewers, secret names."""
    out = {}
    for listed in api("environments")["environments"]:
        name = listed["name"]
        detail = api(f"environments/{name}")
        policies = api(f"environments/{name}/deployment-branch-policies")["branch_policies"]
        secrets = api(f"environments/{name}/secrets")["secrets"]
        variables = api(f"environments/{name}/variables").get("variables") or []
        reviewers = sum(
            len(rule.get("reviewers") or [])
            for rule in detail.get("protection_rules") or []
            if rule.get("type") == "required_reviewers"
        )
        out[name] = {
            "can_admins_bypass": bool(detail["can_admins_bypass"]),
            "branch_policies": sorted(policy["name"] for policy in policies),
            "required_reviewers": reviewers,
            "secrets": sorted(secret["name"] for secret in secrets),
            "variables": sorted(variable["name"] for variable in variables),
        }
    return dict(sorted(out.items()))


def rulesets():
    out = []
    for listed in api("rulesets"):
        detail = api(f"rulesets/{listed['id']}")
        ref_name = (detail.get("conditions") or {}).get("ref_name") or {}
        out.append(
            {
                "name": detail["name"],
                "target": detail["target"],
                "enforcement": detail["enforcement"],
                "include": sorted(ref_name.get("include") or []),
                "rules": sorted(rule["type"] for rule in detail.get("rules") or []),
            }
        )
    return sorted(out, key=lambda item: item["name"])


def permissions():
    actions = api("actions/permissions")
    workflow = api("actions/permissions/workflow")
    return {
        "actions": {
            "enabled": bool(actions["enabled"]),
            "allowed_actions": actions["allowed_actions"],
            "sha_pinning_required": bool(actions["sha_pinning_required"]),
        },
        "workflow": {
            "default_workflow_permissions": workflow["default_workflow_permissions"],
            "can_approve_pull_request_reviews": bool(
                workflow["can_approve_pull_request_reviews"]
            ),
        },
    }


def registrations():
    """Workflow registrations, split into file-backed and platform-generated."""
    out = {"file": {}, "dynamic": {}}
    for workflow in api("actions/workflows")["workflows"]:
        path = workflow["path"]
        entry = {"name": workflow["name"], "state": workflow["state"]}
        kind = "file" if path.startswith(".github/workflows/") else "dynamic"
        out[kind][path] = entry
    return {
        "file": dict(sorted(out["file"].items())),
        "dynamic": dict(sorted(out["dynamic"].items())),
    }


def observe():
    return {
        "schema": "bitcoin-easy-multisig-signer/platform-state/1",
        "recorded_from": REPO,
        "recorded_with": "scripts/check-platform-state.sh --record",
        "values": (
            "names only: no secret and no variable value is recorded. Secret values "
            "are unreadable through the API; variable values are deliberately not "
            "copied so this record can be published and reviewed."
        ),
        "environments": environments(),
        "repository_secrets": sorted(
            secret["name"] for secret in api("actions/secrets")["secrets"]
        ),
        "repository_variables": sorted(
            variable["name"] for variable in api("actions/variables").get("variables") or []
        ),
        "rulesets": rulesets(),
        "permissions": permissions(),
        "workflow_registrations": registrations(),
    }


def differences(recorded, live, path=""):
    """Every leaf that moved, named by its path, so drift is never a summary."""
    if isinstance(recorded, dict) and isinstance(live, dict):
        out = []
        for key in sorted(set(recorded) | set(live)):
            where = f"{path}{key}".replace("..", ".")
            if key not in recorded:
                out.append(f"{where}: not in the record (live: {live[key]!r})")
            elif key not in live:
                out.append(f"{where}: recorded but not on the platform ({recorded[key]!r})")
            else:
                out.extend(differences(recorded[key], live[key], f"{where}."))
        return out
    if recorded != live:
        return [f"{path.rstrip('.')}: recorded {recorded!r}, live {live!r}"]
    return []


def without_volatile(document):
    return {key: value for key, value in document.items() if key not in NOT_OBSERVED}


live = observe()

if MODE == "record":
    carried = {}
    if RECORD.exists():
        try:
            existing = json.loads(RECORD.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"refusing: {RECORD} is not readable JSON: {exc}")
        for key in ("optional_secret_routes", "notes"):
            if key in existing:
                carried[key] = existing[key]
    document = dict(live)
    document.update(carried)
    document["recorded_at"] = (
        datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
        .replace("+00:00", "Z")
    )
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    carried_note = f" (carried forward: {', '.join(sorted(carried))})" if carried else ""
    print(f"recorded: {RECORD} from {REPO}{carried_note}")
    raise SystemExit(0)

if not RECORD.exists():
    raise SystemExit(
        f"refusing: {RECORD} does not exist, so there is nothing to compare against.\n"
        "Record the platform state first: scripts/check-platform-state.sh --record"
    )
try:
    recorded = json.loads(RECORD.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    raise SystemExit(f"refusing: {RECORD} is not readable JSON: {exc}")

if recorded.get("recorded_from") not in (None, REPO):
    raise SystemExit(
        f"refusing: {RECORD} was recorded from {recorded['recorded_from']!r}, "
        f"not {REPO!r}."
    )

drift = differences(without_volatile(recorded), without_volatile(live))
if drift:
    print(f"the live platform does not match {RECORD}:", file=sys.stderr)
    for item in drift:
        print(f"  - {item}", file=sys.stderr)
    print(
        "\nIf the change is intended, re-record it and review the diff:\n"
        "  scripts/check-platform-state.sh --record",
        file=sys.stderr,
    )
    raise SystemExit(1)

environments_seen = len(live["environments"])
print(
    f"ok: {REPO} matches {RECORD} "
    f"({environments_seen} environments, {len(live['rulesets'])} rulesets, "
    f"{len(live['workflow_registrations']['file'])} workflow files registered)"
)
PY
