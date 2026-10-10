"""Run GitHub Actions ``run:`` steps for real, and assert on what they do.

Why this exists (CT-74, CT-75). A workflow step is code. For two cycles the
release guards were "pinned" by asserting that the guard's *words* were
present — the string ``exit 1``, the refusal sentence, ``>&2``. Every one of
those pins stayed green while the guard's logic was defeated: a condition
inverted, ``if: ${{ false }}``, ``|| true`` appended to a checksum check, a
predicate OR-ed with ``true``. The audit's coaching document calls this
"string-pins vs behaviour-pins", and it is the reason CT-74/75 exist.

This module makes the honest version cheap:

* ``render()`` substitutes every ``${{ ... }}`` expression into the step text
  the way a runner does — *before* the shell parses it. That is not a detail:
  textual substitution is the whole mechanism behind CT-72, where the line
  validating ``candidate_run_id`` was the line executing it. Rendering
  faithfully is what lets a test demonstrate that.
* ``evaluate_if()`` evaluates a step's ``if:`` expression, so a test can assert
  that a guard is actually *reached* — the defeat where the guard's body is
  perfect and its condition is impossible.
* ``run_step()`` runs the rendered body under ``bash -e`` with the shell
  functions in ``stubs`` shadowing ``gh``, ``git``, ``gpg`` and friends. Each
  stub records the argv it was called with, so a test asserts outcomes: exit
  status, which tool ran with which arguments, which files appeared.

Stubs are shell functions rather than executables on ``PATH`` on purpose: the
suite runs on macOS, Linux and Windows (Git Bash), and generated shell
functions need no shebang, no ``chmod``, and no PATH surgery to work on all
three.

There is no network access here and there must never be: every external tool
is a stub, and the tests that use real tools (``shasum``, ``grep``) do so
against fixtures in a temporary directory.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from support import bash_executable

ROOT = Path(__file__).resolve().parent.parent

EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}", re.DOTALL)

__all__ = [
    "ROOT",
    "Stub",
    "StepResult",
    "active_workflow",
    "evaluate_if",
    "find_step",
    "load_workflow",
    "render",
    "run_step",
    "step_runs",
    "yaml_available",
]


def yaml_available() -> bool:
    try:
        import yaml  # noqa: F401
    except ImportError:
        return False
    return True


def active_workflow() -> Path:
    """The canonical workflow, from the checkout or from an extracted archive."""
    checkout = ROOT / ".github" / "workflows" / "build-candidate.yml"
    if checkout.is_file():
        return checkout
    archived = ROOT / "ci" / "build-candidate.yml"
    if archived.is_file():
        return archived
    raise FileNotFoundError("no build-candidate.yml in the checkout or the archive")


def load_workflow(path: Path | str | None = None) -> dict:
    import yaml

    return yaml.safe_load(Path(path or active_workflow()).read_text(encoding="utf-8"))


def find_step(workflow: dict, job: str, name: str) -> dict:
    """The step named ``name`` in job ``job``.

    Addressing by name rather than by line is deliberate: a test that reaches
    into a neighbouring step is how the previous generation of body pins went
    blind (see GuardBodyPins in tests/test_workflow_config.py).
    """
    steps = workflow["jobs"][job].get("steps", [])
    for step in steps:
        if step.get("name") == name:
            return step
    available = ", ".join(repr(step.get("name")) for step in steps)
    raise KeyError(f"job {job!r} has no step named {name!r}; it has: {available}")


# --------------------------------------------------------------------------
# Expressions
# --------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
      (?P<space>\s+)
    | (?P<op>==|!=|&&|\|\||!|\(|\))
    | (?P<string>'[^']*'|"[^"]*")
    | (?P<name>[A-Za-z_][A-Za-z0-9_.]*)
    """,
    re.VERBOSE,
)


def _tokenize(text: str) -> list[tuple[str, object]]:
    tokens: list[tuple[str, object]] = []
    position = 0
    while position < len(text):
        match = _TOKEN_RE.match(text, position)
        if match is None:
            raise ValueError(f"cannot parse expression at {text[position:]!r}")
        position = match.end()
        if match.group("space"):
            continue
        if match.group("op"):
            tokens.append(("op", match.group("op")))
        elif match.group("string"):
            raw = match.group("string")
            tokens.append(("value", raw[1:-1]))
        else:
            name = match.group("name")
            if name == "true":
                tokens.append(("value", True))
            elif name == "false":
                tokens.append(("value", False))
            elif name == "null":
                tokens.append(("value", None))
            else:
                tokens.append(("name", name))
    return tokens


def resolve(name: str, context: dict) -> object:
    """Look up one dotted expression name.

    Unknown names raise instead of resolving to the empty string. GitHub would
    substitute nothing; here that would let a typo in a test turn an assertion
    about a guard into an assertion about an empty string, which passes.
    """
    if name not in context:
        raise KeyError(f"unknown workflow expression {name!r}; add it to the context")
    return context[name]


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value != ""
    return bool(value)


def _parse_atom(tokens, index, context):
    kind, value = tokens[index]
    if kind == "op" and value == "(":
        result, index = _parse_or(tokens, index + 1, context)
        if tokens[index] != ("op", ")"):
            raise ValueError("missing closing parenthesis")
        return result, index + 1
    if kind in ("value", "name"):
        return (resolve(value, context) if kind == "name" else value), index + 1
    raise ValueError(f"unexpected token {tokens[index]!r}")


def _parse_compare(tokens, index, context):
    left, index = _parse_atom(tokens, index, context)
    if index < len(tokens) and tokens[index] in (("op", "=="), ("op", "!=")):
        operator = tokens[index][1]
        right, index = _parse_atom(tokens, index + 1, context)
        return (left == right) if operator == "==" else (left != right), index
    return left, index


def _parse_not(tokens, index, context):
    if index < len(tokens) and tokens[index] == ("op", "!"):
        value, index = _parse_not(tokens, index + 1, context)
        return (not _truthy(value)), index
    return _parse_compare(tokens, index, context)


def _parse_and(tokens, index, context):
    value, index = _parse_not(tokens, index, context)
    while index < len(tokens) and tokens[index] == ("op", "&&"):
        right, index = _parse_not(tokens, index + 1, context)
        # GitHub's && returns the second operand when the first is truthy.
        value = right if _truthy(value) else value
    return value, index


def _parse_or(tokens, index, context):
    value, index = _parse_and(tokens, index, context)
    while index < len(tokens) and tokens[index] == ("op", "||"):
        right, index = _parse_and(tokens, index + 1, context)
        value = value if _truthy(value) else right
    return value, index


def evaluate_expression(expression: str, context: dict) -> object:
    """Evaluate a ``${{ ... }}`` expression to its value, as the runner would."""
    text = expression.strip()
    if text.startswith("${{") and text.endswith("}}"):
        text = text[3:-2].strip()
    if not text:
        return ""
    tokens = _tokenize(text)
    value, index = _parse_or(tokens, 0, context)
    if index != len(tokens):
        raise ValueError(f"unparsed expression tail: {tokens[index:]}")
    return value


def evaluate_if(expression: str | bool, context: dict) -> bool:
    """Evaluate a step's ``if:`` the way the runner decides whether to run it."""
    if isinstance(expression, bool):
        return expression
    return _truthy(evaluate_expression(expression, context))


def _coerce(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def render(text: str, context: dict) -> str:
    """Substitute ``${{ ... }}`` into text, as a runner does before running it."""

    def substitute(match: re.Match) -> str:
        return _coerce(evaluate_expression(match.group(1), context))

    return EXPRESSION.sub(substitute, text)


def render_value(text: str, context: dict) -> str:
    """Render a ``with:`` / ``env:`` value the way the runner resolves it."""
    stripped = str(text).strip()
    match = re.fullmatch(r"\$\{\{(.*?)\}\}", stripped, re.DOTALL)
    if match:
        return _coerce(evaluate_expression(match.group(1), context))
    return render(str(text), context)


def runner_environment(context: dict, step: dict, overrides: dict | None) -> dict:
    """The environment a step runs in.

    ``github.*`` context values become the ``GITHUB_*`` variables the runner
    exports; the step's own ``env:`` block is rendered from the context (so a
    test that deletes an ``env:`` key the script depends on fails here); and
    explicit ``overrides`` win, for things only the test can know.
    """
    environment = dict(os.environ)
    for name, value in context.items():
        if name.startswith("github."):
            environment["GITHUB_" + name.split(".", 1)[1].upper()] = _coerce(value)
    for key, value in (step.get("env") or {}).items():
        environment[str(key)] = render_value(str(value), context)
    for key, value in (overrides or {}).items():
        environment[str(key)] = str(value)
    return environment


def step_runs(step: dict, context: dict) -> bool:
    """Whether the runner would run this step at all."""
    if "if" not in step:
        return True
    return evaluate_if(step["if"], context)


# --------------------------------------------------------------------------
# Stubs and execution
# --------------------------------------------------------------------------


@dataclass
class Stub:
    """One scripted response for a shadowed tool.

    ``contains`` are substrings that must all appear in the joined argv for the
    rule to apply; the first matching rule wins, and a tool with no matching
    rule succeeds silently and prints nothing.
    """

    contains: tuple[str, ...] = ()
    exit: int = 0
    stdout: str = ""
    create: tuple[str, ...] = ()


@dataclass
class StepResult:
    returncode: int
    stdout: str
    stderr: str
    calls: list[tuple[str, str]] = field(default_factory=list)

    def called(self, tool: str, *needles: str) -> list[str]:
        """Calls to ``tool`` whose joined argv contains every needle."""
        found = []
        for name, argv in self.calls:
            if name == tool and all(needle in argv for needle in needles):
                found.append(argv)
        return found


def _bash_quote(text: str) -> str:
    return "'" + text.replace("'", "'\\''") + "'"


def _case_pattern(part: str) -> str:
    escaped = part.replace("\\", "\\\\").replace('"', '\\"')
    return f'*"{escaped}"*'


def stub_preamble(stubs: dict[str, list[Stub]], log: Path) -> str:
    """Bash functions that shadow the named tools and record every call."""
    lines = [
        "# --- workflow_harness stub tools (M1) ---",
        f"STUB_LOG={_bash_quote(str(log))}",
        ": > \"$STUB_LOG\"",
    ]
    for tool, rules in stubs.items():
        lines.append(f"{tool}() {{")
        lines.append(f"  printf '%s\\t%s\\n' {_bash_quote(tool)} \"$*\" >> \"$STUB_LOG\"")
        if rules:
            lines.append('  case "$*" in')
            for rule in rules:
                pattern = "".join(_case_pattern(part) for part in rule.contains) or "*"
                lines.append(f"    {pattern})")
                for path in rule.create:
                    lines.append(
                        f"      mkdir -p \"$(dirname {_bash_quote(path)})\""
                    )
                    lines.append(f"      : > {_bash_quote(path)}")
                if rule.stdout:
                    lines.append(f"      printf '%s\\n' {_bash_quote(rule.stdout)}")
                lines.append(f"      return {rule.exit} ;;")
            lines.append("  esac")
        lines.append("  return 0")
        lines.append("}")
    lines.append("# --- end harness stubs ---")
    return "\n".join(lines)


def run_step(
    step: dict,
    context: dict,
    *,
    stubs: dict[str, list[Stub]] | None = None,
    env: dict | None = None,
    cwd: Path | str | None = None,
    timeout: int = 60,
) -> StepResult:
    """Render and run a step's ``run:`` body under ``bash -e``.

    ``cwd`` defaults to a fresh temporary directory so a step can write files
    (release notes, a manifest, a checksum file) without touching the checkout.
    """
    body = step.get("run")
    if body is None:
        raise ValueError("only run: steps can be executed; this one has no run: body")

    with tempfile.TemporaryDirectory(prefix="besa-step-") as workspace:
        workdir = Path(cwd) if cwd is not None else Path(workspace)
        workdir.mkdir(parents=True, exist_ok=True)
        log = Path(workspace) / "calls.tsv"
        script = Path(workspace) / "step.sh"
        text = stub_preamble(stubs or {}, log) + "\n" + render(body, context) + "\n"
        script.write_text(text, encoding="utf-8", newline="\n")

        environment = runner_environment(context, step, env)
        environment["GITHUB_STEP_SUMMARY"] = str(Path(workspace) / "summary.md")
        environment.setdefault("RUNNER_TEMP", str(Path(workspace) / "runner"))
        Path(environment["RUNNER_TEMP"]).mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            [bash_executable(), "-e", str(script)],
            capture_output=True,
            text=True,
            env=environment,
            cwd=str(workdir),
            timeout=timeout,
        )
        calls: list[tuple[str, str]] = []
        if log.is_file():
            for line in log.read_text(encoding="utf-8").splitlines():
                if "\t" in line:
                    tool, argv = line.split("\t", 1)
                    calls.append((tool, argv))
        return StepResult(result.returncode, result.stdout, result.stderr, calls)
