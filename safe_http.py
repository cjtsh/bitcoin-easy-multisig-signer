"""The single outbound HTTP client used for explorer, price and fee requests.

Two guarantees, because both were previously missing:

1. **TLS verification stays on.** The default context is used, so a certificate
   failure raises instead of being silently accepted.
2. **Redirects are refused.** ``urllib`` follows 30x responses by default, which
   let a server move an explorer request to a different host — or downgrade an
   HTTPS request to plaintext HTTP — without the user's consent. That silently
   defeated the "custom servers require HTTPS" rule and could expose derived
   wallet addresses to a network observer. Every configured endpoint is an
   Esplora API base that never legitimately redirects, so a redirect is treated
   as a failure.

Callers import :func:`open_url`; ``wallet_service``, ``gui`` and
``network_settings`` bind it to the name ``urlopen`` so every existing call site
and test patch target keeps working.
"""

from __future__ import annotations

from http.client import HTTPMessage
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, build_opener


class RedirectRefused(Exception):
    """A server tried to redirect a request that must stay on its verified host."""


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


OPENER = build_opener(_RefuseRedirects())


def open_url(request, timeout: float):
    """Open an http(s) request without following redirects or skipping TLS checks."""
    response = OPENER.open(request, timeout=timeout)
    final = response.geturl()
    if final != request.full_url:
        response.close()
        raise HTTPError(
            request.full_url, 0,
            "Server changed the request URL; the response was discarded.",
            None, None,
        )
    return response
