"""No real wallet, explorer, or broadcast calls in network settings tests."""

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from network_config import NETWORKS
from network_settings import (
    SettingsError, default_servers, load_servers, save_servers,
    validate_esplora_url, verify_esplora,
)


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "settings.json"
        path_patch = patch("network_settings.settings_path", return_value=self.path)
        path_patch.start()
        self.addCleanup(path_patch.stop)

    def test_default_persistence_and_invalid_electrum_url(self):
        self.assertEqual(load_servers(), default_servers())
        servers = default_servers()
        servers["main"]["explorer"] = "https://explorer.btc21.cc/api"
        save_servers(servers)
        self.assertEqual(load_servers(), servers)
        self.assertNotIn("address", self.path.read_text())
        for url in ("https://electrum.btc21.cc/", "http://remote.example/api",
                    "https://name:password@example.org/api"):
            with self.subTest(url=url), self.assertRaises(SettingsError):
                validate_esplora_url(url)
        self.assertEqual(validate_esplora_url("http://127.0.0.1:3000/api/"),
                         "http://127.0.0.1:3000/api")

    def test_custom_endpoint_must_return_selected_chain_genesis(self):
        class Response(io.BytesIO):
            length = 64
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                self.close()
        for chain in NETWORKS:
            with self.subTest(chain=chain), patch(
                "network_settings.urlopen",
                return_value=Response(NETWORKS[chain].genesis_hash.encode()),
            ) as fetch:
                verify_esplora(chain, "https://custom.example/api")
                self.assertEqual(fetch.call_args.args[0].full_url,
                                 "https://custom.example/api/block-height/0")
            other = "main" if chain == "testnet4" else "testnet4"
            with patch("network_settings.urlopen",
                       return_value=Response(NETWORKS[other].genesis_hash.encode())):
                with self.assertRaisesRegex(SettingsError, "wrong Bitcoin network"):
                    verify_esplora(chain, "https://custom.example/api")

    def test_corrupt_settings_do_not_silently_switch_to_public_defaults(self):
        self.path.write_text('{"version": 1, "servers": []}')
        with self.assertRaises(SettingsError):
            load_servers()


if __name__ == "__main__":
    unittest.main()