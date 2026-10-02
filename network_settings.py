"""Optional, local-only Esplora server preferences. Never store wallet data."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request

from safe_http import open_url as urlopen  # TLS-verified, never follows a redirect

from network_config import NETWORKS
from version import APP_VERSION


class SettingsError(Exception):
    pass


def settings_path() -> Path:
    """The operator's own per-user configuration file, on each platform.

    Every location is inside the user's profile: macOS and Windows both protect
    those directories with a per-user access list, and the POSIX fallback is
    created 0700. Server preferences are not wallet data, but they are still the
    operator's own.
    """
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/Easy Bitcoin Multisig/settings.json"
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
        return Path(base) / "Easy Bitcoin Multisig" / "settings.json"
    return Path.home() / ".config/easy-bitcoin-multisig/settings.json"


def default_servers() -> dict:
    return {
        chain: {"explorer": config.explorer_url, "broadcaster": config.explorer_url}
        for chain, config in NETWORKS.items()
    }


def validate_esplora_url(value: str) -> str:
    """Accept HTTPS Esplora API bases; allow plain HTTP only on loopback."""
    if not isinstance(value, str) or not 1 <= len(value) <= 300:
        raise SettingsError("Enter an Esplora API base URL, such as https://example.com/api.")
    if value != value.strip() or any(c.isspace() or ord(c) < 32 for c in value):
        raise SettingsError("Server URLs cannot contain spaces or control characters.")
    try:
        parsed = urlsplit(value)
        port = parsed.port  # Force validation of an invalid port.
    except ValueError as exc:
        raise SettingsError("Server URL or port is invalid.") from exc
    host = parsed.hostname
    if (parsed.scheme not in ("https", "http") or not host
        or parsed.username or parsed.password or parsed.query or parsed.fragment
        or "%" in parsed.path or ".." in parsed.path or "\\" in value):
        raise SettingsError("Use a plain Esplora URL without credentials, query, or fragment.")
    if parsed.scheme == "http" and host not in ("localhost", "127.0.0.1", "::1"):
        raise SettingsError("Custom remote servers require HTTPS; HTTP is loopback-only.")
    if not parsed.path.rstrip("/").endswith("/api"):
        raise SettingsError("Use the Esplora API base ending in /api, not an Electrum server or website.")
    return value.rstrip("/")


def load_servers() -> dict:
    path = settings_path()
    try:
        if not path.exists():
            return default_servers()
        if path.stat().st_size > 8192:
            raise SettingsError("Saved server settings are unexpectedly large.")
        data = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or data.get("version") != 1
            or not isinstance(data.get("servers"), dict)
            or not {"main", "testnet4"}.issubset(data["servers"])
            or not set(data["servers"]).issubset(NETWORKS)):
            raise SettingsError("Saved server settings have an unsupported format.")
        return {
            chain: ({
                key: validate_esplora_url(data["servers"][chain][key])
                for key in ("explorer", "broadcaster")
            } if chain in data["servers"] else default_servers()[chain])
            for chain in NETWORKS
        }
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        raise SettingsError("Could not read saved server settings. Reset them in Advanced settings.") from exc


def save_servers(servers: dict) -> None:
    validated = {
        chain: {key: validate_esplora_url(servers[chain][key])
                for key in ("explorer", "broadcaster")}
        for chain in NETWORKS
    }
    path = settings_path()
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix=".settings-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                json.dump({"version": 1, "servers": validated}, output)
                output.write("\n")
            os.chmod(temp_path, 0o600)
            os.replace(temp_path, path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except OSError as exc:
        raise SettingsError("Could not save server settings on this computer.") from exc


def verify_esplora(chain: str, base_url: str) -> None:
    """Check genesis and any chain-specific checkpoint before trusting a server."""
    if chain not in NETWORKS:
        raise SettingsError("Unsupported Bitcoin network.")
    base = validate_esplora_url(base_url)
    try:
        config = NETWORKS[chain]
        points = [(0, config.genesis_hash)]
        if config.checkpoint_height is not None:
            points.append((config.checkpoint_height, config.checkpoint_hash))
        for height, expected in points:
            request = Request(
                base + f"/block-height/{height}",
                headers={"User-Agent": f"EasyMultisig/{APP_VERSION}", "Accept": "text/plain"},
            )
            with urlopen(request, timeout=8) as response:
                if response.length is not None and response.length > 80:
                    raise SettingsError("Explorer returned an invalid block hash.")
                body = response.read(81)
            found = body.decode("ascii").strip().lower()
            if not re.fullmatch(r"[0-9a-f]{64}", found):
                raise SettingsError("Explorer did not return an Esplora block hash.")
            if found != expected:
                raise SettingsError("Explorer is on the wrong Bitcoin network; settings were not changed.")
    except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError) as exc:
        raise SettingsError(
            "Could not verify this Esplora server's network. Check its /api URL and availability."
        ) from exc
