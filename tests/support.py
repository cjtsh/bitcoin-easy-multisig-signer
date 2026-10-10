"""Shared test helpers. Not collected as a test module (no ``test`` prefix).

Windows portability rules live here so every future build (0.6.6, 0.7.x, 1.x)
reuses one implementation instead of rediscovering three Windows quirks:

1. ``subprocess.run(["bash", "-c", "<multiline>"])`` is unreliable from Windows
   Python — CreateProcess quoting mangles newlines and the failure is a bare
   exit 1 with empty stderr. Write the script to a file and run that instead.
2. Python's default text mode writes CRLF on Windows. ``bash -n`` rejects those
   as a syntax error, so every script we hand to bash must be written with LF.
3. ``os.chmod(0o600)`` is not a permission on Windows — ``st_mode`` always
   reports 0666. Privacy there is the profile-directory ACL; ask
   ``gui.assert_private_file`` which already encodes both rules.

The Windows runner also ships Git Bash at a known path that may not be the
``bash`` on PATH. ``bash_executable`` finds one that actually works.
"""

from __future__ import annotations

import os
import ssl
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def real_ca_bundle() -> str | None:
    """Path to a genuine CA bundle on this machine, or None.

    Tests must not hardcode a macOS-only path such as ``/etc/ssl/cert.pem``:
    Ubuntu keeps its roots elsewhere. certifi comes first because it is pinned in
    ``requirements-ci.txt`` for exactly this purpose and Windows has no default
    OpenSSL verify path; without it these tests would report a skip, and both
    build workflows refuse a suite that skips at all. Then ask OpenSSL where it
    looks, then the common locations.
    """
    try:
        import certifi
    except ImportError:
        pass
    else:
        if Path(certifi.where()).is_file():
            return certifi.where()
    paths = ssl.get_default_verify_paths()
    for candidate in (
        paths.cafile,
        paths.openssl_cafile,
        "/etc/ssl/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
    ):
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def bash_executable() -> str:
    """A bash that can actually run scripts on this machine.

    Windows runners put Git Bash on PATH eventually, but a stub or a WSL
    launcher can shadow it and return exit 1 with no output. Probe the known
    Git locations first on Windows.
    """
    if sys.platform != "win32":
        return "bash"
    for candidate in (
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ):
        if Path(candidate).is_file():
            return candidate
    import shutil
    return shutil.which("bash") or "bash"


def write_lf_script(body: str, *, suffix: str = ".sh") -> Path:
    """Write ``body`` to a temp file with Unix newlines and return the path.

    CRLF is a bash syntax error; Windows text mode produces CRLF by default.
    """
    fd, name = tempfile.mkstemp(suffix=suffix)
    path = Path(name)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
        if not body.endswith("\n"):
            handle.write("\n")
    return path


def bash_syntax_check(body: str) -> subprocess.CompletedProcess:
    """``bash -n`` a script body without executing it."""
    path = write_lf_script(body)
    try:
        return subprocess.run(
            [bash_executable(), "-n", str(path)],
            capture_output=True,
            text=True,
        )
    finally:
        path.unlink(missing_ok=True)


def run_bash_script(
    body: str,
    *,
    args: tuple[str, ...] = (),
    env: dict | None = None,
    cwd: Path | str | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess:
    """Run a bash script body reliably on every platform.

    Always goes through a file (see ``write_lf_script``) rather than
    ``bash -c`` so Windows cannot mangle the script text.
    """
    path = write_lf_script(body)
    try:
        return subprocess.run(
            [bash_executable(), str(path), *args],
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd,
            timeout=timeout,
        )
    finally:
        path.unlink(missing_ok=True)


def run_bash_file(
    script: Path | str,
    *args: str,
    env: dict | None = None,
    cwd: Path | str | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess:
    """Run an existing repo shell script (e.g. scripts/notary-args.sh)."""
    return subprocess.run(
        [bash_executable(), str(script), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
        timeout=timeout,
    )


def find_build_recipe(root: Path, name: str) -> Path | None:
    """Locate a build recipe in the checkout or in a source archive.

    A checkout keeps them under ``.github/workflows/``. ``scripts/build-source.sh``
    ships the same three under ``ci/``, because a source tarball is a source
    tree and has no GitHub workflow directory. Every pin that reads a recipe
    must go through this helper: the 0.6.6 source-archive job found
    ``PipToolsPinTests`` looking only at ``.github/workflows/``, and the 0.6.7
    job found ``ToolchainPinTests`` making the same mistake. One resolver, one
    place to get it right.
    """
    for candidate in (root / ".github" / "workflows" / name, root / "ci" / name):
        if candidate.is_file():
            return candidate
    return None


def assert_private_file(test: unittest.TestCase, path: Path) -> None:
    """Assert a file the app wrote is private, using the app's own rule.

    On POSIX that is mode 0600. On Windows it is "inside this user's profile".
    Importing ``gui.assert_private_file`` keeps one definition of the rule.
    """
    import gui
    try:
        gui.assert_private_file(Path(path))
    except RuntimeError as exc:
        test.fail(str(exc))


def missing_test_reason(name: str, loader: unittest.TestLoader | None = None):
    """Why ``module.Class[.method]`` names no test, or ``None`` when it does.

    ``unittest``'s own loader is not an existence check: asked for a name that
    does not exist it hands back a one-case placeholder that fails only when it
    is run, so ``loader.loadTestsFromName("test_x.NoSuchClass").countTestCases()``
    is ``1``. A tripwire built on that number stays green for a citation whose
    class was renamed or whose method was deleted — the whole failure mode the
    tripwire exists to catch. It was found the hard way: the 0.6.8
    break-and-watch run reported ``MISSED  a ledger row cites a closing test
    that cannot be loaded`` against a check that used exactly this count.

    Resolve the name by hand instead, and refuse anything that is not a
    ``TestCase`` subclass or a ``test_*`` method on one.
    """
    import importlib

    module_name, _, rest = name.partition(".")
    try:
        obj = importlib.import_module(module_name)
    except Exception as error:  # noqa: BLE001 - report whatever the import raised
        return "%s cannot be imported: %s: %s" % (
            module_name, type(error).__name__, error)
    if not rest:
        # A bare module citation: the module imports, so it can be collected.
        return None
    parent = None
    for part in rest.split("."):
        parent, obj = obj, getattr(obj, part, None)
        if obj is None:
            return "%s names no attribute %r" % (name, part)
    if isinstance(obj, type):
        if not issubclass(obj, unittest.TestCase):
            return "%s is not a TestCase" % name
        loader = loader or unittest.TestLoader()
        if loader.loadTestsFromTestCase(obj).countTestCases() == 0:
            return "%s holds no tests" % name
        return None
    if not callable(obj) or not getattr(obj, "__name__", "").startswith("test"):
        return "%s is not a test method" % name
    if not (isinstance(parent, type) and issubclass(parent, unittest.TestCase)):
        return "%s is not a method of a TestCase" % name
    return None
