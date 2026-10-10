"""The single outbound HTTP client used for explorer, price and fee requests.

Three guarantees, each of which was previously missing or silently ineffective:

1. **TLS verification stays on.** A certificate failure raises; it is never
   accepted.
2. **Redirects are refused.** ``urllib`` follows 30x responses by default, which
   let a server move an explorer request to a different host — or downgrade an
   HTTPS request to plaintext HTTP — without the user's consent. That silently
   defeated the "custom servers require HTTPS" rule and could expose derived
   wallet addresses to a network observer. Every configured endpoint is an
   Esplora API base that never legitimately redirects, so a redirect is a failure.
3. **The trust store the app ships is the one it actually uses.** A frozen app
   sets its bundled CA store in ``main()``, which runs *after* modules are
   imported. ``urllib``'s ``HTTPSHandler`` builds its ``SSLContext`` eagerly when
   it is constructed, so an opener created at import time captures the host's
   ambient trust configuration and silently ignores the bundle — which made every
   HTTPS request depend on the machine the app happened to run on. The opener is
   therefore built on first use, and the configured bundle is loaded explicitly.
4. **A request has a total deadline, not a per-socket timeout.** Passing a
   ``timeout`` to ``urllib`` arms the *socket*, so every ``recv`` may take that
   long again: a server that sends one byte just inside the timeout holds the
   connection open indefinitely while the app waits. :class:`Deadline` measures
   the whole call on a monotonic clock, :func:`open_url` arms the connect with
   what is left of it, and :func:`read_bounded` re-arms the socket before every
   read and refuses to read past it.

Callers import :func:`open_url`; ``wallet_service``, ``gui`` and
``network_settings`` bind it to the name ``urlopen`` so every existing call site
and test patch target keeps working.
"""

from __future__ import annotations

import os
import ssl
import threading
import time
from http.client import HTTPMessage
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import (
    HTTPRedirectHandler, HTTPSHandler, OpenerDirector, build_opener,
)


class RedirectRefused(Exception):
    """A server tried to redirect a request that must stay on its verified host."""


class Deadline:
    """The total wall-clock budget for one outbound request.

    ``time.monotonic`` cannot go backwards when the system clock is set, which
    matters for a guarantee that must hold while a user is sending money.
    """

    def __init__(self, seconds: float):
        self.total = float(seconds)
        self._end = time.monotonic() + self.total

    def remaining(self) -> float:
        """Seconds left, or a value <= 0 once the budget is spent."""
        return self._end - time.monotonic()

    def expired(self) -> bool:
        return self.remaining() <= 0


def _socket_of(response):
    """The socket under a urllib response (or an HTTPError), if it can be found.

    Re-arming the socket timeout only works if this lookup succeeds, so every
    caller treats ``None`` as "no per-read re-arming available" rather than as an
    error: the deadline checks still bound the loop.
    """
    node = response
    for _ in range(3):
        raw = getattr(getattr(node, "fp", None), "raw", None)
        sock = getattr(raw, "_sock", None)
        if sock is not None:
            return sock
        node = getattr(node, "fp", None)
        if node is None:
            break
    return None


def _read_once(response, amount: int) -> bytes:
    """One underlying read, so the caller can re-check the clock in between.

    ``read1`` returns after a single socket read where it exists (the stdlib's
    ``HTTPResponse`` has it); ``read`` is the fallback for simple stand-ins.
    """
    reader = getattr(response, "read1", None)
    if reader is None:
        return response.read(amount)
    return reader(amount)


def read_bounded(response, limit: int, deadline: Deadline | None = None,
                 *, chunk: int = 65536) -> bytes:
    """Read at most ``limit + 1`` bytes without outliving ``deadline``.

    The caller keeps its own "is this response too large" check on the returned
    length. One extra byte is read so an over-large body is detectable rather
    than silently truncated. Without a deadline this is a plain bounded read.
    """
    if deadline is None:
        return response.read(limit + 1)
    sock = _socket_of(response)
    body = bytearray()
    while len(body) <= limit:
        remaining = deadline.remaining()
        if remaining <= 0:
            _close_quietly(response)
            raise TimeoutError(
                f"The request exceeded its {deadline.total:g}-second deadline.")
        if sock is not None:
            # Re-armed every pass: the timeout bounds *this* read, and the loop
            # condition above bounds the whole call.
            try:
                sock.settimeout(remaining)
            except OSError:
                # The connection can already be at EOF (urllib closes the
                # socket under us), so re-arming the timeout is best
                # effort: the deadline check above still bounds the call.
                sock = None
        piece = _read_once_or_deadline(response, min(chunk, limit + 1 - len(body)),
                                       deadline)
        if not piece:
            break
        body += piece
    return bytes(body)


def _read_once_or_deadline(response, amount: int, deadline: Deadline) -> bytes:
    """One read, with a socket-level timeout reported as a deadline overrun.

    The socket timeout is re-armed to whatever is left of the budget, so when
    less than one inter-byte gap remains it can fire first. Callers only need to
    know the budget was spent, not which of the two clocks noticed.
    """
    try:
        return _read_once(response, amount)
    except TimeoutError as exc:
        _close_quietly(response)
        raise TimeoutError(
            f"The request exceeded its {deadline.total:g}-second deadline.") from exc


def _close_quietly(response) -> None:
    try:
        response.close()
    except Exception:  # noqa: BLE001 - the deadline error is the one that matters
        pass


class _RefuseRedirects(HTTPRedirectHandler):
    """Reject every 3xx instead of following it.

    ``handler_order`` is below the default 500 so this runs before urllib's own
    redirect handler. ``build_opener`` also recognises it as a subclass of the
    default handler and does not add the permissive one alongside it.
    """

    handler_order = 100

    def _refuse(self, req, fp, code, msg, headers: HTTPMessage):
        location = headers.get("Location") if headers is not None else None
        raise HTTPError(
            req.full_url, code,
            f"Refused redirect to {location!r}: explorer and fee requests must "
            "not change host or drop HTTPS.",
            headers, fp,
        )

    http_error_300 = _refuse
    http_error_301 = _refuse
    http_error_302 = _refuse
    http_error_303 = _refuse
    http_error_305 = _refuse
    http_error_307 = _refuse
    http_error_308 = _refuse


_bundle: str | None = None
_client: OpenerDirector | None = None
_lock = threading.Lock()


def set_trust_bundle(path) -> None:
    """Trust this CA bundle, in addition to the platform defaults.

    The packaged app calls this with its bundled certifi store. Any cached opener
    is dropped so the bundle takes effect immediately.
    """
    global _bundle, _client
    candidate = Path(path)
    with _lock:
        _bundle = str(candidate) if candidate.is_file() else None
        _client = None


def trust_bundle() -> str | None:
    """The CA bundle this client will load, if one is configured and present.

    Existence is re-checked on every call: a configured path can disappear (a
    temp file, an ejected volume), and a stale path must degrade to the platform
    defaults rather than break every request.
    """
    if _bundle and Path(_bundle).is_file():
        return _bundle
    from_env = os.environ.get("SSL_CERT_FILE")
    return from_env if from_env and Path(from_env).is_file() else None


def _ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    bundle = trust_bundle()
    if bundle:
        # Load the app's own store explicitly, so trust does not depend on the
        # host's OpenSSL defaults being present or correct.
        try:
            context.load_verify_locations(cafile=bundle)
        except (OSError, ssl.SSLError):
            # An unreadable bundle must not turn into a crash; the request will
            # fail later with a clear certificate error instead.
            pass
    return context


def loaded_ca_count() -> int:
    """How many CA certificates this client will actually trust.

    Zero means every HTTPS request must fail. The packaged app asserts this is
    non-zero, so a missing trust store can never ship unnoticed again — the
    earlier build passed its own network self-check on the build machine while
    being unable to verify any certificate on the user's machine.
    """
    try:
        return len(_ssl_context().get_ca_certs())
    except Exception:  # noqa: BLE001 - a diagnostic, never fatal by itself
        return 0


def _opener() -> OpenerDirector:
    global _client
    with _lock:
        if _client is None:
            # Passing the handler instance also stops build_opener from adding its
            # own HTTPSHandler, whose context would be built eagerly.
            _client = build_opener(
                HTTPSHandler(context=_ssl_context()), _RefuseRedirects()
            )
        return _client


def open_url(request, timeout: float, *, deadline: Deadline | None = None):
    """Open an http(s) request without following redirects or skipping TLS checks.

    With a ``deadline``, the connect is armed with whatever is left of the total
    budget (never more than ``timeout``) and the read is left to
    :func:`read_bounded`.
    """
    if deadline is not None:
        remaining = deadline.remaining()
        if remaining <= 0:
            raise TimeoutError(
                f"The request exceeded its {deadline.total:g}-second deadline.")
        timeout = min(timeout, remaining)
    response = _opener().open(request, timeout=timeout)
    final = response.geturl()
    if final != request.full_url:
        response.close()
        raise HTTPError(
            request.full_url, 0,
            "Server changed the request URL; the response was discarded.",
            None, None,
        )
    return response
