"""Shared test helpers. Not collected as a test module (no ``test`` prefix)."""

from __future__ import annotations

import ssl
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
