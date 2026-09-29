"""Shared test helpers. Not collected as a test module (no ``test`` prefix)."""

from __future__ import annotations

import ssl
from pathlib import Path


def real_ca_bundle() -> str | None:
    """Path to a genuine CA bundle on this machine, or None.

    Tests must not hardcode a macOS-only path such as ``/etc/ssl/cert.pem``:
    Ubuntu keeps its roots elsewhere. Ask OpenSSL where it looks, then fall back
    to the common locations.
    """
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
